"""
Food Wastage Engine for PM POSHAN Tracker
Distinguishes between:
1. Kitchen Leftovers (Production waste: food left unserved in degchis/cooking pots)
2. Plate Waste (Consumption waste: edible food served onto student plates but discarded uneaten)

Provides:
- Exact metric calculations (kg, percentages, grams per student).
- Visual estimation support (quarter-waste method).
- Strict validation rules to detect impossible or inconsistent records.
"""
from typing import Dict, Any, List, Optional
from config import VISUAL_WASTE_CATEGORIES


class WasteValidationError(ValueError):
    """Custom exception raised when waste records violate physical consistency."""
    pass


def estimate_plate_waste_from_visual(
    visual_category: str,
    cooked_food_distributed_kg: float
) -> float:
    """
    Translates visual plate waste categorical assessment into estimated kilograms.
    Formula: Estimated Plate Waste (kg) = Cooked Distributed (kg) * Waste Fraction
    """
    fraction = VISUAL_WASTE_CATEGORIES.get(visual_category)
    if fraction is None:
        raise ValueError(f"Category '{visual_category}' requires manual measurement or is not recognized.")
    
    return round(cooked_food_distributed_kg * fraction, 3)


def validate_meal_record(
    students_present: int,
    meals_served: int,
    cooked_food_prepared_kg: float,
    kitchen_waste_kg: float,
    plate_waste_kg: float
) -> List[str]:
    """
    Validates logical consistency of daily meal reporting.
    Returns a list of validation error messages. Empty list indicates valid entry.
    """
    errors = []

    if students_present < 0:
        errors.append("Students present cannot be negative.")
    if meals_served <= 0:
        errors.append("Meals served must be strictly greater than 0.")
    if meals_served > students_present and students_present > 0:
        errors.append(f"Inconsistent: Meals served ({meals_served}) cannot exceed students present ({students_present}).")
    if cooked_food_prepared_kg <= 0:
        errors.append("Quantity of cooked food prepared must be greater than 0 kg.")
    if kitchen_waste_kg < 0:
        errors.append("Kitchen leftovers cannot be negative.")
    if plate_waste_kg < 0:
        errors.append("Plate waste cannot be negative.")
        
    distributed_food = cooked_food_prepared_kg - kitchen_waste_kg
    if kitchen_waste_kg > cooked_food_prepared_kg:
        errors.append(f"Physical impossibility: Kitchen waste ({kitchen_waste_kg:.2f} kg) exceeds total food prepared ({cooked_food_prepared_kg:.2f} kg).")
    
    if distributed_food >= 0 and plate_waste_kg > distributed_food:
        errors.append(f"Physical impossibility: Plate waste ({plate_waste_kg:.2f} kg) exceeds food actually distributed ({distributed_food:.2f} kg).")
    
    total_waste = kitchen_waste_kg + plate_waste_kg
    if total_waste > cooked_food_prepared_kg:
        errors.append(f"Physical impossibility: Total waste ({total_waste:.2f} kg) exceeds total prepared food ({cooked_food_prepared_kg:.2f} kg).")

    return errors


def calculate_food_wastage(
    students_present: int,
    meals_served: int,
    cooked_food_prepared_kg: float,
    kitchen_waste_kg: float,
    plate_waste_kg: Optional[float] = None,
    visual_category: Optional[str] = None
) -> Dict[str, Any]:
    """
    Calculates detailed food wastage metrics.
    Supports either manual plate waste entry or visual category estimation.
    """
    # If visual category provided and plate_waste_kg is not directly given
    distributed_food = max(0.0, cooked_food_prepared_kg - kitchen_waste_kg)
    is_visual_estimate = False

    if plate_waste_kg is None:
        if visual_category and visual_category != "Manual Measurement (weighed on scale)":
            plate_waste_kg = estimate_plate_waste_from_visual(visual_category, distributed_food)
            is_visual_estimate = True
        else:
            plate_waste_kg = 0.0

    # Validate physical consistency
    errors = validate_meal_record(
        students_present=students_present,
        meals_served=meals_served,
        cooked_food_prepared_kg=cooked_food_prepared_kg,
        kitchen_waste_kg=kitchen_waste_kg,
        plate_waste_kg=plate_waste_kg
    )
    if errors:
        raise WasteValidationError("; ".join(errors))

    total_waste_kg = round(kitchen_waste_kg + plate_waste_kg, 3)
    food_consumed_kg = round(cooked_food_prepared_kg - total_waste_kg, 3)

    kitchen_waste_pct = round((kitchen_waste_kg / cooked_food_prepared_kg) * 100.0, 2)
    plate_waste_pct = round((plate_waste_kg / cooked_food_prepared_kg) * 100.0, 2)
    total_waste_pct = round((total_waste_kg / cooked_food_prepared_kg) * 100.0, 2)

    # Waste per student served (in grams)
    plate_waste_per_student_g = round((plate_waste_kg * 1000.0) / meals_served, 2)
    portion_served_per_student_g = round((distributed_food * 1000.0) / meals_served, 2)

    # Waste severity categorization
    if total_waste_pct < 8.0:
        waste_category = "Low / Acceptable (<8%)"
        waste_status_color = "green"
    elif total_waste_pct < 20.0:
        waste_category = "Moderate Wastage (8-20%)"
        waste_status_color = "orange"
    else:
        waste_category = "Critical Wastage (>20%)"
        waste_status_color = "red"

    return {
        "students_present": students_present,
        "meals_served": meals_served,
        "cooked_food_prepared_kg": round(cooked_food_prepared_kg, 3),
        "distributed_food_kg": round(distributed_food, 3),
        "food_consumed_kg": food_consumed_kg,
        "kitchen_waste_kg": round(kitchen_waste_kg, 3),
        "plate_waste_kg": round(plate_waste_kg, 3),
        "total_waste_kg": total_waste_kg,
        "kitchen_waste_pct": kitchen_waste_pct,
        "plate_waste_pct": plate_waste_pct,
        "total_waste_pct": total_waste_pct,
        "plate_waste_per_student_g": plate_waste_per_student_g,
        "portion_served_per_student_g": portion_served_per_student_g,
        "is_visual_estimate": is_visual_estimate,
        "visual_category": visual_category or "Manual Measurement (weighed on scale)",
        "waste_category": waste_category,
        "waste_status_color": waste_status_color
    }
