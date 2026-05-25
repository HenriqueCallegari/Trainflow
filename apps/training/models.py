"""Modelos de programação de treino para powerlifting.

Hierarquia: ``TrainingPlan`` → ``TrainingWeek`` → ``TrainingSession`` → ``SessionExercise``.

Três tiers em :class:`ExerciseLibrary.Tier`:

- **PRINCIPAL**: os três da prova (agacho, supino, terra de competição).
- **PRIMARY_VARIATION**: variações que contam na tonelagem do movimento-pai
  (supino fechado conta como supino; deficit conta como terra).
- **ACCESSORY**: acessório puro (remada, rosca, core). Não entra na tonelagem.

Tonelagem = ``actual_load_kg × actual_reps × actual_sets``, somada por
semana e por ``main_lift``.

``SessionFeedback`` é o feedback estruturado do atleta após a sessão.
"""
from __future__ import annotations

from decimal import Decimal

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone


class ExerciseLibrary(models.Model):
    """Biblioteca de exercícios, classificada em três tiers."""

    class Tier(models.TextChoices):
        PRINCIPAL = "principal", "Principal (SBD)"
        PRIMARY_VARIATION = "primary_var", "Primeira ordem (variação)"
        ACCESSORY = "accessory", "Acessório"

    class MainLift(models.TextChoices):
        """Movimento-pai — usado para agrupar tonelagem."""

        SQUAT = "squat", "Agachamento"
        BENCH = "bench", "Supino"
        DEADLIFT = "deadlift", "Terra"
        NONE = "none", "Outro / Acessório"

    name = models.CharField(max_length=120, unique=True)
    tier = models.CharField(
        max_length=20, choices=Tier.choices, default=Tier.ACCESSORY,
        verbose_name="Classificação",
    )
    main_lift = models.CharField(
        max_length=20, choices=MainLift.choices, default=MainLift.NONE,
        verbose_name="Movimento-pai",
        help_text="Usado na tonelagem. Ex.: supino fechado tem movimento-pai 'Supino'.",
    )
    cues = models.TextField(blank=True, verbose_name="Cues técnicos")
    video_url = models.URLField(blank=True, verbose_name="Vídeo demonstrativo")
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["tier", "main_lift", "name"]
        verbose_name = "Exercício"
        verbose_name_plural = "Biblioteca de exercícios"

    def __str__(self) -> str:
        return self.name

    @property
    def counts_in_tonnage(self) -> bool:
        """True se este exercício entra no cálculo de tonelagem."""
        return (
            self.tier in {self.Tier.PRINCIPAL, self.Tier.PRIMARY_VARIATION}
            and self.main_lift != self.MainLift.NONE
        )

    @property
    def uses_percentage(self) -> bool:
        """True para principais e variações primárias (usam % do 1RM)."""
        return self.tier in {self.Tier.PRINCIPAL, self.Tier.PRIMARY_VARIATION}


class RepScheme(models.Model):
    """Esquema de reps pré-salvo (ex.: '6×3', '3×10')."""

    trainer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="rep_schemes",
    )
    label = models.CharField(
        max_length=20, verbose_name="Padrão",
        help_text="Ex.: '6×3', '3×10', '5×5'.",
    )
    sets = models.PositiveSmallIntegerField(default=3, verbose_name="Séries")
    reps = models.CharField(max_length=20, verbose_name="Reps")
    is_default = models.BooleanField(default=False, verbose_name="Padrão favorito")

    class Meta:
        ordering = ["-is_default", "label"]
        unique_together = [("trainer", "label")]
        verbose_name = "Esquema de reps"
        verbose_name_plural = "Esquemas de reps"

    def __str__(self) -> str:
        return self.label


