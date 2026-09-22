from django.test import TestCase
from rest_framework.test import APIClient

from apps.accounts.models import Role
from apps.testing import make_user

from .models import Notification


def client_for(user):
    client = APIClient()
    client.force_authenticate(user)
    return client


class NotificationApiTests(TestCase):
    def setUp(self):
        self.user = make_user(Role.DONOR)
        self.other = make_user(Role.DONOR)
        self.client = client_for(self.user)
        self.mine_unread = Notification.objects.create(user=self.user, type='alert', message='a')
        self.mine_read = Notification.objects.create(user=self.user, type='alert', message='b', is_read=True)
        Notification.objects.create(user=self.other, type='alert', message='c')

    def test_requires_auth(self):
        self.assertEqual(APIClient().get('/api/notifications/').status_code, 401)

    def test_only_own_notifications(self):
        body = self.client.get('/api/notifications/').json()
        self.assertEqual({n['id'] for n in body['results']}, {self.mine_unread.id, self.mine_read.id})

    def test_filter_by_read_state(self):
        unread = self.client.get('/api/notifications/?is_read=false').json()['results']
        self.assertEqual([n['id'] for n in unread], [self.mine_unread.id])

    def test_unread_count(self):
        self.assertEqual(self.client.get('/api/notifications/unread_count/').json(), {'count': 1})

    def test_mark_read(self):
        response = self.client.post(f'/api/notifications/{self.mine_unread.id}/read/')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['is_read'])
        self.assertEqual(self.client.get('/api/notifications/unread_count/').json(), {'count': 0})

    def test_cannot_mark_others_notification_read(self):
        others = Notification.objects.get(user=self.other)
        self.assertEqual(self.client.post(f'/api/notifications/{others.id}/read/').status_code, 404)

    def test_mark_all_read(self):
        response = self.client.post('/api/notifications/read-all/')
        self.assertEqual(response.json(), {'updated': 1})
        self.assertEqual(self.client.get('/api/notifications/unread_count/').json(), {'count': 0})
        self.assertEqual(Notification.objects.get(user=self.other).is_read, False)

    def test_admin_sees_everyones_notifications_read_only(self):
        admin = client_for(make_user(Role.ADMIN))
        self.assertEqual(admin.get('/api/notifications/').json()['count'], 3)
        self.assertEqual(admin.post(f'/api/notifications/{self.mine_unread.id}/read/').status_code, 404)
