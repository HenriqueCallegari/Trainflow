"""Modelos de perfil de usuário.

Papéis no sistema: Treinador (quem programa e gerencia) e Atleta (quem executa
e registra a carga feita). Só treinadores podem se registrar publicamente;
atletas são criados pelos treinadores.

Cada :class:`AthleteProfile` é ligado ao User de atleta e referencia o treinador
responsável, que é quem gerencia planos daquele atleta.
"""
from __future__ import annotations

from decimal import Decimal

from django.conf import settings
from django.db import models


class Profile(models.Model):
    """Perfil básico: papel (treinador/atleta) e contato."""

    class Role(models.TextChoices):
        TRAINER = "trainer", "Treinador(a)"
        ATHLETE = "athlete", "Atleta"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile",
    )
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.ATHLETE)
    phone = models.CharField(max_length=30, blank=True)
    bio = models.TextField(blank=True)

    class Meta:
        verbose_name = "Perfil"
        verbose_name_plural = "Perfis"

    def __str__(self) -> str:
        full = self.user.get_full_name() or self.user.get_username()
        return f"{full} ({self.get_role_display()})"

    @property
    def is_athlete(self) -> bool:
        return self.role == self.Role.ATHLETE

    @property
    def is_trainer(self) -> bool:
        return self.role == self.Role.TRAINER


class AthleteProfile(models.Model):
    """Dados de competição/antropometria do atleta.

    Ligação ``trainer`` indica qual treinador gerencia este atleta.
    """

    class Sex(models.TextChoices):
        MALE = "M", "Masculino"
        FEMALE = "F", "Feminino"

    class Equipment(models.TextChoices):
        RAW = "raw", "Clássica (Raw)"
        EQUIPPED = "equipped", "Equipado (Multiply)"

    class Federation(models.TextChoices):
        IPF = "IPF", "IPF"
        CBLB = "CBLB", "CBLB"
        OTHER = "other", "Outra"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="athlete_profile",
    )
    trainer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name="athletes",
        null=True, blank=True,
        verbose_name="Treinador(a) responsável",
    )
    sex = models.CharField(max_length=1, choices=Sex.choices, default=Sex.MALE)
    birth_date = models.DateField(null=True, blank=True, verbose_name="Data de nascimento")
    bodyweight_kg = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
        verbose_name="Peso corporal (kg)",
    )
    weight_class_kg = models.DecimalField(
        max_digits=5, decimal_places=1, null=True, blank=True,
        verbose_name="Categoria de peso (kg)",
    )
    equipment = models.CharField(
        max_length=20, choices=Equipment.choices, default=Equipment.RAW,
    )
    federation = models.CharField(
        max_length=20, choices=Federation.choices, default=Federation.CBLB,
    )
    best_squat_kg = models.DecimalField(
        max_digits=6, decimal_places=2, null=True, blank=True,
        verbose_name="Melhor agachamento (kg)",
    )
    best_bench_kg = models.DecimalField(
        max_digits=6, decimal_places=2, null=True, blank=True,
        verbose_name="Melhor supino (kg)",
    )
    best_deadlift_kg = models.DecimalField(
        max_digits=6, decimal_places=2, null=True, blank=True,
        verbose_name="Melhor terra (kg)",
    )

    class Meta:
        verbose_name = "Perfil de atleta"
        verbose_name_plural = "Perfis de atleta"

    def __str__(self) -> str:
        return f"Perfil de atleta — {self.user.get_username()}"

    @property
    def best_total_kg(self) -> Decimal | None:
        parts = [self.best_squat_kg, self.best_bench_kg, self.best_deadlift_kg]
        if any(p is None for p in parts):
            return None
        return sum((Decimal(str(p)) for p in parts), Decimal("0"))
