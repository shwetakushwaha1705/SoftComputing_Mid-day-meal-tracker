"""
Synthetic Demonstration Data Generator for PM POSHAN Tracker.
NOTICE: ALL DATA GENERATED HERE IS EXPLICITLY MARKED AS SYNTHETIC SIMULATION DATA
FOR ACADEMIC REVIEW AND PROJECT DEMONSTRATION. NO REAL STUDENT PERSONAL DATA IS USED.
"""
import random
from datetime import datetime, timedelta
from database.db import init_db, add_school, add_meal_entry, get_schools, get_connection
from config import DATABASE_PATH

# Standard synthetic menus
SAMPLE_MENUS = [
    {
        "menu_name": "Steamed Rice, Toor Dal & Mixed Vegetable Sabzi",
        "primary_ingredients": [
            {"name": "Rice (Raw Milled)", "base_g_per_student": 100, "unit": "kg"},
            {"name": "Toor Dal (Split Red Gram)", "base_g_per_student": 22, "unit": "kg"},
            {"name": "Mixed Other Vegetables (Gourd/Beans/Tomato)", "base_g_per_student": 50, "unit": "kg"},
            {"name": "Mustard / Cooking Vegetable Oil", "base_g_per_student": 5, "unit": "kg"}
        ]
    },
    {
        "menu_name": "Nutritious Khichdi with Soya Chunks & Green Leafy Veg",
        "primary_ingredients": [
            {"name": "Rice (Raw Milled)", "base_g_per_student": 90, "unit": "kg"},
            {"name": "Moong Dal (Split Green Gram)", "base_g_per_student": 25, "unit": "kg"},
            {"name": "Soya Chunks (TVP)", "base_g_per_student": 15, "unit": "kg"},
            {"name": "Green Leafy Vegetables (Spinach/Methi)", "base_g_per_student": 40, "unit": "kg"},
            {"name": "Mustard / Cooking Vegetable Oil", "base_g_per_student": 5, "unit": "kg"}
        ]
    },
    {
        "menu_name": "Whole Wheat Roti, Kala Chana Dal & Potatoes",
        "primary_ingredients": [
            {"name": "Wheat Flour (Whole Atta)", "base_g_per_student": 105, "unit": "kg"},
            {"name": "Bengal Gram Whole (Kala Chana)", "base_g_per_student": 25, "unit": "kg"},
            {"name": "Potatoes (Raw)", "base_g_per_student": 45, "unit": "kg"},
            {"name": "Mustard / Cooking Vegetable Oil", "base_g_per_student": 5, "unit": "kg"}
        ]
    },
    {
        "menu_name": "Rice, Masoor Dal, Veg Curry & Boiled Egg Supplement",
        "primary_ingredients": [
            {"name": "Rice (Raw Milled)", "base_g_per_student": 100, "unit": "kg"},
            {"name": "Masoor Dal (Split Red Lentil)", "base_g_per_student": 20, "unit": "kg"},
            {"name": "Mixed Other Vegetables (Gourd/Beans/Tomato)", "base_g_per_student": 45, "unit": "kg"},
            {"name": "Mustard / Cooking Vegetable Oil", "base_g_per_student": 5, "unit": "kg"},
            {"name": "Whole Hen Egg (Boiled)", "base_g_per_student": 1, "unit": "piece"}
        ]
    }
]

SCHOOLS_DATA = [
    {
        "school_code": "SCH-101",
        "name": "Govt. Primary School, Rampur Central",
        "block": "Rampur Block",
        "district": "Adarsh District",
        "registered_primary": 120,
        "registered_upper_primary": 0,
        "persona": "compliant"
    },
    {
        "school_code": "SCH-102",
        "name": "Govt. Model Middle School, Rampur East",
        "block": "Rampur Block",
        "district": "Adarsh District",
        "registered_primary": 110,
        "registered_upper_primary": 95,
        "persona": "compliant"
    },
    {
        "school_code": "SCH-103",
        "name": "Govt. Girls Primary School, Rampur West",
        "block": "Rampur Block",
        "district": "Adarsh District",
        "registered_primary": 85,
        "registered_upper_primary": 0,
        "persona": "missing_reports"  # Deliberately skips reporting some days
    },
    {
        "school_code": "SCH-201",
        "name": "Govt. Upper Primary School, Sundarpur North",
        "block": "Sundarpur Block",
        "district": "Adarsh District",
        "registered_primary": 90,
        "registered_upper_primary": 110,
        "persona": "high_waste"  # High leftover in kitchen
    },
    {
        "school_code": "SCH-202",
        "name": "Govt. Primary School, Sundarpur South",
        "block": "Sundarpur Block",
        "district": "Adarsh District",
        "registered_primary": 130,
        "registered_upper_primary": 0,
        "persona": "nutrition_deficit"  # Under-allocated pulses/grains
    },
    {
        "school_code": "SCH-203",
        "name": "Govt. Tribal Ashram School, Sundarpur Hills",
        "block": "Sundarpur Block",
        "district": "Adarsh District",
        "registered_primary": 75,
        "registered_upper_primary": 60,
        "persona": "visual_estimates"
    }
]


