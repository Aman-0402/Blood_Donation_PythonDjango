from django.test import TestCase
from rest_framework.test import APIClient

from apps.accounts.models import Role
from apps.notifications.models import Notification
from apps.testing import make_user


def client_for(user):
    client = APIClient()
    client.force_authenticate(user)
    return client


class AdminUserListTests(TestCase):
    def test_filters(self):
        admin = client_for(make_user(Role.ADMIN))
        make_user(Role.DONOR, username='alice')
        make_user(Role.DONOR, username='bob', is_active=False)
        make_user(Role.SEEKER, username='carol')

        by_role = admin.get('/api/users/?role=donor').json()['results']
        self.assertEqual({u['username'] for u in by_role}, {'alice', 'bob'})

        by_active = admin.get('/api/users/?is_active=false').json()['results']
        self.assertEqual({u['username'] for u in by_active}, {'bob'})

        by_search = admin.get('/api/users/?search=ali').json()['results']
        self.assertEqual({u['username'] for u in by_search}, {'alice'})

    def test_non_admin_forbidden(self):
        self.assertEqual(client_for(make_user(Role.DONOR)).get('/api/users/').status_code, 403)


class AdminUserDeactivateTests(TestCase):
    def setUp(self):
        self.admin = make_user(Role.ADMIN)
        self.target = make_user(Role.DONOR)

    def test_deactivate_and_reactivate(self):
        client = client_for(self.admin)
        response = client.post(f'/api/users/{self.target.id}/deactivate/')
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()['is_active'])
        self.target.refresh_from_db()
        self.assertFalse(self.target.is_active)

        response = client.post(f'/api/users/{self.target.id}/activate/')
        self.assertTrue(response.json()['is_active'])
        self.assertTrue(Notification.objects.filter(user=self.target, type='alert').exists())

    def test_cannot_deactivate_self(self):
        response = client_for(self.admin).post(f'/api/users/{self.admin.id}/deactivate/')
        self.assertEqual(response.status_code, 400)
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.is_active)

    def test_cannot_deactivate_another_admin(self):
        other_admin = make_user(Role.ADMIN)
        response = client_for(self.admin).post(f'/api/users/{other_admin.id}/deactivate/')
        self.assertEqual(response.status_code, 400)

    def test_deactivated_user_cannot_log_in(self):
        client_for(self.admin).post(f'/api/users/{self.target.id}/deactivate/')
        response = APIClient().post(
            '/api/auth/login/', {'username': self.target.username, 'password': 'pass12345!'}, format='json'
        )
        self.assertEqual(response.status_code, 401)

    def test_only_admin_can_deactivate(self):
        other = make_user(Role.DONOR)
        response = client_for(other).post(f'/api/users/{self.target.id}/deactivate/')
        self.assertEqual(response.status_code, 403)
        self.assertEqual(APIClient().post(f'/api/users/{self.target.id}/deactivate/').status_code, 401)
