"""
Unit tests for Nutrition Engine in PM POSHAN Tracker.
"""
import pytest
from engines.nutrition_engine import (
    calculate_ingredient_nutrition,
    calculate_meal_nutrition,
    normalize_quantity_to_grams,
    INGREDIENT_DATABASE
)


def test_normalize_units():
    assert normalize_quantity_to_grams(1.5, "kg") == 1500.0
    assert normalize_quantity_to_grams(250.0, "g") == 250.0
    assert normalize_quantity_to_grams(2.0, "liter") == 2000.0
    assert normalize_quantity_to_grams(100.0, "ml") == 100.0
    # Egg piece unit test
    assert normalize_quantity_to_grams(4, "piece", "Whole Hen Egg (Boiled)") == 200.0


def test_raw_ingredient_nutrition():
    # 10 kg of Rice (Raw Milled) -> 10,000 g -> 100 * 100g -> 100 * 356 = 35600 kcal, 790 g protein
    res = calculate_ingredient_nutrition("Rice (Raw Milled)", 10.0, "kg", form="raw")
    assert res["calories_kcal"] == 35600.0
    assert res["protein_g"] == 790.0
    assert res["effective_raw_grams"] == 10000.0


def test_cooked_ingredient_nutrition():
    # 2.8 kg cooked rice with yield factor 2.8 should equate to 1.0 kg raw dry rice
    res = calculate_ingredient_nutrition("Rice (Raw Milled)", 2.8, "kg", form="cooked")
    assert pytest.approx(res["effective_raw_grams"], rel=1e-2) == 1000.0
    assert pytest.approx(res["calories_kcal"], rel=1e-2) == 3560.0
    assert pytest.approx(res["protein_g"], rel=1e-2) == 79.0


def test_meal_nutrition_adequacy_primary():
    # Feeding 100 primary students
    # PM POSHAN Primary Norms: 450 kcal, 12g protein
    ingredients = [
        {"name": "Rice (Raw Milled)", "quantity": 10.0, "unit": "kg", "form": "raw"},      # 35600 kcal, 790g protein
        {"name": "Toor Dal (Split Red Gram)", "quantity": 2.2, "unit": "kg", "form": "raw"}, # 7546 kcal, 490.6g protein
        {"name": "Mustard / Cooking Vegetable Oil", "quantity": 0.5, "unit": "kg", "form": "raw"} # 4500 kcal, 0g protein
    ]
    # Total batch calories: 35600 + 7546 + 4500 = 47646 kcal -> 476.46 kcal / serving
    # Target: 450 kcal -> Adequacy ~ 105.88%
    # Total batch protein: 790 + 490.6 = 1280.6g -> 12.81g / serving
    # Target: 12g -> Adequacy ~ 106.72%
    res = calculate_meal_nutrition(ingredients, meals_served=100, class_group="Primary (Class 1-5)")

    assert res["meals_served"] == 100
    assert res["per_serving_calories_kcal"] > 450.0
    assert res["per_serving_protein_g"] > 12.0
    assert res["energy_adequacy_pct"] > 100.0
    assert res["protein_adequacy_pct"] > 100.0
    assert "Adequate" in res["status"]


def test_meal_nutrition_deficit():
    # Severe deficit: only 2 kg rice for 100 students (underfed)
    ingredients = [
        {"name": "Rice (Raw Milled)", "quantity": 2.0, "unit": "kg", "form": "raw"}
    ]
    res = calculate_meal_nutrition(ingredients, meals_served=100, class_group="Primary (Class 1-5)")
    assert res["per_serving_calories_kcal"] < 100.0
    assert res["energy_adequacy_pct"] < 30.0
    assert res["status"] == "Severe Deficit"


def test_invalid_nutrition_inputs():
    # Meals served must be > 0
    with pytest.raises(ValueError, match="Meals served must be greater than zero"):
        calculate_meal_nutrition([], meals_served=0, class_group="Primary (Class 1-5)")

    # Negative quantity
    with pytest.raises(ValueError, match="cannot be negative"):
        calculate_ingredient_nutrition("Rice (Raw Milled)", -5.0, "kg")

    # Unknown ingredient
    with pytest.raises(ValueError, match="Unknown ingredient"):
        calculate_ingredient_nutrition("Unknown Magic Berry", 2.0, "kg")
