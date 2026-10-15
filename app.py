"""
Mid-Day Meal Nutrition + Wastage Tracker (PM POSHAN)
College Capstone & Soft Computing Demonstration Application.

Main Streamlit Application Entrypoint.
"""
import streamlit as st
from pathlib import Path
from database.db import init_db, get_schools
from database.seed_data import seed_database
from views.dashboard import render_dashboard_view
from views.daily_entry import render_daily_entry_view
from views.fuzzy_analysis import render_fuzzy_analysis_view
from views.reports import render_reports_view
from views.reference_norms import render_reference_norms_view
from config import DATABASE_PATH

# 1. Page Configuration
st.set_page_config(
    page_title="PM POSHAN - Nutrition & Wastage Tracker",
    page_icon="🍲",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Custom CSS for Clean, Professional, Mobile-First Government/Institutional UI
st.markdown("""
<style>
    /* Main container adjustments */
    .main .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2.5rem;
        padding-left: 2rem;
        padding-right: 2rem;
    }
    
    /* Brand Header Banner */
    .brand-header {
        background: linear-gradient(135deg, #1A365D 0%, #2B6CB0 100%);
        color: white;
        padding: 1.2rem 1.6rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        border-left: 6px solid #ED8936; /* Saffron accent */
    }
    .brand-header h1 {
        color: #FFFFFF;
        font-size: 1.8rem;
        font-weight: 700;
        margin: 0;
        letter-spacing: -0.5px;
    }
    .brand-header p {
        color: #E2E8F0;
        font-size: 0.95rem;
        margin: 0.3rem 0 0 0;
    }

    /* Metric cards styling */
    [data-testid="stMetric"] {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        padding: 0.8rem 1rem;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05);
    }
    [data-testid="stMetricLabel"] {
        font-size: 0.85rem !important;
        color: #4A5568 !important;
        font-weight: 600 !important;
    }
    [data-testid="stMetricValue"] {
        font-size: 1.5rem !important;
        font-weight: 700 !important;
        color: #1A202C !important;
    }

    /* Badges & Pills */
    .badge-high {
        background-color: #FED7D7;
        color: #C53030;
        padding: 0.2rem 0.6rem;
        border-radius: 9999px;
        font-weight: bold;
        font-size: 0.8rem;
    }
    .badge-med {
        background-color: #FEEBC8;
        color: #C05621;
        padding: 0.2rem 0.6rem;
        border-radius: 9999px;
        font-weight: bold;
        font-size: 0.8rem;
    }
    .badge-low {
        background-color: #C6F6D5;
        color: #22543D;
        padding: 0.2rem 0.6rem;
        border-radius: 9999px;
        font-weight: bold;
        font-size: 0.8rem;
    }

    /* Mobile responsive optimization */
    @media (max-width: 768px) {
        .main .block-container {
            padding-left: 0.8rem;
            padding-right: 0.8rem;
        }
        .brand-header h1 {
            font-size: 1.3rem;
        }
    }
</style>
""", unsafe_allow_html=True)


def ensure_initialized():
    """Initializes schema and seeds demo data on first boot if DB is empty."""
    init_db()
    schools = get_schools()
    if not schools:
        seed_database(days_back=12, clear_existing=False)


ensure_initialized()


# 3. Header Banner
st.markdown("""
<div class="brand-header">
    <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap;">
        <div>
            <h1>PM POSHAN: Mid-Day Meal Nutrition & Wastage Tracker</h1>
            <p>School Education Department Monitoring System &bull; Soft Computing Decision Support Engine</p>
        </div>
        <div style="text-align: right; margin-top: 0.4rem;">
            <span style="background-color: #ED8936; color: white; padding: 4px 10px; border-radius: 6px; font-size: 0.75rem; font-weight: 600; letter-spacing: 0.5px;">GOVERNMENT OF INDIA NORMS</span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)


# 4. Sidebar Navigation
st.sidebar.title("🧭 Navigation")

view_selection = st.sidebar.radio(
    "Select Portal View:",
    options=[
        "📊 Monitoring Dashboard",
        "🍲 Daily Meal Data Entry",
        "🧠 Soft Computing Fuzzy Lab",
        "📑 Reports & Audit Exports",
        "📋 PM POSHAN Norms & ICMR IFCT"
    ],
    index=0
)

st.sidebar.markdown("---")

# Project Metadata & Soft Computing Viva Information in Sidebar
st.sidebar.markdown("### 🎓 Academic Capstone Context")
st.sidebar.markdown(
    """
    **Project:** Mid-Day Meal Nutrition + Wastage Tracker  
    **Specialization:** Soft Computing (Mamdani FIS)  
    **Tech Stack:** Streamlit, SQLite, Plotly, scikit-fuzzy  
    **Data Standard:** ICMR-NIN IFCT 2017 & PM POSHAN
    """
)

st.sidebar.markdown("---")
st.sidebar.caption("⚡ Status: SQLite Active | Mamdani FIS Engine Ready")


# 5. Route to Selected View
if view_selection == "📊 Monitoring Dashboard":
    render_dashboard_view()
elif view_selection == "🍲 Daily Meal Data Entry":
    render_daily_entry_view()
elif view_selection == "🧠 Soft Computing Fuzzy Lab":
    render_fuzzy_analysis_view()
elif view_selection == "📑 Reports & Audit Exports":
    render_reports_view()
elif view_selection == "📋 PM POSHAN Norms & ICMR IFCT":
    render_reference_norms_view()
