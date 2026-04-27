"""Testes unitários para apps.dashboard.scoring.

A validação do IPF GL é feita com totais e pesos de atletas conhecidos,
comparados contra o calculador oficial (ipfpointscalculator.com).
"""
from __future__ import annotations

from decimal import Decimal

import pytest

from apps.dashboard import scoring


class TestIPFGLPoints:
    """Valida IPF GL contra exemplos conhecidos."""

    def test_male_raw_sbd_elite_range(self):
        """Total elite masculino SHW (1105 kg @ 183 kg BW) ≈ 107–112 pts."""
        pts = scoring.calculate_ipf_gl_points(
            total_kg=1105, bodyweight_kg=183, sex="M", equipment="raw", event="sbd"
        )
        assert Decimal("107") <= pts <= Decimal("112")

    def test_female_raw_sbd_elite_range(self):
        """Feminino 63 kg BW com total 500 kg ≈ 107–112 pts (nível elite)."""
        pts = scoring.calculate_ipf_gl_points(
            total_kg=500, bodyweight_kg=63, sex="F", equipment="raw", event="sbd"
        )
        assert Decimal("107") <= pts <= Decimal("112")

    def test_intermediate_male_range(self):
        """700 kg @ 93 kg BW é um intermediário forte: ~88–95 pts."""
        pts = scoring.calculate_ipf_gl_points(
            total_kg=700, bodyweight_kg=93, sex="M", equipment="raw", event="sbd"
        )
        assert Decimal("88") <= pts <= Decimal("95")

    def test_male_raw_bench_returns_positive(self):
        pts = scoring.calculate_ipf_gl_points(
            total_kg=200, bodyweight_kg=90, sex="M", equipment="raw", event="bench"
        )
        assert pts > 0

    def test_raises_on_zero_bodyweight(self):
        with pytest.raises(ValueError):
            scoring.calculate_ipf_gl_points(
                total_kg=500, bodyweight_kg=0, sex="M", equipment="raw", event="sbd"
            )

    def test_raises_on_zero_total(self):
        with pytest.raises(ValueError):
            scoring.calculate_ipf_gl_points(
                total_kg=0, bodyweight_kg=80, sex="M", equipment="raw", event="sbd"
            )

    def test_raises_on_invalid_combination(self):
        with pytest.raises(ValueError):
            scoring.calculate_ipf_gl_points(
                total_kg=500, bodyweight_kg=80, sex="X", equipment="raw", event="sbd"  # type: ignore[arg-type]
            )

    def test_returns_two_decimal_places(self):
        pts = scoring.calculate_ipf_gl_points(
            total_kg=700, bodyweight_kg=93, sex="M", equipment="raw", event="sbd"
        )
        # Um Decimal com casas=2.
        assert pts.as_tuple().exponent == -2

    def test_heavier_lifter_gets_lower_points_for_same_total(self):
        """Mesma total em peso maior -> menos pontos (a curva IPF penaliza)."""
        lighter = scoring.calculate_ipf_gl_points(700, 80, "M", "raw", "sbd")
        heavier = scoring.calculate_ipf_gl_points(700, 120, "M", "raw", "sbd")
        assert lighter > heavier


class TestEpley:
    def test_basic(self):
        # 100 kg x 5 reps -> 100 * (1 + 5/30) = 116.666..., arredondado 116.7.
        assert scoring.estimate_1rm_epley(100, 5) == Decimal("116.7")

    def test_one_rep_is_self(self):
        assert scoring.estimate_1rm_epley(150, 1) == Decimal("155.0")

    def test_raises_on_zero_reps(self):
        with pytest.raises(ValueError):
            scoring.estimate_1rm_epley(100, 0)

    def test_raises_on_negative_weight(self):
        with pytest.raises(ValueError):
            scoring.estimate_1rm_epley(-10, 5)


class TestBrzycki:
    def test_basic(self):
        # 100 kg x 5 reps -> 100 * 36 / 32 = 112.5.
        assert scoring.estimate_1rm_brzycki(100, 5) == Decimal("112.5")

    def test_raises_out_of_range(self):
        with pytest.raises(ValueError):
            scoring.estimate_1rm_brzycki(100, 11)
        with pytest.raises(ValueError):
            scoring.estimate_1rm_brzycki(100, 0)


class TestRpe1RM:
    def test_single_at_rpe10_equals_weight(self):
        # 1 rep @ RPE 10 = 100% do 1RM.
        assert scoring.estimate_1rm_from_rpe(200, 1, 10) == Decimal("200.0")

    def test_triple_at_rpe8(self):
        # 3 reps @ RPE 8 = 0.883 * 1RM, então 1RM = w / 0.883.
        result = scoring.estimate_1rm_from_rpe(150, 3, 8)
        assert Decimal("169.0") <= result <= Decimal("171.0")

    def test_rpe_rounds_to_half(self):
        """RPE 8.2 deve arredondar para 8.0."""
        a = scoring.estimate_1rm_from_rpe(100, 5, 8.2)
        b = scoring.estimate_1rm_from_rpe(100, 5, 8.0)
        assert a == b

    def test_raises_on_invalid_rpe(self):
        with pytest.raises(ValueError):
            scoring.estimate_1rm_from_rpe(100, 5, 5.5)
        with pytest.raises(ValueError):
            scoring.estimate_1rm_from_rpe(100, 5, 11)


class TestLoadFromPercentage:
    def test_basic_with_rounding(self):
        # 75% de 200 = 150. Já múltiplo de 2.5.
        assert scoring.load_from_percentage(200, 75) == Decimal("150.0")

    def test_rounds_to_nearest_2_5(self):
        # 72.5% de 200 = 145. Múltiplo de 2.5.
        assert scoring.load_from_percentage(200, 72.5) == Decimal("145.0")

    def test_rounds_non_standard(self):
        # 73% de 200 = 146. Mais próximo de 2.5 é 145.
        assert scoring.load_from_percentage(200, 73) == Decimal("145.0")

    def test_no_rounding(self):
        result = scoring.load_from_percentage(200, 73, round_to_kg=0)
        assert result == Decimal("146.0")

    def test_custom_step(self):
        # Step de 0.5 kg (típico para micro-placas em supino).
        assert scoring.load_from_percentage(100, 77.5, round_to_kg=Decimal("0.5")) == Decimal("77.5")

    def test_raises_on_negative(self):
        with pytest.raises(ValueError):
            scoring.load_from_percentage(-100, 75)


class TestWarmupSets:
    def test_includes_bar(self):
        warmups = scoring.suggest_warmup_sets(200, bar_kg=20)
        assert warmups[0] == {"pct": 0, "load": Decimal("20")}

    def test_never_below_bar(self):
        """30% de 50kg = 15kg. Deve ser substituído pela barra de 20kg."""
        warmups = scoring.suggest_warmup_sets(50, bar_kg=20, percentages=(0, 30, 60, 90))
        loads = [w["load"] for w in warmups]
        for load in loads:
            assert load >= Decimal("20")

    def test_strictly_non_decreasing(self):
        warmups = scoring.suggest_warmup_sets(250)
        loads = [w["load"] for w in warmups]
        assert loads == sorted(loads)

    def test_empty_for_zero_target(self):
        assert scoring.suggest_warmup_sets(0) == []
