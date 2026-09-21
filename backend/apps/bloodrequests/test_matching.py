from datetime import timedelta

from django.test import TestCase
from rest_framework.test import APIClient

from apps.accounts.models import Role
from apps.notifications.models import Notification
from apps.testing import blood_group, make_bloodbank, make_donor, make_hospital, make_inventory, make_user, today

from .models import BloodRequest, DonorResponse

Status = BloodRequest.Status


def client_for(user):
    client = APIClient()
    client.force_authenticate(user)
    return client


def verified_bank(**kwargs):
    return make_bloodbank(user=make_user(Role.BLOODBANK, is_verified=True), **kwargs)


def make_request(group='A+', city='Pune', status=Status.APPROVED, requester=None, **kwargs):
    data = dict(
        requester=requester or make_user(Role.SEEKER), patient_name='Secret Patient',
        contact_phone='555-0100', notes='private', blood_group=blood_group(group),
        units_required=2, city=city, location='Ward 4, City Hospital', status=status,
    )
    data.update(kwargs)
    return BloodRequest.objects.create(**data)


class RequestCityTests(TestCase):
    def payload(self, **overrides):
        data = {'patient_name': 'P', 'blood_group': blood_group('A+').id, 'units_required': 1, 'location': 'X', 'city': 'Pune'}
        data.update(overrides)
        return data

    def test_seeker_must_give_a_city_and_it_is_trimmed(self):
        client = client_for(make_user(Role.SEEKER))
        self.assertEqual(client.post('/api/requests/', self.payload(city=''), format='json').status_code, 400)
        response = client.post('/api/requests/', self.payload(city='  Pune  '), format='json')
        self.assertEqual((response.status_code, response.json()['city']), (201, 'Pune'))

    def test_hospital_city_comes_from_its_profile(self):
        hospital = make_hospital(user=make_user(Role.HOSPITAL, is_verified=True), city='Nagpur')
        response = client_for(hospital.user).post(
            '/api/requests/', self.payload(patient_name='', city='Somewhere Else'), format='json'
        )
        self.assertEqual((response.status_code, response.json()['city']), (201, 'Nagpur'))


class DonorOpenRequestsTests(TestCase):
    def setUp(self):
        self.donor = make_donor('A+', city='Pune')
        self.client = client_for(self.donor.user)

    def listing(self):
        response = self.client.get('/api/donors/me/requests/')
        self.assertEqual(response.status_code, 200, response.content)
        return response.json()['results']

    def test_only_compatible_open_requests_in_the_donors_city(self):
        ok_exact = make_request('A+')
        ok_wider = make_request('AB+')                    # A+ can give to AB+
        make_request('O+')                                # A+ cannot give to O+
        make_request('A-')                                # Rh+ cannot give to Rh-
        make_request('A+', city='Mumbai')                 # other city
        make_request('A+', status=Status.PENDING)         # not approved yet
        make_request('A+', status=Status.COMPLETED)
        make_request('A+', status=Status.CANCELLED)
        matched = make_request('B+', status=Status.MATCHED, blood_group=blood_group('AB+'))
        self.assertEqual({r['id'] for r in self.listing()}, {ok_exact.id, ok_wider.id, matched.id})

    def test_city_matching_ignores_case_and_spacing_of_the_donor_city(self):
        make_request('A+', city='PUNE')
        self.assertEqual(len(self.listing()), 1)

    def test_no_patient_or_requester_details_are_exposed(self):
        make_request('A+')
        row = self.listing()[0]
        self.assertEqual(set(row), {'id', 'blood_group_name', 'units_required', 'urgency', 'city', 'location',
                                     'hospital_name', 'status', 'created_at', 'my_response'})

    def test_most_urgent_first(self):
        normal = make_request('A+', urgency='normal')
        critical = make_request('A+', urgency='critical')
        urgent = make_request('A+', urgency='urgent')
        self.assertEqual([r['id'] for r in self.listing()], [critical.id, urgent.id, normal.id])

    def test_shows_my_previous_response(self):
        request = make_request('A+')
        DonorResponse.objects.create(request=request, donor=self.donor, answer='declined')
        self.assertEqual(self.listing()[0]['my_response'], 'declined')

    def test_donor_only_endpoint(self):
        for role in (Role.SEEKER, Role.HOSPITAL, Role.BLOODBANK, Role.ADMIN):
            self.assertEqual(client_for(make_user(role)).get('/api/donors/me/requests/').status_code, 403)
        self.assertEqual(APIClient().get('/api/donors/me/requests/').status_code, 401)
        self.assertEqual(client_for(make_user(Role.DONOR)).get('/api/donors/me/requests/').status_code, 404)

    def test_dashboard_counts_matching_requests(self):
        make_request('A+')
        make_request('O+')
        body = self.client.get('/api/donors/me/dashboard/').json()
        self.assertEqual(body['matching_requests'], 1)


