"""Views de auth, registro de treinador, gestão de atletas."""
from __future__ import annotations

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import CreateView, FormView, ListView, UpdateView

from .forms import (
    AthleteCreationForm, AthleteProfileEditForm,
    MyProfileForm, TrainerRegistrationForm,
)
from .models import AthleteProfile, Profile
from .permissions import TrainerRequiredMixin, is_trainer


class TrainerRegisterView(CreateView):
    """Registro público — cria um treinador."""

    template_name = "registration/register.html"
    form_class = TrainerRegistrationForm
    success_url = reverse_lazy("dashboard:home")

    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)
        messages.success(self.request, "Conta de treinador criada.")
        return response


class MyAthletesListView(LoginRequiredMixin, TrainerRequiredMixin, ListView):
    """Lista os atletas do treinador logado."""

    template_name = "accounts/athlete_list.html"
    context_object_name = "athlete_profiles"

    def get_queryset(self):
        return (
            AthleteProfile.objects
            .filter(trainer=self.request.user)
            .select_related("user")
            .order_by("user__first_name", "user__username")
        )


class AthleteCreateView(LoginRequiredMixin, TrainerRequiredMixin, FormView):
    """Treinador cria um novo atleta."""

    form_class = AthleteCreationForm
    template_name = "accounts/athlete_create.html"
    success_url = reverse_lazy("accounts:my_athletes")

    def form_valid(self, form):
        user = form.save(trainer=self.request.user)
        messages.success(
            self.request,
            f"Atleta '{user.username}' criado. "
            f"Senha inicial: {form.cleaned_data['initial_password']}",
        )
        return redirect("accounts:my_athletes")


class AthleteProfileEditView(LoginRequiredMixin, TrainerRequiredMixin, UpdateView):
    """Treinador edita o perfil de um atleta sob sua responsabilidade.

    Permite também resetar a senha do atleta — útil quando o atleta esquece.
    """

    model = AthleteProfile
    form_class = AthleteProfileEditForm
    template_name = "accounts/athlete_edit.html"
    success_url = reverse_lazy("accounts:my_athletes")

    def get_queryset(self):
        return AthleteProfile.objects.filter(trainer=self.request.user)

    def post(self, request, *args, **kwargs):
        # Tratar reset de senha como ação separada.
        if "reset_password" in request.POST:
            import secrets
            self.object = self.get_object()
            new_password = secrets.token_urlsafe(8)
            self.object.user.set_password(new_password)
            self.object.user.save()
            messages.success(
                request,
                f"Senha de {self.object.user.username} resetada para: {new_password}",
            )
            return redirect("accounts:athlete_edit", pk=self.object.pk)
        return super().post(request, *args, **kwargs)


class MyProfileView(LoginRequiredMixin, UpdateView):
    """Usuário logado edita seu próprio perfil (Profile: phone, bio, nome, email)."""

    form_class = MyProfileForm
    template_name = "accounts/my_profile.html"
    success_url = reverse_lazy("dashboard:home")

    def get_object(self, queryset=None):
        profile, _ = Profile.objects.get_or_create(user=self.request.user)
        return profile

    def form_valid(self, form):
        messages.success(self.request, "Perfil atualizado.")
        return super().form_valid(form)
