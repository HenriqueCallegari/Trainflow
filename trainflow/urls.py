"""URLs de mais alto nível do TrainFlow."""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    # Views padrão de autenticação (login, logout, troca de senha).
    path("accounts/", include("django.contrib.auth.urls")),
    path("accounts/", include("apps.accounts.urls")),
    path("treinos/", include("apps.training.urls")),
    path("", include("apps.dashboard.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
