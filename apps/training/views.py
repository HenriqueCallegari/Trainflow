"""Views do módulo de treino, com permissões treinador × atleta.

- Treinador gerencia planos/semanas/sessões/exercícios livremente.
- Atleta vê apenas os seus próprios planos/sessões e edita somente
  os campos de execução (carga feita, reps, séries, RPE real).
"""
from __future__ import annotations

from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.http import Http404, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.generic import (
    CreateView, DeleteView, ListView, TemplateView, UpdateView,
)

from apps.accounts.permissions import (
    TrainerRequiredMixin, is_athlete, is_trainer,
    user_can_view_plan, user_manages_plan,
)

from .forms import (
    AccessoryTemplateForm, AthleteAnamnesisForm,
    CreateExerciseInlineForm, PersonalRecordForm, RepSchemeForm,
    SessionExerciseCreateForm, SessionExerciseExecutionForm,
    SessionExerciseFullForm, SessionFeedbackForm,
    TrainingPlanForm, TrainingSessionForm,
)
from .models import (
    AccessoryTemplate, AthleteAnamnesis, ExerciseLibrary,
    PersonalRecord, RepScheme, SessionExercise, SessionFeedback,
    TrainingPlan, TrainingSession, TrainingWeek,
)


# ============================================================================
# Planos
# ============================================================================


class TrainingPlanListView(LoginRequiredMixin, ListView):
    """Treinador vê seus planos; atleta vê os planos em que é atleta."""

    model = TrainingPlan
    template_name = "training/plan_list.html"
    context_object_name = "plans"

    def get_queryset(self):
        user = self.request.user
        qs = TrainingPlan.objects.select_related("athlete", "trainer")
        if user.is_superuser:
            return qs
        if is_trainer(user):
            return qs.filter(trainer=user)
        return qs.filter(athlete=user)


class TrainingPlanDetailView(LoginRequiredMixin, TemplateView):
    """Visão do plano em calendário por data real, com todas as semanas."""

    template_name = "training/plan_detail.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        plan = get_object_or_404(
            TrainingPlan.objects.select_related("athlete", "trainer"),
            pk=self.kwargs["pk"],
        )
        if not user_can_view_plan(self.request.user, plan):
            raise Http404

        weeks = (
            plan.weeks.prefetch_related(
                "sessions__session_exercises__exercise",
                "sessions__feedback",
            )
            .order_by("week_number")
        )

        ctx.update({
            "plan": plan,
            "weeks": list(weeks),
            "can_edit": user_manages_plan(self.request.user, plan),
        })
        return ctx


class TrainingPlanCreateView(LoginRequiredMixin, TrainerRequiredMixin, CreateView):
    """Criação de plano — só treinador. Trainer é preenchido automaticamente."""

    model = TrainingPlan
    form_class = TrainingPlanForm
    template_name = "training/form.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["trainer"] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.trainer = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("training:plan_detail", kwargs={"pk": self.object.pk})


class TrainingPlanUpdateView(LoginRequiredMixin, TrainerRequiredMixin, UpdateView):
    model = TrainingPlan
    form_class = TrainingPlanForm
    template_name = "training/form.html"

    def get_queryset(self):
        return TrainingPlan.objects.filter(trainer=self.request.user)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["trainer"] = self.request.user
        return kwargs

    def get_success_url(self):
        return reverse_lazy("training:plan_detail", kwargs={"pk": self.object.pk})


class TrainingPlanDeleteView(LoginRequiredMixin, TrainerRequiredMixin, DeleteView):
    model = TrainingPlan
    template_name = "training/confirm_delete.html"
    success_url = reverse_lazy("training:plan_list")

    def get_queryset(self):
        return TrainingPlan.objects.filter(trainer=self.request.user)


# ============================================================================
# Semanas — gerenciamento simplificado (inline + e ×)
# ============================================================================


