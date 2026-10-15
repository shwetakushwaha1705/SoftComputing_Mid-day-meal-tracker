"""
Daily Meal Entry View - Mobile-first interface for school data entry
Supports manual measurements, visual plate waste estimation, dynamic ingredient builder,
live nutrition preview, and strict validation against duplicate meal sessions.
"""
import streamlit as st
import pandas as pd
from datetime import datetime, date
from typing import List, Dict, Any

from database.db import get_schools, add_meal_entry, get_reference_norms
from engines.nutrition_engine import INGREDIENT_DATABASE, calculate_meal_nutrition
from engines.wastage_engine import calculate_food_wastage, WasteValidationError
from engines.fuzzy_engine import fuzzy_engine
from config import VISUAL_WASTE_CATEGORIES


def render_daily_entry_view():
    st.markdown("## 🍲 Daily Mid-Day Meal Data Entry")
    st.caption("Mobile-first daily reporting for School Headmasters, Teachers, and Cooking Staff")

    schools = get_schools()
    if not schools:
        st.error("No schools registered in database. Please seed the database or add schools.")
        return

    # Initialize session state for ingredients if not present
    if "entry_ingredients" not in st.session_state:
        # Default starting template (Standard Rice + Dal + Veg)
        st.session_state.entry_ingredients = [
            {"name": "Rice (Raw Milled)", "quantity": 10.0, "unit": "kg", "form": "raw"},
            {"name": "Toor Dal (Split Red Gram)", "quantity": 2.2, "unit": "kg", "form": "raw"},
            {"name": "Mixed Other Vegetables (Gourd/Beans/Tomato)", "quantity": 5.0, "unit": "kg", "form": "raw"},
            {"name": "Mustard / Cooking Vegetable Oil", "quantity": 0.5, "unit": "kg", "form": "raw"}
        ]

    # Card 1: School & Session Information
    with st.container():
        st.markdown("### 1. School & Session Information")
        col_sch, col_date, col_grp = st.columns([2, 1, 1])

        with col_sch:
            school_options = {s["id"]: f"{s['name']} ({s['school_code']}) - {s['block']}" for s in schools}
            selected_school_id = st.selectbox(
                "School Name & Code *",
                options=list(school_options.keys()),
                format_func=lambda x: school_options[x],
                key="sel_school_id"
            )
            # Find selected school details
            curr_school = next(s for s in schools if s["id"] == selected_school_id)

        with col_date:
            entry_date = st.date_input("Date of Meal Session *", value=datetime.now().date(), key="sel_entry_date")

        with col_grp:
            class_group = st.selectbox(
                "Class Group *",
                options=["Primary (Class 1-5)", "Upper Primary (Class 6-8)"],
                key="sel_class_group"
            )

        menu_title = st.text_input(
            "Meal Menu Description *",
            value="Steamed Rice, Sambhar Dal & Green Veggies",
            placeholder="e.g. Rice + Dal + Soy Sabzi, Khichdi, Roti + Chana Dal",
            key="txt_menu_name"
        )

    st.markdown("---")

    # Card 2: Attendance & Portion Prepared
    with st.container():
        st.markdown("### 2. Student Attendance & Meal Distribution")
        reg_count = curr_school["registered_primary"] if "Primary" in class_group else curr_school["registered_upper_primary"]
        
        st.markdown(f"**Enrolled Students in {class_group}:** `{reg_count}` children")

        c_att1, c_att2, c_att3 = st.columns(3)

        with c_att1:
            students_present = st.number_input(
                "Students Present Today *",
                min_value=1,
                max_value=max(500, reg_count + 50),
                value=min(reg_count, 95) if reg_count > 0 else 80,
                step=1,
                key="num_present"
            )

        with c_att2:
            meals_served = st.number_input(
                "Meals Actually Served *",
                min_value=1,
                max_value=max(500, students_present),
                value=students_present,
                step=1,
                help="Cannot exceed students present.",
                key="num_served"
            )

        with c_att3:
            # Recommend standard cooked weight based on class group (~350g primary, 450g upper primary)
            recommended_kg = round(meals_served * (0.35 if "Primary" in class_group else 0.45), 2)
            cooked_prepared_kg = st.number_input(
                "Total Cooked Food Prepared (kg) *",
                min_value=0.5,
                max_value=200.0,
                value=float(recommended_kg),
                step=0.5,
                help=f"Total weight of cooked food ready in kitchen vessels. Recommended for {meals_served} students: ~{recommended_kg} kg.",
                key="num_cooked_prep"
            )

    st.markdown("---")

    # Card 3: Food Wastage Measurement (Kitchen vs Plate)
    with st.container():
        st.markdown("### 3. Food Wastage Measurement")
        st.caption("PM POSHAN audits distinguish unserved kitchen leftovers from student plate waste.")

        col_w1, col_w2 = st.columns(2)

        with col_w1:
            st.markdown("##### 🍲 Kitchen Leftovers")
            st.caption("Food left unserved in cooking pots/degchis (production waste)")
            kitchen_leftovers_kg = st.number_input(
                "Unserved Kitchen Leftovers (kg)",
                min_value=0.0,
                max_value=float(cooked_prepared_kg),
                value=0.8,
                step=0.1,
                key="num_kitchen_leftover"
            )

        with col_w2:
            st.markdown("##### 🍽️ Student Plate Waste")
            st.caption("Food served on plates but left uneaten (consumption waste)")
            
            waste_method = st.radio(
                "Measurement Method",
                options=["Manual Measurement (weighed on scale)", "Visual Category Estimation"],
                horizontal=True,
                key="radio_waste_method"
            )

            if waste_method == "Manual Measurement (weighed on scale)":
                distributed_food = max(0.0, cooked_prepared_kg - kitchen_leftovers_kg)
                plate_waste_kg = st.number_input(
                    "Measured Plate Waste (kg)",
                    min_value=0.0,
                    max_value=float(distributed_food),
                    value=min(1.2, distributed_food),
                    step=0.1,
                    key="num_manual_plate_waste"
                )
                visual_category = None
            else:
                visual_category = st.selectbox(
                    "Visual Plate Waste Category (Quarter-waste observation)",
                    options=[
                        "No visible waste (< 2%)",
                        "Slight leftovers (~5%)",
                        "Quarter plate remaining (~25%)",
                        "Half plate remaining (~50%)",
                        "Substantial plate waste (> 75%)"
                    ],
                    index=1,
                    key="sel_visual_cat"
                )
                distributed_food = max(0.0, cooked_prepared_kg - kitchen_leftovers_kg)
                fraction = VISUAL_WASTE_CATEGORIES[visual_category]
                calculated_plate_kg = round(distributed_food * fraction, 2)
                st.info(f"📊 Estimated Plate Waste: **{calculated_plate_kg} kg** ({round(fraction*100)}% of {distributed_food:.1f} kg distributed)")
                plate_waste_kg = calculated_plate_kg

    st.markdown("---")

    # Card 4: Dynamic Ingredients Table
    with st.container():
        st.markdown("### 4. Ingredients & Rations Allocated")
        st.caption("Specify raw ingredients issued from school grain stock according to ICMR-NIN composition.")

        # Quick preset buttons
        preset_cols = st.columns([1, 1, 1, 2])
        with preset_cols[0]:
            if st.button("➕ Preset: Rice + Dal", use_container_width=True):
                mult = meals_served
                st.session_state.entry_ingredients = [
                    {"name": "Rice (Raw Milled)", "quantity": round(mult * 0.100, 2), "unit": "kg", "form": "raw"},
                    {"name": "Toor Dal (Split Red Gram)", "quantity": round(mult * 0.022, 2), "unit": "kg", "form": "raw"},
                    {"name": "Mixed Other Vegetables (Gourd/Beans/Tomato)", "quantity": round(mult * 0.050, 2), "unit": "kg", "form": "raw"},
                    {"name": "Mustard / Cooking Vegetable Oil", "quantity": round(mult * 0.005, 2), "unit": "kg", "form": "raw"}
                ]
                st.rerun()
        with preset_cols[1]:
            if st.button("➕ Preset: Khichdi + Egg", use_container_width=True):
                mult = meals_served
                st.session_state.entry_ingredients = [
                    {"name": "Rice (Raw Milled)", "quantity": round(mult * 0.090, 2), "unit": "kg", "form": "raw"},
                    {"name": "Moong Dal (Split Green Gram)", "quantity": round(mult * 0.025, 2), "unit": "kg", "form": "raw"},
                    {"name": "Green Leafy Vegetables (Spinach/Methi)", "quantity": round(mult * 0.040, 2), "unit": "kg", "form": "raw"},
                    {"name": "Mustard / Cooking Vegetable Oil", "quantity": round(mult * 0.005, 2), "unit": "kg", "form": "raw"},
                    {"name": "Whole Hen Egg (Boiled)", "quantity": float(mult), "unit": "piece", "form": "cooked"}
                ]
                st.rerun()
        with preset_cols[2]:
            if st.button("➕ Preset: Roti + Chana", use_container_width=True):
                mult = meals_served
                st.session_state.entry_ingredients = [
                    {"name": "Wheat Flour (Whole Atta)", "quantity": round(mult * 0.105, 2), "unit": "kg", "form": "raw"},
                    {"name": "Bengal Gram Whole (Kala Chana)", "quantity": round(mult * 0.025, 2), "unit": "kg", "form": "raw"},
                    {"name": "Potatoes (Raw)", "quantity": round(mult * 0.045, 2), "unit": "kg", "form": "raw"},
                    {"name": "Mustard / Cooking Vegetable Oil", "quantity": round(mult * 0.005, 2), "unit": "kg", "form": "raw"}
                ]
                st.rerun()

        # Render list of ingredients
        ing_keys = list(INGREDIENT_DATABASE.keys())
        updated_ingredients = []

        for idx, item in enumerate(st.session_state.entry_ingredients):
            row_c1, row_c2, row_c3, row_c4, row_c5 = st.columns([3, 1.5, 1.2, 1.2, 0.8])
            with row_c1:
                cur_name = item["name"] if item["name"] in ing_keys else ing_keys[0]
                name = st.selectbox(
                    f"Ingredient #{idx+1}",
                    options=ing_keys,
                    index=ing_keys.index(cur_name),
                    key=f"ing_name_{idx}"
                )
            with row_c2:
                qty = st.number_input(
                    "Quantity",
                    min_value=0.01,
                    max_value=200.0,
                    value=float(item.get("quantity", 1.0)),
                    step=0.1,
                    key=f"ing_qty_{idx}"
                )
            with row_c3:
                u_opts = ["kg", "g", "liter", "ml", "piece"]
                cur_u = item.get("unit", "kg")
                unit = st.selectbox(
                    "Unit",
                    options=u_opts,
                    index=u_opts.index(cur_u) if cur_u in u_opts else 0,
                    key=f"ing_unit_{idx}"
                )
            with row_c4:
                form_opts = ["raw", "cooked"]
                cur_f = item.get("form", "raw")
                form = st.selectbox(
                    "Form",
                    options=form_opts,
                    index=form_opts.index(cur_f) if cur_f in form_opts else 0,
                    key=f"ing_form_{idx}"
                )
            with row_c5:
                st.write("")
                st.write("")
                if st.button("🗑️", key=f"del_ing_{idx}", help="Remove ingredient"):
                    st.session_state.entry_ingredients.pop(idx)
                    st.rerun()

            updated_ingredients.append({
                "name": name,
                "quantity": qty,
                "unit": unit,
                "form": form
            })

        st.session_state.entry_ingredients = updated_ingredients

        col_add_btn, _ = st.columns([1, 4])
        with col_add_btn:
            if st.button("➕ Add Custom Ingredient", use_container_width=True):
                st.session_state.entry_ingredients.append({
                    "name": "Toor Dal (Split Red Gram)",
                    "quantity": 2.0,
                    "unit": "kg",
                    "form": "raw"
                })
                st.rerun()

    st.markdown("---")

    # Card 5: Real-time Live Calculation & Soft Computing Priority Preview
    st.markdown("### 5. Live Calculation & Soft Computing Priority Preview")
    
    validation_passed = True
    calc_error_msg = ""

    try:
        # Live calculation
        nutri_prev = calculate_meal_nutrition(
            ingredients=st.session_state.entry_ingredients,
            meals_served=meals_served,
            class_group=class_group
        )

        waste_prev = calculate_food_wastage(
            students_present=students_present,
            meals_served=meals_served,
            cooked_food_prepared_kg=cooked_prepared_kg,
            kitchen_waste_kg=kitchen_leftovers_kg,
            plate_waste_kg=plate_waste_kg,
            visual_category=visual_category
        )

        fuzzy_prev = fuzzy_engine.evaluate(
            nutrition_adequacy_pct=nutri_prev["combined_adequacy_pct"],
            food_waste_pct=waste_prev["total_waste_pct"]
        )

        # Display preview KPI cards
        kpi_c1, kpi_c2, kpi_c3, kpi_c4 = st.columns(4)

        with kpi_c1:
            st.metric(
                label="Calories / Child",
                value=f"{nutri_prev['per_serving_calories_kcal']} kcal",
                delta=f"{nutri_prev['energy_adequacy_pct']}% of {nutri_prev['target_calories_kcal']} target",
                delta_color="normal" if nutri_prev['energy_adequacy_pct'] >= 90 else "inverse"
            )

        with kpi_c2:
            st.metric(
                label="Protein / Child",
                value=f"{nutri_prev['per_serving_protein_g']} g",
                delta=f"{nutri_prev['protein_adequacy_pct']}% of {nutri_prev['target_protein_g']}g target",
                delta_color="normal" if nutri_prev['protein_adequacy_pct'] >= 90 else "inverse"
            )

        with kpi_c3:
            st.metric(
                label="Food Wastage",
                value=f"{waste_prev['total_waste_pct']}% ({waste_prev['total_waste_kg']} kg)",
                delta=f"Plate: {waste_prev['plate_waste_pct']}% | Kitchen: {waste_prev['kitchen_waste_pct']}%",
                delta_color="inverse" if waste_prev['total_waste_pct'] > 10 else "normal"
            )

        with kpi_c4:
            st.metric(
                label="Soft Computing Priority",
                value=f"{fuzzy_prev['review_priority_score']} / 100",
                delta=fuzzy_prev['priority_badge'],
                delta_color="off"
            )

        st.caption(f"🧠 **Fuzzy Reasoning:** {fuzzy_prev['priority_label']}. Active rule: *{fuzzy_prev['active_rules'][0]['condition'] if fuzzy_prev['active_rules'] else 'None'}*")

    except Exception as e:
        validation_passed = False
        calc_error_msg = str(e)
        st.error(f"⚠️ Validation Warning: {calc_error_msg}")

    st.markdown("---")

    # Card 6: Submit Session Entry
    submit_col1, submit_col2 = st.columns([2, 1])
    with submit_col1:
        st.caption("Submitting will persist the meal record and lock this session to prevent duplicates.")
    with submit_col2:
        btn_submit = st.button("🚀 Verify & Save Meal Entry", type="primary", use_container_width=True, disabled=not validation_passed)

    if btn_submit and validation_passed:
        date_str = entry_date.strftime("%Y-%m-%d")
        try:
            new_id = add_meal_entry(
                school_id=selected_school_id,
                entry_date=date_str,
                class_group=class_group,
                menu_name=menu_title,
                students_present=students_present,
                meals_served=meals_served,
                cooked_food_prepared_kg=cooked_prepared_kg,
                kitchen_waste_kg=kitchen_leftovers_kg,
                plate_waste_kg=plate_waste_kg,
                waste_method=waste_method,
                visual_category=visual_category,
                ingredients=st.session_state.entry_ingredients
            )
            st.success(f"✅ Success! Meal entry #{new_id} saved for {curr_school['name']} on {date_str}.")
            st.balloons()
        except ValueError as ve:
            st.error(f"❌ Submission Blocked: {ve}")
        except Exception as ex:
            st.error(f"❌ Database Error: {ex}")