def seed_database(db_path=None, days_back=12, clear_existing=True):
    """
    Populates database with realistic synthetic schools and historical meal logs.
    """
    init_db(db_path)
    conn = get_connection(db_path)
    cur = conn.cursor()

    if clear_existing:
        cur.execute("DELETE FROM meal_entries;")
        cur.execute("DELETE FROM schools;")
        conn.commit()

    # 1. Create Schools
    school_map = {}
    for s_info in SCHOOLS_DATA:
        cur.execute("""
            INSERT INTO schools (school_code, name, block, district, registered_primary, registered_upper_primary)
            VALUES (?, ?, ?, ?, ?, ?);
        """, (
            s_info["school_code"], s_info["name"], s_info["block"],
            s_info["district"], s_info["registered_primary"], s_info["registered_upper_primary"]
        ))
        s_id = cur.lastrowid
        school_map[s_info["school_code"]] = {
            "id": s_id,
            "info": s_info
        }
    conn.commit()
    conn.close()

    # 2. Generate meal sessions for the last N working days
    today = datetime.now().date()
    dates = []
    curr = today - timedelta(days=days_back)
    while curr <= today:
        if curr.weekday() != 6:  # Skip Sunday
            dates.append(curr.strftime("%Y-%m-%d"))
        curr += timedelta(days=1)

    random.seed(42)  # Deterministic seed for reproducible testing

    total_entries_created = 0

    for s_code, s_obj in school_map.items():
        s_id = s_obj["id"]
        persona = s_obj["info"]["persona"]
        reg_p = s_obj["info"]["registered_primary"]
        reg_up = s_obj["info"]["registered_upper_primary"]

        class_groups = []
        if reg_p > 0:
            class_groups.append("Primary (Class 1-5)")
        if reg_up > 0:
            class_groups.append("Upper Primary (Class 6-8)")

        for day_str in dates:
            # If persona is missing_reports, randomly skip ~35% of days to demonstrate missing report detection
            if persona == "missing_reports" and random.random() < 0.35:
                continue

            for c_group in class_groups:
                menu = random.choice(SAMPLE_MENUS)
                reg_count = reg_p if "Primary (Class 1-5)" in c_group else reg_up
                
                # Attendance fluctuates realistically between 80% to 96%
                present_ratio = random.uniform(0.82, 0.95)
                students_present = int(reg_count * present_ratio)
                meals_served = students_present - random.randint(0, 2)  # 0 to 2 kids might be absent for meal

                # Portion scaling multiplier
                multiplier = 1.45 if "Upper Primary" in c_group else 1.0

                # Persona adjustments
                if persona == "nutrition_deficit":
                    nutrition_scale = 0.65  # Deliberate calorie/protein shortage
                else:
                    nutrition_scale = random.uniform(0.95, 1.10)

                # Build ingredient list
                ingredients = []
                for ing in menu["primary_ingredients"]:
                    name = ing["name"]
                    base_g = ing["base_g_per_student"] * multiplier * nutrition_scale
                    total_g = base_g * meals_served

                    if ing["unit"] == "piece":
                        total_qty = round(meals_served, 0)
                        u = "piece"
                    elif ing["unit"] == "kg":
                        total_qty = round(total_g / 1000.0, 3)
                        u = "kg"
                    else:
                        total_qty = round(total_g, 2)
                        u = "g"

                    ingredients.append({
                        "name": name,
                        "quantity": total_qty,
                        "unit": u,
                        "form": "raw"
                    })

                # Cooked food prepared estimation (Standard ~350g primary, 500g upper primary cooked per child)
                cooked_per_child_kg = 0.48 if "Upper Primary" in c_group else 0.35
                if persona == "high_waste":
                    # Cooked far too much food
                    cooked_food_prepared_kg = round(meals_served * cooked_per_child_kg * 1.35, 2)
                    kitchen_waste_kg = round(cooked_food_prepared_kg * random.uniform(0.18, 0.25), 2)
                    plate_waste_kg = round(cooked_food_prepared_kg * random.uniform(0.08, 0.12), 2)
                    waste_method = "Manual Measurement (weighed on scale)"
                    vis_cat = None
                elif persona == "visual_estimates":
                    cooked_food_prepared_kg = round(meals_served * cooked_per_child_kg * 1.05, 2)
                    kitchen_waste_kg = round(random.uniform(0.4, 1.2), 2)
                    vis_cat = random.choice([
                        "No visible waste (< 2%)",
                        "Slight leftovers (~5%)",
                        "Quarter plate remaining (~25%)"
                    ])
                    waste_method = "Visual Category Estimation"
                    plate_waste_kg = None  # Will be calculated by engine from visual cat
                else:
                    # Compliant / standard persona
                    cooked_food_prepared_kg = round(meals_served * cooked_per_child_kg * 1.05, 2)
                    kitchen_waste_kg = round(random.uniform(0.2, 0.8), 2)
                    plate_waste_kg = round(random.uniform(0.5, 1.5), 2)
                    waste_method = "Manual Measurement (weighed on scale)"
                    vis_cat = None

                # Record in database
                add_meal_entry(
                    school_id=s_id,
                    entry_date=day_str,
                    class_group=c_group,
                    menu_name=menu["menu_name"],
                    students_present=students_present,
                    meals_served=meals_served,
                    cooked_food_prepared_kg=cooked_food_prepared_kg,
                    kitchen_waste_kg=kitchen_waste_kg,
                    plate_waste_kg=plate_waste_kg,
                    waste_method=waste_method,
                    visual_category=vis_cat,
                    ingredients=ingredients,
                    db_path=db_path
                )
                total_entries_created += 1

    print(f"[SYNTHETIC SEED SUCCESS] Initialized {len(SCHOOLS_DATA)} schools and {total_entries_created} synthetic meal entries.")
    return total_entries_created


if __name__ == "__main__":
    seed_database()