class DonorRespondTests(TestCase):
    def setUp(self):
        self.donor = make_donor('O-', city='Pune', user=make_user(Role.DONOR, first_name='Ravi', last_name='K', phone='555-0177'))
        self.client = client_for(self.donor.user)
        self.request = make_request('B+')

    def respond(self, answer='accepted', request=None, client=None):
        return (client or self.client).post(
            f'/api/donors/me/requests/{(request or self.request).id}/respond/', {'answer': answer}, format='json'
        )

    def test_accept_and_decline_are_recorded(self):
        self.assertEqual(self.respond('accepted').status_code, 200)
        self.assertEqual(DonorResponse.objects.get().answer, 'accepted')

    def test_changing_your_mind_updates_the_same_row(self):
        self.respond('accepted')
        self.respond('declined')
        self.respond('accepted')
        self.assertEqual(DonorResponse.objects.count(), 1)
        self.assertEqual(DonorResponse.objects.get().answer, 'accepted')

    def test_invalid_answer(self):
        self.assertEqual(self.respond('maybe').status_code, 400)
        self.assertEqual(self.client.post(f'/api/donors/me/requests/{self.request.id}/respond/', {}, format='json').status_code, 400)

    def test_must_be_a_match(self):
        wrong_group = make_request('O+', blood_group=blood_group('O+'))
        wrong_city = make_request('B+', city='Mumbai')
        donor_a = make_donor('A+', city='Pune', user=make_user(Role.DONOR))
        for request, client in ((wrong_city, self.client), (make_request('O-'), client_for(donor_a.user))):
            with self.subTest(request=request.id):
                self.assertEqual(self.respond(request=request, client=client).status_code, 400)
        self.assertEqual(self.respond(request=wrong_group).status_code, 200)  # O- can give to O+
        self.assertFalse(DonorResponse.objects.filter(request=wrong_city).exists())

    def test_closed_or_unapproved_requests_reject_responses(self):
        for status in (Status.PENDING, Status.PROCESSING, Status.COMPLETED, Status.CANCELLED, Status.REJECTED):
            request = make_request('B+', status=status)
            with self.subTest(status=status):
                self.assertEqual(self.respond(request=request).status_code, 400)

    def test_unknown_request(self):
        response = self.client.post('/api/donors/me/requests/99999/respond/', {'answer': 'accepted'}, format='json')
        self.assertEqual(response.status_code, 400)

    def test_accepting_requires_eligibility_and_availability_but_declining_does_not(self):
        self.donor.last_donation_date = today() - timedelta(days=5)
        self.donor.save()
        self.assertEqual(self.respond('accepted').status_code, 400)
        self.assertEqual(self.respond('declined').status_code, 200)
        self.donor.last_donation_date = None
        self.donor.is_available = False
        self.donor.save()
        self.assertEqual(self.respond('accepted').status_code, 400)

    def test_only_donors_can_respond(self):
        for role in (Role.SEEKER, Role.HOSPITAL, Role.BLOODBANK, Role.ADMIN):
            self.assertEqual(self.respond(client=client_for(make_user(role))).status_code, 403)
        self.assertEqual(self.respond(client=APIClient()).status_code, 401)