class TrainingPlan(models.Model):
    """Plano (macrociclo) de um atleta, conduzido por um treinador."""

    athlete = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name="plans_as_athlete", verbose_name="Atleta",
    )
    trainer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name="plans_as_trainer", verbose_name="Treinador(a)",
    )
    name = models.CharField(max_length=150, verbose_name="Nome do plano")
    goal = models.CharField(max_length=200, blank=True, verbose_name="Objetivo")
    start_date = models.DateField(default=timezone.localdate, verbose_name="Início")
    meet_date = models.DateField(null=True, blank=True, verbose_name="Data da competição")
    weekly_frequency = models.PositiveSmallIntegerField(
        default=4,
        validators=[MinValueValidator(1), MaxValueValidator(7)],
        verbose_name="Treinos por semana",
    )
    general_notes = models.TextField(blank=True, verbose_name="Observações gerais")
    is_active = models.BooleanField(default=True, verbose_name="Ativo")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-is_active", "-created_at"]
        verbose_name = "Plano de treino"
        verbose_name_plural = "Planos de treino"

    def __str__(self) -> str:
        return self.name

    @property
    def total_weeks(self) -> int:
        return self.weeks.count()

    @property
    def weeks_until_meet(self) -> int | None:
        if not self.meet_date:
            return None
        delta = self.meet_date - timezone.localdate()
        return max(0, delta.days // 7)


class TrainingWeek(models.Model):
    """Semana de treino dentro de um plano."""

    class BlockType(models.TextChoices):
        ACCUMULATION = "accumulation", "Acumulação"
        INTENSIFICATION = "intensification", "Intensificação"
        PEAKING = "peaking", "Peaking"
        DELOAD = "deload", "Deload"
        TEST = "test", "Teste de máximas"

    plan = models.ForeignKey(TrainingPlan, on_delete=models.CASCADE, related_name="weeks")
    week_number = models.PositiveIntegerField(verbose_name="Semana")
    start_date = models.DateField(verbose_name="Início da semana")
    end_date = models.DateField(verbose_name="Fim da semana")
    block_type = models.CharField(
        max_length=20, choices=BlockType.choices, default=BlockType.ACCUMULATION,
        verbose_name="Tipo de bloco",
    )
    focus = models.CharField(max_length=150, blank=True, verbose_name="Foco")
    notes = models.TextField(blank=True, verbose_name="Notas da semana")

    class Meta:
        ordering = ["week_number"]
        unique_together = [("plan", "week_number")]
        verbose_name = "Semana"
        verbose_name_plural = "Semanas"

    def __str__(self) -> str:
        return f"Semana {self.week_number} — {self.plan.name}"


class TrainingSession(models.Model):
    """Sessão de treino (um dia real)."""

    week = models.ForeignKey(TrainingWeek, on_delete=models.CASCADE, related_name="sessions")
    label = models.CharField(
        max_length=20, blank=True,
        verbose_name="Letra (A/B/C…)",
        help_text="Ex.: 'A', 'B', 'C'. Aparece como 'TREINO A' no calendário.",
    )
    title = models.CharField(
        max_length=150, blank=True, verbose_name="Título (opcional)",
    )
    scheduled_date = models.DateField(verbose_name="Data")
    completed = models.BooleanField(default=False, verbose_name="Concluída")
    notes = models.TextField(blank=True, verbose_name="Notas do treinador")

    class Meta:
        ordering = ["scheduled_date", "id"]
        verbose_name = "Sessão"
        verbose_name_plural = "Sessões"

    def __str__(self) -> str:
        return f"{self.scheduled_date:%d/%m/%Y}" + (f" — {self.title}" if self.title else "")


class SessionExercise(models.Model):
    """Exercício prescrito numa sessão, com planejado × executado."""

    session = models.ForeignKey(
        TrainingSession, on_delete=models.CASCADE, related_name="session_exercises"
    )
    exercise = models.ForeignKey(ExerciseLibrary, on_delete=models.PROTECT)
    order = models.PositiveSmallIntegerField(default=1, verbose_name="Ordem")

    # --- Planejado ---
    planned_sets = models.PositiveSmallIntegerField(default=3, verbose_name="Séries")
    planned_reps = models.CharField(
        max_length=20, blank=True, verbose_name="Reps",
        help_text="Ex.: 5, 3-5, 8×2",
    )
    # Só para PRINCIPAL / PRIMARY_VARIATION.
    planned_load_percentage = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
        verbose_name="% do 1RM",
    )
    reference_1rm_kg = models.DecimalField(
        max_digits=7, decimal_places=2, null=True, blank=True,
        verbose_name="1RM de referência (kg)",
    )
    # Carga absoluta direta (prioriza sobre % × 1RM se preenchido).
    planned_load_kg_manual = models.DecimalField(
        max_digits=7, decimal_places=2, null=True, blank=True,
        verbose_name="Carga prevista (kg)",
        help_text="Para acessórios, informe a carga direta.",
    )
    planned_rpe = models.DecimalField(
        max_digits=3, decimal_places=1, null=True, blank=True,
        validators=[MinValueValidator(Decimal("1")), MaxValueValidator(Decimal("10"))],
        verbose_name="RPE alvo",
    )
    rest_seconds = models.PositiveSmallIntegerField(default=180, verbose_name="Descanso (s)")

    # --- Executado (editável pelo atleta) ---
    actual_load_kg = models.DecimalField(
        max_digits=7, decimal_places=2, null=True, blank=True,
        verbose_name="Carga feita (kg)",
    )
    actual_reps = models.PositiveSmallIntegerField(
        null=True, blank=True, verbose_name="Reps executadas (por série)",
    )
    actual_sets = models.PositiveSmallIntegerField(
        null=True, blank=True, verbose_name="Séries completadas",
    )
    actual_rpe = models.DecimalField(
        max_digits=3, decimal_places=1, null=True, blank=True,
        validators=[MinValueValidator(Decimal("1")), MaxValueValidator(Decimal("10"))],
        verbose_name="RPE real",
    )

    notes = models.TextField(blank=True, verbose_name="Observações")

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "Exercício da sessão"
        verbose_name_plural = "Exercícios da sessão"

    def __str__(self) -> str:
        return f"{self.exercise.name} — {self.session}"

    @property
    def planned_load_kg(self) -> Decimal | None:
        """Carga planejada efetiva. Manual tem prioridade; senão, % × 1RM."""
        if self.planned_load_kg_manual is not None:
            return Decimal(self.planned_load_kg_manual)
        if self.planned_load_percentage is None or self.reference_1rm_kg is None:
            return None
        from apps.dashboard.scoring import load_from_percentage
        return load_from_percentage(
            self.reference_1rm_kg, self.planned_load_percentage, round_to_kg=Decimal("2.5")
        )

    @property
    def executed_tonnage_kg(self) -> Decimal:
        """Tonelagem executada = carga × reps × séries (0 se incompleto)."""
        if not (self.actual_load_kg and self.actual_reps and self.actual_sets):
            return Decimal("0")
        return (
            Decimal(self.actual_load_kg)
            * Decimal(self.actual_reps)
            * Decimal(self.actual_sets)
        )


