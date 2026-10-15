"""
Reports, Aggregations, and CSV Export View for PM POSHAN Tracker
"""
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

from database.db import get_schools, get_meal_entries, get_reporting_compliance, delete_meal_entry
from database.seed_data import seed_database


def render_reports_view():
    st.markdown("## 📑 Mid-Day Meal Reports & Data Exports")
    st.caption("School-wise and Block-wise Aggregations, Audit Trails, and CSV Downloads")

    schools = get_schools()
    if not schools:
        st.warning("No data found in database.")
        return

    # Section 1: Filters
    with st.container():
        f1, f2, f3 = st.columns(3)
        today = datetime.now().date()
        two_weeks_ago = today - timedelta(days=14)

        with f1:
            date_filter = st.date_input("Audit Period", value=(two_weeks_ago, today), key="rep_date_filter")
            if isinstance(date_filter, tuple) and len(date_filter) == 2:
                s_str = date_filter[0].strftime("%Y-%m-%d")
                e_str = date_filter[1].strftime("%Y-%m-%d")
            else:
                s_str = two_weeks_ago.strftime("%Y-%m-%d")
                e_str = today.strftime("%Y-%m-%d")

        with f2:
            blocks = sorted(list(set(s["block"] for s in schools)))
            sel_block = st.selectbox("Block Filter", options=["All Blocks"] + blocks, key="rep_block_filter")

        with f3:
            badge_filter = st.selectbox("Priority Status Filter", options=["All", "HIGH", "MEDIUM", "LOW"], key="rep_badge_filter")

    # Fetch records
    entries = get_meal_entries(
        start_date=s_str,
        end_date=e_str,
        block=sel_block,
        priority_badge=badge_filter
    )

    tab_detailed, tab_block_agg, tab_admin = st.tabs([
        "📋 Daily Meal Log Register",
        "🏢 Block & School Summary",
        "⚙️ Synthetic Data & Admin"
    ])

    with tab_detailed:
        st.markdown(f"### Meal Session Records ({len(entries)} entries found)")
        
        if entries:
            df = pd.DataFrame(entries)
            display_cols = [
                "entry_date", "school_name", "block", "class_group", "menu_name",
                "students_present", "meals_served", "cooked_food_prepared_kg",
                "per_serving_calories", "per_serving_protein",
                "energy_adequacy_pct", "protein_adequacy_pct",
                "total_waste_kg", "total_waste_pct",
                "fuzzy_priority_score", "fuzzy_badge"
            ]
            
            df_display = df[display_cols].rename(columns={
                "entry_date": "Date",
                "school_name": "School",
                "block": "Block",
                "class_group": "Class Group",
                "menu_name": "Menu",
                "students_present": "Present",
                "meals_served": "Served",
                "cooked_food_prepared_kg": "Cooked (kg)",
                "per_serving_calories": "Calories/Child",
                "per_serving_protein": "Protein/Child (g)",
                "energy_adequacy_pct": "Energy Adeq %",
                "protein_adequacy_pct": "Protein Adeq %",
                "total_waste_kg": "Waste (kg)",
                "total_waste_pct": "Waste %",
                "fuzzy_priority_score": "Fuzzy Score",
                "fuzzy_badge": "Priority"
            })

            st.dataframe(df_display, use_container_width=True, hide_index=True)

            # CSV Download
            csv_data = df_display.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Export Filtered Records as CSV",
                data=csv_data,
                file_name=f"pm_poshan_meal_records_{s_str}_to_{e_str}.csv",
                mime="text/csv",
                type="primary"
            )
        else:
            st.info("No meal entries match the selected filters.")

    with tab_block_agg:
        st.markdown("### Aggregated Block & School Summary")
        if entries:
            df = pd.DataFrame(entries)

            # Block Aggregation
            st.markdown("#### 1. Block-Level Performance Metrics")
            block_summary = df.groupby("block").agg({
                "meals_served": "sum",
                "cooked_food_prepared_kg": "sum",
                "total_waste_kg": "sum",
                "energy_adequacy_pct": "mean",
                "protein_adequacy_pct": "mean",
                "fuzzy_priority_score": "mean"
            }).reset_index()

            block_summary["waste_pct_overall"] = (block_summary["total_waste_kg"] / block_summary["cooked_food_prepared_kg"]) * 100.0
            block_summary = block_summary.round(2)

            st.dataframe(
                block_summary.rename(columns={
                    "block": "Block",
                    "meals_served": "Total Meals Served",
                    "cooked_food_prepared_kg": "Total Prepared (kg)",
                    "total_waste_kg": "Total Waste (kg)",
                    "energy_adequacy_pct": "Mean Energy Adeq %",
                    "protein_adequacy_pct": "Mean Protein Adeq %",
                    "fuzzy_priority_score": "Mean Priority Score",
                    "waste_pct_overall": "Overall Waste %"
                }),
                use_container_width=True,
                hide_index=True
            )

            # School Aggregation
            st.markdown("#### 2. School-Level Performance Metrics")
            school_summary = df.groupby(["school_name", "block"]).agg({
                "meals_served": "sum",
                "cooked_food_prepared_kg": "sum",
                "total_waste_kg": "sum",
                "energy_adequacy_pct": "mean",
                "protein_adequacy_pct": "mean",
                "fuzzy_priority_score": "mean"
            }).reset_index()

            school_summary["waste_pct_overall"] = (school_summary["total_waste_kg"] / school_summary["cooked_food_prepared_kg"]) * 100.0
            school_summary = school_summary.round(2)

            st.dataframe(
                school_summary.rename(columns={
                    "school_name": "School Name",
                    "block": "Block",
                    "meals_served": "Meals Served",
                    "cooked_food_prepared_kg": "Cooked (kg)",
                    "total_waste_kg": "Waste (kg)",
                    "energy_adequacy_pct": "Avg Energy %",
                    "protein_adequacy_pct": "Avg Protein %",
                    "fuzzy_priority_score": "Avg Priority",
                    "waste_pct_overall": "Waste %"
                }),
                use_container_width=True,
                hide_index=True
            )

            # Export Summary CSV
            summary_csv = school_summary.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Export School Summary as CSV",
                data=summary_csv,
                file_name=f"pm_poshan_school_summary_{s_str}_to_{e_str}.csv",
                mime="text/csv"
            )
        else:
            st.info("No data available to aggregate.")

    with tab_admin:
        st.markdown("### Synthetic Demonstration Data Management")
        st.info(
            "💡 **Notice:** To allow seamless demonstration for university assessors, "
            "you can re-seed the SQLite database with 12 days of realistic synthetic simulation "
            "data across multiple school profiles (compliant schools, high-waste schools, "
            "nutrition-deficit schools, and schools with missing reports)."
        )

        col_seed1, col_seed2 = st.columns([1, 2])
        with col_seed1:
            if st.button("🔄 Reset & Re-Seed Synthetic Demo Data", type="secondary"):
                with st.spinner("Generating synthetic data..."):
                    count = seed_database(days_back=12, clear_existing=True)
                st.success(f"Database successfully re-seeded with {count} synthetic meal records across 6 schools!")
                st.rerun()

        with col_seed2:
            st.caption(
                "All synthetic data is generated algorithmically according to PM POSHAN nutrition standards "
                "and ICMR-NIN food composition tables. No real student personal identifiable information (PII) is involved."
            )
