from django.db import models


class Notification(models.Model):
    class Type(models.TextChoices):
        REQUEST = 'request', 'Blood Request'
        DONATION = 'donation', 'Donation'
        STATUS_CHANGE = 'status_change', 'Status Change'
        VERIFICATION = 'verification', 'Account Verification'
        ALERT = 'alert', 'Alert'

    user = models.ForeignKey(
        'accounts.User', on_delete=models.CASCADE, related_name='notifications'
    )
    type = models.CharField(max_length=20, choices=Type.choices)
    message = models.CharField(max_length=500)
    related_object_type = models.CharField(max_length=50, blank=True)
    related_object_id = models.PositiveBigIntegerField(null=True, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at', '-id']

    def __str__(self):
        return f'{self.type} for {self.user_id}: {self.message[:40]}'
