from django.db.models import Count
from django.db.models.functions import Lower
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.compatibility import donor_groups_for
from apps.accounts.models import BloodGroup, Role
from apps.accounts.permissions import role_permission
from apps.bloodrequests.matching import band
from apps.donors.eligibility import eligible_donors
from apps.hospitals.models import Hospital
from apps.inventory.services import search_stock

IsSearcher = role_permission(Role.SEEKER, Role.HOSPITAL, Role.BLOODBANK, Role.ADMIN)


class SearchQuerySerializer(serializers.Serializer):
    blood_group = serializers.PrimaryKeyRelatedField(queryset=BloodGroup.objects.all(), required=False)
    compatible = serializers.BooleanField(required=False, default=False)
    city = serializers.CharField(required=False, max_length=100)
    bank = serializers.IntegerField(required=False, min_value=1)
    bank_name = serializers.CharField(required=False, max_length=200)
    min_units = serializers.IntegerField(required=False, min_value=1, max_value=1000)


class HospitalSearchSerializer(serializers.Serializer):
    city = serializers.CharField(required=False, max_length=100)
    name = serializers.CharField(required=False, max_length=200)


class SearchBase(APIView):
    """Signed-in seekers, hospitals, blood banks and admins. Hospitals and banks must be verified."""

    permission_classes = [IsSearcher]

    def check_permissions(self, request):
        super().check_permissions(request)
        user = request.user
        if user.role in (Role.HOSPITAL, Role.BLOODBANK) and not user.is_verified:
            raise PermissionDenied('Your account must be verified by an administrator before searching.')

    def group_ids(self, params):
        group = params.get('blood_group')
        if group is None:
            return None, None
        if params.get('compatible'):
            return [g.id for g in donor_groups_for(group)], group
        return [group.id], group


class BloodSearchView(SearchBase):
    """Where is blood available? Exact matches come first; `compatible=true` adds groups that can safely be given."""

    def get(self, request):
        query = SearchQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        params = query.validated_data
        ids, wanted = self.group_ids(params)
        rows = search_stock(
            group_ids=ids,
            city=params.get('city'),
            bank_id=params.get('bank'),
            bank_name=params.get('bank_name'),
            min_units=params.get('min_units'),
        )
        for row in rows:
            row['exact'] = wanted is None or row['blood_group'] == wanted.id
        rows.sort(key=lambda r: (not r['exact'], -r['units_available'], r['bloodbank_name']))
        return Response(rows)


class DonorSearchView(SearchBase):
    """How many eligible, available donors are there? Banded counts per city and blood group, never individuals."""

    def get(self, request):
        query = SearchQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        params = query.validated_data
        ids, _ = self.group_ids(params)
        donors = eligible_donors()
        if ids is not None:
            donors = donors.filter(blood_group_id__in=ids)
        if params.get('city'):
            donors = donors.filter(city__iexact=params['city'])
        rows = (
            donors.annotate(city_key=Lower('city'))
            .values('city_key', 'blood_group__name')
            .annotate(total=Count('id'))
            .order_by('city_key', 'blood_group__name')
        )
        return Response(
            [
                {'city': row['city_key'].title(), 'blood_group_name': row['blood_group__name'], 'available_donors': band(row['total'])}
                for row in rows
            ]
        )


class HospitalSearchView(SearchBase):
    """Verified hospitals: organisation details only."""

    def get(self, request):
        query = HospitalSearchSerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        params = query.validated_data
        hospitals = Hospital.objects.filter(user__is_verified=True).order_by('name')
        if params.get('city'):
            hospitals = hospitals.filter(city__iexact=params['city'])
        if params.get('name'):
            hospitals = hospitals.filter(name__icontains=params['name'])
        return Response(list(hospitals.values('id', 'name', 'city', 'address')))
