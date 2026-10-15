"""
Unit tests for Food Wastage Engine in PM POSHAN Tracker.
"""
import pytest
from engines.wastage_engine import (
    calculate_food_wastage,
    validate_meal_record,
    estimate_plate_waste_from_visual,
    WasteValidationError
)


def test_standard_manual_waste_calculation():
    # 100 students, 35 kg cooked food prepared, 2.0 kg kitchen leftover, 1.5 kg plate waste
    res = calculate_food_wastage(
        students_present=100,
        meals_served=100,
        cooked_food_prepared_kg=35.0,
        kitchen_waste_kg=2.0,
        plate_waste_kg=1.5
    )

    assert res["cooked_food_prepared_kg"] == 35.0
    assert res["total_waste_kg"] == 3.5
    assert res["food_consumed_kg"] == 31.5
    # Total waste % = (3.5 / 35.0) * 100 = 10.0%
    assert res["total_waste_pct"] == 10.0
    assert res["kitchen_waste_pct"] == pytest.approx(5.71, rel=1e-2)
    assert res["plate_waste_pct"] == pytest.approx(4.29, rel=1e-2)
    # Plate waste per student = 1.5kg * 1000 / 100 = 15.0 grams
    assert res["plate_waste_per_student_g"] == 15.0
    assert res["waste_category"] == "Moderate Wastage (8-20%)"


def test_visual_plate_waste_estimation():
    # 35 kg prepared, 5 kg leftover in kitchen -> 30 kg distributed to students
    # Visual estimate: Quarter plate remaining (~25%) -> 30 * 0.25 = 7.5 kg plate waste
    res = calculate_food_wastage(
        students_present=100,
        meals_served=100,
        cooked_food_prepared_kg=35.0,
        kitchen_waste_kg=5.0,
        visual_category="Quarter plate remaining (~25%)"
    )

    assert res["is_visual_estimate"] is True
    assert res["plate_waste_kg"] == 7.5
    assert res["total_waste_kg"] == 12.5
    assert res["total_waste_pct"] == pytest.approx(35.71, rel=1e-2)
    assert res["waste_category"] == "Critical Wastage (>20%)"


def test_invalid_records_rejected():
    # 1. Meals served > students present
    with pytest.raises(WasteValidationError, match="cannot exceed students present"):
        calculate_food_wastage(
            students_present=80,
            meals_served=95,
            cooked_food_prepared_kg=30.0,
            kitchen_waste_kg=1.0,
            plate_waste_kg=1.0
        )

    # 2. Total waste > prepared food
    with pytest.raises(WasteValidationError, match="Total waste.*exceeds total prepared food"):
        calculate_food_wastage(
            students_present=50,
            meals_served=50,
            cooked_food_prepared_kg=10.0,
            kitchen_waste_kg=8.0,
            plate_waste_kg=5.0
        )

    # 3. Kitchen waste > prepared food
    with pytest.raises(WasteValidationError, match="Kitchen waste.*exceeds total food prepared"):
        calculate_food_wastage(
            students_present=50,
            meals_served=50,
            cooked_food_prepared_kg=10.0,
            kitchen_waste_kg=12.0,
            plate_waste_kg=0.0
        )

    # 4. Plate waste exceeds distributed food
    with pytest.raises(WasteValidationError, match="Plate waste.*exceeds food actually distributed"):
        calculate_food_wastage(
            students_present=50,
            meals_served=50,
            cooked_food_prepared_kg=10.0,
            kitchen_waste_kg=9.0,
            plate_waste_kg=3.0  # Distributed was only 1.0 kg!
        )


def test_zero_waste_clean_record():
    res = calculate_food_wastage(
        students_present=50,
        meals_served=50,
        cooked_food_prepared_kg=15.0,
        kitchen_waste_kg=0.0,
        plate_waste_kg=0.0
    )
    assert res["total_waste_pct"] == 0.0
    assert res["waste_category"] == "Low / Acceptable (<8%)"
