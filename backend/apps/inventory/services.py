from django.db.models import Sum
from django.utils import timezone

from apps.accounts.models import BloodGroup

from .models import BloodInventory


def usable_stock():
    """Units that can actually be issued: marked available and not yet past expiry (a unit expires on its expiry date)."""
    return BloodInventory.objects.filter(
        status=BloodInventory.Status.AVAILABLE, expiry_date__gt=timezone.localdate()
    )


def stock_by_bloodbank(blood_group_id=None, city=None):
    stock = usable_stock()
    if blood_group_id:
        stock = stock.filter(blood_group_id=blood_group_id)
    if city:
        stock = stock.filter(bloodbank__city__iexact=city)
    return list(
        stock.values(
            'bloodbank_id',
            'bloodbank__name',
            'bloodbank__city',
            'blood_group_id',
            'blood_group__name',
        )
        .annotate(units_available=Sum('units'))
        .order_by('blood_group__name', '-units_available', 'bloodbank__name')
    )


def stock_by_blood_group():
    totals = {
        row['blood_group_id']: row['units']
        for row in usable_stock().values('blood_group_id').annotate(units=Sum('units'))
    }
    return [
        {'blood_group': group.id, 'blood_group_name': group.name, 'units_available': totals.get(group.id, 0)}
        for group in BloodGroup.objects.all()
    ]
