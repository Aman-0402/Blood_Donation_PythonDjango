from django.test import TestCase
from rest_framework.test import APIClient

from apps.accounts.models import Role
from apps.testing import make_user

ENDPOINTS = [
    '/api/users/',
    '/api/blood-groups/',
    '/api/donors/',
    '/api/hospitals/',
    '/api/bloodbanks/',
    '/api/inventory/',
    '/api/donations/',
    '/api/requests/',
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
        for url in ENDPOINTS:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 401)

    def test_non_admin_forbidden(self):
        self.client.force_authenticate(make_user(Role.DONOR))
        for url in ENDPOINTS:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 403)

    def test_admin_can_read(self):
        admin = make_user(Role.ADMIN, is_staff=True)
        self.client.force_authenticate(admin)
        for url in ENDPOINTS:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)

    def test_write_methods_not_allowed(self):
        admin = make_user(Role.ADMIN, is_staff=True)
        self.client.force_authenticate(admin)
        for url in ENDPOINTS:
            with self.subTest(url=url):
                self.assertEqual(self.client.post(url, {}).status_code, 405)

    def test_user_payload_excludes_password(self):
        admin = make_user(Role.ADMIN, is_staff=True)
        self.client.force_authenticate(admin)
        results = self.client.get('/api/users/').json()
        rows = results['results'] if isinstance(results, dict) else results
        self.assertNotIn('password', rows[0])
