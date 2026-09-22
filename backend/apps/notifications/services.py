from .models import Notification


def notify(user, type, message, related_object_type='', related_object_id=None):
    return Notification.objects.create(
        user=user, type=type, message=message[:500],
        related_object_type=related_object_type, related_object_id=related_object_id,
    )


def notify_many(users, type, message, related_object_type='', related_object_id=None):
    Notification.objects.bulk_create([
        Notification(
            user=user, type=type, message=message[:500],
            related_object_type=related_object_type, related_object_id=related_object_id,
        )
        for user in users
    ])
