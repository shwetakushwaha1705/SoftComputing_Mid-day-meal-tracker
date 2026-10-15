"""
Database access and schema management for PM POSHAN Tracker.
Uses SQLite for zero-configuration, persistent relational storage.
"""
import sqlite3
import json
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional, Tuple
from config import DATABASE_PATH, DEFAULT_NORMS
from engines.nutrition_engine import calculate_meal_nutrition
from engines.wastage_engine import calculate_food_wastage
from engines.fuzzy_engine import fuzzy_engine


def get_connection(db_path=None) -> sqlite3.Connection:
    path = db_path or DATABASE_PATH
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    # Enable foreign keys
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db(db_path=None):
    """
    Creates tables and indices if they do not exist.
    """
    conn = get_connection(db_path)
    cur = conn.cursor()

    # 1. Schools table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS schools (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            school_code TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            block TEXT NOT NULL,
            district TEXT NOT NULL DEFAULT 'District HQ',
            registered_primary INTEGER NOT NULL DEFAULT 100,
            registered_upper_primary INTEGER NOT NULL DEFAULT 80,
            is_active INTEGER NOT NULL DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # 2. Daily Meal Entries table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS meal_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            school_id INTEGER NOT NULL,
            entry_date TEXT NOT NULL,
            class_group TEXT NOT NULL,
            menu_name TEXT NOT NULL,
            students_present INTEGER NOT NULL,
            meals_served INTEGER NOT NULL,
            cooked_food_prepared_kg REAL NOT NULL,
            kitchen_waste_kg REAL NOT NULL DEFAULT 0.0,
            plate_waste_kg REAL NOT NULL DEFAULT 0.0,
            waste_method TEXT NOT NULL,
            visual_category TEXT,
            ingredients_json TEXT NOT NULL,
            
            -- Precomputed Nutritional Values
            total_calories_kcal REAL NOT NULL,
            total_protein_g REAL NOT NULL,
            per_serving_calories REAL NOT NULL,
            per_serving_protein REAL NOT NULL,
            energy_adequacy_pct REAL NOT NULL,
            protein_adequacy_pct REAL NOT NULL,
            combined_adequacy_pct REAL NOT NULL,
            nutrition_status TEXT NOT NULL,

            -- Precomputed Wastage Values
            total_waste_kg REAL NOT NULL,
            total_waste_pct REAL NOT NULL,
            kitchen_waste_pct REAL NOT NULL,
            plate_waste_pct REAL NOT NULL,
            plate_waste_per_student_g REAL NOT NULL,
            waste_category TEXT NOT NULL,

            -- Soft Computing Assessment Values
            fuzzy_priority_score REAL NOT NULL,
            fuzzy_priority_label TEXT NOT NULL,
            fuzzy_badge TEXT NOT NULL,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (school_id) REFERENCES schools(id) ON DELETE CASCADE,
            UNIQUE(school_id, entry_date, class_group)
        );
    """)

    # 3. Reference Targets Configuration table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS reference_norms (
            class_group TEXT PRIMARY KEY,
            calories_kcal REAL NOT NULL,
            protein_g REAL NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # Insert default norms if not present
    for group_name, vals in DEFAULT_NORMS.items():
        cur.execute("""
            INSERT OR IGNORE INTO reference_norms (class_group, calories_kcal, protein_g)
            VALUES (?, ?, ?);
        """, (group_name, vals["calories_kcal"], vals["protein_g"]))

    conn.commit()
    conn.close()


def get_reference_norms(db_path=None) -> Dict[str, Dict[str, float]]:
    conn = get_connection(db_path)
    cur = conn.cursor()
    cur.execute("SELECT class_group, calories_kcal, protein_g FROM reference_norms")
    rows = cur.fetchall()
    conn.close()
    
    norms = {}
    for r in rows:
        norms[r["class_group"]] = {
            "calories_kcal": float(r["calories_kcal"]),
            "protein_g": float(r["protein_g"])
        }
    return norms if norms else DEFAULT_NORMS


def update_reference_norm(class_group: str, calories_kcal: float, protein_g: float, db_path=None):
    conn = get_connection(db_path)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO reference_norms (class_group, calories_kcal, protein_g, updated_at)
        VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(class_group) DO UPDATE SET
            calories_kcal = excluded.calories_kcal,
            protein_g = excluded.protein_g,
            updated_at = CURRENT_TIMESTAMP;
    """, (class_group, calories_kcal, protein_g))
    conn.commit()
    conn.close()


