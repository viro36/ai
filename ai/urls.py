"""
URL configuration for ai project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from apps.esia_auth import views

urlpatterns = [
    # Главная страница
    path("", TemplateView.as_view(template_name="home.html"), name="home"),
    # Админка
    path("admin/", admin.site.urls),
    # ESIA аутентификация
    path("esia/login/", views.esia_login, name="esia_login"),
    path("esia/callback/", views.esia_callback, name="esia_callback"),
    path("esia/logout/", views.esia_logout, name="esia_logout"),
    # Нестандартная аутентификация
    path("accounts/", include("apps.accounts.urls")),
    # Стандартная аутентификация Django
    path("accounts/", include("django.contrib.auth.urls")),
    # Приложения
    path("", include("apps.organizations.urls")),
    # Опросы
    path("surveys/", include("apps.surveys.urls")),
    # Курсы
    path("courses/", include("apps.courses.urls")),
]