@login_required
@require_POST
def plan_add_week(request, pk: int):
    """Adiciona uma semana ao fim do plano. Cria sessões vazias por frequência."""
    plan = get_object_or_404(TrainingPlan, pk=pk)
    if not user_manages_plan(request.user, plan):
        return HttpResponseForbidden()

    with transaction.atomic():
        last = plan.weeks.order_by("-week_number").first()
        next_num = (last.week_number if last else 0) + 1
        if last:
            start = last.end_date + timedelta(days=1)
        else:
            start = plan.start_date
        end = start + timedelta(days=6)

        week = TrainingWeek.objects.create(
            plan=plan, week_number=next_num,
            start_date=start, end_date=end,
        )
        _create_default_sessions_for_week(week, plan.weekly_frequency)

    messages.success(request, f"Semana {next_num} adicionada.")
    return redirect("training:plan_detail", pk=plan.pk)


@login_required
@require_POST
def plan_remove_week(request, pk: int, week_number: int):
    """Remove a semana N do plano (cascata em sessões/exercícios)."""
    plan = get_object_or_404(TrainingPlan, pk=pk)
    if not user_manages_plan(request.user, plan):
        return HttpResponseForbidden()

    week = get_object_or_404(TrainingWeek, plan=plan, week_number=week_number)
    week.delete()
    messages.success(request, f"Semana {week_number} removida.")
    return redirect("training:plan_detail", pk=plan.pk)


def _create_default_sessions_for_week(week: TrainingWeek, frequency: int) -> None:
    """Cria sessões vazias distribuídas na semana, conforme a frequência."""
    frequency = max(1, min(frequency, 7))
    if frequency == 1:
        offsets = [0]
    else:
        offsets = sorted({round(i * 6 / (frequency - 1)) for i in range(frequency)})
    for offset in offsets:
        TrainingSession.objects.create(
            week=week,
            scheduled_date=week.start_date + timedelta(days=offset),
        )


# ============================================================================
# Sessões
# ============================================================================


class TrainingSessionDetailView(LoginRequiredMixin, TemplateView):
    """Detalhe da sessão. Treinador edita tudo; atleta edita só 'executado'."""

    template_name = "training/session_detail.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        session = get_object_or_404(
            TrainingSession.objects.select_related("week__plan")
            .prefetch_related("session_exercises__exercise"),
            pk=self.kwargs["pk"],
        )
        plan = session.week.plan
        if not user_can_view_plan(self.request.user, plan):
            raise Http404

        can_edit = user_manages_plan(self.request.user, plan)

        ctx.update({
            "session": session,
            "plan": plan,
            "can_edit": can_edit,
            "can_feedback": session.week.plan.athlete_id == self.request.user.id,
            "add_exercise_form": self._build_add_exercise_form(session) if can_edit else None,
            "create_exercise_form": CreateExerciseInlineForm() if can_edit else None,
            "rep_schemes": (
                RepScheme.objects.filter(trainer=plan.trainer)
                if can_edit else RepScheme.objects.none()
            ),
            "feedback": getattr(session, "feedback", None),
            "feedback_form": self._build_feedback_form(session),
            "ml_squat": ExerciseLibrary.MainLift.SQUAT,
            "ml_bench": ExerciseLibrary.MainLift.BENCH,
            "ml_deadlift": ExerciseLibrary.MainLift.DEADLIFT,
        })
        return ctx

    def _build_add_exercise_form(self, session):
        """Pré-preenche com reps/séries do último exercício adicionado."""
        last = (
            session.session_exercises.order_by("-order", "-id")
            .first()
        )
        initial = {}
        if last:
            initial = {
                "planned_sets": last.planned_sets,
                "planned_reps": last.planned_reps,
                "planned_rpe": last.planned_rpe,
                "rest_seconds": last.rest_seconds,
            }
        return SessionExerciseCreateForm(initial=initial)

    def _build_feedback_form(self, session: TrainingSession):
        if session.week.plan.athlete_id != self.request.user.id:
            return None
        try:
            fb = session.feedback
        except SessionFeedback.DoesNotExist:
            fb = None
        return SessionFeedbackForm(instance=fb)