class AccessoryTemplate(models.Model):
    """Template reutilizável de acessório (carga absoluta direta)."""

    trainer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name="accessory_templates",
    )
    name = models.CharField(max_length=120, verbose_name="Nome do template")
    exercise = models.ForeignKey(ExerciseLibrary, on_delete=models.PROTECT)
    sets = models.PositiveSmallIntegerField(default=3, verbose_name="Séries")
    reps = models.CharField(max_length=20, blank=True, verbose_name="Reps")
    load_kg = models.DecimalField(
        max_digits=7, decimal_places=2, null=True, blank=True, verbose_name="Carga (kg)",
    )
    rpe = models.DecimalField(
        max_digits=3, decimal_places=1, null=True, blank=True, verbose_name="RPE alvo",
    )
    rest_seconds = models.PositiveSmallIntegerField(default=90, verbose_name="Descanso (s)")
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Template de acessório"
        verbose_name_plural = "Templates de acessórios"

    def __str__(self) -> str:
        return self.name


class AthleteAnamnesis(models.Model):
    """Anamnese do atleta."""

    athlete = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="anamneses"
    )
    trainer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="anamneses_written"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    years_training = models.PositiveSmallIntegerField(
        null=True, blank=True, verbose_name="Anos de treino com carga",
    )
    years_competing = models.PositiveSmallIntegerField(
        null=True, blank=True, verbose_name="Anos competindo",
    )
    best_meet_total = models.CharField(
        max_length=120, blank=True, verbose_name="Melhor total em competição",
    )
    injuries = models.TextField(blank=True, verbose_name="Lesões passadas ou em curso")
    limitations = models.TextField(blank=True, verbose_name="Limitações de movimento")
    medical_history = models.TextField(blank=True, verbose_name="Histórico médico")
    training_goal = models.TextField(blank=True, verbose_name="Meta do ciclo")
    observations = models.TextField(blank=True, verbose_name="Outras observações")

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Anamnese"
        verbose_name_plural = "Anamneses"

    def __str__(self) -> str:
        return f"Anamnese — {self.athlete.get_username()} ({self.created_at:%d/%m/%Y})"


