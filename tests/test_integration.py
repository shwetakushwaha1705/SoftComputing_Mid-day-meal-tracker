"""
Integration test for PM POSHAN Tracker
Tests end-to-end workflow: database seeding, adding records, duplicate check,
reporting compliance, and fuzzy evaluation consistency.
"""
import pytest
import tempfile
from pathlib import Path
from database.db import (
    init_db,
    add_school,
    get_schools,
    add_meal_entry,
    get_meal_entries,
    get_reporting_compliance,
    update_reference_norm,
    get_reference_norms
)


@pytest.fixture
def test_db():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        temp_path = Path(f.name)
    init_db(temp_path)
    yield temp_path
    if temp_path.exists():
        temp_path.unlink()


def test_full_lifecycle(test_db):
    # 1. Add School
    s_id = add_school(
        school_code="TEST-001",
        name="Test Model Primary School",
        block="Demo Block",
        district="Demo District",
        registered_primary=100,
        registered_upper_primary=0,
        db_path=test_db
    )
    assert s_id > 0
    schools = get_schools(test_db)
    assert len(schools) == 1
    assert schools[0]["name"] == "Test Model Primary School"

    # 2. Add Meal Entry
    ingredients = [
        {"name": "Rice (Raw Milled)", "quantity": 10.0, "unit": "kg", "form": "raw"},
        {"name": "Toor Dal (Split Red Gram)", "quantity": 2.2, "unit": "kg", "form": "raw"},
        {"name": "Mustard / Cooking Vegetable Oil", "quantity": 0.5, "unit": "kg", "form": "raw"}
    ]

    entry_id = add_meal_entry(
        school_id=s_id,
        entry_date="2026-10-10",
        class_group="Primary (Class 1-5)",
        menu_name="Rice & Sambhar",
        students_present=95,
        meals_served=95,
        cooked_food_prepared_kg=33.0,
        kitchen_waste_kg=1.0,
        plate_waste_kg=1.5,
        waste_method="Manual Measurement (weighed on scale)",
        visual_category=None,
        ingredients=ingredients,
        db_path=test_db
    )
    assert entry_id > 0

    # 3. Check Duplicate Prevention Constraint
    with pytest.raises(ValueError, match="Duplicate Entry Error"):
        add_meal_entry(
            school_id=s_id,
            entry_date="2026-10-10",
            class_group="Primary (Class 1-5)",
            menu_name="Rice & Sambhar Duplicate",
            students_present=95,
            meals_served=95,
            cooked_food_prepared_kg=33.0,
            kitchen_waste_kg=1.0,
            plate_waste_kg=1.5,
            waste_method="Manual Measurement (weighed on scale)",
            visual_category=None,
            ingredients=ingredients,
            db_path=test_db
        )

    # 4. Fetch Entries and Verify Precomputed Nutrition & Waste
    entries = get_meal_entries(school_id=s_id, db_path=test_db)
    assert len(entries) == 1
    rec = entries[0]
    assert rec["per_serving_calories"] > 450.0
    assert rec["per_serving_protein"] > 12.0
    assert rec["total_waste_kg"] == 2.5
    assert rec["total_waste_pct"] == pytest.approx(7.58, rel=1e-2)
    assert rec["fuzzy_priority_score"] >= 0.0
    assert rec["fuzzy_badge"] in ["LOW", "MEDIUM", "HIGH"]

    # 5. Verify Reporting Compliance (Missing Report Detection)
    # Between 2026-10-05 and 2026-10-10 (6 days, 1 Sunday -> 5 working days)
    # Only 1 report submitted on 2026-10-10 -> 4 missing days!
    comp = get_reporting_compliance("2026-10-05", "2026-10-10", db_path=test_db)
    assert comp["total_schools"] == 1
    assert comp["total_received_reports"] == 1
    assert comp["school_stats"][0]["missing_reports_count"] >= 4
    assert comp["school_stats"][0]["compliance_pct"] < 100.0


def test_reference_norm_update(test_db):
    update_reference_norm("Primary (Class 1-5)", 480.0, 14.0, db_path=test_db)
    norms = get_reference_norms(test_db)
    assert norms["Primary (Class 1-5)"]["calories_kcal"] == 480.0
    assert norms["Primary (Class 1-5)"]["protein_g"] == 14.0
