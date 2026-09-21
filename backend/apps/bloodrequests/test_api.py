from django.test import TestCase
from rest_framework.test import APIClient

from apps.accounts.models import Role
from apps.testing import blood_group, make_hospital, make_user

from .models import BloodRequest
from .workflow import ALLOWED_TRANSITIONS, InvalidTransition, change_status

Status = BloodRequest.Status


def payload(**overrides):
    data = {
        'patient_name': 'Patient One',
        'contact_phone': '9999999999',
        'blood_group': blood_group('B-').id,
        'units_required': 2,
        'urgency': 'urgent',
        'location': 'City Hospital, Pune',
    }
    data.update(overrides)
    return data


def client_for(user):
    client = APIClient()
    client.force_authenticate(user)
    return client


class CreateRequestTests(TestCase):
    def setUp(self):
        self.seeker = make_user(Role.SEEKER)
        self.client = client_for(self.seeker)

    def test_seeker_creates_pending_request(self):
        response = self.client.post('/api/requests/', payload(), format='json')
        self.assertEqual(response.status_code, 201)
        body = response.json()
        self.assertEqual(body['status'], 'pending')
        self.assertEqual(body['requester'], self.seeker.id)
        self.assertEqual(body['blood_group_name'], 'B-')
        self.assertEqual(body['allowed_next_statuses'], ['approved', 'cancelled', 'rejected'])
        instance = BloodRequest.objects.get()
        entry = instance.history.get()
        self.assertEqual((entry.from_status, entry.to_status, entry.changed_by), ('', 'pending', self.seeker))

    def test_server_controlled_fields_cannot_be_set(self):
        other = make_user(Role.SEEKER)
        response = self.client.post(
            '/api/requests/',
            payload(status='completed', requester=other.id, fulfilled_by_bloodbank=1, hospital=1),
            format='json',
        )
        self.assertEqual(response.status_code, 201)
        instance = BloodRequest.objects.get()
        self.assertEqual(instance.status, Status.PENDING)
        self.assertEqual(instance.requester, self.seeker)
        self.assertIsNone(instance.fulfilled_by_bloodbank)
        self.assertIsNone(instance.hospital)

    def test_validation(self):
        cases = {
            'missing patient name': payload(patient_name=''),
            'zero units': payload(units_required=0),
            'too many units': payload(units_required=101),
            'negative units': payload(units_required=-1),
            'unknown blood group': payload(blood_group=9999),
            'bad urgency': payload(urgency='whenever'),
            'missing location': {k: v for k, v in payload().items() if k != 'location'},
        }
        for name, data in cases.items():
            with self.subTest(name):
                self.assertEqual(self.client.post('/api/requests/', data, format='json').status_code, 400)
        self.assertFalse(BloodRequest.objects.exists())

    def test_only_seekers_and_hospitals_can_create(self):
        self.assertEqual(APIClient().post('/api/requests/', payload(), format='json').status_code, 401)
        for role in (Role.DONOR, Role.BLOODBANK, Role.ADMIN):
            with self.subTest(role=role):
                response = client_for(make_user(role)).post('/api/requests/', payload(), format='json')
                self.assertEqual(response.status_code, 403)

    def test_unverified_hospital_cannot_create(self):
        hospital = make_hospital()
        response = client_for(hospital.user).post('/api/requests/', payload(patient_name=''), format='json')
        self.assertEqual(response.status_code, 403)

    def test_unverified_hospital_without_profile_is_forbidden_before_validation(self):
        user = make_user(Role.HOSPITAL)
        response = client_for(user).post('/api/requests/', payload(patient_name=''), format='json')
        self.assertEqual(response.status_code, 403)

    def test_verified_hospital_without_profile_gets_clear_error(self):
        user = make_user(Role.HOSPITAL, is_verified=True)
        response = client_for(user).post('/api/requests/', payload(patient_name=''), format='json')
        self.assertEqual(response.status_code, 400)

    def test_verified_hospital_creates_request_linked_to_profile(self):
        hospital = make_hospital(user=make_user(Role.HOSPITAL, is_verified=True))
        response = client_for(hospital.user).post('/api/requests/', payload(patient_name=''), format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()['hospital'], hospital.id)
        self.assertEqual(response.json()['hospital_name'], hospital.name)


