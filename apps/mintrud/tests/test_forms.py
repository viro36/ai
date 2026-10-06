import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.mintrud.forms import UploadFileForm


@pytest.mark.django_db
def test_form_valid_with_xlsx():
    f = SimpleUploadedFile(
        "test.xlsx",
        b"fake-bytes",
        content_type=(
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        ),
    )
    form = UploadFileForm(files={"file": f})
    assert form.is_valid()


@pytest.mark.django_db
def test_form_invalid_without_file():
    form = UploadFileForm(files={})
    assert not form.is_valid()
    assert "file" in form.errors
