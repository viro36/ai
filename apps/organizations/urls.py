from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import api
from . import views

router = DefaultRouter()
router.register(r"districts", views.DistrictViewSet, basename="district")
router.register(
    r"organization-types", views.OrganizationTypeViewSet, basename="organizationtype"
)
router.register(r"organizations", views.OrganizationViewSet, basename="organization")

urlpatterns = [
    path(
        "api/get-organization-types-html/",
        api.get_organization_types_html,
        name="get_organization_types_html",
    ),
    path(
        "api/get-organizations-html/",
        api.get_organizations_html,
        name="get_organizations_html",
    ),
    path("api/", include(router.urls)),
]