class TrainingSessionUpdateView(LoginRequiredMixin, UpdateView):
    """Editar título/data/notas da sessão (só treinador)."""

    model = TrainingSession
    form_class = TrainingSessionForm
    template_name = "training/form.html"

    def get_queryset(self):
        return TrainingSession.objects.filter(week__plan__trainer=self.request.user)

    def get_success_url(self):
        return reverse_lazy("training:session_detail", kwargs={"pk": self.object.pk})


@login_required
@require_POST
def session_add(request, plan_pk: int, week_number: int):
    """Adiciona nova sessão em data específica (treinador)."""
    plan = get_object_or_404(TrainingPlan, pk=plan_pk)
    if not user_manages_plan(request.user, plan):
        return HttpResponseForbidden()

    week = get_object_or_404(TrainingWeek, plan=plan, week_number=week_number)
    scheduled = request.POST.get("scheduled_date") or week.start_date.isoformat()
    label = request.POST.get("label", "").strip()
    TrainingSession.objects.create(
        week=week, scheduled_date=scheduled, label=label,
    )
    messages.success(request, "Sessão adicionada.")
    return redirect("training:plan_detail", pk=plan.pk)


@login_required
@require_POST
def session_toggle_complete(request, pk: int):
    """Marca/desmarca sessão como concluída."""
    session = get_object_or_404(TrainingSession.objects.select_related("week__plan"), pk=pk)
    plan = session.week.plan
    if not (user_manages_plan(request.user, plan) or plan.athlete_id == request.user.id):
        return HttpResponseForbidden()
    session.completed = not session.completed
    session.save(update_fields=["completed"])
    return redirect("training:session_detail", pk=pk)


@login_required
@require_POST
def session_delete_inline(request, pk: int):
    """Remove a sessão, volta para o detalhe do plano."""
    session = get_object_or_404(TrainingSession.objects.select_related("week__plan"), pk=pk)
    plan = session.week.plan
    if not user_manages_plan(request.user, plan):
        return HttpResponseForbidden()
    session.delete()
    messages.success(request, "Sessão removida.")
    return redirect("training:plan_detail", pk=plan.pk)


# ============================================================================
# Exercícios da sessão
# ============================================================================


@login_required
@require_POST
def session_add_exercise(request, pk: int):
    """Adiciona exercício a uma sessão (inline)."""
    session = get_object_or_404(TrainingSession.objects.select_related("week__plan"), pk=pk)
    plan = session.week.plan
    if not user_manages_plan(request.user, plan):
        return HttpResponseForbidden()

    form = SessionExerciseCreateForm(request.POST)
    if form.is_valid():
        se = form.save(commit=False)
        se.session = session
        last_order = (
            session.session_exercises.order_by("-order")
            .values_list("order", flat=True).first()
            or 0
        )
        se.order = last_order + 1
        se.save()
        messages.success(request, f"Exercício '{se.exercise.name}' adicionado.")
    else:
        messages.error(
            request, "Erros: " + "; ".join(
                f"{k}: {', '.join(v)}" for k, v in form.errors.items()
            )
        )
    return redirect("training:session_detail", pk=pk)


@login_required
@require_POST
def session_create_exercise_inline(request, pk: int):
    """Cria novo exercício na biblioteca e já adiciona à sessão."""
    session = get_object_or_404(TrainingSession.objects.select_related("week__plan"), pk=pk)
    plan = session.week.plan
    if not user_manages_plan(request.user, plan):
        return HttpResponseForbidden()

    form = CreateExerciseInlineForm(request.POST)
    if form.is_valid():
        exercise = form.save()
        last_order = (
            session.session_exercises.order_by("-order")
            .values_list("order", flat=True).first()
            or 0
        )
        SessionExercise.objects.create(
            session=session, exercise=exercise, order=last_order + 1,
            planned_sets=form.cleaned_data.get("default_sets") or 3,
        )
        messages.success(request, f"Exercício '{exercise.name}' criado e adicionado.")
    else:
        messages.error(
            request, "Erros: " + "; ".join(
                f"{k}: {', '.join(v)}" for k, v in form.errors.items()
            )
        )
    return redirect("training:session_detail", pk=pk)


