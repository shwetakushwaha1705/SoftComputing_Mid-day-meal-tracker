"""
Reference Norms and Transparent ICMR-NIN Ingredient Composition View
"""
import streamlit as st
import pandas as pd
from engines.nutrition_engine import INGREDIENT_DATABASE
from database.db import get_reference_norms, update_reference_norm


def render_reference_norms_view():
    st.markdown("## 📋 PM POSHAN Reference Norms & ICMR-NIN Nutrition Database")
    st.markdown(
        "PM POSHAN guidelines establish statutory nutritional norms per child per school day. "
        "This module ensures full transparency by exposing both official targets and the "
        "verified biochemical food composition database (ICMR-NIN IFCT)."
    )

    # Section 1: Official PM POSHAN Reference Norms Editor
    st.markdown("### 1. PM POSHAN Nutritional Reference Norms (Configurable)")
    st.info(
        "💡 **Government Benchmark:** Primary children (Classes I–V) require a minimum of **450 kcal** "
        "and **12g protein**, while Upper Primary children (Classes VI–VIII) require a minimum of "
        "**700 kcal** and **20g protein** per midday meal serving."
    )

    current_norms = get_reference_norms()

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 🎒 Primary (Class 1-5)")
        p_cals = current_norms.get("Primary (Class 1-5)", {}).get("calories_kcal", 450.0)
        p_prot = current_norms.get("Primary (Class 1-5)", {}).get("protein_g", 12.0)
        
        new_p_cals = st.number_input(
            "Primary Target Calories (kcal)",
            min_value=300.0, max_value=800.0, value=float(p_cals), step=10.0, key="norm_p_cals"
        )
        new_p_prot = st.number_input(
            "Primary Target Protein (grams)",
            min_value=5.0, max_value=30.0, value=float(p_prot), step=1.0, key="norm_p_prot"
        )
        if st.button("Save Primary Norms", key="btn_save_p"):
            update_reference_norm("Primary (Class 1-5)", new_p_cals, new_p_prot)
            st.success("Updated Primary reference norms successfully!")
            st.rerun()

    with col2:
        st.markdown("#### 🎓 Upper Primary (Class 6-8)")
        up_cals = current_norms.get("Upper Primary (Class 6-8)", {}).get("calories_kcal", 700.0)
        up_prot = current_norms.get("Upper Primary (Class 6-8)", {}).get("protein_g", 20.0)

        new_up_cals = st.number_input(
            "Upper Primary Target Calories (kcal)",
            min_value=400.0, max_value=1200.0, value=float(up_cals), step=10.0, key="norm_up_cals"
        )
        new_up_prot = st.number_input(
            "Upper Primary Target Protein (grams)",
            min_value=10.0, max_value=40.0, value=float(up_prot), step=1.0, key="norm_up_prot"
        )
        if st.button("Save Upper Primary Norms", key="btn_save_up"):
            update_reference_norm("Upper Primary (Class 6-8)", new_up_cals, new_up_prot)
            st.success("Updated Upper Primary reference norms successfully!")
            st.rerun()

    st.markdown("---")

    # Section 2: Verified ICMR-NIN Ingredient Table
    st.markdown("### 2. Transparent Food Composition Table (ICMR - NIN IFCT)")
    st.markdown(
        "Nutrient values are derived directly from the **Indian Food Composition Tables (IFCT)** "
        "published by the National Institute of Nutrition (ICMR-NIN), Hyderabad. "
        "Values represent edible portions on a **raw dry basis**, with standardized cooked yield conversion factors."
    )

    data_rows = []
    for ing_name, details in INGREDIENT_DATABASE.items():
        data_rows.append({
            "Ingredient": ing_name,
            "Category": details["category"],
            "Energy (kcal/100g)": details["calories_per_100g"],
            "Protein (g/100g)": details["protein_per_100g"],
            "Cooked Yield Multiplier": f"{details.get('cooked_yield_factor', 1.0)}x",
            "Data Source & Code": details["source"]
        })

    df_ing = pd.DataFrame(data_rows)
    st.dataframe(df_ing, use_container_width=True, hide_index=True)

    # Section 3: Scientific Accounting Assumptions
    st.markdown("### 3. Scientific Assumptions & Accounting Methodology")
    with st.expander("🔍 View Technical Documentation on Raw vs. Cooked Quantities"):
        st.markdown("""
        **1. Institutional Dry Weight Standard:**
        In PM POSHAN institutional catering, grain allocations (e.g., 100g raw rice for primary, 150g for upper primary) 
        and pulses are measured dry in the store room prior to washing and boiling. Dry raw weight provides 
        the invariant biochemical baseline for calorie and protein computation.
        
        **2. Cooked Hydration & Yield Factors:**
        - **Rice:** Expands ~2.7x to 2.8x due to water absorption during boiling. 100g raw rice produces ~280g cooked rice.
        - **Dal (Pulses):** Absorbs 3x to 3.2x water depending on consistency.
        - **Wheat (Atta to Roti):** Yields ~1.4x weight due to kneaded moisture.
        
        **3. Food Wastage Segregation:**
        - **Kitchen Leftovers:** Over-prepared food remaining unserved in cooking vessels. Indicates forecasting error in kitchen stock management.
        - **Plate Waste:** Cooked food served onto student plates but rejected or discarded. Indicates child taste preferences, portion excess, or meal quality issues.
        """)
