from django.test import TestCase

from apps.testing import make_user

from .models import Notification


class NotificationTests(TestCase):
    def test_defaults_and_relationship(self):
        user = make_user()
        note = Notification.objects.create(
            user=user, type=Notification.Type.ALERT, message='Hello'
        )
        self.assertFalse(note.is_read)
        self.assertEqual(user.notifications.count(), 1)

    def test_newest_first(self):
        user = make_user()
        first = Notification.objects.create(user=user, type='alert', message='one')
        second = Notification.objects.create(user=user, type='alert', message='two')
        self.assertEqual(list(user.notifications.all()), [second, first])

    def test_deleting_user_removes_notifications(self):
        user = make_user()
        Notification.objects.create(user=user, type='alert', message='x')
        user.delete()
        self.assertFalse(Notification.objects.exists())
