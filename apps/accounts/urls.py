"""URLs do app accounts."""
from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("register/", views.TrainerRegisterView.as_view(), name="register"),
    path("me/", views.MyProfileView.as_view(), name="my_profile"),
    path("atletas/", views.MyAthletesListView.as_view(), name="my_athletes"),
    path("atletas/novo/", views.AthleteCreateView.as_view(), name="athlete_create"),
    path("atletas/<int:pk>/editar/", views.AthleteProfileEditView.as_view(), name="athlete_edit"),
]
