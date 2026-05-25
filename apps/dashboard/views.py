"""Views do painel: home, calculadoras IPF GL, tonelagem, PRs."""
from __future__ import annotations

from decimal import Decimal, InvalidOperation

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Max
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.generic import TemplateView

from apps.accounts.permissions import (
    is_athlete, is_trainer, user_can_view_plan,
)
from apps.training.models import (
    ExerciseLibrary, PersonalRecord, SessionFeedback,
    TrainingPlan, TrainingSession,
)

from . import scoring
from .tonnage import tonnage_for_plan


def _decimal_or_none(value):
    if value in (None, ""):
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError):
        return None


def _int_or_none(value):
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


class DashboardHomeView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard/home.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        today = timezone.localdate()

        if user.is_superuser:
            plans = TrainingPlan.objects.filter(is_active=True)
            sessions = TrainingSession.objects.filter(
                scheduled_date__gte=today, completed=False
            )
            prs = PersonalRecord.objects.all()
            feedbacks = SessionFeedback.objects.all()
        elif is_trainer(user):
            plans = TrainingPlan.objects.filter(is_active=True, trainer=user)
            sessions = TrainingSession.objects.filter(
                scheduled_date__gte=today, completed=False,
                week__plan__trainer=user,
            )
            prs = PersonalRecord.objects.filter(
                athlete__athlete_profile__trainer=user
            )
            feedbacks = SessionFeedback.objects.filter(
                session__week__plan__trainer=user
            )
        else:
            plans = TrainingPlan.objects.filter(is_active=True, athlete=user)
            sessions = TrainingSession.objects.filter(
                scheduled_date__gte=today, completed=False,
                week__plan__athlete=user,
            )
            prs = PersonalRecord.objects.filter(athlete=user)
            feedbacks = SessionFeedback.objects.filter(athlete=user)

        ctx.update({
            "is_trainer": is_trainer(user),
            "active_plans": plans.select_related("athlete", "trainer")[:6],
            "upcoming_sessions": sessions.select_related("week__plan")
                .order_by("scheduled_date")[:6],
            "recent_feedbacks": feedbacks.select_related(
                "session__week__plan", "athlete"
            ).order_by("-created_at")[:5],
            "recent_prs": prs.select_related("athlete", "exercise")
                .order_by("-date")[:6],
            "total_active_plans": plans.count(),
        })
        return ctx


class CalculatorsView(LoginRequiredMixin, TemplateView):
    """IPF GL + 1RM + warm-ups por %."""

    template_name = "dashboard/calculators.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        p = self.request.GET

        bodyweight = _decimal_or_none(p.get("bodyweight"))
        squat = _decimal_or_none(p.get("squat")) or Decimal("0")
        bench = _decimal_or_none(p.get("bench")) or Decimal("0")
        deadlift = _decimal_or_none(p.get("deadlift")) or Decimal("0")
        sex = p.get("sex", "M")
        equipment = p.get("equipment", "raw")
        event = p.get("event", "sbd")

        ipf_points = None
        total = squat + bench + deadlift
        if bodyweight and bodyweight > 0 and total > 0:
            try:
                ipf_points = scoring.calculate_ipf_gl_points(
                    total, bodyweight, sex, equipment, event,
                )
            except ValueError:
                ipf_points = None

        lifted = _decimal_or_none(p.get("lifted"))
        reps = _int_or_none(p.get("reps"))
        rpe = _decimal_or_none(p.get("rpe"))
        est_epley = est_brzycki = est_rpe = None
        if lifted and lifted > 0 and reps and reps >= 1:
            try:
                est_epley = scoring.estimate_1rm_epley(lifted, reps)
            except ValueError:
                pass
            try:
                est_brzycki = scoring.estimate_1rm_brzycki(lifted, reps)
            except ValueError:
                pass
            if rpe is not None:
                try:
                    est_rpe = scoring.estimate_1rm_from_rpe(lifted, reps, float(rpe))
                except ValueError:
                    pass

        target = _decimal_or_none(p.get("target"))
        warmup_sets = scoring.suggest_warmup_sets(target) if target and target > 0 else []

        ctx.update({
            "input_values": {k: p.get(k, "") for k in [
                "bodyweight", "squat", "bench", "deadlift",
                "lifted", "reps", "rpe", "target",
            ]},
            "sex": sex, "equipment": equipment, "event": event,
            "ipf_total": total if total > 0 else None,
            "ipf_points": ipf_points,
            "estimated_1rm_epley": est_epley,
            "estimated_1rm_brzycki": est_brzycki,
            "estimated_1rm_rpe": est_rpe,
            "warmup_sets": warmup_sets,
        })
        return ctx


class TonnageDashboardView(LoginRequiredMixin, TemplateView):
    """Dashboard de tonelagem por plano, com totais por movimento por semana."""

    template_name = "dashboard/tonnage.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user

        # Lista de planos que o usuário tem acesso.
        if user.is_superuser:
            plans_qs = TrainingPlan.objects.all()
        elif is_trainer(user):
            plans_qs = TrainingPlan.objects.filter(trainer=user)
        else:
            plans_qs = TrainingPlan.objects.filter(athlete=user)
        plans_qs = plans_qs.select_related("athlete").order_by("-is_active", "-created_at")

        selected_plan = None
        plan_pk = self.request.GET.get("plan")
        if plan_pk:
            try:
                selected_plan = plans_qs.get(pk=int(plan_pk))
            except (TrainingPlan.DoesNotExist, ValueError):
                selected_plan = None
        if selected_plan is None:
            selected_plan = plans_qs.first()

        weekly = tonnage_for_plan(selected_plan) if selected_plan else []

        # Totais agregados.
        total_squat = sum((w.squat_kg for w in weekly), Decimal("0"))
        total_bench = sum((w.bench_kg for w in weekly), Decimal("0"))
        total_deadlift = sum((w.deadlift_kg for w in weekly), Decimal("0"))

        # Maior valor pra escalar as barras no gráfico simples.
        max_value = Decimal("0")
        for w in weekly:
            for v in (w.squat_kg, w.bench_kg, w.deadlift_kg):
                if v > max_value:
                    max_value = v

        ctx.update({
            "plans": plans_qs,
            "selected_plan": selected_plan,
            "weekly_tonnage": weekly,
            "total_squat": total_squat,
            "total_bench": total_bench,
            "total_deadlift": total_deadlift,
            "total_all": total_squat + total_bench + total_deadlift,
            "max_value": max_value,
        })
        return ctx


class PRLogView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard/pr_log.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user

        if user.is_superuser:
            qs = PersonalRecord.objects.all()
        elif is_trainer(user):
            qs = PersonalRecord.objects.filter(
                athlete__athlete_profile__trainer=user
            )
        else:
            qs = PersonalRecord.objects.filter(athlete=user)

        ctx["all_prs"] = qs.select_related("athlete", "exercise")[:50]

        main_lifts = (
            qs.filter(exercise__tier=ExerciseLibrary.Tier.PRINCIPAL)
              .values("athlete__username", "athlete__first_name",
                      "exercise__main_lift")
              .annotate(best=Max("weight_kg"))
              .order_by("athlete__username", "exercise__main_lift")
        )
        ctx["main_lifts"] = list(main_lifts)
        return ctx


class RPEChartView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard/rpe_chart.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["rpes"] = [6, 7, 8, 9, 10]
        ctx["reps_range"] = list(range(1, 11))
        ctx["rpe_table"] = scoring._RPE_PERCENTAGES  # noqa: SLF001
        return ctx
