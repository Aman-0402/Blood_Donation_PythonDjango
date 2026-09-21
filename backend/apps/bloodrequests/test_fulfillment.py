import threading

from django.core.exceptions import ValidationError
from django.db import connection
from django.test import TestCase, TransactionTestCase
from rest_framework.test import APIClient

from apps.accounts.models import Role
from apps.inventory.models import BloodInventory, InventoryTransaction
from apps.testing import blood_group, make_bloodbank, make_inventory, make_user

from . import fulfillment
from .models import BloodRequest

Status = BloodRequest.Status


def client_for(user):
    client = APIClient()
    client.force_authenticate(user)
    return client


def verified_bank(**kwargs):
    return make_bloodbank(user=make_user(Role.BLOODBANK, is_verified=True), **kwargs)


def approved_request(group='A+', units=3, **kwargs):
    requester = kwargs.pop('requester', None) or make_user(Role.SEEKER)
    data = dict(requester=requester, patient_name='Secret Patient', contact_phone='555-0100',
                notes='private note', blood_group=blood_group(group), units_required=units,
                location='City Hospital', status=Status.APPROVED)
    data.update(kwargs)
    return BloodRequest.objects.create(**data)


class BankRequestVisibilityTests(TestCase):
    def setUp(self):
        self.bank = verified_bank()
        self.other_bank = verified_bank()
        self.client = client_for(self.bank.user)
        self.open = approved_request()
        self.pending = approved_request(status=Status.PENDING)
        self.mine = approved_request(status=Status.MATCHED, fulfilled_by_bloodbank=self.bank)
        self.theirs = approved_request(status=Status.MATCHED, fulfilled_by_bloodbank=self.other_bank)

    def ids(self, query=''):
        return {r['id'] for r in self.client.get(f'/api/requests/{query}').json()['results']}

    def test_sees_open_approved_and_own_only(self):
        self.assertEqual(self.ids(), {self.open.id, self.mine.id})

    def test_cannot_open_pending_or_other_banks_requests(self):
        self.assertEqual(self.client.get(f'/api/requests/{self.pending.id}/').status_code, 404)
        self.assertEqual(self.client.get(f'/api/requests/{self.theirs.id}/').status_code, 404)

    def test_personal_details_hidden_until_the_bank_owns_the_request(self):
        open_body = self.client.get(f'/api/requests/{self.open.id}/').json()
        for field in ('patient_name', 'contact_phone', 'notes', 'requester', 'requester_username'):
            self.assertNotIn(field, open_body)
        self.assertEqual(open_body['blood_group_name'], 'A+')
        mine_body = self.client.get(f'/api/requests/{self.mine.id}/').json()
        self.assertEqual(mine_body['patient_name'], 'Secret Patient')
        self.assertEqual(mine_body['contact_phone'], '555-0100')

    def test_banks_cannot_use_requester_only_endpoints(self):
        for method, url in (
            ('post', f'/api/requests/{self.mine.id}/cancel/'),
            ('get', f'/api/requests/{self.mine.id}/history/'),
            ('post', f'/api/requests/{self.mine.id}/status/'),
            ('post', '/api/requests/'),
        ):
            with self.subTest(url=url):
                self.assertEqual(getattr(self.client, method)(url, {}, format='json').status_code, 403)

    def test_unverified_bank_is_blocked(self):
        unverified = make_bloodbank()
        client = client_for(unverified.user)
        self.assertEqual(client.get('/api/requests/').status_code, 403)
        self.assertEqual(client.post(f'/api/requests/{self.open.id}/accept/').status_code, 403)

    def test_other_roles_cannot_use_bank_actions(self):
        for role in (Role.SEEKER, Role.HOSPITAL, Role.DONOR, Role.ADMIN):
            client = client_for(make_user(role))
            for action in ('accept', 'release', 'dispatch', 'complete'):
                with self.subTest(role=role, action=action):
                    self.assertEqual(client.post(f'/api/requests/{self.open.id}/{action}/').status_code, 403)


