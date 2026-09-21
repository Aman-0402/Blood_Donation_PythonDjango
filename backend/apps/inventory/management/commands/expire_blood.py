from django.core.management.base import BaseCommand

from apps.inventory.services import expire_stock


class Command(BaseCommand):
    help = 'Mark all blood batches past their expiry date as expired (run daily, e.g. from cron).'

    def handle(self, *args, **options):
        units = expire_stock()
        self.stdout.write(self.style.SUCCESS(f'Expired {units} unit(s).'))