class SessionExerciseUpdateView(LoginRequiredMixin, UpdateView):
    """Treinador edita tudo; atleta edita apenas execução (carga/reps/sets/rpe)."""

    model = SessionExercise
    template_name = "training/exercise_edit.html"

    def get_form_class(self):
        se = self.get_object()
        plan = se.session.week.plan
        if user_manages_plan(self.request.user, plan):
            return SessionExerciseFullForm
        if plan.athlete_id == self.request.user.id:
            return SessionExerciseExecutionForm
        raise Http404

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return SessionExercise.objects.all()
        return SessionExercise.objects.filter(
            models_filter_or_athlete(user)
        )

    def get_success_url(self):
        return reverse("training:session_detail", kwargs={"pk": self.object.session_id})


def models_filter_or_athlete(user):
    """Q para permitir ao treinador editar seus planos e ao atleta só os próprios."""
    from django.db.models import Q
    return Q(session__week__plan__trainer=user) | Q(session__week__plan__athlete=user)


@login_required
@require_POST
def session_exercise_delete(request, pk: int):
    se = get_object_or_404(
        SessionExercise.objects.select_related("session__week__plan"), pk=pk,
    )
    plan = se.session.week.plan
    if not user_manages_plan(request.user, plan):
        return HttpResponseForbidden()
    session_pk = se.session_id
    se.delete()
    messages.success(request, "Exercício removido.")
    return redirect("training:session_detail", pk=session_pk)


# ============================================================================
# Feedback estruturado (atleta)
# ============================================================================


@login_required
@require_POST
def session_submit_feedback(request, pk: int):
    """Atleta envia/atualiza feedback da sessão."""
    session = get_object_or_404(TrainingSession.objects.select_related("week__plan"), pk=pk)
    plan = session.week.plan
    if plan.athlete_id != request.user.id and not request.user.is_superuser:
        return HttpResponseForbidden()

    try:
        fb = session.feedback
    except SessionFeedback.DoesNotExist:
        fb = None

    form = SessionFeedbackForm(request.POST, instance=fb)
    if form.is_valid():
        obj = form.save(commit=False)
        obj.session = session
        obj.athlete = request.user
        obj.save()
        # Marcar sessão como concluída automaticamente.
        if not session.completed:
            session.completed = True
            session.save(update_fields=["completed"])
        messages.success(request, "Feedback registrado.")
    else:
        messages.error(request, "Confira os campos do feedback.")
    return redirect("training:session_detail", pk=pk)


@login_required
@require_POST
def session_feedback_respond(request, pk: int):
    """Treinador responde ao feedback."""
    feedback = get_object_or_404(
        SessionFeedback.objects.select_related("session__week__plan"), pk=pk
    )
    plan = feedback.session.week.plan
    if not user_manages_plan(request.user, plan):
        return HttpResponseForbidden()

    feedback.trainer_response = request.POST.get("trainer_response", "").strip()
    feedback.save(update_fields=["trainer_response"])
    messages.success(request, "Resposta enviada.")
    return redirect("training:session_detail", pk=feedback.session_id)


# ============================================================================
# Biblioteca de exercícios (treinador)
# ============================================================================


class ExerciseLibraryListView(LoginRequiredMixin, TrainerRequiredMixin, ListView):
    model = ExerciseLibrary
    template_name = "training/exercise_list.html"
    context_object_name = "exercises"

    def get_queryset(self):
        qs = ExerciseLibrary.objects.all()
        tier = self.request.GET.get("tier")
        if tier:
            qs = qs.filter(tier=tier)
        query = self.request.GET.get("q", "").strip()
        if query:
            qs = qs.filter(name__icontains=query)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["tiers"] = ExerciseLibrary.Tier.choices
        ctx["active_tier"] = self.request.GET.get("tier", "")
        ctx["query"] = self.request.GET.get("q", "")
        return ctx