class SessionFeedback(models.Model):
    """Feedback estruturado do atleta após a sessão."""

    session = models.OneToOneField(
        TrainingSession, on_delete=models.CASCADE, related_name="feedback",
    )
    athlete = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name="session_feedbacks",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    had_pain = models.BooleanField(default=False, verbose_name="Sentiu dor?")
    pain_description = models.CharField(
        max_length=200, blank=True, verbose_name="Onde/como foi a dor?",
    )
    was_tired = models.BooleanField(default=False, verbose_name="Estava cansado?")
    tired_description = models.CharField(
        max_length=200, blank=True, verbose_name="Do que veio o cansaço?",
    )
    session_rpe = models.PositiveSmallIntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        verbose_name="RPE geral da sessão (1–10)",
    )
    sleep_hours = models.DecimalField(
        max_digits=3, decimal_places=1, null=True, blank=True,
        verbose_name="Horas de sono na noite anterior",
    )
    bodyweight_kg = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
        verbose_name="Peso do dia (kg)",
    )
    general_notes = models.TextField(blank=True, verbose_name="Alguma observação extra?")

    trainer_response = models.TextField(blank=True, verbose_name="Resposta do treinador")

    class Meta:
        verbose_name = "Feedback de sessão"
        verbose_name_plural = "Feedbacks de sessão"

    def __str__(self) -> str:
        return f"Feedback — {self.session}"


class PersonalRecord(models.Model):
    """PR (treino ou competição)."""

    class Context(models.TextChoices):
        TRAINING = "training", "Treino"
        MEET = "meet", "Competição"

    athlete = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="personal_records",
    )
    exercise = models.ForeignKey(ExerciseLibrary, on_delete=models.PROTECT)
    weight_kg = models.DecimalField(max_digits=7, decimal_places=2, verbose_name="Carga (kg)")
    reps = models.PositiveSmallIntegerField(default=1, verbose_name="Repetições")
    rpe = models.DecimalField(
        max_digits=3, decimal_places=1, null=True, blank=True,
        validators=[MinValueValidator(Decimal("1")), MaxValueValidator(Decimal("10"))],
    )
    date = models.DateField(default=timezone.localdate)
    context = models.CharField(max_length=20, choices=Context.choices, default=Context.TRAINING)
    meet_name = models.CharField(max_length=150, blank=True, verbose_name="Nome da competição")
    video_url = models.URLField(blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-date", "-weight_kg"]
        verbose_name = "PR"
        verbose_name_plural = "PRs"

    def __str__(self) -> str:
        return f"{self.exercise.name} — {self.weight_kg} kg × {self.reps}"
