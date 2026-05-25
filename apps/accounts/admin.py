"""Admin accounts."""
from django.contrib import admin

from .models import AthleteProfile, Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "role", "phone")
    list_filter = ("role",)
    search_fields = ("user__username", "user__email")


@admin.register(AthleteProfile)
class AthleteProfileAdmin(admin.ModelAdmin):
    list_display = (
        "user", "trainer", "sex", "bodyweight_kg", "weight_class_kg",
        "equipment", "federation",
    )
    list_filter = ("sex", "equipment", "federation")
    search_fields = ("user__username", "trainer__username")
