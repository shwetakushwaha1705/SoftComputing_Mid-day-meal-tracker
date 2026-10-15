"""
Nutrition Calculation Engine for PM POSHAN Tracker
Based on Indian Food Composition Tables (IFCT) published by ICMR - National Institute of Nutrition (NIN), Hyderabad.

Institutional standard:
In the PM POSHAN scheme, food grains, pulses, vegetables, and oils are issued and recorded
predominantly in raw weight per batch. Calories and protein values are derived from raw composition.
If cooked quantities are provided, standardized yield hydration factors are applied.
"""
from typing import Dict, List, Any, Optional

# Standard ICMR-NIN IFCT reference data (Values per 100g edible portion, raw unless specified)
INGREDIENT_DATABASE: Dict[str, Dict[str, Any]] = {
    "Rice (Raw Milled)": {
        "calories_per_100g": 356.0,
        "protein_per_100g": 7.9,
        "default_unit": "kg",
        "category": "Foodgrain",
        "cooked_yield_factor": 2.8,  # 100g raw yields ~280g cooked
        "source": "ICMR-NIN IFCT 2017 (Code: A001)"
    },
    "Rice (Parboiled)": {
        "calories_per_100g": 352.0,
        "protein_per_100g": 7.4,
        "default_unit": "kg",
        "category": "Foodgrain",
        "cooked_yield_factor": 2.7,
        "source": "ICMR-NIN IFCT 2017 (Code: A002)"
    },
    "Wheat Flour (Whole Atta)": {
        "calories_per_100g": 341.0,
        "protein_per_100g": 12.1,
        "default_unit": "kg",
        "category": "Foodgrain",
        "cooked_yield_factor": 1.4,  # Chapati/roti yield factor
        "source": "ICMR-NIN IFCT 2017 (Code: A012)"
    },
    "Toor Dal (Split Red Gram)": {
        "calories_per_100g": 343.0,
        "protein_per_100g": 22.3,
        "default_unit": "kg",
        "category": "Pulses",
        "cooked_yield_factor": 3.0,
        "source": "ICMR-NIN IFCT 2017 (Code: B001)"
    },
    "Moong Dal (Split Green Gram)": {
        "calories_per_100g": 348.0,
        "protein_per_100g": 24.5,
        "default_unit": "kg",
        "category": "Pulses",
        "cooked_yield_factor": 3.2,
        "source": "ICMR-NIN IFCT 2017 (Code: B004)"
    },
    "Chana Dal (Bengal Gram Split)": {
        "calories_per_100g": 372.0,
        "protein_per_100g": 20.8,
        "default_unit": "kg",
        "category": "Pulses",
        "cooked_yield_factor": 2.5,
        "source": "ICMR-NIN IFCT 2017 (Code: B002)"
    },
    "Masoor Dal (Split Red Lentil)": {
        "calories_per_100g": 343.0,
        "protein_per_100g": 25.1,
        "default_unit": "kg",
        "category": "Pulses",
        "cooked_yield_factor": 3.0,
        "source": "ICMR-NIN IFCT 2017 (Code: B005)"
    },
    "Soya Chunks (TVP)": {
        "calories_per_100g": 345.0,
        "protein_per_100g": 52.0,
        "default_unit": "kg",
        "category": "Pulses/Soy",
        "cooked_yield_factor": 3.5,
        "source": "ICMR-NIN & Commercial standard IFCT"
    },
    "Mustard / Cooking Vegetable Oil": {
        "calories_per_100g": 900.0,
        "protein_per_100g": 0.0,
        "default_unit": "kg",
        "category": "Fats & Oils",
        "cooked_yield_factor": 1.0,
        "source": "ICMR-NIN IFCT 2017 (Fats group)"
    },
    "Potatoes (Raw)": {
        "calories_per_100g": 97.0,
        "protein_per_100g": 1.6,
        "default_unit": "kg",
        "category": "Vegetables",
        "cooked_yield_factor": 0.95,
        "source": "ICMR-NIN IFCT 2017 (Roots & Tubers)"
    },
    "Green Leafy Vegetables (Spinach/Methi)": {
        "calories_per_100g": 26.0,
        "protein_per_100g": 2.0,
        "default_unit": "kg",
        "category": "Vegetables",
        "cooked_yield_factor": 0.85,
        "source": "ICMR-NIN IFCT 2017 (Green Leafy Veg)"
    },
    "Mixed Other Vegetables (Gourd/Beans/Tomato)": {
        "calories_per_100g": 34.0,
        "protein_per_100g": 1.8,
        "default_unit": "kg",
        "category": "Vegetables",
        "cooked_yield_factor": 0.9,
        "source": "ICMR-NIN IFCT 2017 (Other Veg)"
    },
    "Onions & Cooking Condiments": {
        "calories_per_100g": 50.0,
        "protein_per_100g": 1.2,
        "default_unit": "kg",
        "category": "Vegetables/Condiments",
        "cooked_yield_factor": 0.9,
        "source": "ICMR-NIN IFCT 2017 (Condiments)"
    },
    "Whole Hen Egg (Boiled)": {
        "calories_per_100g": 173.0,
        "protein_per_100g": 13.3,
        "calories_per_piece": 86.5,  # Assuming ~50g egg
        "protein_per_piece": 6.65,
        "default_unit": "piece",
        "category": "Egg/Poultry",
        "cooked_yield_factor": 1.0,
        "source": "ICMR-NIN IFCT 2017 (Egg group, ~50g/egg)"
    },
    "Cow's Milk (Boiled/Pasteurized)": {
        "calories_per_100g": 67.0,   # approx 67 kcal per 100ml
        "protein_per_100g": 3.2,
        "default_unit": "liter",
        "category": "Dairy",
        "cooked_yield_factor": 1.0,
        "source": "ICMR-NIN IFCT 2017 (Milk group)"
    },
    "Bengal Gram Whole (Kala Chana)": {
        "calories_per_100g": 360.0,
        "protein_per_100g": 17.1,
        "default_unit": "kg",
        "category": "Pulses",
        "cooked_yield_factor": 2.4,
        "source": "ICMR-NIN IFCT 2017 (Whole legumes)"
    },
    "Jaggery (Gur)": {
        "calories_per_100g": 383.0,
        "protein_per_100g": 0.4,
        "default_unit": "kg",
        "category": "Sugars",
        "cooked_yield_factor": 1.0,
        "source": "ICMR-NIN IFCT 2017 (Sugars group)"
    }
}


