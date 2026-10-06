from unittest import mock

import pytest
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.users.models import CustomUser

# ---------- фикстуры ----------


@pytest.fixture
def mintrud_user(db):
    return CustomUser.objects.create_user(
        username="mintrud_user",
        password="pass12345",
        user_type=CustomUser.UserType.MINTUD,
    )


@pytest.fixture
def regular_user(db):
    return CustomUser.objects.create_user(
        username="regular_user",
        password="pass12345",
        user_type=CustomUser.UserType.EMPLOYEE,
    )


@pytest.fixture
def xlsx_file():
    return SimpleUploadedFile(
        "test.xlsx",
        b"fake-bytes",
        content_type=(
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        ),
    )


# ---------- upload_labor_needs ----------


@pytest.mark.django_db
def test_upload_requires_login(client):
    url = reverse("mintrud:upload_labor_needs")
    response = client.get(url)
    assert response.status_code == 302
    assert "/accounts/login/" in response.url or "login" in response.url


@pytest.mark.django_db
def test_upload_forbidden_for_regular_user(client, regular_user):
    client.force_login(regular_user)
    url = reverse("mintrud:upload_labor_needs")
    response = client.get(url)
    # user_passes_test редиректит на login
    assert response.status_code == 302


@pytest.mark.django_db
def test_upload_page_opens_for_mintrud_user(client, mintrud_user):
    client.force_login(mintrud_user)
    url = reverse("mintrud:upload_labor_needs")
    response = client.get(url)
    assert response.status_code == 200
    assert "form" in response.context


@pytest.mark.django_db
def test_upload_post_calls_celery_task(client, mintrud_user, xlsx_file):
    client.force_login(mintrud_user)
    url = reverse("mintrud:upload_labor_needs")

    with mock.patch("apps.mintrud.views.process_labor_needs_file.delay") as delay_mock:
        delay_mock.return_value = mock.Mock(id="test-task-id")

        response = client.post(url, {"file": xlsx_file})

    assert response.status_code == 302
    assert response.url == reverse("mintrud:upload_labor_needs")

    # Задача вызвана с правильными аргументами
    assert delay_mock.call_count == 1
    kwargs = delay_mock.call_args.kwargs
    assert kwargs["source_name"] == "test.xlsx"
    assert kwargs["skip_zeros"] is False
    assert "file_name" in kwargs

    # Сообщение об успехе
    messages = list(response.wsgi_request._messages)
    assert any("test-task-id" in str(m) for m in messages)


@pytest.mark.django_db
def test_upload_post_skip_zeros(client, mintrud_user, xlsx_file):
    client.force_login(mintrud_user)
    url = reverse("mintrud:upload_labor_needs")

    with mock.patch("apps.mintrud.views.process_labor_needs_file.delay") as delay_mock:
        delay_mock.return_value = mock.Mock(id="t1")
        client.post(url, {"file": xlsx_file, "skip_zeros": "on"})

    assert delay_mock.call_args.kwargs["skip_zeros"] is True


@pytest.mark.django_db
def test_upload_post_without_file_does_not_call_task(client, mintrud_user):
    client.force_login(mintrud_user)
    url = reverse("mintrud:upload_labor_needs")

    with mock.patch("apps.mintrud.views.process_labor_needs_file.delay") as delay_mock:
        response = client.post(url, {})

    assert response.status_code == 200  # форма с ошибкой
    assert delay_mock.call_count == 0


# ---------- task_status ----------


@pytest.mark.django_db
def test_task_status_requires_login(client):
    url = reverse("mintrud:task_status", args=["abc"])
    response = client.get(url)
    assert response.status_code == 302


@pytest.mark.django_db
def test_task_status_forbidden_for_regular_user(client, regular_user):
    client.force_login(regular_user)
    url = reverse("mintrud:task_status", args=["abc"])
    response = client.get(url)
    assert response.status_code == 302


@pytest.mark.django_db
def test_task_status_pending(client, mintrud_user):
    client.force_login(mintrud_user)
    url = reverse("mintrud:task_status", args=["abc"])

    fake_result = mock.Mock()
    fake_result.state = "PENDING"
    fake_result.ready.return_value = False
    fake_result.successful.return_value = False

    with mock.patch("apps.mintrud.views.AsyncResult", return_value=fake_result):
        response = client.get(url)

    assert response.status_code == 200
    data = response.json()
    assert data["state"] == "PENDING"
    assert data["ready"] is False


@pytest.mark.django_db
def test_task_status_success(client, mintrud_user):
    client.force_login(mintrud_user)
    url = reverse("mintrud:task_status", args=["abc"])

    fake_result = mock.Mock()
    fake_result.state = "SUCCESS"
    fake_result.ready.return_value = True
    fake_result.successful.return_value = True
    fake_result.result = {
        "processed_sheets": 15,
        "total_rows": 345825,
        "skipped_sheets": [],
    }

    with mock.patch("apps.mintrud.views.AsyncResult", return_value=fake_result):
        response = client.get(url)

    data = response.json()
    assert data["state"] == "SUCCESS"
    assert data["ready"] is True
    assert data["result"]["total_rows"] == 345825


@pytest.mark.django_db
def test_task_status_failure(client, mintrud_user):
    client.force_login(mintrud_user)
    url = reverse("mintrud:task_status", args=["abc"])

    fake_result = mock.Mock()
    fake_result.state = "FAILURE"
    fake_result.ready.return_value = True
    fake_result.successful.return_value = False
    fake_result.result = "boom"
    fake_result.traceback = "trace"

    with mock.patch("apps.mintrud.views.AsyncResult", return_value=fake_result):
        response = client.get(url)

    data = response.json()
    assert data["state"] == "FAILURE"
    assert data["error"] == "boom"