class ExerciseLibraryCreateView(LoginRequiredMixin, TrainerRequiredMixin, CreateView):
    model = ExerciseLibrary
    fields = ["name", "tier", "main_lift", "cues", "video_url", "is_active"]
    template_name = "training/form.html"
    success_url = reverse_lazy("training:exercise_list")


class ExerciseLibraryUpdateView(LoginRequiredMixin, TrainerRequiredMixin, UpdateView):
    model = ExerciseLibrary
    fields = ["name", "tier", "main_lift", "cues", "video_url", "is_active"]
    template_name = "training/form.html"
    success_url = reverse_lazy("training:exercise_list")


class ExerciseLibraryDeleteView(LoginRequiredMixin, TrainerRequiredMixin, DeleteView):
    model = ExerciseLibrary
    template_name = "training/confirm_delete.html"
    success_url = reverse_lazy("training:exercise_list")


# ============================================================================
# Templates de acessórios (treinador)
# ============================================================================


class AccessoryTemplateListView(LoginRequiredMixin, TrainerRequiredMixin, ListView):
    model = AccessoryTemplate
    template_name = "training/template_list.html"
    context_object_name = "templates"

    def get_queryset(self):
        return AccessoryTemplate.objects.filter(trainer=self.request.user).select_related("exercise")


class AccessoryTemplateCreateView(LoginRequiredMixin, TrainerRequiredMixin, CreateView):
    model = AccessoryTemplate
    form_class = AccessoryTemplateForm
    template_name = "training/form.html"
    success_url = reverse_lazy("training:template_list")

    def form_valid(self, form):
        form.instance.trainer = self.request.user
        return super().form_valid(form)


class AccessoryTemplateUpdateView(LoginRequiredMixin, TrainerRequiredMixin, UpdateView):
    model = AccessoryTemplate
    form_class = AccessoryTemplateForm
    template_name = "training/form.html"
    success_url = reverse_lazy("training:template_list")

    def get_queryset(self):
        return AccessoryTemplate.objects.filter(trainer=self.request.user)


class AccessoryTemplateDeleteView(LoginRequiredMixin, TrainerRequiredMixin, DeleteView):
    model = AccessoryTemplate
    template_name = "training/confirm_delete.html"
    success_url = reverse_lazy("training:template_list")

    def get_queryset(self):
        return AccessoryTemplate.objects.filter(trainer=self.request.user)


# ============================================================================
# Anamnese (treinador)
# ============================================================================


class AthleteAnamnesisListView(LoginRequiredMixin, ListView):
    model = AthleteAnamnesis
    template_name = "training/anamnesis_list.html"
    context_object_name = "anamneses"

    def get_queryset(self):
        user = self.request.user
        qs = AthleteAnamnesis.objects.select_related("athlete", "trainer")
        if user.is_superuser:
            return qs
        if is_trainer(user):
            return qs.filter(trainer=user)
        return qs.filter(athlete=user)


