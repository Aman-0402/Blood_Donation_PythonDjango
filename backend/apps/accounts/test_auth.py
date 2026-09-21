from datetime import timedelta

from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

from apps.accounts.models import Role, User
from apps.testing import make_user

PASSWORD = 'S3cure-Pass!9'


def register_payload(**overrides):
    payload = {
        'username': 'alice',
        'email': 'alice@example.com',
        'password': PASSWORD,
        'role': 'donor',
        'phone': '9999999999',
    }
    payload.update(overrides)
    return payload


class RegistrationTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_register_success_returns_tokens_and_unverified_user(self):
        response = self.client.post('/api/auth/register/', register_payload(), format='json')
        self.assertEqual(response.status_code, 201)
        body = response.json()
        self.assertIn('access', body)
        self.assertIn('refresh', body)
        self.assertEqual(body['user']['role'], 'donor')
        self.assertFalse(body['user']['is_verified'])
        self.assertNotIn('password', body['user'])
        user = User.objects.get(username='alice')
        self.assertTrue(user.check_password(PASSWORD))
        self.assertNotEqual(user.password, PASSWORD)

    def test_cannot_self_register_as_admin(self):
        response = self.client.post(
            '/api/auth/register/', register_payload(role='admin'), format='json'
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('role', response.json())
        self.assertFalse(User.objects.filter(username='alice').exists())

    def test_cannot_escalate_via_extra_fields(self):
        response = self.client.post(
            '/api/auth/register/',
            register_payload(is_staff=True, is_superuser=True, is_verified=True),
            format='json',
        )
        self.assertEqual(response.status_code, 201)
        user = User.objects.get(username='alice')
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertFalse(user.is_verified)

    def test_weak_password_rejected(self):
        response = self.client.post(
            '/api/auth/register/', register_payload(password='12345678'), format='json'
        )
        self.assertEqual(response.status_code, 400)

    def test_duplicate_email_case_insensitive(self):
        make_user(email='alice@example.com')
        response = self.client.post(
            '/api/auth/register/',
            register_payload(email='ALICE@example.com'),
            format='json',
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('email', response.json())

    def test_duplicate_username_rejected(self):
        make_user(username='alice')
        response = self.client.post('/api/auth/register/', register_payload(), format='json')
        self.assertEqual(response.status_code, 400)

    def test_missing_fields_rejected(self):
        response = self.client.post('/api/auth/register/', {}, format='json')
        self.assertEqual(response.status_code, 400)


class LoginTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            'bob', 'bob@example.com', PASSWORD, role=Role.SEEKER
        )

    def login(self, username='bob', password=PASSWORD):
        return self.client.post(
            '/api/auth/login/', {'username': username, 'password': password}, format='json'
        )

    def test_valid_login(self):
        response = self.login()
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertIn('access', body)
        self.assertIn('refresh', body)
        self.assertEqual(body['user']['username'], 'bob')
        self.assertEqual(AccessToken(body['access'])['role'], 'seeker')

    def test_wrong_password(self):
        self.assertEqual(self.login(password='wrong').status_code, 401)

    def test_unknown_user(self):
        self.assertEqual(self.login(username='nobody').status_code, 401)

    def test_inactive_user_cannot_login(self):
        self.user.is_active = False
        self.user.save()
        self.assertEqual(self.login().status_code, 401)

    def test_missing_credentials(self):
        self.assertEqual(self.client.post('/api/auth/login/', {}, format='json').status_code, 400)


class TokenLifecycleTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user('carol', 'carol@example.com', PASSWORD)
        tokens = self.client.post(
            '/api/auth/login/', {'username': 'carol', 'password': PASSWORD}, format='json'
        ).json()
        self.access = tokens['access']
        self.refresh = tokens['refresh']

    def auth(self, token):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

    def test_me_requires_authentication(self):
        self.assertEqual(self.client.get('/api/auth/me/').status_code, 401)

    def test_me_with_valid_token(self):
        self.auth(self.access)
        response = self.client.get('/api/auth/me/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['username'], 'carol')

    def test_garbage_token_rejected(self):
        self.auth('not-a-token')
        self.assertEqual(self.client.get('/api/auth/me/').status_code, 401)

    def test_expired_access_token_rejected(self):
        token = AccessToken.for_user(self.user)
        token.set_exp(lifetime=-timedelta(minutes=1))
        self.auth(str(token))
        self.assertEqual(self.client.get('/api/auth/me/').status_code, 401)

    def test_refresh_returns_new_access_and_rotates_refresh(self):
        response = self.client.post('/api/auth/refresh/', {'refresh': self.refresh}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertIn('access', response.json())
        self.assertNotEqual(response.json().get('refresh'), self.refresh)

    def test_rotated_refresh_token_cannot_be_reused(self):
        self.client.post('/api/auth/refresh/', {'refresh': self.refresh}, format='json')
        again = self.client.post('/api/auth/refresh/', {'refresh': self.refresh}, format='json')
        self.assertEqual(again.status_code, 401)

    def test_refresh_token_not_accepted_as_access_token(self):
        self.auth(self.refresh)
        self.assertEqual(self.client.get('/api/auth/me/').status_code, 401)

    def test_logout_blacklists_refresh_token(self):
        self.auth(self.access)
        response = self.client.post('/api/auth/logout/', {'refresh': self.refresh}, format='json')
        self.assertEqual(response.status_code, 205)
        self.client.credentials()
        refreshed = self.client.post('/api/auth/refresh/', {'refresh': self.refresh}, format='json')
        self.assertEqual(refreshed.status_code, 401)

    def test_logout_requires_authentication(self):
        response = self.client.post('/api/auth/logout/', {'refresh': self.refresh}, format='json')
        self.assertEqual(response.status_code, 401)

    def test_logout_rejects_other_users_refresh_token(self):
        other = User.objects.create_user('dave', 'dave@example.com', PASSWORD)
        other_refresh = self.client.post(
            '/api/auth/login/', {'username': 'dave', 'password': PASSWORD}, format='json'
        ).json()['refresh']
        self.auth(self.access)
        response = self.client.post('/api/auth/logout/', {'refresh': other_refresh}, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertTrue(other.is_active)

    def test_logout_invalid_token(self):
        self.auth(self.access)
        response = self.client.post('/api/auth/logout/', {'refresh': 'junk'}, format='json')
        self.assertEqual(response.status_code, 400)


class ProfileAndPasswordTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user('erin', 'erin@example.com', PASSWORD)
        self.client.force_authenticate(self.user)

    def test_patch_me_updates_only_allowed_fields(self):
        response = self.client.patch(
            '/api/auth/me/',
            {'first_name': 'Erin', 'phone': '123', 'role': 'admin', 'is_verified': True},
            format='json',
        )
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Erin')
        self.assertEqual(self.user.phone, '123')
        self.assertEqual(self.user.role, Role.SEEKER)
        self.assertFalse(self.user.is_verified)

    def test_change_password_success(self):
        response = self.client.post(
            '/api/auth/change-password/',
            {'old_password': PASSWORD, 'new_password': 'An0ther-Str0ng-Pass'},
            format='json',
        )
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('An0ther-Str0ng-Pass'))

    def test_change_password_wrong_old(self):
        response = self.client.post(
            '/api/auth/change-password/',
            {'old_password': 'nope', 'new_password': 'An0ther-Str0ng-Pass'},
            format='json',
        )
        self.assertEqual(response.status_code, 400)

    def test_change_password_weak_new(self):
        response = self.client.post(
            '/api/auth/change-password/',
            {'old_password': PASSWORD, 'new_password': 'short'},
            format='json',
        )
        self.assertEqual(response.status_code, 400)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(PASSWORD))
