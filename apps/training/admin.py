"""Admin do módulo de treino."""
from django.contrib import admin

from .models import (
    AccessoryTemplate, AthleteAnamnesis, ExerciseLibrary,
    PersonalRecord, SessionExercise, SessionFeedback,
    TrainingPlan, TrainingSession, TrainingWeek,
)


class SessionExerciseInline(admin.TabularInline):
    model = SessionExercise
    extra = 0
    fields = (
        "order", "exercise", "planned_sets", "planned_reps",
        "planned_load_percentage", "planned_load_kg_manual",
        "actual_load_kg", "actual_reps", "actual_sets",
    )


class TrainingSessionInline(admin.TabularInline):
    model = TrainingSession
    extra = 0
    fields = ("scheduled_date", "title", "completed")


class TrainingWeekInline(admin.TabularInline):
    model = TrainingWeek
    extra = 0
    fields = ("week_number", "start_date", "end_date", "block_type", "focus")


@admin.register(ExerciseLibrary)
class ExerciseLibraryAdmin(admin.ModelAdmin):
    list_display = ("name", "tier", "main_lift", "is_active")
    list_filter = ("tier", "main_lift", "is_active")
    search_fields = ("name",)


@admin.register(AccessoryTemplate)
class AccessoryTemplateAdmin(admin.ModelAdmin):
    list_display = ("name", "trainer", "exercise", "sets", "reps", "load_kg", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name",)


@admin.register(TrainingPlan)
class TrainingPlanAdmin(admin.ModelAdmin):
    list_display = ("name", "athlete", "trainer", "is_active", "start_date", "meet_date")
    list_filter = ("is_active",)
    search_fields = ("name", "athlete__username", "trainer__username")
    inlines = [TrainingWeekInline]


@admin.register(TrainingWeek)
class TrainingWeekAdmin(admin.ModelAdmin):
    list_display = ("plan", "week_number", "block_type", "start_date", "end_date")
    list_filter = ("block_type",)
    inlines = [TrainingSessionInline]


@admin.register(TrainingSession)
class TrainingSessionAdmin(admin.ModelAdmin):
    list_display = ("scheduled_date", "title", "week", "completed")
    list_filter = ("completed",)
    inlines = [SessionExerciseInline]


@admin.register(SessionExercise)
class SessionExerciseAdmin(admin.ModelAdmin):
    list_display = (
        "session", "exercise", "order", "planned_sets", "planned_reps",
        "actual_load_kg", "actual_reps", "actual_sets",
    )


@admin.register(AthleteAnamnesis)
class AthleteAnamnesisAdmin(admin.ModelAdmin):
    list_display = ("athlete", "trainer", "created_at", "years_training")


@admin.register(SessionFeedback)
class SessionFeedbackAdmin(admin.ModelAdmin):
    list_display = ("session", "athlete", "session_rpe", "had_pain", "created_at")
    list_filter = ("had_pain", "was_tired")


@admin.register(PersonalRecord)
class PersonalRecordAdmin(admin.ModelAdmin):
    list_display = ("athlete", "exercise", "weight_kg", "reps", "date", "context")
    list_filter = ("context",)