class ListAndRetrieveTests(TestCase):
    def setUp(self):
        self.alice = make_user(Role.SEEKER)
        self.bob = make_user(Role.SEEKER)
        self.admin = make_user(Role.ADMIN)

        def make(user, **kw):
            data = dict(requester=user, patient_name='P', blood_group=blood_group('A+'),
                        units_required=1, location='X')
            data.update(kw)
            return BloodRequest.objects.create(**data)

        self.a1 = make(self.alice, urgency='critical')
        self.a2 = make(self.alice, status=Status.APPROVED)
        self.b1 = make(self.bob, blood_group=blood_group('O-'))

    def ids(self, client, query=''):
        return {r['id'] for r in client.get(f'/api/requests/{query}').json()['results']}

    def test_users_only_see_their_own(self):
        self.assertEqual(self.ids(client_for(self.alice)), {self.a1.id, self.a2.id})
        self.assertEqual(self.ids(client_for(self.bob)), {self.b1.id})

    def test_admin_sees_all(self):
        self.assertEqual(self.ids(client_for(self.admin)), {self.a1.id, self.a2.id, self.b1.id})

    def test_filters(self):
        admin = client_for(self.admin)
        self.assertEqual(self.ids(admin, '?status=approved'), {self.a2.id})
        self.assertEqual(self.ids(admin, '?urgency=critical'), {self.a1.id})
        self.assertEqual(self.ids(admin, f'?blood_group={blood_group("O-").id}'), {self.b1.id})

    def test_newest_first(self):
        results = client_for(self.admin).get('/api/requests/').json()['results']
        self.assertEqual([r['id'] for r in results], [self.b1.id, self.a2.id, self.a1.id])

    def test_other_roles_forbidden(self):
        for role in (Role.DONOR, Role.BLOODBANK):
            self.assertEqual(client_for(make_user(role)).get('/api/requests/').status_code, 403)

    def test_cannot_read_someone_elses_request(self):
        self.assertEqual(client_for(self.bob).get(f'/api/requests/{self.a1.id}/').status_code, 404)
        self.assertEqual(client_for(self.alice).get(f'/api/requests/{self.a1.id}/').status_code, 200)
        self.assertEqual(client_for(self.admin).get(f'/api/requests/{self.a1.id}/').status_code, 200)

    def test_delete_not_allowed(self):
        self.assertEqual(client_for(self.alice).delete(f'/api/requests/{self.a1.id}/').status_code, 405)
        self.assertEqual(client_for(self.admin).delete(f'/api/requests/{self.a1.id}/').status_code, 405)


class UpdateRequestTests(TestCase):
    def setUp(self):
        self.owner = make_user(Role.SEEKER)
        self.client = client_for(self.owner)
        self.request = BloodRequest.objects.get(
            pk=self.client.post('/api/requests/', payload(), format='json').json()['id']
        )

    def test_owner_can_edit_pending(self):
        response = self.client.patch(
            f'/api/requests/{self.request.id}/', {'units_required': 5, 'urgency': 'critical'}, format='json'
        )
        self.assertEqual(response.status_code, 200)
        self.request.refresh_from_db()
        self.assertEqual((self.request.units_required, self.request.urgency), (5, 'critical'))

    def test_edit_validates(self):
        response = self.client.patch(f'/api/requests/{self.request.id}/', {'units_required': 0}, format='json')
        self.assertEqual(response.status_code, 400)
        response = self.client.patch(f'/api/requests/{self.request.id}/', {'patient_name': ''}, format='json')
        self.assertEqual(response.status_code, 400)

    def test_cannot_edit_after_approval(self):
        change_status(self.request.id, Status.APPROVED, make_user(Role.ADMIN))
        response = self.client.patch(f'/api/requests/{self.request.id}/', {'units_required': 5}, format='json')
        self.assertEqual(response.status_code, 400)
        self.request.refresh_from_db()
        self.assertEqual(self.request.units_required, 2)

    def test_cannot_change_status_or_owner_via_patch(self):
        other = make_user(Role.SEEKER)
        self.client.patch(
            f'/api/requests/{self.request.id}/', {'status': 'completed', 'requester': other.id}, format='json'
        )
        self.request.refresh_from_db()
        self.assertEqual(self.request.status, Status.PENDING)
        self.assertEqual(self.request.requester, self.owner)

    def test_others_cannot_edit(self):
        stranger = client_for(make_user(Role.SEEKER))
        self.assertEqual(stranger.patch(f'/api/requests/{self.request.id}/', {'units_required': 9}, format='json').status_code, 404)
        admin = client_for(make_user(Role.ADMIN))
        self.assertEqual(admin.patch(f'/api/requests/{self.request.id}/', {'units_required': 9}, format='json').status_code, 403)


