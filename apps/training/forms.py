"""Formulários do módulo de treino.

Princípio: treinador vê formulários completos; atleta usa apenas
:class:`SessionExerciseExecutionForm` e :class:`SessionFeedbackForm`.

Limitamos o queryset de ``athlete`` nos forms a atletas que sejam do
treinador logado (via ``AthleteProfile.trainer``).
"""
from __future__ import annotations

from django import forms
from django.contrib.auth.models import User

from apps.accounts.models import AthleteProfile

from .models import (
    AccessoryTemplate, AthleteAnamnesis, ExerciseLibrary,
    PersonalRecord, RepScheme, SessionExercise, SessionFeedback,
    TrainingPlan, TrainingSession,
)


class StyledModelForm(forms.ModelForm):
    """Aplica classe CSS 'input' em todos widgets não-checkbox."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            widget = field.widget
            if isinstance(widget, (forms.CheckboxInput, forms.CheckboxSelectMultiple)):
                continue
            css = widget.attrs.get("class", "")
            widget.attrs["class"] = f"{css} input".strip()


def _athletes_of_trainer(trainer: User):
    """Atletas com AthleteProfile apontando para este treinador."""
    return User.objects.filter(athlete_profile__trainer=trainer).order_by("username")


# ---------------------------------------------------------------------------
# Plano
# ---------------------------------------------------------------------------


class TrainingPlanForm(StyledModelForm):
    class Meta:
        model = TrainingPlan
        fields = [
            "athlete", "name", "goal",
            "start_date", "meet_date",
            "weekly_frequency", "general_notes", "is_active",
        ]
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "meet_date": forms.DateInput(attrs={"type": "date"}),
            "general_notes": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, trainer: User | None = None, **kwargs):
        super().__init__(*args, **kwargs)
        if trainer is not None:
            self.fields["athlete"].queryset = _athletes_of_trainer(trainer)
            self.fields["athlete"].help_text = (
                "Se o atleta não aparece, cadastre-o em 'Meus atletas' antes."
            )


# ---------------------------------------------------------------------------
# Sessão
# ---------------------------------------------------------------------------


class TrainingSessionForm(StyledModelForm):
    class Meta:
        model = TrainingSession
        fields = ["label", "title", "scheduled_date", "completed", "notes"]
        widgets = {
            "scheduled_date": forms.DateInput(attrs={"type": "date"}),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }


# ---------------------------------------------------------------------------
# SessionExercise
# ---------------------------------------------------------------------------


class SessionExerciseCreateForm(StyledModelForm):
    """Adicionar exercício existente à sessão, inline na página."""

    class Meta:
        model = SessionExercise
        fields = [
            "exercise",
            "planned_sets", "planned_reps",
            "planned_load_percentage", "reference_1rm_kg",
            "planned_load_kg_manual",
            "planned_rpe", "rest_seconds",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["exercise"].queryset = ExerciseLibrary.objects.filter(
            is_active=True
        ).order_by("tier", "name")


class SessionExerciseFullForm(StyledModelForm):
    """Treinador edita todos os campos (planejado + executado)."""

    class Meta:
        model = SessionExercise
        fields = [
            "exercise", "order",
            "planned_sets", "planned_reps",
            "planned_load_percentage", "reference_1rm_kg", "planned_load_kg_manual",
            "planned_rpe", "rest_seconds",
            "actual_load_kg", "actual_reps", "actual_sets", "actual_rpe",
            "notes",
        ]
        widgets = {"notes": forms.Textarea(attrs={"rows": 2})}


class SessionExerciseExecutionForm(StyledModelForm):
    """Atleta edita apenas execução: carga feita, reps, séries, RPE."""

    class Meta:
        model = SessionExercise
        fields = ["actual_load_kg", "actual_reps", "actual_sets", "actual_rpe", "notes"]
        widgets = {"notes": forms.Textarea(attrs={"rows": 2})}


class CreateExerciseInlineForm(forms.ModelForm):
    """Cria novo exercício na biblioteca a partir da tela da sessão."""

    default_sets = forms.IntegerField(
        required=False, min_value=1, max_value=20, label="Séries iniciais",
        help_text="Quantas séries já adicionar ao criar.",
    )

    class Meta:
        model = ExerciseLibrary
        fields = ["name", "tier", "main_lift", "cues"]
        widgets = {"cues": forms.Textarea(attrs={"rows": 2})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            css = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = f"{css} input".strip()


# ---------------------------------------------------------------------------
# Feedback estruturado
# ---------------------------------------------------------------------------


class SessionFeedbackForm(StyledModelForm):
    """Feedback estruturado com perguntas objetivas."""

    class Meta:
        model = SessionFeedback
        fields = [
            "had_pain", "pain_description",
            "was_tired", "tired_description",
            "session_rpe", "sleep_hours", "bodyweight_kg",
            "general_notes",
        ]
        widgets = {"general_notes": forms.Textarea(attrs={"rows": 3})}

    def clean(self):
        data = super().clean()
        if data.get("had_pain") and not data.get("pain_description"):
            self.add_error(
                "pain_description",
                "Se sentiu dor, descreva brevemente.",
            )
        return data


# ---------------------------------------------------------------------------
# Acessórios, anamnese, PR
# ---------------------------------------------------------------------------


class AccessoryTemplateForm(StyledModelForm):
    class Meta:
        model = AccessoryTemplate
        fields = [
            "name", "exercise", "sets", "reps", "load_kg",
            "rpe", "rest_seconds", "notes", "is_active",
        ]
        widgets = {"notes": forms.Textarea(attrs={"rows": 2})}


class AthleteAnamnesisForm(StyledModelForm):
    class Meta:
        model = AthleteAnamnesis
        fields = [
            "athlete",
            "years_training", "years_competing", "best_meet_total",
            "injuries", "limitations", "medical_history",
            "training_goal", "observations",
        ]
        widgets = {
            "injuries": forms.Textarea(attrs={"rows": 3}),
            "limitations": forms.Textarea(attrs={"rows": 3}),
            "medical_history": forms.Textarea(attrs={"rows": 3}),
            "training_goal": forms.Textarea(attrs={"rows": 3}),
            "observations": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, trainer: User | None = None, **kwargs):
        super().__init__(*args, **kwargs)
        if trainer is not None:
            self.fields["athlete"].queryset = _athletes_of_trainer(trainer)


class PersonalRecordForm(StyledModelForm):
    class Meta:
        model = PersonalRecord
        fields = [
            "athlete", "exercise", "weight_kg", "reps", "rpe",
            "date", "context", "meet_name", "video_url", "notes",
        ]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}),
            "notes": forms.Textarea(attrs={"rows": 2}),
        }

    def __init__(self, *args, current_user: User | None = None, **kwargs):
        super().__init__(*args, **kwargs)
        if current_user and not current_user.is_superuser:
            self.fields["athlete"].queryset = _athletes_of_trainer(current_user) | User.objects.filter(pk=current_user.pk)


class RepSchemeForm(StyledModelForm):
    """Esquema de reps pré-salvo: ex.: '6×3', '3×10'."""

    class Meta:
        model = RepScheme
        fields = ["label", "sets", "reps", "is_default"]


class TrainingSessionForm2(StyledModelForm):
    """Form de sessão atualizado para incluir 'label' (TREINO A/B/C)."""

    class Meta:
        model = TrainingSession
        fields = ["label", "title", "scheduled_date", "completed", "notes"]
        widgets = {
            "scheduled_date": forms.DateInput(attrs={"type": "date"}),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }
