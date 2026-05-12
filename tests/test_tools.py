"""
Pytest unit tests for backend audit tools.

Run: pytest tests/test_tools.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

import pytest
from tools.cfr_lookup import cfr_lookup, cfr_compare_rating
from tools.pact_act_check import pact_act_check
from tools.tdiu_check import tdiu_check
from tools.va_pay_lookup import va_pay_lookup, calculate_pay_impact
from tools.combined_rating import calculate_combined_rating, check_combined_rating_error


# ---------------------------------------------------------------------------
# cfr_lookup
# ---------------------------------------------------------------------------

class TestCfrLookup:
    def test_returns_condition_name(self):
        result = cfr_lookup("9411")
        assert "condition" in result
        assert isinstance(result["condition"], str)
        assert len(result["condition"]) > 0

    def test_returns_rating_criteria(self):
        result = cfr_lookup("9411")
        assert "rating_criteria" in result
        assert isinstance(result["rating_criteria"], dict)

    def test_returns_cfr_section(self):
        result = cfr_lookup("9411")
        assert "cfr_section" in result

    def test_unknown_code_returns_error_or_empty(self):
        result = cfr_lookup("9999")
        # Should not raise — either returns error key or empty criteria
        assert isinstance(result, dict)


# ---------------------------------------------------------------------------
# cfr_compare_rating
# ---------------------------------------------------------------------------

class TestCfrCompareRating:
    def test_returns_assigned_rating(self):
        result = cfr_compare_rating(
            "9411",
            assigned_rating=30,
            symptom_description="near-constant panic, occupational impairment",
        )
        assert result["assigned_rating"] == 30

    def test_returns_next_rating_level(self):
        result = cfr_compare_rating(
            "9411",
            assigned_rating=30,
            symptom_description="near-constant panic",
        )
        assert "next_rating_level" in result


# ---------------------------------------------------------------------------
# pact_act_check
# ---------------------------------------------------------------------------

class TestPactActCheck:
    def test_asthma_iraq_eligible(self):
        result = pact_act_check(
            "asthma",
            deployment_locations=["Iraq", "Afghanistan"],
            service_era="post-9/11",
        )
        assert result["pact_act_eligible"] is True

    def test_returns_legal_citation(self):
        result = pact_act_check(
            "asthma",
            deployment_locations=["Iraq"],
            service_era="post-9/11",
        )
        assert "legal_citation" in result
        assert isinstance(result["legal_citation"], str)

    def test_non_qualifying_condition(self):
        result = pact_act_check(
            "broken_arm",
            deployment_locations=["Germany"],
            service_era="peacetime",
        )
        assert isinstance(result, dict)
        # Should not raise regardless of eligibility


# ---------------------------------------------------------------------------
# tdiu_check
# ---------------------------------------------------------------------------

class TestTdiuCheck:
    def test_single_70_qualifies_schedular(self):
        result = tdiu_check([70], veteran_employed=False)
        assert result["tdiu_schedular_eligible"] is True

    def test_combined_70_with_one_60_qualifies(self):
        result = tdiu_check([60, 20], veteran_employed=False)
        assert result["tdiu_schedular_eligible"] is True

    def test_low_ratings_not_schedular_eligible(self):
        result = tdiu_check([10, 10], veteran_employed=False)
        assert result["tdiu_schedular_eligible"] is False

    def test_returns_combined_rating(self):
        result = tdiu_check([70, 30], veteran_employed=False)
        assert "combined_rating" in result
        assert isinstance(result["combined_rating"], (int, float))


# ---------------------------------------------------------------------------
# calculate_combined_rating
# ---------------------------------------------------------------------------

class TestCombinedRating:
    def test_single_rating_passthrough(self):
        result = calculate_combined_rating([50])
        assert result["combined_rating"] == 50

    def test_two_ratings_whole_person_math(self):
        # 1 - (0.7 * 0.8) = 1 - 0.56 = 0.44 → rounds to 40
        result = calculate_combined_rating([30, 20])
        assert result["combined_rating"] == 40

    def test_empty_list_returns_zero(self):
        result = calculate_combined_rating([])
        assert result["combined_rating"] == 0

    def test_result_never_exceeds_100(self):
        result = calculate_combined_rating([90, 80, 70, 60])
        assert result["combined_rating"] <= 100


# ---------------------------------------------------------------------------
# calculate_pay_impact
# ---------------------------------------------------------------------------

class TestPayImpact:
    def test_higher_rating_increases_pay(self):
        result = calculate_pay_impact(
            current_rating=30,
            potential_rating=70,
            dependent_status="alone",
        )
        assert result["monthly_increase_usd"] > 0
        assert result["annual_increase_usd"] > 0

    def test_same_rating_zero_increase(self):
        result = calculate_pay_impact(
            current_rating=50,
            potential_rating=50,
            dependent_status="alone",
        )
        assert result["monthly_increase_usd"] == 0

    def test_annual_is_12x_monthly(self):
        result = calculate_pay_impact(
            current_rating=30,
            potential_rating=70,
            dependent_status="alone",
        )
        assert abs(result["annual_increase_usd"] - result["monthly_increase_usd"] * 12) < 0.01
