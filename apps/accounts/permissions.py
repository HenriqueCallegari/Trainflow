"""Permissões centralizadas: quem pode editar planos, sessões, exercícios.

Regras básicas:
- **Treinador** gerencia os planos dos atletas sob sua responsabilidade.
- **Atleta** pode ver seus próprios planos e sessões, e editar apenas os
  campos ``actual_load_kg``, ``actual_reps``, ``actual_sets`` e ``actual_rpe``
  em cada :class:`SessionExercise` — além de registrar seu próprio feedback.
- Superusuários podem tudo.
"""
from __future__ import annotations

from django.contrib.auth.mixins import UserPassesTestMixin
from django.http import Http404, HttpResponseForbidden

from apps.accounts.models import Profile


def is_trainer(user) -> bool:
    """True se o usuário autenticado for treinador (ou superuser)."""
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    profile = getattr(user, "profile", None)
    return profile is not None and profile.role == Profile.Role.TRAINER


def is_athlete(user) -> bool:
    """True se for atleta (ou seja, NÃO treinador e NÃO superuser)."""
    if not user.is_authenticated:
        return False
    profile = getattr(user, "profile", None)
    return profile is not None and profile.role == Profile.Role.ATHLETE


def user_manages_plan(user, plan) -> bool:
    """Treinador pode gerenciar planos em que figure como trainer."""
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return plan.trainer_id == user.id


def user_can_view_plan(user, plan) -> bool:
    """Treinador (do plano) ou atleta (do plano) pode ver."""
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return plan.trainer_id == user.id or plan.athlete_id == user.id


class TrainerRequiredMixin(UserPassesTestMixin):
    """CBV mixin: exige que o usuário seja treinador."""

    def test_func(self) -> bool:
        return is_trainer(self.request.user)

    def handle_no_permission(self):
        from django.shortcuts import redirect
        if not self.request.user.is_authenticated:
            return redirect("login")
        return HttpResponseForbidden(
            "Esta área é restrita a treinadores."
        )


def require_plan_access(plan, user, *, require_edit: bool = False):
    """Helper para views function-based. Levanta Http404 se não autorizado."""
    if require_edit:
        if not user_manages_plan(user, plan):
            raise Http404
    else:
        if not user_can_view_plan(user, plan):
            raise Http404
