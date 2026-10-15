"""
Executive Monitoring Dashboard for PM POSHAN Tracker
Provides school & block-wise KPI cards, Plotly interactive trend charts,
multi-dimensional filtering, and clear distinction between compliant and missing reports.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

from database.db import get_schools, get_meal_entries, get_reporting_compliance


def render_dashboard_view():
    st.markdown("## 📊 PM POSHAN Monitoring & Wastage Dashboard")
    st.caption("State & District Education Monitoring System — Mid-Day Meal Nutrition & Wastage Analytics")

    schools = get_schools()
    if not schools:
        st.warning("No data found in the database. Please seed the database with synthetic data.")
        return

    # 1. Dashboard Filters Bar
    with st.expander("🔍 Filter Dashboard Data", expanded=True):
        f_col1, f_col2, f_col3, f_col4 = st.columns(4)

        # Dates range defaults
        today = datetime.now().date()
        two_weeks_ago = today - timedelta(days=14)

        with f_col1:
            date_range = st.date_input(
                "Date Period",
                value=(two_weeks_ago, today),
                key="dash_date_range"
            )
            if isinstance(date_range, tuple) and len(date_range) == 2:
                start_date_str = date_range[0].strftime("%Y-%m-%d")
                end_date_str = date_range[1].strftime("%Y-%m-%d")
            else:
                start_date_str = two_weeks_ago.strftime("%Y-%m-%d")
                end_date_str = today.strftime("%Y-%m-%d")

        with f_col2:
            blocks = sorted(list(set(s["block"] for s in schools)))
            sel_block = st.selectbox("Block", options=["All Blocks"] + blocks, key="dash_block")

        with f_col3:
            filtered_schools = schools if sel_block == "All Blocks" else [s for s in schools if s["block"] == sel_block]
            school_options = {"All Schools": None}
            for s in filtered_schools:
                school_options[f"{s['name']} ({s['school_code']})"] = s["id"]
            sel_school_label = st.selectbox("School", options=list(school_options.keys()), key="dash_school")
            sel_school_id = school_options[sel_school_label]

        with f_col4:
            sel_class_grp = st.selectbox(
                "Class Group",
                options=["All Classes", "Primary (Class 1-5)", "Upper Primary (Class 6-8)"],
                key="dash_class"
            )

    # 2. Query Data from Database
    entries = get_meal_entries(
        start_date=start_date_str,
        end_date=end_date_str,
        school_id=sel_school_id,
        block=sel_block,
        class_group=sel_class_grp
    )

    # 3. Fetch Reporting Compliance (Detect Missing Reports)
    compliance_data = get_reporting_compliance(
        start_date=start_date_str,
        end_date=end_date_str,
        block=sel_block
    )

    # 4. Top KPI Cards
    st.markdown("### Key Monitoring Indicators")
    kpi_row1 = st.columns(4)
    kpi_row2 = st.columns(4)

    total_schools_monitored = len(filtered_schools)
    total_meals_served = sum(e["meals_served"] for e in entries) if entries else 0
    total_food_cooked_kg = sum(e["cooked_food_prepared_kg"] for e in entries) if entries else 0.0
    total_waste_kg = sum(e["total_waste_kg"] for e in entries) if entries else 0.0

    avg_energy_adeq = round(sum(e["energy_adequacy_pct"] for e in entries) / len(entries), 1) if entries else 0.0
    avg_protein_adeq = round(sum(e["protein_adequacy_pct"] for e in entries) / len(entries), 1) if entries else 0.0
    avg_waste_pct = round((total_waste_kg / max(1.0, total_food_cooked_kg)) * 100.0, 1) if entries else 0.0
    high_priority_incidents = sum(1 for e in entries if e["fuzzy_badge"] == "HIGH")

    with kpi_row1[0]:
        st.metric(
            label="Schools Monitored",
            value=f"{total_schools_monitored}",
            delta=f"{compliance_data['overall_compliance_pct']}% Reporting Compliance"
        )
    with kpi_row1[1]:
        st.metric(
            label="Total Meals Served",
            value=f"{total_meals_served:,}",
            delta=f"{total_food_cooked_kg:.1f} kg Prepared"
        )
    with kpi_row1[2]:
        st.metric(
            label="Energy Adequacy",
            value=f"{avg_energy_adeq}%",
            delta=f"{round(avg_energy_adeq - 100.0, 1)}% vs PM POSHAN Norm",
            delta_color="normal" if avg_energy_adeq >= 90 else "inverse"
        )
    with kpi_row1[3]:
        st.metric(
            label="Protein Adequacy",
            value=f"{avg_protein_adeq}%",
            delta=f"{round(avg_protein_adeq - 100.0, 1)}% vs PM POSHAN Norm",
            delta_color="normal" if avg_protein_adeq >= 90 else "inverse"
        )

    with kpi_row2[0]:
        st.metric(
            label="Estimated Food Waste",
            value=f"{avg_waste_pct}%",
            delta=f"{total_waste_kg:.1f} kg Total Waste",
            delta_color="inverse" if avg_waste_pct > 10 else "normal"
        )
    with kpi_row2[1]:
        # Kitchen waste vs plate waste split
        total_kitchen_kg = sum(e["kitchen_waste_kg"] for e in entries) if entries else 0.0
        total_plate_kg = sum(e["plate_waste_kg"] for e in entries) if entries else 0.0
        st.metric(
            label="Waste Breakdown (Kg)",
            value=f"Pot: {total_kitchen_kg:.1f} kg",
            delta=f"Plate: {total_plate_kg:.1f} kg",
            delta_color="off"
        )
    with kpi_row2[2]:
        st.metric(
            label="Fuzzy High-Priority Alerts",
            value=f"{high_priority_incidents}",
            delta="Review required" if high_priority_incidents > 0 else "All compliant",
            delta_color="inverse" if high_priority_incidents > 0 else "normal"
        )
    with kpi_row2[3]:
        missing_count = compliance_data["total_expected_reports"] - compliance_data["total_received_reports"]
        st.metric(
            label="Missing School Reports",
            value=f"{max(0, missing_count)}",
            delta="Not treated as compliant" if missing_count > 0 else "100% on time",
            delta_color="inverse" if missing_count > 0 else "normal"
        )

    # 5. Missing Reports vs Compliance Callout
    if compliance_data["total_received_reports"] < compliance_data["total_expected_reports"]:
        st.error(
            f"⚠️ **REPORTING INTEGRITY NOTICE:** {missing_count} expected school daily meal reports are missing in this period. "
            "Under PM POSHAN guidelines, **missing reports are never treated as zero waste or automatic compliance**. "
            "See the compliance breakdown table below for schools requiring physical verification."
        )

    st.markdown("---")

    if not entries:
        st.info("No meal records found for the selected filter combination.")
        return

    df_entries = pd.DataFrame(entries)

    # 6. Interactive Plotly Charts
    chart_c1, chart_c2 = st.columns(2)

    with chart_c1:
        st.markdown("#### 📈 Nutrition Adequacy Trends")
        # Aggregate daily average
        df_daily = df_entries.groupby("entry_date").agg({
            "energy_adequacy_pct": "mean",
            "protein_adequacy_pct": "mean",
            "combined_adequacy_pct": "mean"
        }).reset_index().sort_values("entry_date")

        fig_nutri = go.Figure()
        fig_nutri.add_trace(go.Scatter(
            x=df_daily["entry_date"], y=df_daily["energy_adequacy_pct"],
            mode="lines+markers", name="Energy Adequacy %", line=dict(color="#DD6B20", width=2.5)
        ))
        fig_nutri.add_trace(go.Scatter(
            x=df_daily["entry_date"], y=df_daily["protein_adequacy_pct"],
            mode="lines+markers", name="Protein Adequacy %", line=dict(color="#3182CE", width=2.5)
        ))
        # Benchmark line at 100%
        fig_nutri.add_hline(y=100.0, line_dash="dash", line_color="green", annotation_text="PM POSHAN 100% Target")
        fig_nutri.update_layout(
            yaxis_title="Target Attainment (%)",
            xaxis_title="Date",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            height=340,
            margin=dict(l=20, r=20, t=30, b=20)
        )
        st.plotly_chart(fig_nutri, use_container_width=True)

    with chart_c2:
        st.markdown("#### 🗑️ Food Wastage Composition Trends")
        df_waste_daily = df_entries.groupby("entry_date").agg({
            "kitchen_waste_kg": "sum",
            "plate_waste_kg": "sum",
            "total_waste_pct": "mean"
        }).reset_index().sort_values("entry_date")

        fig_waste = go.Figure()
        fig_waste.add_trace(go.Bar(
            x=df_waste_daily["entry_date"], y=df_waste_daily["kitchen_waste_kg"],
            name="Kitchen Leftovers (kg)", marker_color="#E53E3E"
        ))
        fig_waste.add_trace(go.Bar(
            x=df_waste_daily["entry_date"], y=df_waste_daily["plate_waste_kg"],
            name="Student Plate Waste (kg)", marker_color="#ED8936"
        ))
        fig_waste.update_layout(
            barmode="stack",
            yaxis_title="Waste Quantity (kg)",
            xaxis_title="Date",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            height=340,
            margin=dict(l=20, r=20, t=30, b=20)
        )
        st.plotly_chart(fig_waste, use_container_width=True)

    chart_c3, chart_c4 = st.columns(2)

    with chart_c3:
        st.markdown("#### 🏫 School Risk Matrix (Nutrition vs Wastage)")
        fig_scatter = px.scatter(
            df_entries,
            x="combined_adequacy_pct",
            y="total_waste_pct",
            color="fuzzy_badge",
            color_discrete_map={"LOW": "#38A169", "MEDIUM": "#DD6B20", "HIGH": "#E53E3E"},
            size="meals_served",
            hover_name="school_name",
            hover_data=["entry_date", "menu_name", "fuzzy_priority_score"],
            labels={
                "combined_adequacy_pct": "Combined Nutrition Adequacy (%)",
                "total_waste_pct": "Total Food Waste (%)",
                "fuzzy_badge": "Soft Computing Priority"
            }
        )
        # Add target quadrant lines
        fig_scatter.add_vline(x=100.0, line_dash="dot", line_color="gray", annotation_text="100% Target")
        fig_scatter.add_hline(y=10.0, line_dash="dot", line_color="gray", annotation_text="10% Waste Limit")
        fig_scatter.update_layout(height=340, margin=dict(l=20, r=20, t=30, b=20))
        st.plotly_chart(fig_scatter, use_container_width=True)

    with chart_c4:
        st.markdown("#### 🏢 Block-wise Aggregation")
        df_block = df_entries.groupby("block").agg({
            "meals_served": "sum",
            "combined_adequacy_pct": "mean",
            "total_waste_pct": "mean",
            "fuzzy_priority_score": "mean"
        }).reset_index()

        fig_block = go.Figure()
        fig_block.add_trace(go.Bar(
            x=df_block["block"], y=df_block["combined_adequacy_pct"],
            name="Avg Nutrition Adequacy %", marker_color="#3182CE"
        ))
        fig_block.add_trace(go.Bar(
            x=df_block["block"], y=df_block["total_waste_pct"],
            name="Avg Wastage %", marker_color="#E53E3E"
        ))
        fig_block.update_layout(
            barmode="group",
            yaxis_title="Percentage (%)",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            height=340,
            margin=dict(l=20, r=20, t=30, b=20)
        )
        st.plotly_chart(fig_block, use_container_width=True)

    st.markdown("---")

    # 7. Reporting Compliance & Missing Records Ledger
    st.markdown("### 📋 School-Level Compliance & Missing Reports Roster")
    st.caption("Explicitly highlights non-reporting schools to avoid false assumptions of compliance.")

    comp_rows = []
    for s_stat in compliance_data["school_stats"]:
        status_tag = "✅ Fully Compliant" if s_stat["missing_reports_count"] == 0 else f"⚠️ Missing {s_stat['missing_reports_count']} Days"
        comp_rows.append({
            "School Code": s_stat["school_code"],
            "School Name": s_stat["name"],
            "Block": s_stat["block"],
            "Expected Reports": s_stat["expected_reports"],
            "Received Reports": s_stat["received_reports"],
            "Reporting Compliance (%)": f"{s_stat['compliance_pct']}%",
            "Avg Nutrition Adequacy": f"{s_stat['avg_adequacy_pct']}%" if s_stat['avg_adequacy_pct'] is not None else "No Data",
            "Avg Food Waste": f"{s_stat['avg_waste_pct']}%" if s_stat['avg_waste_pct'] is not None else "No Data",
            "High-Priority Alerts": s_stat["high_priority_count"],
            "Reporting Status": status_tag,
            "Missing Dates": ", ".join(s_stat["missing_dates"][:3]) + ("..." if len(s_stat["missing_dates"]) > 3 else "") if s_stat["missing_dates"] else "None"
        })

    df_comp = pd.DataFrame(comp_rows)
    st.dataframe(df_comp, use_container_width=True, hide_index=True)
