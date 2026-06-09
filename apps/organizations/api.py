from rest_framework.decorators import api_view
from django.http import HttpResponse
from django.db.models import Count
from .models import District, OrganizationType, Organization


@api_view(["GET"])
def get_organization_types_html(request):
    """
    Возвращает HTML с опциями для выпадающего списка типов организаций
    """
    district_id = request.GET.get("district")

    if not district_id:
        return HttpResponse('<option value="">---------</option>')

    try:
        organization_types = (
            OrganizationType.objects.filter(
                organization__district_id=district_id, organization__status="ACTIVE"
            )
            .annotate(org_count=Count("organization"))
            .filter(org_count__gt=0)
            .distinct()
            .order_by("name")
        )

        # Возвращаем ТОЛЬКО опции, без тега select
        html = '<option value="">---------</option>'
        for org_type in organization_types:
            html += f'<option value="{org_type.id}">{org_type.name}</option>'

        return HttpResponse(html)

    except Exception as e:
        print(f"Error: {e}")
        return HttpResponse('<option value="">---------</option>')


@api_view(["GET"])
def get_organizations_html(request):
    """
    Возвращает HTML с опциями для выпадающего списка организаций
    """
    district_id = request.GET.get("district")
    type_id = request.GET.get("type")

    if not district_id or not type_id:
        return HttpResponse('<option value="">---------</option>')

    try:
        organizations = Organization.objects.filter(
            district_id=district_id, organization_type_id=type_id, status="ACTIVE"
        ).order_by("short_name")

        html = '<option value="">---------</option>'
        for org in organizations:
            html += f'<option value="{org.id}">{org.short_name}</option>'

        return HttpResponse(html)

    except Exception as e:
        print(f"Error in get_organizations_html: {e}")
        import traceback

        traceback.print_exc()
        return HttpResponse('<option value="">---------</option>')