class CancelRequestTests(TestCase):
    def setUp(self):
        self.owner = make_user(Role.SEEKER)
        self.admin = make_user(Role.ADMIN)
        self.request = BloodRequest.objects.create(
            requester=self.owner, patient_name='P', blood_group=blood_group('A+'),
            units_required=1, location='X',
        )

    def cancel(self, user=None):
        return client_for(user or self.owner).post(f'/api/requests/{self.request.id}/cancel/')

    def test_owner_cancels_pending_and_it_is_audited(self):
        response = self.cancel()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'cancelled')
        entry = self.request.history.last()
        self.assertEqual((entry.from_status, entry.to_status, entry.changed_by), ('pending', 'cancelled', self.owner))

    def test_owner_can_cancel_approved_and_matched(self):
        for status in (Status.APPROVED, Status.MATCHED):
            with self.subTest(status=status):
                BloodRequest.objects.filter(pk=self.request.pk).update(status=status)
                self.assertEqual(self.cancel().status_code, 200)

    def test_owner_cannot_cancel_once_processing_or_finished(self):
        for status in (Status.PROCESSING, Status.COMPLETED, Status.REJECTED, Status.CANCELLED):
            with self.subTest(status=status):
                BloodRequest.objects.filter(pk=self.request.pk).update(status=status)
                self.assertEqual(self.cancel().status_code, 400)

    def test_double_cancel_rejected(self):
        self.cancel()
        self.assertEqual(self.cancel().status_code, 400)

    def test_stranger_gets_404(self):
        self.assertEqual(self.cancel(make_user(Role.SEEKER)).status_code, 404)
        self.request.refresh_from_db()
        self.assertEqual(self.request.status, Status.PENDING)

    def test_anonymous_and_wrong_roles(self):
        self.assertEqual(APIClient().post(f'/api/requests/{self.request.id}/cancel/').status_code, 401)
        self.assertEqual(self.cancel(make_user(Role.DONOR)).status_code, 403)


class AdminWorkflowTests(TestCase):
    def setUp(self):
        self.owner = make_user(Role.SEEKER)
        self.admin = make_user(Role.ADMIN)
        self.request = BloodRequest.objects.create(
            requester=self.owner, patient_name='P', blood_group=blood_group('A+'),
            units_required=1, location='X',
        )
        self.url = f'/api/requests/{self.request.id}/status/'

    def set(self, status, user=None, **extra):
        return client_for(user or self.admin).post(self.url, {'status': status, **extra}, format='json')

    def test_full_happy_path_with_history(self):
        for status in ('approved', 'matched', 'processing', 'completed'):
            response = self.set(status, note=f'to {status}')
            self.assertEqual(response.status_code, 200, response.content)
            self.assertEqual(response.json()['status'], status)
        self.assertEqual(response.json()['allowed_next_statuses'], [])
        history = list(self.request.history.values_list('from_status', 'to_status', 'note'))
        self.assertEqual(history, [
            ('pending', 'approved', 'to approved'),
            ('approved', 'matched', 'to matched'),
            ('matched', 'processing', 'to processing'),
            ('processing', 'completed', 'to completed'),
        ])

    def test_invalid_jumps_rejected(self):
        for status in ('matched', 'processing', 'completed', 'pending'):
            with self.subTest(status=status):
                self.assertEqual(self.set(status).status_code, 400)
        self.request.refresh_from_db()
        self.assertEqual(self.request.status, Status.PENDING)
        self.assertFalse(self.request.history.exists())

    def test_unknown_status_rejected(self):
        self.assertEqual(self.set('teleported').status_code, 400)

    def test_terminal_states_are_final(self):
        self.assertEqual(self.set('rejected').status_code, 200)
        for status in ('approved', 'pending', 'cancelled'):
            self.assertEqual(self.set(status).status_code, 400)

    def test_only_admin_can_set_status(self):
        for user in (self.owner, make_user(Role.DONOR), make_user(Role.BLOODBANK), make_user(Role.HOSPITAL)):
            with self.subTest(role=user.role):
                self.assertEqual(self.set('approved', user=user).status_code, 403)
        self.assertEqual(APIClient().post(self.url, {'status': 'approved'}, format='json').status_code, 401)

    def test_history_endpoint_access(self):
        self.set('approved')
        body = client_for(self.owner).get(f'/api/requests/{self.request.id}/history/').json()
        self.assertEqual([h['to_status'] for h in body], ['approved'])
        self.assertEqual(body[0]['changed_by_username'], self.admin.username)
        self.assertEqual(client_for(self.admin).get(f'/api/requests/{self.request.id}/history/').status_code, 200)
        stranger = client_for(make_user(Role.SEEKER))
        self.assertEqual(stranger.get(f'/api/requests/{self.request.id}/history/').status_code, 404)


class WorkflowUnitTests(TestCase):
    def setUp(self):
        self.user = make_user(Role.SEEKER)
        self.request = BloodRequest.objects.create(
            requester=self.user, patient_name='P', blood_group=blood_group('A+'),
            units_required=1, location='X',
        )

    def test_every_status_has_a_transition_entry(self):
        self.assertEqual(set(ALLOWED_TRANSITIONS), set(Status))

    def test_terminal_states_have_no_exits(self):
        for status in (Status.COMPLETED, Status.CANCELLED, Status.REJECTED):
            self.assertEqual(ALLOWED_TRANSITIONS[status], set())

    def test_repeating_a_transition_fails_the_second_time(self):
        change_status(self.request.id, Status.APPROVED, self.user)
        with self.assertRaises(InvalidTransition):
            change_status(self.request.id, Status.APPROVED, self.user)
        self.assertEqual(self.request.history.count(), 1)
