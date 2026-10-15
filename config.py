"""
Configuration and Reference Standards for PM POSHAN Mid-Day Meal Tracker
Sources:
- PM POSHAN (formerly Mid-Day Meal Scheme) Guidelines, Ministry of Education, Govt. of India
- ICMR - National Institute of Nutrition (NIN) Indian Food Composition Tables (IFCT)
"""
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = BASE_DIR / "poshan_tracker.db"

# PM POSHAN Reference Norms per Child per Serving (Configurable defaults)
DEFAULT_NORMS = {
    "Primary (Class 1-5)": {
        "calories_kcal": 450.0,
        "protein_g": 12.0,
        "foodgrains_g": 100.0,
        "pulses_g": 20.0,
        "vegetables_g": 50.0,
        "oil_fat_g": 5.0,
        "min_meals_recommended_serving_cooked_g": 250.0
    },
    "Upper Primary (Class 6-8)": {
        "calories_kcal": 700.0,
        "protein_g": 20.0,
        "foodgrains_g": 150.0,
        "pulses_g": 30.0,
        "vegetables_g": 75.0,
        "oil_fat_g": 7.5,
        "min_meals_recommended_serving_cooked_g": 375.0
    }
}

# Fuzzy Logic Universe of Discourse Limits
FUZZY_BOUNDS = {
    "adequacy_min": 0.0,
    "adequacy_max": 150.0,   # Percentage of combined nutrition target attained
    "waste_min": 0.0,
    "waste_max": 50.0,       # Food waste percentage of total prepared food
    "priority_min": 0.0,
    "priority_max": 100.0    # Soft computing review priority index (0-100)
}

# Visual Plate Waste Estimation Categories (Quarter-waste standard method)
VISUAL_WASTE_CATEGORIES = {
    "Manual Measurement (weighed on scale)": None,
    "No visible waste (< 2%)": 0.01,
    "Slight leftovers (~5%)": 0.05,
    "Quarter plate remaining (~25%)": 0.25,
    "Half plate remaining (~50%)": 0.50,
    "Substantial plate waste (> 75%)": 0.75
}

# Soft Computing Legal / Monitoring Disclaimer
SOFT_COMPUTING_DISCLAIMER = (
    "EXPERIMENTAL SOFT COMPUTING MONITORING AID: The Fuzzy Logic Review Priority "
    "is an algorithmic decision-support tool created for academic demonstration "
    "and academic soft computing evaluation. It does not constitute an official "
    "Government of India administrative audit, punitive notice, or clinical dietary diagnosis."
)