class RequesterViewsTests(TestCase):
    def setUp(self):
        self.owner = make_user(Role.SEEKER)
        self.request = make_request('A+', requester=self.owner)
        self.helper = make_donor('O-', city='Pune', user=make_user(Role.DONOR, first_name='Asha', last_name='Rao', phone='555-0101'))
        self.other = make_donor('A+', city='Pune', user=make_user(Role.DONOR, phone='555-0202'))
        self.decliner = make_donor('A-', city='Pune', user=make_user(Role.DONOR, phone='555-0303'))
        for donor, answer in ((self.helper, 'accepted'), (self.decliner, 'declined')):
            DonorResponse.objects.create(request=self.request, donor=donor, answer=answer)

    def responses(self, user):
        return client_for(user).get(f'/api/requests/{self.request.id}/responses/')

    def test_owner_sees_only_accepting_donors_with_consented_details(self):
        response = self.responses(self.owner)
        self.assertEqual(response.status_code, 200)
        rows = response.json()
        self.assertEqual(len(rows), 1)
        self.assertEqual((rows[0]['donor_name'], rows[0]['donor_phone'], rows[0]['blood_group_name'], rows[0]['city']),
                         ('Asha Rao', '555-0101', 'O-', 'Pune'))
        self.assertEqual(set(rows[0]), {'id', 'donor_name', 'donor_phone', 'blood_group_name', 'city', 'updated_at'})
        self.assertNotIn('555-0303', str(response.json()))

    def test_admin_can_see_and_others_cannot(self):
        self.assertEqual(self.responses(make_user(Role.ADMIN)).status_code, 200)
        self.assertEqual(self.responses(make_user(Role.SEEKER)).status_code, 404)
        self.assertEqual(self.responses(self.other.user).status_code, 403)
        self.assertEqual(self.responses(verified_bank().user).status_code, 403)

    def test_matches_lists_banks_by_fit_and_bands_donor_counts(self):
        pune = verified_bank(name='Pune Bank', city='Pune')
        make_inventory(pune, 'O-', units=9)
        make_inventory(pune, 'A+', units=2)
        make_inventory(verified_bank(name='Mumbai Bank', city='Mumbai'), 'A+', units=50)
        make_inventory(make_bloodbank(name='Unverified Bank', city='Pune'), 'A+', units=50)
        body = client_for(self.owner).get(f'/api/requests/{self.request.id}/matches/').json()
        self.assertEqual(body['city'], 'Pune')
        self.assertEqual([(r['bloodbank_name'], r['blood_group_name'], r['exact']) for r in body['blood_banks']],
                         [('Pune Bank', 'A+', True), ('Pune Bank', 'O-', False)])
        self.assertEqual((body['exact_stock_units'], body['compatible_stock_units']), (2, 11))
        self.assertEqual(body['available_donors'], '3-5')   # helper (O-), other (A+), decliner (A-)
        self.assertEqual(body['accepted_donors'], 1)

    def test_matches_city_override_and_access(self):
        make_inventory(verified_bank(name='Mumbai Bank', city='Mumbai'), 'A+', units=5)
        body = client_for(self.owner).get(f'/api/requests/{self.request.id}/matches/?city=Mumbai').json()
        self.assertEqual([r['bloodbank_name'] for r in body['blood_banks']], ['Mumbai Bank'])
        self.assertEqual(client_for(make_user(Role.SEEKER)).get(f'/api/requests/{self.request.id}/matches/').status_code, 404)
        self.assertEqual(client_for(make_user(Role.DONOR)).get(f'/api/requests/{self.request.id}/matches/').status_code, 403)
        self.assertEqual(client_for(make_user(Role.ADMIN)).get(f'/api/requests/{self.request.id}/matches/').status_code, 200)

    def test_matches_never_lists_individual_donors(self):
        body = client_for(self.owner).get(f'/api/requests/{self.request.id}/matches/').json()
        self.assertEqual(set(body), {'city', 'blood_banks', 'exact_stock_units', 'compatible_stock_units',
                                      'available_donors', 'accepted_donors'})
        self.assertNotIn('555-', str(body))