def add_school(
    school_code: str,
    name: str,
    block: str,
    district: str = "District HQ",
    registered_primary: int = 100,
    registered_upper_primary: int = 80,
    db_path=None
) -> int:
    conn = get_connection(db_path)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO schools (school_code, name, block, district, registered_primary, registered_upper_primary)
        VALUES (?, ?, ?, ?, ?, ?);
    """, (school_code, name, block, district, registered_primary, registered_upper_primary))
    school_id = cur.lastrowid
    conn.commit()
    conn.close()
    return school_id


def get_schools(db_path=None) -> List[Dict[str, Any]]:
    conn = get_connection(db_path)
    cur = conn.cursor()
    cur.execute("SELECT * FROM schools WHERE is_active = 1 ORDER BY block ASC, name ASC")
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def get_school_by_id(school_id: int, db_path=None) -> Optional[Dict[str, Any]]:
    conn = get_connection(db_path)
    cur = conn.cursor()
    cur.execute("SELECT * FROM schools WHERE id = ?", (school_id,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def add_meal_entry(
    school_id: int,
    entry_date: str,
    class_group: str,
    menu_name: str,
    students_present: int,
    meals_served: int,
    cooked_food_prepared_kg: float,
    kitchen_waste_kg: float,
    plate_waste_kg: Optional[float],
    waste_method: str,
    visual_category: Optional[str],
    ingredients: List[Dict[str, Any]],
    db_path=None
) -> int:
    """
    Computes nutrition, wastage, and soft computing priority, then records entry.
    Prevents duplicate entries for the same school, date, and class group.
    """
    # 1. Check for duplicates
    conn = get_connection(db_path)
    cur = conn.cursor()
    cur.execute("""
        SELECT id FROM meal_entries 
        WHERE school_id = ? AND entry_date = ? AND class_group = ?
    """, (school_id, entry_date, class_group))
    existing = cur.fetchone()
    if existing:
        conn.close()
        raise ValueError(
            f"Duplicate Entry Error: A meal session record already exists for this school, "
            f"date ({entry_date}), and class group ({class_group})."
        )

    # 2. Get active norms
    norms = get_reference_norms(db_path)
    custom_target = norms.get(class_group)

    # 3. Calculate Nutrition
    nutri = calculate_meal_nutrition(
        ingredients=ingredients,
        meals_served=meals_served,
        class_group=class_group,
        custom_targets=custom_target
    )

    # 4. Calculate Wastage
    waste = calculate_food_wastage(
        students_present=students_present,
        meals_served=meals_served,
        cooked_food_prepared_kg=cooked_food_prepared_kg,
        kitchen_waste_kg=kitchen_waste_kg,
        plate_waste_kg=plate_waste_kg,
        visual_category=visual_category
    )

    # 5. Soft Computing Fuzzy Logic Assessment
    fuzzy_eval = fuzzy_engine.evaluate(
        nutrition_adequacy_pct=nutri["combined_adequacy_pct"],
        food_waste_pct=waste["total_waste_pct"]
    )

    # 6. Save to database
    cur.execute("""
        INSERT INTO meal_entries (
            school_id, entry_date, class_group, menu_name,
            students_present, meals_served, cooked_food_prepared_kg,
            kitchen_waste_kg, plate_waste_kg, waste_method, visual_category,
            ingredients_json,
            total_calories_kcal, total_protein_g, per_serving_calories, per_serving_protein,
            energy_adequacy_pct, protein_adequacy_pct, combined_adequacy_pct, nutrition_status,
            total_waste_kg, total_waste_pct, kitchen_waste_pct, plate_waste_pct,
            plate_waste_per_student_g, waste_category,
            fuzzy_priority_score, fuzzy_priority_label, fuzzy_badge
        ) VALUES (
            ?, ?, ?, ?,
            ?, ?, ?,
            ?, ?, ?, ?,
            ?,
            ?, ?, ?, ?,
            ?, ?, ?, ?,
            ?, ?, ?, ?,
            ?, ?,
            ?, ?, ?
        );
    """, (
        school_id, entry_date, class_group, menu_name,
        students_present, meals_served, waste["cooked_food_prepared_kg"],
        waste["kitchen_waste_kg"], waste["plate_waste_kg"], waste_method, visual_category,
        json.dumps(ingredients),
        nutri["total_batch_calories_kcal"], nutri["total_batch_protein_g"],
        nutri["per_serving_calories_kcal"], nutri["per_serving_protein_g"],
        nutri["energy_adequacy_pct"], nutri["protein_adequacy_pct"], nutri["combined_adequacy_pct"],
        nutri["status"],
        waste["total_waste_kg"], waste["total_waste_pct"], waste["kitchen_waste_pct"],
        waste["plate_waste_pct"], waste["plate_waste_per_student_g"], waste["waste_category"],
        fuzzy_eval["review_priority_score"], fuzzy_eval["priority_label"], fuzzy_eval["priority_badge"]
    ))

    entry_id = cur.lastrowid
    conn.commit()
    conn.close()
    return entry_id


def get_meal_entries(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    school_id: Optional[int] = None,
    block: Optional[str] = None,
    class_group: Optional[str] = None,
    priority_badge: Optional[str] = None,
    db_path=None
) -> List[Dict[str, Any]]:
    """
    Flexible query fetcher joining school details with meal records.
    """
    conn = get_connection(db_path)
    cur = conn.cursor()

    query = """
        SELECT m.*, s.name as school_name, s.school_code, s.block, s.district
        FROM meal_entries m
        JOIN schools s ON m.school_id = s.id
        WHERE 1=1
    """
    params = []

    if start_date:
        query += " AND m.entry_date >= ?"
        params.append(start_date)
    if end_date:
        query += " AND m.entry_date <= ?"
        params.append(end_date)
    if school_id:
        query += " AND m.school_id = ?"
        params.append(school_id)
    if block and block != "All Blocks":
        query += " AND s.block = ?"
        params.append(block)
    if class_group and class_group != "All Classes":
        query += " AND m.class_group = ?"
        params.append(class_group)
    if priority_badge and priority_badge != "All":
        query += " AND m.fuzzy_badge = ?"
        params.append(priority_badge)

    query += " ORDER BY m.entry_date DESC, s.name ASC"

    cur.execute(query, params)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def delete_meal_entry(entry_id: int, db_path=None) -> bool:
    conn = get_connection(db_path)
    cur = conn.cursor()
    cur.execute("DELETE FROM meal_entries WHERE id = ?", (entry_id,))
    deleted = cur.rowcount > 0
    conn.commit()
    conn.close()
    return deleted


def get_reporting_compliance(
    start_date: str,
    end_date: str,
    block: Optional[str] = None,
    db_path=None
) -> Dict[str, Any]:
    """
    Examines reporting compliance across schools in the selected period.
    Crucial requirement: Missing reports are NOT treated as 0% waste or compliance.
    Identifies expected school days vs reports submitted.
    """
    conn = get_connection(db_path)
    cur = conn.cursor()

    # Get schools list
    query = "SELECT id, school_code, name, block FROM schools WHERE is_active = 1"
    params = []
    if block and block != "All Blocks":
        query += " AND block = ?"
        params.append(block)
    query += " ORDER BY block, name"
    cur.execute(query, params)
    schools = [dict(r) for r in cur.fetchall()]

    # Generate list of working days (Monday through Saturday, skipping Sunday)
    s_date = datetime.strptime(start_date, "%Y-%m-%d").date()
    e_date = datetime.strptime(end_date, "%Y-%m-%d").date()
    
    working_dates = []
    curr = s_date
    while curr <= e_date:
        # 6 is Sunday
        if curr.weekday() != 6:
            working_dates.append(curr.strftime("%Y-%m-%d"))
        curr += timedelta(days=1)

    expected_reports_per_school = len(working_dates)

    # Fetch actual reports in period
    school_stats = []
    total_expected = len(schools) * expected_reports_per_school
    total_received = 0

    for s in schools:
        cur.execute("""
            SELECT entry_date, combined_adequacy_pct, total_waste_pct, fuzzy_badge
            FROM meal_entries
            WHERE school_id = ? AND entry_date >= ? AND entry_date <= ?
        """, (s["id"], start_date, end_date))
        reports = cur.fetchall()
        reported_dates = {r["entry_date"] for r in reports}
        received_count = len(reported_dates)
        total_received += received_count

        missing_dates = sorted(list(set(working_dates) - reported_dates))
        compliance_pct = round((received_count / max(1, expected_reports_per_school)) * 100.0, 1)

        # Average adequacy and waste for reported days only
        if reports:
            avg_adeq = round(sum([r["combined_adequacy_pct"] for r in reports]) / len(reports), 1)
            avg_waste = round(sum([r["total_waste_pct"] for r in reports]) / len(reports), 1)
            high_priority_count = sum([1 for r in reports if r["fuzzy_badge"] == "HIGH"])
        else:
            avg_adeq = None
            avg_waste = None
            high_priority_count = 0

        school_stats.append({
            "school_id": s["id"],
            "school_code": s["school_code"],
            "name": s["name"],
            "block": s["block"],
            "expected_reports": expected_reports_per_school,
            "received_reports": received_count,
            "missing_reports_count": len(missing_dates),
            "missing_dates": missing_dates,
            "compliance_pct": compliance_pct,
            "avg_adequacy_pct": avg_adeq,
            "avg_waste_pct": avg_waste,
            "high_priority_count": high_priority_count
        })

    conn.close()

    overall_compliance_pct = round((total_received / max(1, total_expected)) * 100.0, 1) if total_expected > 0 else 0.0

    return {
        "start_date": start_date,
        "end_date": end_date,
        "working_days_count": expected_reports_per_school,
        "total_schools": len(schools),
        "total_expected_reports": total_expected,
        "total_received_reports": total_received,
        "overall_compliance_pct": overall_compliance_pct,
        "school_stats": school_stats
    }
