from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count
from .models import District, OrganizationType, Organization
from .serializers import (
    DistrictSerializer,
    OrganizationTypeSerializer,
    OrganizationListSerializer,
    OrganizationDetailSerializer,
    OrganizationCreateUpdateSerializer,
)


class DistrictViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet для районов (только чтение)
    """

    queryset = District.objects.annotate(
        organizations_count=Count("organization")
    ).all()
    serializer_class = DistrictSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["short_name", "full_name"]
    ordering_fields = ["short_name", "organizations_count"]
    ordering = ["short_name"]


class OrganizationTypeViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet для типов организаций (только чтение)
    """

    queryset = OrganizationType.objects.annotate(
        organizations_count=Count("organization")
    ).all()
    serializer_class = OrganizationTypeSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name"]
    ordering_fields = ["name", "organizations_count"]
    ordering = ["name"]


class OrganizationViewSet(viewsets.ModelViewSet):
    """
    ViewSet для организаций (полный CRUD)

    Действия:
    - GET /organizations/ - список организаций
    - GET /organizations/{id}/ - детальная информация
    - POST /organizations/ - создать организацию
    - PUT /organizations/{id}/ - обновить организацию
    - PATCH /organizations/{id}/ - частично обновить
    - DELETE /organizations/{id}/ - удалить организацию

    Фильтры:
    - ?district={id} - по району
    - ?organization_type={id} - по типу
    - ?status=ACTIVE - по статусу
    - ?search=текст - поиск по названию и ИНН
    """

    queryset = Organization.objects.select_related(
        "district", "organization_type"
    ).all()
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["district", "organization_type", "status"]
    search_fields = ["short_name", "full_name", "inn", "ogrn"]
    ordering_fields = ["short_name", "created_at", "status"]
    ordering = ["-created_at"]

    def get_serializer_class(self):
        """Выбор сериализатора в зависимости от действия"""
        if self.action == "list":
            return OrganizationListSerializer
        elif self.action == "retrieve":
            return OrganizationDetailSerializer
        elif self.action in ["create", "update", "partial_update"]:
            return OrganizationCreateUpdateSerializer
        return OrganizationListSerializer

    @action(detail=False, methods=["get"])
    def by_district(self, request):
        """
        Кастомный эндпоинт: организации по району
        GET /organizations/by_district/?district_id=1
        """
        district_id = request.query_params.get("district_id")
        if not district_id:
            return Response(
                {"error": "Не указан district_id"}, status=status.HTTP_400_BAD_REQUEST
            )

        organizations = self.get_queryset().filter(district_id=district_id)
        serializer = self.get_serializer(organizations, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def with_coordinates(self, request):
        """
        Кастомный эндпоинт: организации с координатами
        GET /organizations/with_coordinates/
        """
        organizations = self.get_queryset().exclude(coordinates__isnull=True)
        serializer = self.get_serializer(organizations, many=True)
        return Response(serializer.data)