def normalize_quantity_to_grams(quantity: float, unit: str, item_name: Optional[str] = None) -> float:
    """
    Converts diverse weight/volume units into standard grams for nutrient calculation.
    """
    u = unit.strip().lower()
    if u in ["kg", "kilogram", "kilograms"]:
        return quantity * 1000.0
    elif u in ["g", "gram", "grams"]:
        return quantity
    elif u in ["liter", "l", "liters", "litre", "litres"]:
        # Milk density ~ 1.03 kg/L, approximating 1 L ~ 1000g
        return quantity * 1000.0
    elif u in ["ml", "milliliter", "milliliters"]:
        return quantity * 1.0
    elif u in ["piece", "pieces", "count", "egg", "eggs", "unit", "units"]:
        if item_name and "egg" in item_name.lower():
            return quantity * 50.0  # Standard Indian hen's egg is ~50 grams edible portion
        return quantity * 50.0
    else:
        # Fallback assumes grams
        return quantity


def calculate_ingredient_nutrition(
    ingredient_name: str,
    quantity: float,
    unit: str,
    form: str = "raw"
) -> Dict[str, Any]:
    """
    Calculates calories and protein for a single ingredient entry.
    Handles raw vs cooked state:
    - If 'raw', standard raw dry weight is used.
    - If 'cooked', adjusts for the hydration/moisture gain using cooked_yield_factor.
    """
    if ingredient_name not in INGREDIENT_DATABASE:
        raise ValueError(f"Unknown ingredient: '{ingredient_name}'. Must be in verified database.")
    
    if quantity < 0:
        raise ValueError("Ingredient quantity cannot be negative.")

    info = INGREDIENT_DATABASE[ingredient_name]
    grams = normalize_quantity_to_grams(quantity, unit, ingredient_name)
    
    effective_raw_grams = grams
    form_lower = form.strip().lower()
    if form_lower == "cooked":
        # Convert cooked weight back to equivalent raw dry weight using yield factor
        yield_factor = info.get("cooked_yield_factor", 1.0)
        effective_raw_grams = grams / max(yield_factor, 1.0)
    
    calories = (effective_raw_grams / 100.0) * info["calories_per_100g"]
    protein = (effective_raw_grams / 100.0) * info["protein_per_100g"]

    return {
        "ingredient": ingredient_name,
        "input_quantity": round(quantity, 3),
        "input_unit": unit,
        "form": form,
        "effective_raw_grams": round(effective_raw_grams, 2),
        "calories_kcal": round(calories, 2),
        "protein_g": round(protein, 2),
        "category": info["category"],
        "source": info["source"]
    }


