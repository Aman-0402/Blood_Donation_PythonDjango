from datetime import date

from django.db.models import Avg, Count, ExpressionWrapper, F, Sum, fields
from django.db.models.functions import TruncMonth
from django.utils import timezone
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import BloodGroup
from apps.accounts.permissions import IsAdminRole
from apps.bloodrequests.models import BloodRequest
from apps.donations.models import Donation
from apps.inventory.services import expiring_soon_all, stock_by_blood_group

MONTHS_BACK = 12


def _months_back(n):
    today = timezone.localdate()
    year, month = today.year, today.month
    months = []
    for _ in range(n):
        months.append(date(year, month, 1))
        month -= 1
        if month == 0:
            month = 12
            year -= 1
    return list(reversed(months))


def _by_blood_group(queryset):
    counts = dict(queryset.values_list('blood_group__name', flat=True).order_by().annotate(
        c=Count('id')
    ).values_list('blood_group__name', 'c'))
    return [{'blood_group_name': g.name, 'count': counts.get(g.name, 0)} for g in BloodGroup.objects.all()]


class DonationReportView(APIView):
    permission_classes = [IsAdminRole]

    def get(self, request):
        donations = Donation.objects.all()
        by_status = {s.value: 0 for s in Donation.Status}
        for row in donations.values('status').annotate(c=Count('id')):
            by_status[row['status']] = row['c']

        completed = donations.filter(status=Donation.Status.COMPLETED)
        by_group = _by_blood_group(completed)

        window_start = _months_back(MONTHS_BACK)[0]
        monthly_rows = {
            row['month']: {'count': row['count'], 'units': row['units']}
            for row in completed.filter(donation_date__gte=window_start)
            .annotate(month=TruncMonth('donation_date'))
            .values('month')
            .order_by('month')
            .annotate(count=Count('id'), units=Sum('quantity'))
        }
        monthly = [
            {
                'month': month.strftime('%Y-%m'),
                'count': monthly_rows.get(month, {}).get('count', 0),
                'units': monthly_rows.get(month, {}).get('units', 0) or 0,
            }
            for month in _months_back(MONTHS_BACK)
        ]

        return Response({
            'by_status': by_status,
            'by_blood_group': by_group,
            'monthly': monthly,
            'total_units_collected': completed.aggregate(total=Sum('quantity'))['total'] or 0,
        })


class RequestReportView(APIView):
    permission_classes = [IsAdminRole]

    def get(self, request):
        requests = BloodRequest.objects.all()
        by_status = {s.value: 0 for s in BloodRequest.Status}
        for row in requests.values('status').annotate(c=Count('id')):
            by_status[row['status']] = row['c']

        by_urgency = {u.value: 0 for u in BloodRequest.Urgency}
        for row in requests.values('urgency').annotate(c=Count('id')):
            by_urgency[row['urgency']] = row['c']

        by_group = _by_blood_group(requests)

        total = requests.count()
        completed = by_status[BloodRequest.Status.COMPLETED.value]
        closed = completed + by_status[BloodRequest.Status.CANCELLED.value] + by_status[BloodRequest.Status.REJECTED.value]
        completion_rate = round(completed / total * 100, 1) if total else 0.0

        turnaround = requests.filter(status=BloodRequest.Status.COMPLETED).annotate(
            duration=ExpressionWrapper(F('updated_at') - F('created_at'), output_field=fields.DurationField())
        ).aggregate(avg=Avg('duration'))['avg']
        avg_fulfillment_hours = round(turnaround.total_seconds() / 3600, 1) if turnaround else None

        return Response({
            'total_requests': total,
            'by_status': by_status,
            'by_urgency': by_urgency,
            'by_blood_group': by_group,
            'completion_rate': completion_rate,
            'closed_requests': closed,
            'avg_fulfillment_hours': avg_fulfillment_hours,
        })


class InventoryReportView(APIView):
    permission_classes = [IsAdminRole]

    def get(self, request):
        return Response({
            'by_blood_group': stock_by_blood_group(),
            'expiring_within_7_days': expiring_soon_all(),
        })
