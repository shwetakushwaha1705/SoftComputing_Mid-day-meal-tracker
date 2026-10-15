"""
Soft Computing Fuzzy Logic Assessment & Viva Defense Lab
Visualizes membership functions, interactive simulation, active rule firing strengths,
and full mathematical explanation of Mamdani centroid defuzzification.
"""
import streamlit as st
import numpy as np
import plotly.graph_objects as go
from engines.fuzzy_engine import fuzzy_engine
from config import SOFT_COMPUTING_DISCLAIMER


def render_fuzzy_analysis_view():
    st.markdown("## 🧠 Soft Computing: Fuzzy Logic Review Priority Engine")
    st.caption("Mamdani Fuzzy Inference System (FIS) for Risk Assessment & Priority Ranking")

    # Legal / Academic Disclaimer Alert
    st.warning(f"⚠️ **ACADEMIC NOTICE:** {SOFT_COMPUTING_DISCLAIMER}")

    # Tabs for Interactive Simulator vs Theory & Defense Guide
    tab_sim, tab_curves, tab_theory = st.tabs([
        "🔬 Interactive Fuzzy Simulator",
        "📈 Membership Function Curves",
        "🎓 Viva Defense & Mathematical Theory"
    ])

    with tab_sim:
        st.markdown("### Interactive What-If Soft Computing Assessment")
        st.markdown(
            "Adjust the input parameters to evaluate how the fuzzy inference engine assesses "
            "review priority under different nutrition and wastage scenarios."
        )

        col_in1, col_in2 = st.columns(2)

        with col_in1:
            test_adequacy = st.slider(
                "🥗 Combined Nutrition Adequacy (%)",
                min_value=0.0,
                max_value=150.0,
                value=85.0,
                step=1.0,
                help="Average or minimum percentage of target calories and protein attained."
            )

        with col_in2:
            test_waste = st.slider(
                "🗑️ Total Food Wastage (%)",
                min_value=0.0,
                max_value=50.0,
                value=12.0,
                step=0.5,
                help="Sum of unserved kitchen leftovers and student plate waste divided by total food cooked."
            )

        # Run Fuzzy Engine
        res = fuzzy_engine.evaluate(test_adequacy, test_waste)

        # Display Result Gauge / Score
        res_col1, res_col2 = st.columns([1.2, 2])

        with res_col1:
            st.markdown("#### 🎯 Defuzzified Score")
            
            # Plotly Gauge Chart for Defuzzified Priority
            fig_gauge = go.Figure(go.Indicator(
                mode="gauge+number",
                value=res["review_priority_score"],
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': f"Priority: {res['priority_badge']}", 'font': {'size': 20}},
                gauge={
                    'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "darkblue"},
                    'bar': {'color': res['color'], 'thickness': 0.3},
                    'bgcolor': "white",
                    'borderwidth': 2,
                    'bordercolor': "gray",
                    'steps': [
                        {'range': [0, 35], 'color': 'rgba(56, 161, 105, 0.2)'},   # Green
                        {'range': [35, 60], 'color': 'rgba(221, 107, 32, 0.2)'},  # Orange
                        {'range': [60, 100], 'color': 'rgba(229, 62, 62, 0.2)'}   # Red
                    ],
                    'threshold': {
                        'line': {'color': "black", 'width': 3},
                        'thickness': 0.75,
                        'value': res["review_priority_score"]
                    }
                }
            ))
            fig_gauge.update_layout(height=260, margin=dict(l=20, r=20, t=40, b=20))
            st.plotly_chart(fig_gauge, use_container_width=True)

            st.markdown(f"**Classification:** `{res['priority_label']}`")

        with res_col2:
            st.markdown("#### 🔍 Input Membership Degrees $\\mu(x)$")
            
            m_adeq = res["membership_degrees"]["adequacy"]
            m_waste = res["membership_degrees"]["waste"]

            col_m1, col_m2 = st.columns(2)
            with col_m1:
                st.markdown("**Nutrition Adequacy Membership:**")
                st.write(f"- Low $\\mu_{{low}}({test_adequacy}\\%)$: **{m_adeq['Low']}**")
                st.write(f"- Medium $\\mu_{{med}}({test_adequacy}\\%)$: **{m_adeq['Medium']}**")
                st.write(f"- High $\\mu_{{high}}({test_adequacy}\\%)$: **{m_adeq['High']}**")

            with col_m2:
                st.markdown("**Food Wastage Membership:**")
                st.write(f"- Low $\\mu_{{low}}({test_waste}\\%)$: **{m_waste['Low']}**")
                st.write(f"- Medium $\\mu_{{med}}({test_waste}\\%)$: **{m_waste['Medium']}**")
                st.write(f"- High $\\mu_{{high}}({test_waste}\\%)$: **{m_waste['High']}**")

            st.markdown("---")
            st.markdown("#### ⚡ Active Rules & Firing Strengths (Mamdani Min)")
            if res["active_rules"]:
                for rule in res["active_rules"]:
                    st.markdown(
                        f"- **{rule['rule_id']}** (Firing Strength $\\alpha = {rule['firing_strength']:.3f}$): "
                        f"`{rule['condition']}`<br>"
                        f"&nbsp;&nbsp;&nbsp;&nbsp;*Rationale: {rule['rationale']}*",
                        unsafe_allow_html=True
                    )
            else:
                st.info("No active rules with firing strength > 0.001.")

        # Complete Knowledge Base Matrix
        with st.expander("📖 View All 9 IF-THEN Rules in Knowledge Base"):
            all_rules_data = []
            for r in res["all_rules"]:
                active_str = "🔥 ACTIVE" if r["firing_strength"] > 0.001 else "⚪ Inactive"
                all_rules_data.append({
                    "Rule ID": r["rule_id"],
                    "Status": active_str,
                    "Firing Strength (α)": f"{r['firing_strength']:.3f}",
                    "Rule Condition": r["condition"],
                    "Consequent Priority": r["consequent"],
                    "Expert Rationale": r["rationale"]
                })
            st.table(all_rules_data)

    with tab_curves:
        st.markdown("### Membership Functions (Universe of Discourse)")
        st.caption("Plots showing triangular and trapezoidal fuzzy sets with current test input lines")

        # 1. Nutrition Adequacy Plot
        fig_adeq = go.Figure()
        fig_adeq.add_trace(go.Scatter(x=fuzzy_engine.x_adequacy, y=fuzzy_engine.adequacy_low, mode='lines', name='Low (<75%)', line=dict(color='red', width=2)))
        fig_adeq.add_trace(go.Scatter(x=fuzzy_engine.x_adequacy, y=fuzzy_engine.adequacy_med, mode='lines', name='Medium (60-110%)', line=dict(color='orange', width=2)))
        fig_adeq.add_trace(go.Scatter(x=fuzzy_engine.x_adequacy, y=fuzzy_engine.adequacy_high, mode='lines', name='High (>95%)', line=dict(color='green', width=2)))
        # Vertical marker for current input
        fig_adeq.add_vline(x=test_adequacy, line_dash="dash", line_color="blue", annotation_text=f"Input: {test_adequacy}%")
        fig_adeq.update_layout(
            title="Input 1: Nutrition Adequacy Membership Functions",
            xaxis_title="Nutrition Adequacy Percentage (%)",
            yaxis_title="Membership Degree μ",
            height=300,
            margin=dict(l=20, r=20, t=40, b=20)
        )
        st.plotly_chart(fig_adeq, use_container_width=True)

        # 2. Food Wastage Plot
        fig_w = go.Figure()
        fig_w.add_trace(go.Scatter(x=fuzzy_engine.x_waste, y=fuzzy_engine.waste_low, mode='lines', name='Low (<12%)', line=dict(color='green', width=2)))
        fig_w.add_trace(go.Scatter(x=fuzzy_engine.x_waste, y=fuzzy_engine.waste_med, mode='lines', name='Medium (8-28%)', line=dict(color='orange', width=2)))
        fig_w.add_trace(go.Scatter(x=fuzzy_engine.x_waste, y=fuzzy_engine.waste_high, mode='lines', name='High (>22%)', line=dict(color='red', width=2)))
        # Vertical marker for current input
        fig_w.add_vline(x=test_waste, line_dash="dash", line_color="blue", annotation_text=f"Input: {test_waste}%")
        fig_w.update_layout(
            title="Input 2: Food Wastage Percentage Membership Functions",
            xaxis_title="Food Wastage (%)",
            yaxis_title="Membership Degree μ",
            height=300,
            margin=dict(l=20, r=20, t=40, b=20)
        )
        st.plotly_chart(fig_w, use_container_width=True)

        # 3. Output Review Priority Plot
        fig_p = go.Figure()
        fig_p.add_trace(go.Scatter(x=fuzzy_engine.x_priority, y=fuzzy_engine.priority_low, mode='lines', name='Low Priority (0-40)', line=dict(color='green', width=2)))
        fig_p.add_trace(go.Scatter(x=fuzzy_engine.x_priority, y=fuzzy_engine.priority_med, mode='lines', name='Medium Priority (25-75)', line=dict(color='orange', width=2)))
        fig_p.add_trace(go.Scatter(x=fuzzy_engine.x_priority, y=fuzzy_engine.priority_high, mode='lines', name='High Priority (60-100)', line=dict(color='red', width=2)))
        fig_p.add_vline(x=res["review_priority_score"], line_dash="dash", line_color="purple", annotation_text=f"Defuzzified: {res['review_priority_score']}")
        fig_p.update_layout(
            title="Output Consequent: Review Priority Score Membership Functions",
            xaxis_title="Review Priority Score (0-100)",
            yaxis_title="Membership Degree μ",
            height=300,
            margin=dict(l=20, r=20, t=40, b=20)
        )
        st.plotly_chart(fig_p, use_container_width=True)

    with tab_theory:
        st.markdown("### 🎓 Soft Computing Viva Defense Notes")
        st.markdown("""
        #### 1. Why Fuzzy Logic for PM POSHAN School Meals?
        - **Handling Ambiguity & Imprecision:** School meal measurement involves real-world imprecision (e.g., estimating plate waste visually, minor variation in vegetable moisture, fluctuating student appetites).
        - **Gradual Transitions vs. Rigid Binary Thresholds:** If the target calorie standard is 450 kcal, an entry of 448 kcal in crisp logic fails as 'non-compliant' just as severely as 200 kcal. Fuzzy logic provides smooth graded membership.
        - **Multi-Objective Trade-off:** High nutrition can sometimes be accompanied by high waste (over-rationing), or clean plates might mask under-rationing. Fuzzy rules synthesize these two non-linear variables into an actionable priority score.

        #### 2. Fuzzy Inference Architecture (Mamdani)
        1. **Fuzzification:**
           Convert crisp inputs $x_1$ (Adequacy %) and $x_2$ (Waste %) into linguistic membership values using triangular ($\text{trimf}$) and trapezoidal ($\text{trapmf}$) functions:
           $$\mu_A(x) \in [0, 1]$$
        2. **Rule Evaluation (Fuzzy Operator AND):**
           For rule $k$: IF $A_k$ AND $B_k$ THEN $C_k$, the firing strength $\alpha_k$ uses the Mamdani minimum t-norm:
           $$\alpha_k = \min(\mu_{A_k}(x_1), \mu_{B_k}(x_2))$$
        3. **Implication:**
           Each rule's consequent fuzzy set is clipped by its firing strength $\alpha_k$:
           $$\mu_{C'_k}(z) = \min(\alpha_k, \mu_{C_k}(z))$$
        4. **Aggregation:**
           Max s-norm aggregates all clipped rule outputs:
           $$\mu_{Agg}(z) = \max_{k=1}^9 \mu_{C'_k}(z)$$
        5. **Defuzzification (Centroid / Center of Gravity):**
           Calculates the center of mass of the aggregated area:
           $$Z^* = \frac{\sum z \cdot \mu_{Agg}(z)}{\sum \mu_{Agg}(z)}$$
        """)