class FulfilmentFlowTests(TestCase):
    def setUp(self):
        self.bank = verified_bank()
        self.client = client_for(self.bank.user)
        self.request = approved_request('A+', units=5)
        self.old = make_inventory(self.bank, 'A+', units=3, days_to_expiry=4)
        self.new = make_inventory(self.bank, 'A+', units=4, days_to_expiry=25)

    def act(self, action, request=None):
        return self.client.post(f'/api/requests/{(request or self.request).id}/{action}/')

    def test_full_lifecycle(self):
        response = self.act('accept')
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual((response.json()['status'], response.json()['fulfilled_by_bloodbank']), ('matched', self.bank.id))
        self.assertEqual(response.json()['patient_name'], 'Secret Patient')
        self.assertEqual(BloodInventory.objects.get(pk=self.old.pk).units, 3)  # accepting does not move stock

        response = self.act('dispatch')
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.json()['status'], 'processing')
        self.old.refresh_from_db()
        self.new.refresh_from_db()
        self.assertEqual((self.old.units, self.old.status), (0, BloodInventory.Status.ISSUED))
        self.assertEqual((self.new.units, self.new.status), (2, BloodInventory.Status.AVAILABLE))
        ledger = list(InventoryTransaction.objects.filter(type='issue').order_by('id').values_list('request_id', 'units'))
        self.assertEqual(ledger, [(self.request.id, -3), (self.request.id, -2)])

        response = self.act('complete')
        self.assertEqual((response.status_code, response.json()['status']), (200, 'completed'))
        trail = list(self.request.history.values_list('from_status', 'to_status'))
        self.assertEqual(trail, [('approved', 'matched'), ('matched', 'processing'), ('processing', 'completed')])

    def test_accept_needs_enough_stock(self):
        big = approved_request('A+', units=9)
        response = self.act('accept', big)
        self.assertEqual(response.status_code, 400)
        big.refresh_from_db()
        self.assertEqual((big.status, big.fulfilled_by_bloodbank), (Status.APPROVED, None))

    def test_accept_ignores_expired_stock(self):
        BloodInventory.objects.filter(pk=self.new.pk).update(status=BloodInventory.Status.EXPIRED)
        self.assertEqual(self.act('accept').status_code, 400)  # only 3 usable, 5 needed

    def test_cannot_accept_twice_or_when_not_approved(self):
        self.act('accept')
        self.assertEqual(self.act('accept').status_code, 400)
        pending = approved_request(status=Status.PENDING)
        # pending requests are invisible to banks entirely
        self.assertEqual(self.act('accept', pending).status_code, 404)

    def test_dispatch_requires_matched_and_own(self):
        self.assertEqual(self.act('dispatch').status_code, 400)  # still approved
        self.act('accept')
        rival = verified_bank()
        make_inventory(rival, 'A+', units=10)
        rival_client = client_for(rival.user)
        self.assertEqual(rival_client.post(f'/api/requests/{self.request.id}/dispatch/').status_code, 404)

    def test_dispatch_is_all_or_nothing_when_stock_vanished(self):
        self.act('accept')
        BloodInventory.objects.filter(pk=self.new.pk).update(units=0, status=BloodInventory.Status.ISSUED)
        response = self.act('dispatch')
        self.assertEqual(response.status_code, 400)
        self.request.refresh_from_db()
        self.assertEqual(self.request.status, Status.MATCHED)
        self.old.refresh_from_db()
        self.assertEqual(self.old.units, 3)
        self.assertFalse(InventoryTransaction.objects.filter(type='issue').exists())

    def test_complete_requires_processing(self):
        self.act('accept')
        self.assertEqual(self.act('complete').status_code, 400)

    def test_release_returns_request_to_the_pool(self):
        self.act('accept')
        response = self.act('release')
        self.assertEqual((response.status_code, response.json()['status']), (200, 'approved'))
        self.request.refresh_from_db()
        self.assertIsNone(self.request.fulfilled_by_bloodbank)
        other = verified_bank()
        make_inventory(other, 'A+', units=10)
        self.assertEqual(client_for(other.user).post(f'/api/requests/{self.request.id}/accept/').status_code, 200)

    def test_cannot_release_after_dispatch_or_someone_elses(self):
        self.act('accept')
        self.act('dispatch')
        self.assertEqual(self.act('release').status_code, 400)

    def test_requester_can_still_cancel_while_matched_but_bank_then_loses_it(self):
        self.act('accept')
        owner = client_for(self.request.requester)
        self.assertEqual(owner.post(f'/api/requests/{self.request.id}/cancel/').status_code, 200)
        self.assertEqual(self.act('dispatch').status_code, 400)
        self.assertFalse(InventoryTransaction.objects.filter(type='issue').exists())

    def test_requester_sees_progress_and_fulfilling_bank_name(self):
        self.act('accept')
        body = client_for(self.request.requester).get(f'/api/requests/{self.request.id}/').json()
        self.assertEqual((body['status'], body['fulfilled_by_bloodbank_name']), ('matched', self.bank.name))


class ConcurrentAcceptTests(TransactionTestCase):
    serialized_rollback = True

    def test_only_one_bank_wins_a_request(self):
        request = approved_request('B+', units=2)
        banks = [verified_bank() for _ in range(3)]
        for bank in banks:
            make_inventory(bank, 'B+', units=5)
        results = []
        barrier = threading.Barrier(len(banks))

        def worker(bank):
            try:
                barrier.wait()
                fulfillment.accept_request(request.pk, bank, bank.user)
                results.append(bank.pk)
            except ValidationError:
                results.append(None)
            finally:
                connection.close()

        threads = [threading.Thread(target=worker, args=(b,)) for b in banks]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        winners = [r for r in results if r is not None]
        self.assertEqual(len(winners), 1, results)
        request.refresh_from_db()
        self.assertEqual(request.status, Status.MATCHED)
        self.assertEqual(request.fulfilled_by_bloodbank_id, winners[0])
        self.assertEqual(request.history.filter(to_status='matched').count(), 1)
