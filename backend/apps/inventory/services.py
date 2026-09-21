from datetime import timedelta

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from apps.accounts.models import BloodGroup

from .models import MAX_UNITS_PER_OPERATION, BloodInventory, InventoryTransaction

Status = BloodInventory.Status
TxType = InventoryTransaction.Type


def usable_stock():
    """Units that can actually be issued: marked available and not yet past expiry (a unit expires on its expiry date)."""
    return BloodInventory.objects.filter(
        status=Status.AVAILABLE, expiry_date__gt=timezone.localdate()
    )


def usable_units(bloodbank, blood_group):
    total = usable_stock().filter(bloodbank=bloodbank, blood_group=blood_group).aggregate(
        total=Sum('units')
    )['total']
    return total or 0


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


def stock_by_blood_group(bloodbank=None):
    stock = usable_stock()
    if bloodbank is not None:
        stock = stock.filter(bloodbank=bloodbank)
    totals = {
        row['blood_group_id']: row['units']
        for row in stock.values('blood_group_id').annotate(units=Sum('units'))
    }
    return [
        {'blood_group': group.id, 'blood_group_name': group.name, 'units_available': totals.get(group.id, 0)}
        for group in BloodGroup.objects.all()
    ]


def expiring_soon(bloodbank, days=7):
    today = timezone.localdate()
    rows = (
        usable_stock()
        .filter(bloodbank=bloodbank, expiry_date__lte=today + timedelta(days=days))
        .values('blood_group_id')
        .annotate(units=Sum('units'))
    )
    return {row['blood_group_id']: row['units'] for row in rows}


def _check_units(units):
    if not 1 <= units <= MAX_UNITS_PER_OPERATION:
        raise ValidationError(f'Units must be between 1 and {MAX_UNITS_PER_OPERATION}.')


def record_collection(
    bloodbank, blood_group, units, collection_date=None, expiry_date=None, user=None, note='', donation=None
):
    """Add a new batch of collected blood and log it."""
    _check_units(units)
    today = timezone.localdate()
    collection_date = collection_date or today
    if collection_date > today:
        raise ValidationError('Collection date cannot be in the future.')
    expiry_date = expiry_date or collection_date + timedelta(days=settings.BLOOD_SHELF_LIFE_DAYS)
    if expiry_date <= collection_date:
        raise ValidationError('Expiry date must be after collection date.')
    if expiry_date <= today:
        raise ValidationError('Cannot add blood that has already expired.')
    with transaction.atomic():
        batch = BloodInventory.objects.create(
            bloodbank=bloodbank,
            blood_group=blood_group,
            units=units,
            collection_date=collection_date,
            expiry_date=expiry_date,
        )
        InventoryTransaction.objects.create(
            bloodbank=bloodbank, blood_group=blood_group, batch=batch, type=TxType.COLLECTION,
            units=units, note=note, created_by=user, donation=donation,
        )
    return batch


def issue_units(bloodbank, blood_group, units, user=None, request=None, note=''):
    """Take units from the batches closest to expiry first. All-or-nothing and safe under concurrency."""
    _check_units(units)
    with transaction.atomic():
        batches = list(
            usable_stock()
            .select_for_update()
            .filter(bloodbank=bloodbank, blood_group=blood_group)
            .order_by('expiry_date', 'id')
        )
        available = sum(batch.units for batch in batches)
        if available < units:
            raise ValidationError(
                f'Insufficient stock: {available} unit(s) of {blood_group.name} available, {units} requested.'
            )
        remaining = units
        for batch in batches:
            if remaining == 0:
                break
            taken = min(batch.units, remaining)
            batch.units -= taken
            if batch.units == 0:
                batch.status = Status.ISSUED
            batch.save(update_fields=['units', 'status', 'updated_at'])
            InventoryTransaction.objects.create(
                bloodbank=bloodbank, blood_group=blood_group, batch=batch, type=TxType.ISSUE,
                units=-taken, request=request, note=note, created_by=user,
            )
            remaining -= taken
    return units


def expire_stock(bloodbank=None, user=None):
    """Mark available batches past their expiry date as expired. Returns the number of units expired."""
    today = timezone.localdate()
    expired_units = 0
    with transaction.atomic():
        batches = BloodInventory.objects.select_for_update().filter(
            status=Status.AVAILABLE, expiry_date__lte=today
        )
        if bloodbank is not None:
            batches = batches.filter(bloodbank=bloodbank)
        for batch in list(batches):
            batch.status = Status.EXPIRED
            batch.save(update_fields=['status', 'updated_at'])
            InventoryTransaction.objects.create(
                bloodbank=batch.bloodbank, blood_group=batch.blood_group, batch=batch,
                type=TxType.EXPIRED, units=-batch.units, note='Passed expiry date', created_by=user,
            )
            expired_units += batch.units
    return expired_units


def adjust_batch(batch_id, delta, reason, bloodbank, user=None):
    """Correct a batch count (miscount, damage). A batch reduced to zero is marked discarded."""
    if delta == 0:
        raise ValidationError('Adjustment cannot be zero.')
    if not reason or not reason.strip():
        raise ValidationError('A reason is required for adjustments.')
    with transaction.atomic():
        try:
            batch = BloodInventory.objects.select_for_update().get(pk=batch_id, bloodbank=bloodbank)
        except BloodInventory.DoesNotExist:
            raise ValidationError('Batch not found.')
        if batch.status != Status.AVAILABLE:
            raise ValidationError(f'Only available batches can be adjusted (this one is {batch.status}).')
        new_units = batch.units + delta
        if new_units < 0:
            raise ValidationError('Adjustment would make the batch negative.')
        if new_units > MAX_UNITS_PER_OPERATION:
            raise ValidationError(f'A batch cannot exceed {MAX_UNITS_PER_OPERATION} units.')
        batch.units = new_units
        if new_units == 0:
            batch.status = Status.DISCARDED
        batch.save(update_fields=['units', 'status', 'updated_at'])
        InventoryTransaction.objects.create(
            bloodbank=bloodbank, blood_group=batch.blood_group, batch=batch, type=TxType.ADJUSTMENT,
            units=delta, note=reason.strip()[:255], created_by=user,
        )
    return batch
