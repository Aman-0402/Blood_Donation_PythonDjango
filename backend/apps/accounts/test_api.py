from django.test import TestCase
from rest_framework.test import APIClient

from apps.accounts.models import Role
from apps.testing import make_user

ADMIN_ONLY_ENDPOINTS = [
    '/api/users/',
    '/api/donors/',
    '/api/hospitals/',
    '/api/bloodbanks/',
    '/api/inventory/',
    '/api/donations/',
    '/api/notifications/',
]


class ApiAccessTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_health_is_public(self):
        response = self.client.get('/api/health/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'status': 'ok'})

    def test_anonymous_rejected(self):
        for url in ADMIN_ONLY_ENDPOINTS + ['/api/blood-groups/']:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 401)

    def test_non_admin_forbidden(self):
        for role in (Role.DONOR, Role.SEEKER, Role.HOSPITAL, Role.BLOODBANK):
            self.client.force_authenticate(make_user(role))
            for url in ADMIN_ONLY_ENDPOINTS:
                with self.subTest(role=role, url=url):
                    self.assertEqual(self.client.get(url).status_code, 403)

    def test_staff_flag_alone_is_not_admin(self):
        self.client.force_authenticate(make_user(Role.DONOR, is_staff=True))
        self.assertEqual(self.client.get('/api/users/').status_code, 403)

    def test_admin_role_can_read(self):
        self.client.force_authenticate(make_user(Role.ADMIN))
        for url in ADMIN_ONLY_ENDPOINTS:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)

    def test_any_authenticated_user_can_list_blood_groups(self):
        self.client.force_authenticate(make_user(Role.SEEKER))
        response = self.client.get('/api/blood-groups/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 8)

    def test_write_methods_not_allowed(self):
        self.client.force_authenticate(make_user(Role.ADMIN))
        profile_endpoints = ('/api/donors/', '/api/hospitals/')
        read_only = [u for u in ADMIN_ONLY_ENDPOINTS if u not in profile_endpoints]
        for url in read_only:
            with self.subTest(url=url):
                self.assertEqual(self.client.post(url, {}).status_code, 405)
        for url in profile_endpoints:
            with self.subTest(url=url):
                self.assertEqual(self.client.post(url, {}).status_code, 403)

    def test_user_payload_excludes_password(self):
        self.client.force_authenticate(make_user(Role.ADMIN))
        rows = self.client.get('/api/users/').json()['results']
        self.assertNotIn('password', rows[0])
