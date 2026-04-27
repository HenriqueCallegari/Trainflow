"""Agregações de volume de treino.

Tonelagem é calculada exclusivamente a partir do que foi **executado**:
``actual_load_kg × actual_reps × actual_sets``.

Somada por (semana, movimento-pai), considerando apenas exercícios dos tiers
PRINCIPAL e PRIMARY_VARIATION cujo ``main_lift`` seja SBD — ou seja, supino
fechado conta como volume de supino.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from django.db.models import F, Sum

from apps.training.models import (
    ExerciseLibrary, SessionExercise, TrainingPlan, TrainingWeek,
)


@dataclass(frozen=True)
class WeeklyTonnage:
    """Tonelagem de uma semana, desagregada por movimento."""

    week_number: int
    start_date: str
    block_type: str
    squat_kg: Decimal
    bench_kg: Decimal
    deadlift_kg: Decimal

    @property
    def total_kg(self) -> Decimal:
        return self.squat_kg + self.bench_kg + self.deadlift_kg


def tonnage_for_plan(plan: TrainingPlan) -> list[WeeklyTonnage]:
    """Retorna lista de :class:`WeeklyTonnage` para cada semana do plano."""
    weeks = list(plan.weeks.order_by("week_number"))
    result: list[WeeklyTonnage] = []

    ML = ExerciseLibrary.MainLift

    for week in weeks:
        totals = _aggregate_week_tonnage(week)
        result.append(
            WeeklyTonnage(
                week_number=week.week_number,
                start_date=week.start_date.strftime("%d/%m"),
                block_type=week.get_block_type_display(),
                squat_kg=totals.get(ML.SQUAT, Decimal("0")),
                bench_kg=totals.get(ML.BENCH, Decimal("0")),
                deadlift_kg=totals.get(ML.DEADLIFT, Decimal("0")),
            )
        )
    return result


def _aggregate_week_tonnage(week: TrainingWeek) -> dict[str, Decimal]:
    """Soma tonelagem executada de uma semana, agrupando por ``main_lift``."""
    qs = (
        SessionExercise.objects
        .filter(
            session__week=week,
            actual_load_kg__isnull=False,
            actual_reps__isnull=False,
            actual_sets__isnull=False,
            exercise__tier__in=[
                ExerciseLibrary.Tier.PRINCIPAL,
                ExerciseLibrary.Tier.PRIMARY_VARIATION,
            ],
        )
        .exclude(exercise__main_lift=ExerciseLibrary.MainLift.NONE)
        .values("exercise__main_lift")
        .annotate(
            tonnage=Sum(
                F("actual_load_kg") * F("actual_reps") * F("actual_sets")
            )
        )
    )
    return {row["exercise__main_lift"]: Decimal(row["tonnage"] or 0) for row in qs}
