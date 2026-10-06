import pytest
from django.contrib import admin
from django.urls import reverse

from apps.mintrud.models import (
    Year,
    NeedType,
    Occupation,
    EconomicActivity,
    LaborNeed,
)

# ---------- Регистрация моделей ----------


@pytest.mark.parametrize(
    "model",
    [Year, NeedType, Occupation, EconomicActivity, LaborNeed],
)
def test_model_is_registered_in_admin(model):
    assert model in admin.site._registry


@pytest.mark.parametrize(
    "model,admin_class",
    [
        (Year, admin.ModelAdmin),
        (NeedType, admin.ModelAdmin),
        (Occupation, admin.ModelAdmin),
        (EconomicActivity, admin.ModelAdmin),
        (LaborNeed, admin.ModelAdmin),
    ],
)
def test_admin_class_instance(model, admin_class):
    site_admin = admin.site._registry[model]
    assert isinstance(site_admin, admin_class)


# ---------- Occupation: inline LaborNeed ----------


def test_occupation_admin_has_labor_need_inline():
    site_admin = admin.site._registry[Occupation]
    inline_classes = [inline.__name__ for inline in site_admin.inlines]
    assert "LaborNeedInline" in inline_classes


def test_labor_need_inline_is_readonly():
    site_admin = admin.site._registry[Occupation]
    inline = site_admin.inlines[0]
    assert inline.can_delete is False
    assert "value" in inline.readonly_fields
    assert "year" in inline.readonly_fields


# ---------- LaborNeed: list_display / filters / search ----------


def test_labor_need_admin_list_display_columns():
    site_admin = admin.site._registry[LaborNeed]
    expected = {
        "year",
        "need_type",
        "occupation_code",
        "occupation_name",
        "economic_activity_name",
        "value_display",
        "updated_at",
    }
    assert set(site_admin.list_display) == expected


def test_labor_need_admin_search_fields():
    site_admin = admin.site._registry[LaborNeed]
    assert "occupation__code" in site_admin.search_fields
    assert "occupation__name" in site_admin.search_fields
    assert "economic_activity__name" in site_admin.search_fields


def test_labor_need_admin_autocomplete_fields():
    site_admin = admin.site._registry[LaborNeed]
    assert site_admin.autocomplete_fields == ("occupation", "economic_activity")


# ---------- Доступ к страницам в браузере (smoke) ----------


@pytest.fixture
def superuser(db):
    from apps.users.models import CustomUser

    return CustomUser.objects.create_superuser(
        username="admin",
        password="pass12345",
        email="admin@example.com",
    )


@pytest.mark.django_db
def test_admin_changelist_pages_open(client, superuser):
    client.force_login(superuser)

    urls = [
        reverse("admin:mintrud_year_changelist"),
        reverse("admin:mintrud_needtype_changelist"),
        reverse("admin:mintrud_occupation_changelist"),
        reverse("admin:mintrud_economicactivity_changelist"),
        reverse("admin:mintrud_laborneed_changelist"),
    ]
    for url in urls:
        response = client.get(url)
        assert response.status_code == 200, url


@pytest.mark.django_db
def test_admin_labor_need_changelist_renders(
    client,
    superuser,
    year_2025,
    need_type_general,
    occupation_1111,
    activity_agriculture,
    labor_need,
):
    """Проверим, что кастомные колонки list_display рендерятся без ошибок."""
    client.force_login(superuser)
    url = reverse("admin:mintrud_laborneed_changelist")
    response = client.get(url)

    assert response.status_code == 200
    content = response.content.decode("utf-8")
    # Кастомные @admin.display рендерятся
    assert "1111" in content
    assert "Общее" in content
    assert "2025" in content


@pytest.mark.django_db
def test_admin_occupation_change_page_with_inline(
    client,
    superuser,
    occupation_1111,
    labor_need,
):
    """Страница редактирования занятия должна содержать inline."""
    client.force_login(superuser)
    url = reverse("admin:mintrud_occupation_change", args=[occupation_1111.pk])
    response = client.get(url)

    assert response.status_code == 200
    content = response.content.decode("utf-8")
    assert "Кадровая потребность" in content  # verbose_name inline