def calculate_meal_nutrition(
    ingredients: List[Dict[str, Any]],
    meals_served: int,
    class_group: str,
    custom_targets: Optional[Dict[str, float]] = None
) -> Dict[str, Any]:
    """
    Aggregates batch nutrition and calculates per-student serving compared to PM POSHAN norms.
    
    Formulae:
      Total Batch Energy = sum(ingredient.calories)
      Total Batch Protein = sum(ingredient.protein)
      Per Serving Energy = Total Batch Energy / meals_served
      Per Serving Protein = Total Batch Protein / meals_served
      Energy Adequacy % = (Per Serving Energy / Target Energy) * 100
      Protein Adequacy % = (Per Serving Protein / Target Protein) * 100
      Combined Adequacy Index % = min(Energy Adequacy %, Protein Adequacy %) 
                                 or weighted average for balanced compliance
    """
    if meals_served <= 0:
        raise ValueError("Meals served must be greater than zero.")

    from config import DEFAULT_NORMS
    target_norm = DEFAULT_NORMS.get(class_group, DEFAULT_NORMS["Primary (Class 1-5)"]).copy()
    if custom_targets:
        target_norm.update(custom_targets)

    target_calories = float(target_norm["calories_kcal"])
    target_protein = float(target_norm["protein_g"])

    total_calories = 0.0
    total_protein = 0.0
    itemized_breakdown = []

    for item in ingredients:
        res = calculate_ingredient_nutrition(
            ingredient_name=item["name"],
            quantity=float(item["quantity"]),
            unit=item["unit"],
            form=item.get("form", "raw")
        )
        total_calories += res["calories_kcal"]
        total_protein += res["protein_g"]
        itemized_breakdown.append(res)

    per_serving_calories = round(total_calories / meals_served, 2)
    per_serving_protein = round(total_protein / meals_served, 2)

    energy_adequacy_pct = round((per_serving_calories / target_calories) * 100.0, 2)
    protein_adequacy_pct = round((per_serving_protein / target_protein) * 100.0, 2)

    # Combined adequacy is calculated with harmonic balance (balanced energy and protein attainment)
    # or mean capped for reporting
    combined_adequacy_pct = round((energy_adequacy_pct + protein_adequacy_pct) / 2.0, 2)

    # Nutritional status tag
    if energy_adequacy_pct >= 90.0 and protein_adequacy_pct >= 90.0:
        status = "Adequate (Meets PM POSHAN Norms)"
        status_color = "green"
    elif energy_adequacy_pct >= 75.0 or protein_adequacy_pct >= 75.0:
        status = "Moderate Deficit"
        status_color = "orange"
    else:
        status = "Severe Deficit"
        status_color = "red"

    return {
        "class_group": class_group,
        "meals_served": meals_served,
        "target_calories_kcal": target_calories,
        "target_protein_g": target_protein,
        "total_batch_calories_kcal": round(total_calories, 2),
        "total_batch_protein_g": round(total_protein, 2),
        "per_serving_calories_kcal": per_serving_calories,
        "per_serving_protein_g": per_serving_protein,
        "energy_adequacy_pct": energy_adequacy_pct,
        "protein_adequacy_pct": protein_adequacy_pct,
        "combined_adequacy_pct": combined_adequacy_pct,
        "status": status,
        "status_color": status_color,
        "breakdown": itemized_breakdown
    }
