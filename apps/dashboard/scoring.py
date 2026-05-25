"""Cálculos de pontuação, 1RM e cargas por percentual.

Este módulo concentra toda a matemática do sistema:

- IPF GL Points (Goodlift), fórmula oficial da IPF adotada em 2020
- Estimativa de 1RM por Epley e Brzycki
- Tabela RPE/RIR para cálculo de 1RM a partir de carga, reps e RPE
- Cargas por percentual do 1RM
- Sugestão de warm-ups escalonados

Todos os valores retornados são ``Decimal`` quando fazem sentido como massa,
para evitar imprecisão de ponto flutuante em cálculos acumulados.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Literal

# ---------------------------------------------------------------------------
# Tipos e constantes
# ---------------------------------------------------------------------------

Sex = Literal["M", "F"]
Equipment = Literal["raw", "equipped"]  # Classic (raw) ou Equipped (multiply)
Event = Literal["sbd", "bench"]  # Powerlifting full (SBD) ou Bench only


@dataclass(frozen=True)
class _IPFCoeff:
    """Coeficientes da fórmula IPF GL: ``100 * total / (A - B * e^(-C * bw))``."""

    a: float
    b: float
    c: float


# Coeficientes oficiais IPF GL (2020). Referência:
# https://www.ipfpointscalculator.com/ e documentação da IPF Technical Committee.
_IPF_GL_COEFFICIENTS: dict[tuple[Sex, Equipment, Event], _IPFCoeff] = {
    ("M", "raw", "sbd"): _IPFCoeff(1199.72839, 1025.18162, 0.00921),
    ("M", "raw", "bench"): _IPFCoeff(320.98041, 281.40258, 0.01008),
    ("M", "equipped", "sbd"): _IPFCoeff(1236.25115, 1449.21864, 0.01644),
    ("M", "equipped", "bench"): _IPFCoeff(381.22073, 733.79378, 0.02398),
    ("F", "raw", "sbd"): _IPFCoeff(610.32796, 1045.59282, 0.03048),
    ("F", "raw", "bench"): _IPFCoeff(142.40398, 442.52671, 0.04724),
    ("F", "equipped", "sbd"): _IPFCoeff(758.63878, 949.31382, 0.02435),
    ("F", "equipped", "bench"): _IPFCoeff(221.82209, 357.00377, 0.02937),
}

# Tabela RPE/RIR adotada (Tuchscherer / RTS). Linhas = reps (1..10),
# colunas = RPE (6, 6.5, 7, 7.5, 8, 8.5, 9, 9.5, 10). Valor = % do 1RM.
# Referência amplamente usada em programação de powerlifting; fonte base em
# Mike Tuchscherer, "Reactive Training Systems".
_RPE_PERCENTAGES: dict[int, dict[float, float]] = {
    1:  {6: 0.860, 6.5: 0.878, 7: 0.895, 7.5: 0.913, 8: 0.931, 8.5: 0.950, 9: 0.970, 9.5: 0.985, 10: 1.000},
    2:  {6: 0.836, 6.5: 0.853, 7: 0.871, 7.5: 0.888, 8: 0.907, 8.5: 0.924, 9: 0.942, 9.5: 0.961, 10: 0.978},
    3:  {6: 0.813, 6.5: 0.830, 7: 0.848, 7.5: 0.864, 8: 0.883, 8.5: 0.900, 9: 0.918, 9.5: 0.935, 10: 0.954},
    4:  {6: 0.790, 6.5: 0.807, 7: 0.824, 7.5: 0.840, 8: 0.859, 8.5: 0.875, 9: 0.893, 9.5: 0.910, 10: 0.928},
    5:  {6: 0.766, 6.5: 0.784, 7: 0.800, 7.5: 0.816, 8: 0.834, 8.5: 0.851, 9: 0.868, 9.5: 0.885, 10: 0.904},
    6:  {6: 0.745, 6.5: 0.762, 7: 0.778, 7.5: 0.795, 8: 0.811, 8.5: 0.828, 9: 0.844, 9.5: 0.861, 10: 0.880},
    7:  {6: 0.724, 6.5: 0.740, 7: 0.757, 7.5: 0.772, 8: 0.789, 8.5: 0.805, 9: 0.820, 9.5: 0.837, 10: 0.857},
    8:  {6: 0.704, 6.5: 0.720, 7: 0.736, 7.5: 0.750, 8: 0.767, 8.5: 0.782, 9: 0.797, 9.5: 0.814, 10: 0.835},
    9:  {6: 0.686, 6.5: 0.701, 7: 0.715, 7.5: 0.729, 8: 0.745, 8.5: 0.759, 9: 0.775, 9.5: 0.791, 10: 0.813},
    10: {6: 0.668, 6.5: 0.682, 7: 0.695, 7.5: 0.709, 8: 0.723, 8.5: 0.738, 9: 0.753, 9.5: 0.770, 10: 0.793},
}

_VALID_RPES: tuple[float, ...] = (6, 6.5, 7, 7.5, 8, 8.5, 9, 9.5, 10)

# Percentuais padrão de aquecimento até a série de trabalho.
_DEFAULT_WARMUP_PERCENTAGES: tuple[int, ...] = (0, 40, 55, 70, 85)


# ---------------------------------------------------------------------------
# IPF GL Points
# ---------------------------------------------------------------------------


def calculate_ipf_gl_points(
    total_kg: Decimal | float,
    bodyweight_kg: Decimal | float,
    sex: Sex,
    equipment: Equipment = "raw",
    event: Event = "sbd",
) -> Decimal:
    """Calcula os pontos IPF GL (Goodlift).

    A fórmula oficial é::

        IPF_GL = 100 * total / (A - B * exp(-C * bodyweight))

    Args:
        total_kg: Total da prova (S+B+D) ou supino, em quilos.
        bodyweight_kg: Peso corporal do atleta, em quilos.
        sex: ``"M"`` ou ``"F"``.
        equipment: ``"raw"`` (Classic) ou ``"equipped"`` (Multiply).
        event: ``"sbd"`` (full) ou ``"bench"`` (supino).

    Returns:
        Pontos IPF GL, arredondados a duas casas decimais.

    Raises:
        ValueError: Se peso ou total forem não-positivos, ou se a combinação
            sex/equipment/event não tiver coeficientes registrados.
    """
    total = Decimal(str(total_kg))
    bodyweight = Decimal(str(bodyweight_kg))
    if total <= 0 or bodyweight <= 0:
        raise ValueError("Total e peso corporal devem ser positivos.")

    try:
        coeff = _IPF_GL_COEFFICIENTS[(sex, equipment, event)]
    except KeyError as exc:
        raise ValueError(
            f"Combinação inválida para IPF GL: {sex}/{equipment}/{event}."
        ) from exc

    denominator = coeff.a - coeff.b * math.exp(-coeff.c * float(bodyweight))
    if denominator <= 0:
        # Evita divisão por zero em pesos extremamente baixos (fora de competição).
        return Decimal("0.00")

    points = 100 * float(total) / denominator
    return Decimal(str(points)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


# ---------------------------------------------------------------------------
# Estimativa de 1RM
# ---------------------------------------------------------------------------


def estimate_1rm_epley(weight_kg: Decimal | float, reps: int) -> Decimal:
    """Estima 1RM pela fórmula de Epley: ``w * (1 + reps/30)``.

    Boa para reps altas (>5). Para reps baixas, prefira :func:`estimate_1rm_brzycki`.

    Raises:
        ValueError: Se ``reps < 1`` ou ``weight_kg <= 0``.
    """
    if reps < 1:
        raise ValueError("reps deve ser >= 1.")
    weight = Decimal(str(weight_kg))
    if weight <= 0:
        raise ValueError("weight_kg deve ser positivo.")
    return (weight * (Decimal(1) + Decimal(reps) / Decimal(30))).quantize(
        Decimal("0.1"), rounding=ROUND_HALF_UP
    )


def estimate_1rm_brzycki(weight_kg: Decimal | float, reps: int) -> Decimal:
    """Estima 1RM pela fórmula de Brzycki: ``w * 36 / (37 - reps)``.

    Válida para 1 <= reps <= 10. Acima disso a fórmula degenera.

    Raises:
        ValueError: Se ``reps`` fora de [1, 10] ou ``weight_kg <= 0``.
    """
    if not 1 <= reps <= 10:
        raise ValueError("Brzycki é válido apenas para 1 <= reps <= 10.")
    weight = Decimal(str(weight_kg))
    if weight <= 0:
        raise ValueError("weight_kg deve ser positivo.")
    return (weight * Decimal(36) / (Decimal(37) - Decimal(reps))).quantize(
        Decimal("0.1"), rounding=ROUND_HALF_UP
    )


def estimate_1rm_from_rpe(
    weight_kg: Decimal | float, reps: int, rpe: float
) -> Decimal:
    """Estima 1RM a partir de carga, repetições e RPE declarado.

    Usa a tabela RPE/RIR: se ``weight`` foi uma série de ``reps`` @ ``rpe``,
    então ``1RM ≈ weight / percentage[reps][rpe]``.

    Args:
        weight_kg: Carga utilizada.
        reps: Repetições realizadas (1–10).
        rpe: RPE reportado. Será arredondado ao 0.5 mais próximo dentro de [6, 10].

    Raises:
        ValueError: Se ``reps`` fora de [1, 10] ou RPE fora de [6, 10].
    """
    if not 1 <= reps <= 10:
        raise ValueError("reps deve estar entre 1 e 10.")
    weight = Decimal(str(weight_kg))
    if weight <= 0:
        raise ValueError("weight_kg deve ser positivo.")

    rounded_rpe = round(float(rpe) * 2) / 2
    if rounded_rpe not in _VALID_RPES:
        raise ValueError("RPE deve estar em passos de 0.5 entre 6 e 10.")

    pct = Decimal(str(_RPE_PERCENTAGES[reps][rounded_rpe]))
    return (weight / pct).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)


# ---------------------------------------------------------------------------
# Cargas por percentual e warm-ups
# ---------------------------------------------------------------------------


def load_from_percentage(
    one_rm_kg: Decimal | float,
    percentage: Decimal | float,
    round_to_kg: Decimal | float = Decimal("2.5"),
) -> Decimal:
    """Calcula a carga absoluta correspondente a ``percentage``% de ``one_rm``.

    Faz arredondamento para múltiplos de ``round_to_kg`` (default 2.5 kg, que
    é o incremento mínimo padrão em barras olímpicas IPF).

    Args:
        one_rm_kg: 1RM de referência.
        percentage: Percentual (ex.: 75 para 75%).
        round_to_kg: Incremento para arredondamento. Passe ``Decimal("0")``
            para não arredondar.

    Raises:
        ValueError: Se ``one_rm_kg`` ou ``percentage`` forem negativos.
    """
    one_rm = Decimal(str(one_rm_kg))
    pct = Decimal(str(percentage))
    step = Decimal(str(round_to_kg))
    if one_rm < 0 or pct < 0:
        raise ValueError("one_rm_kg e percentage devem ser >= 0.")

    raw = one_rm * pct / Decimal("100")
    if step == 0:
        return raw.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
    # Arredonda para o múltiplo de ``step`` mais próximo.
    return (raw / step).quantize(Decimal("1"), rounding=ROUND_HALF_UP) * step


def suggest_warmup_sets(
    target_kg: Decimal | float,
    bar_kg: Decimal | float = Decimal("20"),
    percentages: tuple[int, ...] = _DEFAULT_WARMUP_PERCENTAGES,
    round_to_kg: Decimal | float = Decimal("2.5"),
) -> list[dict]:
    """Gera uma sequência de warm-ups partindo da barra até ``target_kg``.

    A série em 0% é sempre a barra vazia (útil para aquecimento).

    Returns:
        Lista de dicts ``{"pct": int, "load": Decimal}``, em ordem crescente.
    """
    target = Decimal(str(target_kg))
    bar = Decimal(str(bar_kg))
    if target <= 0:
        return []

    warmups = []
    for pct in sorted(set(percentages)):
        if pct == 0:
            load = bar
        else:
            load = load_from_percentage(target, pct, round_to_kg=round_to_kg)
            if load < bar:
                load = bar
        warmups.append({"pct": pct, "load": load})
    return warmups
