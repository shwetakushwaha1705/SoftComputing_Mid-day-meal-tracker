"""
Unit tests for Soft Computing Mamdani Fuzzy Logic Engine in PM POSHAN Tracker.
"""
import pytest
from engines.fuzzy_engine import PoshanFuzzyEngine, fuzzy_engine


def test_fuzzy_priority_high_cases():
    # Case 1: Low nutrition (40%), High waste (35%) -> High Priority
    res1 = fuzzy_engine.evaluate(nutrition_adequacy_pct=40.0, food_waste_pct=35.0)
    assert res1["review_priority_score"] >= 60.0
    assert res1["priority_badge"] == "HIGH"
    assert "High Priority" in res1["priority_label"]

    # Case 2: Low nutrition (45%), Low waste (3%) -> High Priority (hunger/portion shortage crisis)
    res2 = fuzzy_engine.evaluate(nutrition_adequacy_pct=45.0, food_waste_pct=3.0)
    assert res2["review_priority_score"] >= 60.0
    assert res2["priority_badge"] == "HIGH"


def test_fuzzy_priority_low_case():
    # High nutrition (110%), Low waste (4%) -> Compliant / Low Priority
    res = fuzzy_engine.evaluate(nutrition_adequacy_pct=110.0, food_waste_pct=4.0)
    assert res["review_priority_score"] <= 40.0
    assert res["priority_badge"] == "LOW"
    assert "Low Priority" in res["priority_label"]


def test_fuzzy_priority_medium_case():
    # Medium nutrition (85%), Medium waste (18%) -> Medium Priority
    res = fuzzy_engine.evaluate(nutrition_adequacy_pct=85.0, food_waste_pct=18.0)
    assert 35.0 <= res["review_priority_score"] <= 75.0
    assert res["priority_badge"] in ["MEDIUM", "HIGH"]


def test_fuzzy_explainability_and_active_rules():
    res = fuzzy_engine.evaluate(nutrition_adequacy_pct=50.0, food_waste_pct=30.0)
    assert len(res["active_rules"]) > 0
    # Rule 1 should have high firing strength
    top_rule = res["active_rules"][0]
    assert "rule_id" in top_rule
    assert "firing_strength" in top_rule
    assert "rationale" in top_rule
    assert top_rule["firing_strength"] > 0.0

    # Check membership degree structure
    assert "adequacy" in res["membership_degrees"]
    assert "waste" in res["membership_degrees"]
    assert res["membership_degrees"]["adequacy"]["Low"] > 0.0


def test_fuzzy_boundary_clamping():
    # Out of range negative adequacy and waste should be safely clamped to 0
    res_neg = fuzzy_engine.evaluate(nutrition_adequacy_pct=-20.0, food_waste_pct=-5.0)
    assert 0.0 <= res_neg["review_priority_score"] <= 100.0

    # Excess adequacy (>150%) and waste (>50%) should be safely clamped
    res_overflow = fuzzy_engine.evaluate(nutrition_adequacy_pct=300.0, food_waste_pct=90.0)
    assert 0.0 <= res_overflow["review_priority_score"] <= 100.0