class AthleteAnamnesisCreateView(LoginRequiredMixin, TrainerRequiredMixin, CreateView):
    model = AthleteAnamnesis
    form_class = AthleteAnamnesisForm
    template_name = "training/form.html"
    success_url = reverse_lazy("training:anamnesis_list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["trainer"] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.trainer = self.request.user
        return super().form_valid(form)


class AthleteAnamnesisUpdateView(LoginRequiredMixin, TrainerRequiredMixin, UpdateView):
    model = AthleteAnamnesis
    form_class = AthleteAnamnesisForm
    template_name = "training/form.html"
    success_url = reverse_lazy("training:anamnesis_list")

    def get_queryset(self):
        return AthleteAnamnesis.objects.filter(trainer=self.request.user)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["trainer"] = self.request.user
        return kwargs


# ============================================================================
# PRs
# ============================================================================


class PersonalRecordListView(LoginRequiredMixin, ListView):
    model = PersonalRecord
    template_name = "training/pr_list.html"
    context_object_name = "prs"
    paginate_by = 30

    def get_queryset(self):
        user = self.request.user
        qs = PersonalRecord.objects.select_related("athlete", "exercise")
        if user.is_superuser:
            return qs
        if is_trainer(user):
            return qs.filter(athlete__athlete_profile__trainer=user)
        return qs.filter(athlete=user)


class PersonalRecordCreateView(LoginRequiredMixin, CreateView):
    model = PersonalRecord
    form_class = PersonalRecordForm
    template_name = "training/form.html"
    success_url = reverse_lazy("training:pr_list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["current_user"] = self.request.user
        return kwargs


class PersonalRecordUpdateView(LoginRequiredMixin, UpdateView):
    model = PersonalRecord
    form_class = PersonalRecordForm
    template_name = "training/form.html"
    success_url = reverse_lazy("training:pr_list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["current_user"] = self.request.user
        return kwargs


class PersonalRecordDeleteView(LoginRequiredMixin, DeleteView):
    model = PersonalRecord
    template_name = "training/confirm_delete.html"
    success_url = reverse_lazy("training:pr_list")


# ============================================================================
# Mover exercício na ordem (↑ / ↓)
# ============================================================================


@login_required
@require_POST
def session_exercise_move(request, pk: int, direction: str):
    """Move exercício uma posição para cima ('up') ou baixo ('down').

    Faz um swap simples com o vizinho. Mantém o resto da ordem.
    """
    se = get_object_or_404(
        SessionExercise.objects.select_related("session__week__plan"), pk=pk,
    )
    plan = se.session.week.plan
    if not user_manages_plan(request.user, plan):
        return HttpResponseForbidden()

    siblings = list(
        se.session.session_exercises.order_by("order", "id")
    )
    idx = next((i for i, x in enumerate(siblings) if x.id == se.id), None)
    if idx is None:
        return redirect("training:session_detail", pk=se.session_id)

    if direction == "up" and idx > 0:
        other = siblings[idx - 1]
    elif direction == "down" and idx < len(siblings) - 1:
        other = siblings[idx + 1]
    else:
        return redirect("training:session_detail", pk=se.session_id)

    se.order, other.order = other.order, se.order
    SessionExercise.objects.bulk_update([se, other], ["order"])
    return redirect("training:session_detail", pk=se.session_id)


# ============================================================================
# Reps pré-salvas (CRUD do treinador)
# ============================================================================


class RepSchemeListView(LoginRequiredMixin, TrainerRequiredMixin, ListView):
    model = RepScheme
    template_name = "training/repscheme_list.html"
    context_object_name = "schemes"

    def get_queryset(self):
        return RepScheme.objects.filter(trainer=self.request.user)


class RepSchemeCreateView(LoginRequiredMixin, TrainerRequiredMixin, CreateView):
    model = RepScheme
    form_class = RepSchemeForm
    template_name = "training/form.html"
    success_url = reverse_lazy("training:repscheme_list")

    def form_valid(self, form):
        form.instance.trainer = self.request.user
        return super().form_valid(form)


class RepSchemeUpdateView(LoginRequiredMixin, TrainerRequiredMixin, UpdateView):
    model = RepScheme
    form_class = RepSchemeForm
    template_name = "training/form.html"
    success_url = reverse_lazy("training:repscheme_list")

    def get_queryset(self):
        return RepScheme.objects.filter(trainer=self.request.user)


class RepSchemeDeleteView(LoginRequiredMixin, TrainerRequiredMixin, DeleteView):
    model = RepScheme
    template_name = "training/confirm_delete.html"
    success_url = reverse_lazy("training:repscheme_list")

    def get_queryset(self):
        return RepScheme.objects.filter(trainer=self.request.user)
