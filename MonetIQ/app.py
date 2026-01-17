"""
MonetIQ - AI-Powered Financial Intelligence Platform
Complete Streamlit Application

A production-grade personal finance super-app with intelligent analytics,
tax optimization, goal tracking, and predictive insights.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import textwrap
from datetime import datetime, timedelta
from typing import Dict, Any, List
import json

# Import MonetIQ modules
from core.expense_tracker import (
    add_transaction, get_all_expenses, get_expenses_by_category,
    monthly_expense_summary, auto_categorize_transaction,
    detect_recurring_expenses, expense_trends, expense_velocity,
    top_merchants, get_category_list, delete_transaction
)
from core.health_score import (
    calculate_financial_health_score, health_score_explanation,
    save_health_score_to_history, get_health_score_history
)
from core.stress_index import (
    calculate_financial_stress_index, stress_index_explanation,
    get_stress_alerts, get_stress_recommendations
)
from core.simulator import (
    run_simulation, compare_scenarios, simulate_income_change,
    simulate_expense_change, simulate_new_emi
)
from analytics.overspending import OverspendingAnalyzer
from analytics.insights import InsightEngine, Transaction, Budget
from analytics.monthly_preview import get_monthly_preview
from goals.savings_goals import (
    SavingsGoalsEngine, create_savings_goal, quick_goal_health_check
)
from tax.tax_estimator import get_tax_estimation_report
from tax.tax_blindspots import get_tax_blindspot_report
from tax.tax_suggestions import get_tax_suggestions_report
from utils.storage import (
    load_state, save_state, update_section, append_to_section,
    get_section, state_exists
)
from utils.helpers import (
    format_currency, percentage, score_to_label,
    health_score_color, normalize_amount, get_current_month
)

# ============================================================================
# PAGE CONFIGURATION
# ============================================================================
def inject_global_css():
    st.markdown("""
    <style>
    .metric-card {
        background: #0f172a;
        border-radius: 16px;
        padding: 1.2rem;
        margin-bottom: 1rem;
        box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        color: #e5e7eb;
    }

    .progress-container {
        width: 100%;
        height: 10px;
        background: #1f2933;
        border-radius: 999px;
        overflow: hidden;
        margin-top: 0.8rem;
    }

    /* Progress Bar - Animated */
    .progress-container {
        background: rgba(229, 231, 235, 0.3);
        border-radius: 20px;
        height: 24px;
        overflow: hidden;
        box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.1);
    }

    .progress-bar {
        height: 100%;
        background: linear-gradient(90deg, #10b981, #059669);
        transition: width 0.6s cubic-bezier(0.4, 0, 0.2, 1);
        border-radius: 20px;
        box-shadow: 0 2px 8px rgba(16, 185, 129, 0.4);
    }

    .progress-bar-warning {
        background: linear-gradient(90deg, #f59e0b, #d97706);
        box-shadow: 0 2px 8px rgba(245, 158, 11, 0.4);
    }

    .progress-bar-danger {
        background: linear-gradient(90deg, #ef4444, #dc2626);
        box-shadow: 0 2px 8px rgba(239, 68, 68, 0.4);
    }

    .section-header {
        font-size: 1.6rem;
        font-weight: 800;
        margin-bottom: 1rem;
        color: #e5e7eb;
    }

    .subsection-header {
        font-size: 1.2rem;
        font-weight: 700;
        margin: 1.5rem 0 0.8rem;
        color: #cbd5f5;
    }

    .alert-warning {
        background: #1f2937;
        border-left: 5px solid #f59e0b;
        padding: 0.9rem;
        border-radius: 10px;
        margin-bottom: 0.6rem;
        color: #fde68a;
    }

    .alert-success {
        background: #052e16;
        border-left: 5px solid #10b981;
        padding: 0.9rem;
        border-radius: 10px;
        color: #bbf7d0;
    }
    </style>
    """, unsafe_allow_html=True)


st.set_page_config(
    page_title="MonetIQ - Financial Intelligence",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)
# Added this block to ensure sidebar toggle is visible
st.markdown("""
<script>
    window.addEventListener('load', function() {
        const style = document.createElement('style');
        style.innerHTML = `
            [data-testid="collapsedControl"] {
                display: block !important;
                visibility: visible !important;
                opacity: 1 !important;
            }
        `;
        document.head.appendChild(style);
    });
</script>
""", unsafe_allow_html=True)
# ============================================================================
# CUSTOM CSS STYLING - PREMIUM FINTECH DESIGN
# ============================================================================
st.markdown("""
<style>
.alert-info {
    background: linear-gradient(135deg, #0f172a, #020617);
    border: 1px solid rgba(99,102,241,0.35);
    border-left: 6px solid #6366f1;
    border-radius: 18px;
    padding: 1.4rem 1.6rem;
    margin-bottom: 1.5rem;
    box-shadow: 0 20px 45px rgba(0,0,0,0.45);
    color: #e5e7eb;
    font-size: 0.95rem;
}

.alert-info strong {
    font-size: 1.15rem;
    color: #a5b4fc;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<style>
    /* Global Styles */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    * {
        font-family: 'Inter', sans-serif;
    }

    .main {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 50%, #7e22ce 100%);
        padding: 2rem 1rem;
    }

    .stApp {
        background: transparent;
    }

    /* Hide Streamlit Branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* CRITICAL: Ensure sidebar toggle button is always visible */
    [data-testid="collapsedControl"] {
    display: flex !important;
    visibility: visible !important;
    opacity: 1 !important;
    position: fixed !important;
    top: 0.5rem !important;
    left: 0.5rem !important;
    z-index: 999999 !important;
    background: linear-gradient(135deg, #667eea, #764ba2) !important;
    border-radius: 8px !important;
    padding: 0.5rem !important;
    box-shadow: 0 4px 12px rgba(0,0,0,0.3) !important;
    }
    
    [data-testid="collapsedControl"] button {
        color: white !important;
    }
    
    [data-testid="collapsedControl"] svg {
        fill: white !important;
        stroke: white !important;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1f2937 0%, #111827 100%);
    }
    
    [data-testid="stSidebar"] * {
        color: white !important;
    }
    
    /* Card Styles - Glass Morphism */
    .metric-card {
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(10px);
        border-radius: 20px;
        padding: 1.5rem;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        margin-bottom: 1rem;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        border: 1px solid rgba(255, 255, 255, 0.2);
    }

    .metric-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 12px 48px rgba(0, 0, 0, 0.15);
    }

    /* Premium Gradient Cards */
    .gradient-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 20px;
        padding: 2rem;
        box-shadow: 0 10px 40px rgba(102, 126, 234, 0.3);
        margin-bottom: 1.5rem;
    }

    .gradient-card-success {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
    }

    .gradient-card-warning {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
    }

    .gradient-card-danger {
        background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
    }

    /* Score Badges - 3D Effect */
    .score-badge {
        display: inline-block;
        padding: 0.75rem 1.5rem;
        border-radius: 50px;
        font-weight: 700;
        font-size: 1.2rem;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
        transform: perspective(1000px);
        transition: all 0.3s;
    }

    .score-badge:hover {
        transform: perspective(1000px) translateY(-2px);
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.3);
    }

    .score-excellent {
        background: linear-gradient(135deg, #10b981, #059669);
        color: white;
    }

    .score-good {
        background: linear-gradient(135deg, #3b82f6, #1d4ed8);
        color: white;
    }

    .score-fair {
        background: linear-gradient(135deg, #f59e0b, #d97706);
        color: white;
    }

    .score-poor {
        background: linear-gradient(135deg, #ef4444, #dc2626);
        color: white;
    }

    .score-critical {
        background: linear-gradient(135deg, #dc2626, #991b1b);
        color: white;
        animation: pulse 2s infinite;
    }

    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.8; }
    }

    /* Alert Styles - Modern Design */
    .alert-critical {
        background: linear-gradient(135deg, #fee2e2, #fecaca);
        border-left: 5px solid #ef4444;
        padding: 1.25rem;
        border-radius: 12px;
        margin: 1rem 0;
        box-shadow: 0 4px 12px rgba(239, 68, 68, 0.2);
    }

    .alert-warning {
        background: linear-gradient(135deg, #fef3c7, #fde68a);
        border-left: 5px solid #f59e0b;
        padding: 1.25rem;
        border-radius: 12px;
        margin: 1rem 0;
        box-shadow: 0 4px 12px rgba(245, 158, 11, 0.2);
    }

    .alert-info {
        background: linear-gradient(135deg, #dbeafe, #bfdbfe);
        border-left: 5px solid #3b82f6;
        padding: 1.25rem;
        border-radius: 12px;
        margin: 1rem 0;
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.2);
    }

    .alert-success {
        background: linear-gradient(135deg, #d1fae5, #a7f3d0);
        border-left: 5px solid #10b981;
        padding: 1.25rem;
        border-radius: 12px;
        margin: 1rem 0;
        box-shadow: 0 4px 12px rgba(16, 185, 129, 0.2);
    }


    /* Section Headers - Premium Typography */
    .section-header {
        font-size: 2.5rem;
        font-weight: 800;
        background: linear-gradient(135deg, #fff, #f0f0f0);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 2rem;
        text-shadow: 2px 2px 8px rgba(0, 0, 0, 0.3);
        letter-spacing: -0.5px;
    }

    .subsection-header {
        font-size: 1.5rem;
        font-weight: 700;
        color: white;
        margin: 1.5rem 0 1rem 0;
        text-shadow: 1px 1px 4px rgba(0, 0, 0, 0.2);
    }

    /* Sidebar Customization - Premium Dark Mode */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1f2937 0%, #111827 100%);
        border-right: 1px solid rgba(255, 255, 255, 0.1);
    }

    [data-testid="stSidebar"] * {
        color: white !important;
    }

    /* Button Styles - Premium 3D */
    .stButton>button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        font-size: 1rem;
        transition: all 0.3s;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    .stButton>button:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.5);
        background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
    }

    .stButton>button:active {
        transform: translateY(-1px);
    }

    /* Metric Container - Elegant Design */
    .metric-container {
        background: rgba(255, 255, 255, 0.95);
        border-radius: 16px;
        padding: 1.5rem;
        text-align: center;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
        transition: all 0.3s;
    }

    .metric-container:hover {
        transform: scale(1.02);
        box-shadow: 0 6px 30px rgba(0, 0, 0, 0.12);
    }

    .metric-value {
        font-size: 2.5rem;
        font-weight: 800;
        background: linear-gradient(135deg, #667eea, #764ba2);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }

    .metric-label {
        font-size: 1rem;
        color: #6b7280;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    .metric-delta-positive {
        color: #10b981;
        font-weight: 600;
        font-size: 0.9rem;
    }

    .metric-delta-negative {
        color: #ef4444;
        font-weight: 600;
        font-size: 0.9rem;
    }

    /* Goal Card - Premium Design */
    .goal-card {
        background: white;
        border-radius: 16px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        border-left: 5px solid #667eea;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
        transition: all 0.3s;
    }

    .goal-card:hover {
        transform: translateX(5px);
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.12);
    }

    .goal-title {
        font-size: 1.3rem;
        font-weight: 700;
        color: #1f2937;
        margin-bottom: 0.75rem;
    }

    .goal-progress {
        font-size: 1rem;
        color: #6b7280;
        margin-bottom: 0.5rem;
    }

    /* Data Table Styling */
    .dataframe {
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    }

    /* Input Fields */
    .stTextInput>div>div>input,
    .stNumberInput>div>div>input,
    .stSelectbox>div>div>select {
        border-radius: 10px;
        border: 2px solid #e5e7eb;
        padding: 0.75rem;
        transition: all 0.3s;
    }

    .stTextInput>div>div>input:focus,
    .stNumberInput>div>div>input:focus,
    .stSelectbox>div>div>select:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    }

    /* Expander Styling */
    .streamlit-expanderHeader {
        background: rgba(255, 255, 255, 0.1);
        border-radius: 10px;
        font-weight: 600;
        padding: 1rem;
        color: white !important;
    }

    /* Tabs Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 0.5rem;
    }

    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        color: white;
        font-weight: 600;
        padding: 0.75rem 1.5rem;
    }

    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #667eea, #764ba2);
    }

    /* Stat Card with Icon */
    .stat-card {
        background: white;
        border-radius: 16px;
        padding: 1.5rem;
        display: flex;
        align-items: center;
        gap: 1rem;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
        transition: all 0.3s;
    }

    .stat-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
    }

    .stat-icon {
        font-size: 3rem;
        width: 70px;
        height: 70px;
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 50%;
        background: linear-gradient(135deg, #667eea, #764ba2);
    }

    .stat-content {
        flex: 1;
    }

    .stat-value {
        font-size: 2rem;
        font-weight: 800;
        color: #1f2937;
    }

    .stat-label {
        font-size: 0.9rem;
        color: #6b7280;
        font-weight: 500;
    }

    /* Animation Classes */
    @keyframes slideIn {
        from {
            opacity: 0;
            transform: translateY(20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }

    .animate-slide-in {
        animation: slideIn 0.5s ease-out;
    }

    @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
    }

    .animate-fade-in {
        animation: fadeIn 0.8s ease-out;
    }

    /* Custom Scrollbar */
    ::-webkit-scrollbar {
        width: 10px;
        height: 10px;
    }

    ::-webkit-scrollbar-track {
        background: rgba(255, 255, 255, 0.1);
        border-radius: 10px;
    }

    ::-webkit-scrollbar-thumb {
        background: linear-gradient(135deg, #667eea, #764ba2);
        border-radius: 10px;
    }

    ::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(135deg, #764ba2, #667eea);
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================

if 'state' not in st.session_state:
    st.session_state.state = load_state()

if 'current_page' not in st.session_state:
    st.session_state.current_page = "Dashboard"


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_risk_emoji(level):
    """Get emoji for risk level."""
    mapping = {
        'Low': '✅',
        'Moderate': '⚠️',
        'High': '🔴',
        'Critical': '🚨'
    }
    return mapping.get(level, '❓')


def format_large_number(num):
    """Format large numbers with K, L, Cr suffixes."""
    if num >= 10000000:  # 1 Crore
        return f"₹{num / 10000000:.2f}Cr"
    elif num >= 100000:  # 1 Lakh
        return f"₹{num / 100000:.2f}L"
    elif num >= 1000:  # 1 Thousand
        return f"₹{num / 1000:.1f}K"
    else:
        return format_currency(num)


# ============================================================================
# SIDEBAR NAVIGATION
# ============================================================================

def render_sidebar():
    """Render premium sidebar navigation with key metrics."""
    with st.sidebar:
        # Logo and Title
        st.markdown("""
        <div style="text-align: center; padding: 1rem 0 2rem 0;">
            <div style="font-size: 3rem;">💰</div>
            <div style="font-size: 1.8rem; font-weight: 800; margin-top: 0.5rem;">MonetIQ</div>
            <div style="font-size: 0.9rem; opacity: 0.7; margin-top: 0.25rem;">Financial Intelligence</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")

        # Quick Stats Cards
        state = st.session_state.get("state", {})

        # Health Score Badge
        try:
            health_report = calculate_financial_health_score(state)
            health_score = health_report.get('health_score', 0)
            health_grade = health_report.get('grade', 'Unknown')

            color_map = {
                'Excellent': 'linear-gradient(135deg, #10b981, #059669)',
                'Good': 'linear-gradient(135deg, #3b82f6, #1d4ed8)',
                'Fair': 'linear-gradient(135deg, #f59e0b, #d97706)',
                'Risky': 'linear-gradient(135deg, #ef4444, #dc2626)',
                'Critical': 'linear-gradient(135deg, #dc2626, #991b1b)'
            }
            color = color_map.get(health_grade, 'linear-gradient(135deg, #6b7280, #4b5563)')

            st.markdown(f"""
            <div style="background: {color}; color: white; padding: 1.5rem; border-radius: 16px; text-align: center; margin-bottom: 1rem; box-shadow: 0 4px 12px rgba(0,0,0,0.2);">
                <div style="font-size: 3rem; font-weight: 800;">{health_score}</div>
                <div style="font-size: 1rem; margin-top: 0.5rem;">Health Score</div>
                <div style="font-size: 0.9rem; margin-top: 0.5rem; opacity: 0.9;">{health_grade}</div>
            </div>
            """, unsafe_allow_html=True)
        except:
            st.markdown("""
            <div style="background: linear-gradient(135deg, #6b7280, #4b5563); color: white; padding: 1.5rem; border-radius: 16px; text-align: center; margin-bottom: 1rem; box-shadow: 0 4px 12px rgba(0,0,0,0.2);">
                <div style="font-size: 2rem;">⚠️</div>
                <div style="font-size: 0.9rem; margin-top: 0.5rem;">Add data to calculate score</div>
            </div>
            """, unsafe_allow_html=True)

        # Stress Index Badge
        try:
            stress_report = calculate_financial_stress_index(state)
            stress_index = stress_report.get('stress_index', 0)
            stress_level = stress_report.get('level', 'Low')

            stress_color_map = {
                'Low': 'linear-gradient(135deg, #10b981, #059669)',
                'Moderate': 'linear-gradient(135deg, #f59e0b, #d97706)',
                'High': 'linear-gradient(135deg, #ef4444, #dc2626)',
                'Critical': 'linear-gradient(135deg, #dc2626, #991b1b)'
            }
            stress_color = stress_color_map.get(stress_level, 'linear-gradient(135deg, #6b7280, #4b5563)')

            st.markdown(f"""
            <div style="background: {stress_color}; color: white; padding: 1.5rem; border-radius: 16px; text-align: center; margin-bottom: 1rem; box-shadow: 0 4px 12px rgba(0,0,0,0.2);">
                <div style="font-size: 3rem; font-weight: 800;">{stress_index}</div>
                <div style="font-size: 1rem; margin-top: 0.5rem;">Stress Index</div>
                <div style="font-size: 0.9rem; margin-top: 0.5rem; opacity: 0.9;">{get_risk_emoji(stress_level)} {stress_level}</div>
            </div>
            """, unsafe_allow_html=True)
        except:
            pass

        st.markdown("---")

        # Navigation Menu with Icons
        st.markdown("### 📊 Navigation")

        pages = {
            "🏠 Dashboard": "Dashboard",
            "💸 Expenses": "Expenses",
            "❤️ Financial Health": "Health",
            "⚠️ Overspending": "Overspending",
            "🧠 AI Insights": "Insights",
            "🎯 Savings Goals": "Goals",
            "🧮 Tax Intelligence": "Tax",
            "🔮 What-If Simulator": "Simulator"
        }

        for label, page in pages.items():
            is_active = st.session_state.current_page == page
            button_style = "primary" if is_active else "secondary"

            if st.button(label, key=f"nav_{page}", use_container_width=True, type=button_style):
                st.session_state.current_page = page
                st.rerun()

        st.markdown("---")




# ============================================================================
# DASHBOARD PAGE
# ============================================================================

def render_dashboard():
    """Render premium dashboard with comprehensive financial overview."""
    st.markdown('<div class="section-header animate-fade-in">🏠 Financial Command Center</div>', unsafe_allow_html=True)

    state = st.session_state.state

    # Quick Action Buttons
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("➕ Add Transaction", use_container_width=True):
            st.session_state.current_page = "Expenses"
            st.rerun()
    with col2:
        if st.button("🎯 Set Goal", use_container_width=True):
            st.session_state.current_page = "Goals"
            st.rerun()
    with col3:
        if st.button("🧮 Check Tax", use_container_width=True):
            st.session_state.current_page = "Tax"
            st.rerun()
    with col4:
        if st.button("🔮 Run Simulation", use_container_width=True):
            st.session_state.current_page = "Simulator"
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # Top Metrics Row - Premium Cards
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        income_data = state.get('monthly_income', 0)
        if isinstance(income_data, dict):
            income = income_data.get('monthly', 0) or income_data.get('amount', 0)
        else:
            income = income_data if income_data else 0
        st.markdown(f"""
        <div class="metric-card animate-slide-in">
            <div style="font-size: 1.5rem; margin-bottom: 0.5rem;">💰</div>
            <div class="metric-value">{format_large_number(income)}</div>
            <div class="metric-label">Monthly Income</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        try:
            now = datetime.now()
            summary = monthly_expense_summary(state, now.year, now.month)
            expenses = summary.get('total_expenses', 0)
        except:
            expenses = 0

        st.markdown(f"""
        <div class="metric-card animate-slide-in" style="animation-delay: 0.1s;">
            <div style="font-size: 1.5rem; margin-bottom: 0.5rem;">💸</div>
            <div class="metric-value">{format_large_number(expenses)}</div>
            <div class="metric-label">Monthly Expenses</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        savings = income - expenses
        savings_rate = (savings / income * 100) if income > 0 else 0

        savings_color = "#10b981" if savings_rate >= 20 else "#f59e0b" if savings_rate >= 10 else "#ef4444"

        st.markdown(f"""
        <div class="metric-card animate-slide-in" style="animation-delay: 0.2s;">
            <div style="font-size: 1.5rem; margin-bottom: 0.5rem;">📈</div>
            <div class="metric-value" style="color: {savings_color};">{savings_rate:.1f}%</div>
            <div class="metric-label">Savings Rate</div>
            <div style="font-size: 0.85rem; color: #6b7280; margin-top: 0.5rem;">{format_large_number(savings)}</div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        try:
            health_report = calculate_financial_health_score(state)
            health_score = health_report.get('health_score', 0)
            grade = health_report.get('grade', 'N/A')
        except:
            health_score = 0
            grade = "N/A"

        score_color = health_score_color(health_score)

        st.markdown(f"""
        <div class="metric-card animate-slide-in" style="animation-delay: 0.3s;">
            <div style="font-size: 1.5rem; margin-bottom: 0.5rem;">❤️</div>
            <div class="metric-value" style="color: {score_color};">{health_score}</div>
            <div class="metric-label">Health Score</div>
            <div style="font-size: 0.85rem; color: #6b7280; margin-top: 0.5rem;">{grade}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Main Content Area - Charts and Insights
    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown('<div class="subsection-header">📊 Spending Overview</div>', unsafe_allow_html=True)

        # Expense Breakdown Chart
        try:
            category_totals = get_expenses_by_category(state)
            if category_totals:
                fig = go.Figure(data=[go.Pie(
                    labels=list(category_totals.keys()),
                    values=list(category_totals.values()),
                    hole=0.5,
                    marker=dict(
                        colors=px.colors.qualitative.Set3,
                        line=dict(color='black', width=2)
                    ),
                    textinfo='label+percent',
                    textfont=dict(size=14, color='black'),
                    hovertemplate='<b>%{label}</b><br>₹%{value:,.0f}<br>%{percent}<extra></extra>'
                )])

                fig.update_layout(
                    paper_bgcolor='rgba(255,255,255,0.95)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    height=400,
                    margin=dict(t=40, b=40, l=40, r=40),
                    font=dict(family='Inter',color='Black', size=13),
                    showlegend=True,
                    legend=dict(
                        orientation="v",
                        yanchor="middle",
                        y=0.5,
                        xanchor="left",
                        x=1.02
                    )
                )

                st.plotly_chart(fig, use_container_width=True)
            else:
                st.markdown("""
                <div class="alert-info">
                    <strong>📝 No Expense Data</strong><br>
                    Start tracking your expenses to see beautiful visualizations here!
                </div>
                """, unsafe_allow_html=True)
        except Exception as e:
            st.info("📝 Add expenses to see breakdown chart")

    with col2:
        st.markdown('<div class="subsection-header">💡 Quick Insights</div>', unsafe_allow_html=True)

        # Recent Alerts
        try:
            stress_report = calculate_financial_stress_index(state)
            alerts = get_stress_alerts(stress_report)

            if alerts:
                for alert in alerts[:3]:
                    severity = alert.get('severity', 'medium')
                    alert_class = f"alert-{severity}"
                    icon = '🚨' if severity == 'critical' else '⚠️' if severity == 'warning' else 'ℹ️'

                    st.markdown(f"""
                    <div class="{alert_class}">
                        <strong>{icon} {alert.get('type', '').replace('_', ' ').title()}</strong><br>
                        <small>{alert.get('message', '')}</small>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div class="alert-success">
                    <strong>✅ All Clear!</strong><br>
                    No critical alerts. Your finances look healthy!
                </div>
                """, unsafe_allow_html=True)
        except:
            st.info("📊 Insights will appear as you add more data")

        # Top Expense Category
        try:
            category_totals = get_expenses_by_category(state)
            if category_totals:
                top_cat = max(category_totals.items(), key=lambda x: x[1])
                st.markdown(f"""
                <div class="metric-card">
                    <div style="font-weight: 700; color: #667eea; margin-bottom: 0.5rem;">Top Spending</div>
                    <div style="font-size: 1.3rem; font-weight: 700;">{top_cat[0]}</div>
                    <div style="color: #6b7280;">{format_currency(top_cat[1])}</div>
                </div>
                """, unsafe_allow_html=True)
        except:
            pass

    st.markdown("<br>", unsafe_allow_html=True)

    # Income vs Expense Trend
    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<div class="subsection-header">💰 Financial Flow</div>', unsafe_allow_html=True)

        fig = go.Figure()

        fig.add_trace(go.Bar(
            name='Income',
            x=['This Month'],
            y=[income],
            marker_color='#10b981',
            text=[format_large_number(income)],
            textposition='outside'
        ))

        fig.add_trace(go.Bar(
            name='Expenses',
            x=['This Month'],
            y=[expenses],
            marker_color='#ef4444',
            text=[format_large_number(expenses)],
            textposition='outside'
        ))

        fig.add_trace(go.Bar(
            name='Savings',
            x=['This Month'],
            y=[savings],
            marker_color='#3b82f6',
            text=[format_large_number(savings)],
            textposition='outside'
        ))

        fig.update_layout(
            paper_bgcolor='rgba(255,255,255,0.95)',
            plot_bgcolor='rgba(0,0,0,0)',
            height=350,
            barmode='group',
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            font=dict(family='Inter'),
            yaxis=dict(title="Amount (₹)", gridcolor='rgba(200,200,200,0.2)'),
            xaxis=dict(showgrid=False)
        )

        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown('<div class="subsection-header">📈 Expense Trends</div>', unsafe_allow_html=True)

        try:
            trends = expense_trends(state)
            trend_type = trends.get('trend', 'stable')
            percentage_change = trends.get('percentage_change', 0)

            if trend_type == "increasing":
                trend_color = "#ef4444"
                trend_icon = "📈"
                trend_text = f"Spending Up {abs(percentage_change):.1f}%"
                alert_type = "alert-warning"
            elif trend_type == "decreasing":
                trend_color = "#10b981"
                trend_icon = "📉"
                trend_text = f"Spending Down {abs(percentage_change):.1f}%"
                alert_type = "alert-success"
            else:
                trend_color = "#3b82f6"
                trend_icon = "➡️"
                trend_text = "Spending Stable"
                alert_type = "alert-info"

            st.markdown(f"""
            <div class="{alert_type}">
                <div style="font-size: 3rem; text-align: center; margin-bottom: 1rem;">{trend_icon}</div>
                <div style="font-size: 1.5rem; font-weight: 700; text-align: center; color: {trend_color};">
                    {trend_text}
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Velocity Metric
            velocity = expense_velocity(state)
            st.markdown(f"""
            <div class="metric-card" style="margin-top: 1rem;">
                <div style="font-weight: 700; color: #667eea; margin-bottom: 0.5rem;">Daily Burn Rate</div>
                <div style="font-size: 1.8rem; font-weight: 700;">{format_currency(velocity)}/day</div>
            </div>
            """, unsafe_allow_html=True)

        except:
            st.info("Add more expense data to see trends")

    st.markdown("<br>", unsafe_allow_html=True)

    # Health Score Breakdown
    st.markdown('<div class="subsection-header">🏥 Health Score Components</div>', unsafe_allow_html=True)

    try:
        health_report = calculate_financial_health_score(state)
        components = health_report.get('components', {})

        if components:
            cols = st.columns(len(components))

            for idx, (comp_name, comp_data) in enumerate(components.items()):
                with cols[idx]:
                    score = comp_data.get('score', 0)
                    score_color = health_score_color(score)

                    st.markdown(f"""
                    <div class="metric-card" style="text-align: center;">
                        <div style="font-size: 2.5rem; font-weight: 800; color: {score_color};">
                            {score:.0f}
                        </div>
                        <div style="font-size: 0.85rem; color: #6b7280; margin-top: 0.5rem; text-transform: uppercase;">
                            {comp_name.replace('_', ' ')}
                        </div>
                        <div class="progress-container" style="margin-top: 1rem;">
                            <div class="progress-bar" style="width: {score}%; background: {score_color};"></div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
    except:
        st.info("💡 Complete your financial profile to see detailed health metrics")


# ============================================================================
# EXPENSES PAGE
# ============================================================================

def render_expenses():
    """Render comprehensive expense tracking interface."""
    st.markdown('<div class="section-header">💸 Expense Manager</div>', unsafe_allow_html=True)

    state = st.session_state.state

    # Add Transaction Section
    with st.expander("➕ Add New Transaction", expanded=True):
        with st.form("add_transaction_form"):
            col1, col2, col3 = st.columns(3)

            with col1:
                amount = st.number_input("Amount (₹)", min_value=0.0, step=100.0, format="%.2f")
                description = st.text_input("Description", placeholder="e.g., Grocery shopping")

            with col2:
                categories = get_category_list()
                category = st.selectbox("Category", ["🤖 Auto-detect"] + categories)
                date = st.date_input("Date", datetime.now())

            with col3:
                source = st.selectbox("Payment Method",
                                      ["Cash", "Credit Card", "Debit Card", "UPI", "Bank Transfer", "Other"])
                merchant = st.text_input("Merchant (Optional)", placeholder="e.g., Amazon")

            submitted = st.form_submit_button("Add Transaction", use_container_width=True, type="primary")

            if submitted:
                if amount > 0 and description:
                    txn = {
                        'amount': amount,
                        'description': description,
                        'category': category if category != "🤖 Auto-detect" else "",
                        'date': date.strftime("%Y-%m-%d"),
                        'source': source,
                        'merchant': merchant if merchant else description
                    }

                    try:
                        state = add_transaction(state, txn)
                        st.session_state.state = state
                        save_state(state)
                        st.success(f"✅ Transaction added: {format_currency(amount)} - {description}")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error adding transaction: {str(e)}")
                else:
                    st.error("❌ Please fill in amount and description")

    st.markdown("<br>", unsafe_allow_html=True)

    # Summary Cards
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        try:
            now = datetime.now()
            summary = monthly_expense_summary(state, now.year, now.month)
            total = summary.get('total_expenses', 0)
            st.markdown(f"""
            <div class="gradient-card">
                <div style="font-size: 2rem; font-weight: 800;">{format_large_number(total)}</div>
                <div style="font-size: 1rem; margin-top: 0.5rem; opacity: 0.9;">This Month</div>
            </div>
            """, unsafe_allow_html=True)
        except:
            st.metric("This Month", format_currency(0))

    with col2:
        try:
            velocity = expense_velocity(state)
            st.markdown(f"""
            <div class="gradient-card gradient-card-warning">
                <div style="font-size: 2rem; font-weight: 800;">{format_currency(velocity)}</div>
                <div style="font-size: 1rem; margin-top: 0.5rem; opacity: 0.9;">Daily Burn Rate</div>
            </div>
            """, unsafe_allow_html=True)
        except:
            st.metric("Daily Burn Rate", format_currency(0))

    with col3:
        expenses = get_all_expenses(state)
        st.markdown(f"""
        <div class="gradient-card gradient-card-success">
            <div style="font-size: 2rem; font-weight: 800;">{len(expenses)}</div>
            <div style="font-size: 1rem; margin-top: 0.5rem; opacity: 0.9;">Transactions</div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        try:
            merchants = top_merchants(state, n=1)
            top_merchant = merchants[0][0] if merchants else "N/A"
            st.markdown(f"""
            <div class="gradient-card">
                <div style="font-size: 1.5rem; font-weight: 800;">{top_merchant[:15]}</div>
                <div style="font-size: 1rem; margin-top: 0.5rem; opacity: 0.9;">Top Merchant</div>
            </div>
            """, unsafe_allow_html=True)
        except:
            st.metric("Top Merchant", "N/A")

    st.markdown("<br>", unsafe_allow_html=True)

    # Transactions Table
    st.markdown('<div class="subsection-header">📋 Transaction History</div>', unsafe_allow_html=True)

    expenses = get_all_expenses(state)

    if expenses:
        # Create DataFrame
        df_data = []
        for idx, txn in enumerate(reversed(expenses[-50:])):  # Last 50 transactions
            df_data.append({
                'ID': len(expenses) - idx,
                'Date': txn.get('date', ''),
                'Description': txn.get('description', ''),
                'Category': txn.get('category', 'Uncategorized'),
                'Merchant': txn.get('merchant', txn.get('description', '')),
                'Source': txn.get('source', ''),
                'Amount': txn.get('amount', 0)
            })

        df = pd.DataFrame(df_data)

        # Format amount column
        df['Amount (₹)'] = df['Amount'].apply(lambda x: f"₹{x:,.2f}")
        df_display = df.drop('Amount', axis=1)

        # Display with custom styling
        st.dataframe(
            df_display,
            use_container_width=True,
            height=450,
            hide_index=True
        )

        # Export option
        csv = df.to_csv(index=False)
        st.download_button(
            label="📥 Download as CSV",
            data=csv,
            file_name=f"monetiq_expenses_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )

    else:
        st.markdown("""
        <div class="alert-info">
            <strong>📝 No Transactions Yet</strong><br>
            Start tracking your expenses by adding your first transaction above!
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Category Analysis and Recurring Expenses
    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<div class="subsection-header">📊 Category Breakdown</div>', unsafe_allow_html=True)

        try:
            category_totals = get_expenses_by_category(state)
            if category_totals:
                # Sort by amount
                sorted_categories = sorted(category_totals.items(), key=lambda x: x[1], reverse=True)

                for cat, amount in sorted_categories:
                    percentage = (amount / sum(category_totals.values()) * 100)
                    st.markdown(f"""
                    <div class="metric-card">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div>
                                <div style="font-weight: 700; font-size: 1.1rem;">{cat}</div>
                                <div style="color: #6b7280; font-size: 0.9rem;">{percentage:.1f}% of total</div>
                            </div>
                            <div style="font-size: 1.5rem; font-weight: 800; color: #667eea;">
                                {format_large_number(amount)}
                            </div>
                        </div>
                        <div class="progress-container" style="margin-top: 1rem;">
                            <div class="progress-bar" style="width: {percentage}%;"></div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("No category data available")
        except:
            st.info("Add expenses to see category breakdown")

    with col2:
        st.markdown('<div class="subsection-header">🔄 Recurring Expenses</div>', unsafe_allow_html=True)

        try:
            recurring = detect_recurring_expenses(state)
            if recurring:
                for rec in recurring[:10]:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div style="font-weight: 700; color: #667eea; margin-bottom: 0.5rem;">
                            {rec.get('description', 'Unknown')}
                        </div>
                        <div style="display: flex; justify-content: space-between; font-size: 0.9rem; color: #6b7280;">
                            <span>{rec.get('category', 'N/A')}</span>
                            <span style="font-weight: 700; color: #1f2937;">{format_currency(rec.get('amount', 0))}</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("🔍 No recurring patterns detected yet. Keep adding transactions!")
        except:
            st.info("Add more transactions to detect recurring expenses")


# ============================================================================
# FINANCIAL HEALTH PAGE
# ============================================================================

def render_health():
    """Render detailed financial health analysis."""
    st.markdown('<div class="section-header">❤️ Financial Health Dashboard</div>', unsafe_allow_html=True)

    state = st.session_state.state

    try:
        health_report = calculate_financial_health_score(state)

        # Hero Score Display
        health_score = health_report.get('health_score', 0)
        grade = health_report.get('grade', 'Unknown')

        col1, col2, col3 = st.columns([1, 2, 1])

        with col2:
            score_color = health_score_color(health_score)
            grade_class = f"score-{grade.lower()}" if grade.lower() in ['excellent', 'good', 'fair',
                                                                        'poor'] else "score-fair"

            st.markdown(f"""
            <div class="gradient-card" style="text-align: center; padding: 3rem 2rem;">
                <div style="font-size: 6rem; font-weight: 900; color: white; text-shadow: 3px 3px 10px rgba(0,0,0,0.3);">
                    {health_score}
                </div>
                <div style="font-size: 1.2rem; margin-top: 1rem; opacity: 0.95;">out of 100</div>
                <div class="score-badge {grade_class}" style="margin-top: 1.5rem; font-size: 1.5rem;">
                    {grade}
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Component Scores
        st.markdown('<div class="subsection-header">📊 Health Components</div>', unsafe_allow_html=True)

        components = health_report.get('components', {})

        if components:
            comp_cols = st.columns(min(len(components), 5))

            for idx, (comp_name, comp_data) in enumerate(components.items()):
                with comp_cols[idx % len(comp_cols)]:
                    score = comp_data.get('score', 0)
                    weight = comp_data.get('weight', 0)
                    score_color = health_score_color(score)

                    # Determine icon based on component
                    icon_map = {
                        'savings_ratio': '💰',
                        'expense_control': '📊',
                        'debt_burden': '💳',
                        'emergency_fund': '🆘',
                        'investment_score': '📈'
                    }
                    icon = icon_map.get(comp_name, '📍')

                    st.markdown(f"""
                    <div class="metric-card" style="text-align: center; min-height: 200px;">
                        <div style="font-size: 2.5rem; margin-bottom: 1rem;">{icon}</div>
                        <div style="font-size: 2rem; font-weight: 800; color: {score_color}; margin-bottom: 0.5rem;">
                            {score:.0f}
                        </div>
                        <div class="progress-container">
                            <div class="progress-bar" style="width: {score}%; background: {score_color};"></div>
                        </div>
                        <div style="font-size: 0.85rem; color: #6b7280; margin-top: 1rem; text-transform: capitalize;">
                            {comp_name.replace('_', ' ')}
                        </div>
                        <div style="font-size: 0.75rem; color: #9ca3af; margin-top: 0.25rem;">
                            Weight: {weight * 100:.0f}%
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

            # Detailed Component Analysis
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown('<div class="subsection-header">🔍 Detailed Analysis</div>', unsafe_allow_html=True)

            for comp_name, comp_data in components.items():
                with st.expander(f"📌 {comp_name.replace('_', ' ').title()} - {comp_data.get('score', 0):.0f}/100"):
                    details = comp_data.get('details', {})

                    col1, col2 = st.columns(2)

                    with col1:
                        st.markdown("**Metrics:**")
                        for key, value in details.items():
                            if isinstance(value, (int, float)):
                                st.markdown(f"- **{key.replace('_', ' ').title()}:** {value:,.2f}")
                            else:
                                st.markdown(f"- **{key.replace('_', ' ').title()}:** {value}")

                    with col2:
                        score = comp_data.get('score', 0)
                        if score >= 80:
                            st.success("✅ Excellent performance in this area!")
                        elif score >= 60:
                            st.info("👍 Good, but room for improvement")
                        elif score >= 40:
                            st.warning("⚠️ Needs attention")
                        else:
                            st.error("🚨 Critical - immediate action needed")

        st.markdown("<br>", unsafe_allow_html=True)

        # Strengths and Weaknesses
        col1, col2 = st.columns(2)

        with col1:
            st.markdown('<div class="subsection-header">✅ Financial Strengths</div>', unsafe_allow_html=True)
            strengths = health_report.get('strengths', [])

            if strengths:
                for strength in strengths:
                    st.markdown(f"""
                    <div class="alert-success">
                        <strong>✓</strong> {strength}
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("Keep building your financial habits to develop strengths!")

        with col2:
            st.markdown('<div class="subsection-header">⚠️ Areas to Improve</div>', unsafe_allow_html=True)
            weaknesses = health_report.get('weaknesses', [])

            if weaknesses:
                for weakness in weaknesses:
                    st.markdown(f"""
                    <div class="alert-warning">
                        <strong>!</strong> {weakness}
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div class="alert-success">
                    <strong>🎉 Excellent!</strong><br>
                    No major weaknesses detected. Keep up the great work!
                </div>
                """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Detailed Explanation
        st.markdown('<div class="subsection-header">📝 Professional Analysis</div>', unsafe_allow_html=True)

        explanation = health_score_explanation(health_report)

        st.markdown(f"""
        <div class="metric-card" style="background: #f9fafb;">
            <pre style="white-space: pre-wrap; font-family: 'Inter', sans-serif; font-size: 0.95rem; line-height: 1.6; color: #374151; margin: 0;">
                {explanation}
            </pre>
        </div>
        """, unsafe_allow_html=True)

        # Save to history
        save_health_score_to_history(state, health_report)
        st.session_state.state = state
        save_state(state)

        # Action Recommendations
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="subsection-header">🎯 Recommended Actions</div>', unsafe_allow_html=True)

        recommendations = []
        if health_score < 60:
            recommendations.extend([
                "Review and reduce unnecessary expenses immediately",
                "Set up an emergency fund (target: 3-6 months expenses)",
                "Create a strict monthly budget and track all spending"
            ])
        elif health_score < 80:
            recommendations.extend([
                "Increase savings rate to at least 20%",
                "Consider investing in diversified portfolios",
                "Review and optimize recurring subscriptions"
            ])
        else:
            recommendations.extend([
                "Maintain current excellent financial habits",
                "Explore advanced investment opportunities",
                "Consider financial planning for long-term goals"
            ])

        for idx, rec in enumerate(recommendations, 1):
            st.markdown(f"""
            <div class="metric-card">
                <div style="display: flex; align-items: center; gap: 1rem;">
                    <div style="background: linear-gradient(135deg, #667eea, #764ba2); color: white; width: 40px; height: 40px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 700;">
                        {idx}
                    </div>
                    <div style="flex: 1; font-size: 1rem;">
                        {rec}
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    except Exception as e:
        st.markdown("""
        <div class="alert-warning">
            <strong>⚠️ Unable to Calculate Health Score</strong><br>
            Please add your income and expense data to see your financial health analysis.
        </div>
        """, unsafe_allow_html=True)

        st.info(
            "💡 **Quick Setup:**\n1. Go to Expenses page\n2. Add your income in settings\n3. Track your daily expenses\n4. Return here for complete analysis")


# ============================================================================
# OVERSPENDING PAGE
# ============================================================================
def render_overspending():
    """Render overspending detection and budget management (FINAL, STABLE)."""

    import textwrap

    # =====================================================
    # HEADER
    # =====================================================
    st.markdown(
        '<div class="section-header">⚠️ Overspending Control Center</div>',
        unsafe_allow_html=True
    )

    # =====================================================
    # LOAD STATE SAFELY
    # =====================================================
    state = st.session_state.get("state", {})
    raw_budgets = state.get("budgets", {}) or {}

    # =====================================================
    # NORMALIZE VALID CATEGORIES (CRITICAL)
    # =====================================================
    VALID_CATEGORIES = {
        str(c).strip().title()
        for c in get_category_list()
        if c and c != "Other"
    }

    # =====================================================
    # NORMALIZE BUDGET VALUES
    # =====================================================
    def get_budget_limit(value):
        if isinstance(value, (int, float)):
            return float(value)

        if isinstance(value, dict):
            return float(value.get("limit") or value.get("amount") or 0)

        return 0.0

    # =====================================================
    # HARD NORMALIZE BUDGET KEYS (BEFORE USE)
    # =====================================================
    budgets = {}
    for key, value in raw_budgets.items():
        normalized_key = str(key).strip().title()
        if normalized_key in VALID_CATEGORIES:
            budgets[normalized_key] = get_budget_limit(value)

    if budgets != raw_budgets:
        state["budgets"] = budgets
        st.session_state.state = state
        save_state(state)

    # =====================================================
    # NO BUDGETS CASE
    # =====================================================
    if not budgets:
        st.markdown("""
        <div class="alert-warning">
            <strong>⚠️ No Budgets Set</strong><br>
            Set up your monthly budgets to start tracking overspending.
        </div>
        """, unsafe_allow_html=True)

        with st.expander("💰 Set Monthly Budgets", expanded=True):
            cols = st.columns(3)
            new_budgets = {}

            for idx, category in enumerate(sorted(VALID_CATEGORIES)):
                with cols[idx % 3]:
                    amt = st.number_input(
                        f"{category} (₹)",
                        min_value=0.0,
                        step=500.0,
                        key=f"new_budget_{category}"
                    )
                    if amt > 0:
                        new_budgets[category] = amt

            if st.button("💾 Save Budgets", use_container_width=True, type="primary"):
                if new_budgets:
                    state["budgets"] = new_budgets
                    st.session_state.state = state
                    save_state(state)
                    st.success("✅ Budgets activated!")
                    st.rerun()
                else:
                    st.error("Please add at least one budget")
        return

    # =====================================================
    # GET NORMALIZED EXPENSE TOTALS (CRITICAL FIX)
    # =====================================================
    try:
        raw_totals = get_expenses_by_category(state) or {}
    except Exception:
        raw_totals = {}

    category_totals = {}
    for k, v in raw_totals.items():
        normalized_key = str(k).strip().title()
        category_totals[normalized_key] = float(v)

    # =====================================================
    # BUDGET STATUS UI
    # =====================================================
    st.markdown(
        '<div class="subsection-header">💰 Budget Status</div>',
        unsafe_allow_html=True
    )

    cols = st.columns(3)
    alerts_list = []
    display_index = 0

    for category in sorted(budgets.keys()):
        with cols[display_index % 3]:
            display_index += 1

            budget_limit = budgets.get(category, 0.0)
            spent = category_totals.get(category, 0.0)

            utilization = (spent / budget_limit * 100) if budget_limit > 0 else 0.0
            remaining = budget_limit - spent

            # ============================
            # STATUS LOGIC
            # ============================
            if utilization >= 100:
                status_color = "#ef4444"
                status_text = "OVER BUDGET"
                progress_class = "progress-bar-danger"
                alerts_list.append((category, "critical", spent - budget_limit))

            elif utilization >= 80:
                status_color = "#f59e0b"
                status_text = "WARNING"
                progress_class = "progress-bar-warning"
                alerts_list.append((category, "warning", remaining))

            else:
                status_color = "#10b981"
                status_text = "ON TRACK"
                progress_class = ""

            html = f"""
            <div class="metric-card">
                <div style="display:flex;justify-content:space-between;align-items:start;margin-bottom:1rem;">
                    <div>
                        <div style="font-weight:800;font-size:1.2rem;">{category}</div>
                        <div style="font-size:0.85rem;color:{status_color};font-weight:700;">
                            {status_text}
                        </div>
                    </div>
                    <div style="font-size:1.8rem;font-weight:800;color:{status_color};">
                        {utilization:.0f}%
                    </div>
            """

            st.markdown(html, unsafe_allow_html=True)

    # =====================================================
    # ALERTS PANEL
    # =====================================================
    st.markdown("<br>", unsafe_allow_html=True)

    if alerts_list:
        st.markdown(
            '<div class="subsection-header">🚨 Active Alerts</div>',
            unsafe_allow_html=True
        )

        for category, severity, value in alerts_list:
            icon = "🚨" if severity == "critical" else "⚠️"
            st.markdown(f"""
            <div class="alert-warning">
                {icon} <strong>{category}</strong>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="alert-success">
            <strong>✅ All Budgets Under Control!</strong><br>
            Excellent financial discipline. Keep it going!
        </div>
        """, unsafe_allow_html=True)

    # =====================================================
    # EDIT BUDGETS
    # =====================================================
    with st.expander("✏️ Edit Budgets"):
        cols = st.columns(3)
        updated_budgets = {}
        edit_index = 0

        for category in sorted(budgets.keys()):
            with cols[edit_index % 3]:
                edit_index += 1
                updated_budgets[category] = st.number_input(
                    f"{category} (₹)",
                    min_value=0.0,
                    value=budgets[category],
                    step=500.0,
                    key=f"edit_budget_{category}"
                )

        if st.button("💾 Update Budgets", use_container_width=True):
            state["budgets"] = updated_budgets
            st.session_state.state = state
            save_state(state)
            st.success("✅ Budgets updated!")
            st.rerun()


# ============================================================================
# INSIGHTS PAGE
# ============================================================================

def render_insights():
    """Render AI-powered insights and recommendations."""
    st.markdown('<div class="section-header">🧠 AI Financial Insights</div>', unsafe_allow_html=True)

    state = st.session_state.state

    try:
        # Generate insights using InsightEngine
        expenses = get_all_expenses(state)
        budgets = state.get('budgets', {})

        transactions = [Transaction(**{
            'amount': e.get('amount', 0),
            'category': e.get('category', 'Other'),
            'description': e.get('description', ''),
            'date': e.get('date', datetime.now().strftime('%Y-%m-%d')),
            'merchant': e.get('merchant', e.get('description', ''))
        }) for e in expenses]

        budget_objs = [Budget(**{
            'category': cat,
            'limit': limit,
            'period': 'monthly'
        }) for cat, limit in budgets.items()]

        engine = InsightEngine(transactions, budget_objs)
        insights = engine.generate_insights()

        if insights:
            st.markdown('<div class="subsection-header">💡 Key Insights</div>', unsafe_allow_html=True)

            # Group insights by type
            anomalies = [i for i in insights if i.get('type') == 'anomaly']
            budget_alerts = [i for i in insights if i.get('type') == 'budget']
            patterns = [i for i in insights if i.get('type') == 'pattern']
            recommendations = [i for i in insights if i.get('type') == 'recommendation']

            # Display anomalies
            if anomalies:
                st.markdown("#### 🔍 Spending Anomalies")
                for insight in anomalies:
                    st.markdown(f"""
                    <div class="alert-warning">
                        <strong>Unusual Activity Detected</strong><br>
                        {insight.get('message', '')}
                    </div>
                    """, unsafe_allow_html=True)

            # Display budget alerts
            if budget_alerts:
                st.markdown("#### 💰 Budget Updates")
                for insight in budget_alerts:
                    severity = insight.get('severity', 'medium')
                    alert_class = f"alert-{severity}"
                    st.markdown(f"""
                    <div class="{alert_class}">
                        <strong>Budget Alert</strong><br>
                        {insight.get('message', '')}
                    </div>
                    """, unsafe_allow_html=True)

            # Display patterns
            if patterns:
                st.markdown("#### 📊 Spending Patterns")
                for insight in patterns:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div style="display: flex; align-items: start; gap: 1rem;">
                            <div style="font-size: 2rem;">📈</div>
                            <div style="flex: 1;">
                                <strong>{insight.get('title', 'Pattern Detected')}</strong><br>
                                <span style="color: #6b7280;">{insight.get('message', '')}</span>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

            # Display recommendations
            if recommendations:
                st.markdown("#### 🎯 Personalized Recommendations")
                for idx, insight in enumerate(recommendations, 1):
                    st.markdown(f"""
                    <div class="metric-card">
                        <div style="display: flex; align-items: start; gap: 1rem;">
                            <div style="background: linear-gradient(135deg, #667eea, #764ba2); color: white; width: 40px; height: 40px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 700; flex-shrink: 0;">
                                {idx}
                            </div>
                            <div style="flex: 1;">
                                <strong style="color: #667eea;">{insight.get('title', 'Recommendation')}</strong><br>
                                <span style="color: #374151;">{insight.get('message', '')}</span>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

        # Additional Insights
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="subsection-header">📈 Advanced Analytics</div>', unsafe_allow_html=True)

        col1, col2 = st.columns(2)

        with col1:
            # Spending velocity
            try:
                velocity = expense_velocity(state)
                st.markdown(f"""
                <div class="gradient-card">
                    <div style="font-size: 1.2rem; margin-bottom: 1rem;">Daily Spending Rate</div>
                    <div style="font-size: 2.5rem; font-weight: 800;">{format_currency(velocity)}</div>
                    <div style="font-size: 0.9rem; margin-top: 0.5rem; opacity: 0.9;">
                        At this rate, monthly spending: {format_currency(velocity * 30)}
                    </div>
                </div>
                """, unsafe_allow_html=True)
            except:
                pass

        with col2:
            # Top merchant
            try:
                merchants = top_merchants(state, n=3)
                if merchants:
                    st.markdown("""
                    <div class="gradient-card gradient-card-success">
                        <div style="font-size: 1.2rem; margin-bottom: 1rem;">Top Merchants</div>
                    """, unsafe_allow_html=True)

                    for merchant, amount in merchants:
                        st.markdown(f"""
                        <div style="display: flex; justify-content: space-between; padding: 0.5rem 0; border-bottom: 1px solid rgba(255,255,255,0.2);">
                            <span style="font-weight: 600;">{merchant[:20]}</span>
                            <span style="font-weight: 800;">{format_currency(amount)}</span>
                        </div>
                        """, unsafe_allow_html=True)

                    st.markdown("</div>", unsafe_allow_html=True)
            except:
                pass

    except Exception as e:
        st.markdown("""
        <div class="alert-info">
            <strong>🧠 AI Insights Pending</strong><br>
            Add more financial data to unlock personalized insights and recommendations.
        </div>
        """, unsafe_allow_html=True)


# ============================================================================
# SAVINGS GOALS PAGE
# ============================================================================
from datetime import datetime
import streamlit as st
from utils.storage import save_state
from utils.helpers import format_currency


def render_goals():
    st.markdown("# 🍎 Savings Goals")

    # =============================
    # LOAD STATE SAFELY
    # =============================
    state = st.session_state.state

    if "savings_goals" not in state or not isinstance(state["savings_goals"], list):
        state["savings_goals"] = []

    goals = state["savings_goals"]

    # =============================
    # CREATE GOAL
    # =============================
    with st.expander("➕ Create New Savings Goal"):
        with st.form("goal_form"):
            col1, col2 = st.columns(2)

            with col1:
                name = st.text_input("Goal Name")
                target = st.number_input("Target Amount (₹)", min_value=0.0, step=1000.0)
                current = st.number_input("Current Saved (₹)", min_value=0.0, step=500.0)

            with col2:
                deadline = st.date_input("Deadline", min_value=datetime.now().date())
                priority = st.selectbox("Priority", ["High", "Medium", "Low"])
                category = st.selectbox(
                    "Category",
                    ["Emergency Fund", "Vacation", "Education", "Purchase", "Retirement", "Other"]
                )

            submitted = st.form_submit_button("Create Goal", use_container_width=True)

            if submitted:
                if not name or target <= 0:
                    st.error("Please enter a goal name and valid target.")
                else:
                    state["savings_goals"].append({
                        # ✅ NEW STRUCTURE
                        "name": name,
                        "target": float(target),
                        "current": float(current),
                        "deadline": deadline.strftime("%Y-%m-%d"),
                        "priority": priority,
                        "category": category
                    })
                    save_state(state)
                    st.success("Goal created successfully!")
                    st.rerun()

    if not goals:
        st.info("🎯 No savings goals yet.")
        return

    # =============================
    # METRICS (BACKWARD SAFE)
    # =============================
    def get_target(g):
        return g.get("target") or g.get("target_amount", 0)

    def get_current(g):
        return g.get("current") or g.get("current_amount", 0)

    total_target = sum(get_target(g) for g in goals)
    total_saved = sum(get_current(g) for g in goals)
    overall_progress = (total_saved / total_target * 100) if total_target else 0

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Active Goals", len(goals))
    col2.metric("Total Target", format_currency(total_target))
    col3.metric("Total Saved", format_currency(total_saved))
    col4.metric("Overall Progress", f"{overall_progress:.1f}%")

    st.divider()

    # =============================
    # GOAL CARDS
    # =============================
    for g in goals:
        name = g.get("name", "Unnamed Goal")
        category = g.get("category", "Other")
        priority = g.get("priority", "Medium")

        target = get_target(g)
        current = get_current(g)

        remaining = max(target - current, 0)
        percent = min((current / target * 100) if target else 0, 100)

        try:
            deadline = datetime.strptime(g.get("deadline", ""), "%Y-%m-%d")
            days_left = max((deadline - datetime.now()).days, 0)
        except:
            days_left = 0

        monthly_required = remaining / max(days_left / 30, 1)

        st.markdown(f"""
        <div style="padding:1.5rem;border-radius:20px;background:#0f172a;margin-bottom:1rem;border:1px solid #1e293b;">
            <h3>{name}</h3>
            <small style="color:#9ca3af;">{category} • Priority: {priority}</small>
        </div>
        """, unsafe_allow_html=True)

        st.progress(percent / 100)

        c1, c2, c3 = st.columns(3)
        c1.metric("Saved", format_currency(current))
        c2.metric("Target", format_currency(target))
        c3.metric("Remaining", format_currency(remaining))

        st.caption(f"📅 {days_left} days left • Monthly needed: {format_currency(monthly_required)}")
        st.markdown("<br>", unsafe_allow_html=True)

# ============================================================================
# TAX INTELLIGENCE PAGE (CONTINUED)
# ============================================================================

def render_tax():
    """Render comprehensive tax analysis and optimization."""
    st.markdown('<div class="section-header">🧮 Tax Intelligence Center</div>', unsafe_allow_html=True)

    state = st.session_state.state

    # Tax tabs
    tab1, tab2, tab3 = st.tabs(["📊 Tax Estimation", "🔍 Missed Deductions", "💡 Tax Suggestions"])

    with tab1:
        st.markdown("### Tax Liability Estimation")

        try:
            tax_report = get_tax_estimation_report(state)

            # Display regime comparison
            old_regime = tax_report.get('old_regime', {})
            new_regime = tax_report.get('new_regime', {})
            recommendation = tax_report.get('recommendation', '')

            col1, col2 = st.columns(2)

            with col1:
                st.markdown("""
                <div class="gradient-card">
                    <div style="font-size: 1.3rem; font-weight: 700; margin-bottom: 1.5rem;">
                        📜 Old Tax Regime
                    </div>
                """, unsafe_allow_html=True)

                gross_income = old_regime.get('gross_income', 0)
                total_deductions = old_regime.get('total_deductions', 0)
                taxable_income = old_regime.get('taxable_income', 0)
                tax_liability = old_regime.get('tax_liability', 0)

                st.markdown(f"""
                    <div style="margin: 0.75rem 0;">
                        <strong>Gross Income:</strong> {format_currency(gross_income)}
                    </div>
                    <div style="margin: 0.75rem 0;">
                        <strong>Deductions:</strong> {format_currency(total_deductions)}
                    </div>
                    <div style="margin: 0.75rem 0;">
                        <strong>Taxable Income:</strong> {format_currency(taxable_income)}
                    </div>
                    <div style="margin: 1.5rem 0 0.5rem 0; padding-top: 1rem; border-top: 2px solid rgba(255,255,255,0.3);">
                        <strong style="font-size: 1.1rem;">Tax Liability:</strong>
                    </div>
                    <div style="font-size: 2.5rem; font-weight: 900;">
                        {format_currency(tax_liability)}
                    </div>
                </div>
                """, unsafe_allow_html=True)

            with col2:
                st.markdown("""
                <div class="gradient-card gradient-card-success">
                    <div style="font-size: 1.3rem; font-weight: 700; margin-bottom: 1.5rem;">
                        ✨ New Tax Regime
                    </div>
                """, unsafe_allow_html=True)

                gross_income_new = new_regime.get('gross_income', 0)
                taxable_income_new = new_regime.get('taxable_income', 0)
                tax_liability_new = new_regime.get('tax_liability', 0)

                st.markdown(f"""
                    <div style="margin: 0.75rem 0;">
                        <strong>Gross Income:</strong> {format_currency(gross_income_new)}
                    </div>
                    <div style="margin: 0.75rem 0;">
                        <strong>Deductions:</strong> Not Applicable
                    </div>
                    <div style="margin: 0.75rem 0;">
                        <strong>Taxable Income:</strong> {format_currency(taxable_income_new)}
                    </div>
                    <div style="margin: 1.5rem 0 0.5rem 0; padding-top: 1rem; border-top: 2px solid rgba(255,255,255,0.3);">
                        <strong style="font-size: 1.1rem;">Tax Liability:</strong>
                    </div>
                    <div style="font-size: 2.5rem; font-weight: 900;">
                        {format_currency(tax_liability_new)}
                    </div>
                </div>
                """, unsafe_allow_html=True)

            # Recommendation
            savings = abs(tax_liability - tax_liability_new)
            better_regime = "Old Regime" if tax_liability < tax_liability_new else "New Regime"

            st.markdown(f"""
            <div class="alert-success" style="margin-top: 1.5rem;">
                <div style="text-align: center;">
                    <strong style="font-size: 1.3rem;">🎯 Recommended: {better_regime}</strong><br>
                    <p style="margin-top: 1rem; font-size: 1.1rem;">
                        Save <strong style="color: #10b981;">{format_currency(savings)}</strong> by choosing this regime!
                    </p>
                    <p style="margin-top: 0.5rem; font-size: 0.9rem; opacity: 0.9;">
                        {recommendation}
                    </p>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Tax Slab Breakdown
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown('<div class="subsection-header">📋 Tax Slab Breakdown</div>', unsafe_allow_html=True)

            # Visual representation of tax slabs
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("**Old Regime Slabs**")
                slabs_old = old_regime.get('slab_breakdown', [])

                if slabs_old:
                    for slab in slabs_old:
                        st.markdown(f"""
                        <div class="metric-card" style="margin-bottom: 0.5rem;">
                            <div style="display: flex; justify-content: space-between;">
                                <span style="color: #6b7280;">{slab.get('range', '')}</span>
                                <span style="font-weight: 700; color: #667eea;">{format_currency(slab.get('tax', 0))}</span>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.info("No tax in this bracket")

            with col2:
                st.markdown("**New Regime Slabs**")
                slabs_new = new_regime.get('slab_breakdown', [])

                if slabs_new:
                    for slab in slabs_new:
                        st.markdown(f"""
                        <div class="metric-card" style="margin-bottom: 0.5rem;">
                            <div style="display: flex; justify-content: space-between;">
                                <span style="color: #6b7280;">{slab.get('range', '')}</span>
                                <span style="font-weight: 700; color: #10b981;">{format_currency(slab.get('tax', 0))}</span>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.info("No tax in this bracket")

            # Effective Tax Rate
            st.markdown("<br>", unsafe_allow_html=True)
            col1, col2, col3 = st.columns(3)

            with col1:
                effective_rate_old = (tax_liability / gross_income * 100) if gross_income > 0 else 0
                st.markdown(f"""
                <div class="metric-card" style="text-align: center;">
                    <div style="font-size: 2rem; font-weight: 800; color: #667eea;">
                        {effective_rate_old:.2f}%
                    </div>
                    <div style="color: #6b7280; margin-top: 0.5rem;">Old Regime ETR</div>
                </div>
                """, unsafe_allow_html=True)

            with col2:
                effective_rate_new = (tax_liability_new / gross_income_new * 100) if gross_income_new > 0 else 0
                st.markdown(f"""
                <div class="metric-card" style="text-align: center;">
                    <div style="font-size: 2rem; font-weight: 800; color: #10b981;">
                        {effective_rate_new:.2f}%
                    </div>
                    <div style="color: #6b7280; margin-top: 0.5rem;">New Regime ETR</div>
                </div>
                """, unsafe_allow_html=True)

            with col3:
                take_home_old = gross_income - tax_liability
                st.markdown(f"""
                <div class="metric-card" style="text-align: center;">
                    <div style="font-size: 1.5rem; font-weight: 800; color: #3b82f6;">
                        {format_large_number(take_home_old)}
                    </div>
                    <div style="color: #6b7280; margin-top: 0.5rem;">Take Home (Old)</div>
                </div>
                """, unsafe_allow_html=True)

        except Exception as e:
            st.markdown("""
            <div class="alert-warning">
                <strong>⚠️ Unable to Calculate Tax</strong><br>
                Please ensure your income and deductions data is properly configured.
            </div>
            """, unsafe_allow_html=True)

            # Quick setup guide
            with st.expander("📝 Setup Tax Profile"):
                st.markdown("**Configure your income and deductions:**")

                annual_income = st.number_input("Annual Income (₹)", min_value=0.0, step=50000.0)

                st.markdown("**Deductions (80C, 80D, etc.)**")
                section_80c = st.number_input("Section 80C (₹)", min_value=0.0, max_value=150000.0, step=10000.0)
                section_80d = st.number_input("Section 80D (₹)", min_value=0.0, max_value=50000.0, step=5000.0)
                hra = st.number_input("HRA Exemption (₹)", min_value=0.0, step=10000.0)

                if st.button("💾 Save Tax Profile", use_container_width=True):
                    state['income'] = {'annual': annual_income, 'monthly': annual_income / 12}
                    state['deductions'] = {
                        '80C': section_80c,
                        '80D': section_80d,
                        'HRA': hra
                    }
                    st.session_state.state = state
                    save_state(state)
                    st.success("✅ Tax profile saved!")
                    st.rerun()

    with tab2:
        st.markdown("### 🔍 Missed Tax Deductions")

        try:
            blindspot_report = get_tax_blindspot_report(state)

            missed_deductions = blindspot_report.get('missed_deductions', [])
            potential_savings = blindspot_report.get('total_potential_savings', 0)

            # Savings overview
            if potential_savings > 0:
                st.markdown(f"""
                <div class="gradient-card gradient-card-warning" style="text-align: center;">
                    <div style="font-size: 1.3rem; margin-bottom: 1rem;">💰 Potential Tax Savings</div>
                    <div style="font-size: 3rem; font-weight: 900;">
                        {format_large_number(potential_savings)}
                    </div>
                    <div style="font-size: 1rem; margin-top: 1rem; opacity: 0.95;">
                        You could save this much by claiming missed deductions!
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div class="alert-success">
                    <strong>✅ Great Job!</strong><br>
                    You're utilizing all available deductions. No missed opportunities detected!
                </div>
                """, unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)

            # Display missed deductions
            if missed_deductions:
                st.markdown('<div class="subsection-header">📋 Unclaimed Deductions</div>', unsafe_allow_html=True)

                for idx, deduction in enumerate(missed_deductions, 1):
                    section = deduction.get('section', 'Unknown')
                    description = deduction.get('description', '')
                    max_limit = deduction.get('max_limit', 0)
                    estimated_savings = deduction.get('estimated_savings', 0)
                    priority = deduction.get('priority', 'Medium')

                    priority_colors = {
                        'High': '#ef4444',
                        'Medium': '#f59e0b',
                        'Low': '#3b82f6'
                    }
                    priority_color = priority_colors.get(priority, '#6b7280')

                    st.markdown(f"""
                    <div class="metric-card">
                        <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 1rem;">
                            <div style="flex: 1;">
                                <div style="display: flex; align-items: center; gap: 1rem; margin-bottom: 0.5rem;">
                                    <div style="background: linear-gradient(135deg, #667eea, #764ba2); color: white; width: 35px; height: 35px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 700;">
                                        {idx}
                                    </div>
                                    <div style="font-size: 1.3rem; font-weight: 800; color: #1f2937;">
                                        Section {section}
                                    </div>
                                    <div style="background: {priority_color}; color: white; padding: 0.25rem 0.75rem; border-radius: 20px; font-size: 0.8rem; font-weight: 600;">
                                        {priority} Priority
                                    </div>
                                </div>
                                <div style="color: #6b7280; font-size: 0.95rem; line-height: 1.6; margin-top: 0.5rem;">
                                    {description}
                                </div>
                            </div>
                        </div>

                        <div style="display: flex; justify-content: space-between; align-items: center; padding-top: 1rem; border-top: 1px solid #e5e7eb;">
                            <div>
                                <div style="font-size: 0.85rem; color: #6b7280; margin-bottom: 0.25rem;">Max Deduction Limit</div>
                                <div style="font-size: 1.3rem; font-weight: 800; color: #667eea;">
                                    {format_currency(max_limit)}
                                </div>
                            </div>
                            <div style="text-align: right;">
                                <div style="font-size: 0.85rem; color: #6b7280; margin-bottom: 0.25rem;">Potential Savings</div>
                                <div style="font-size: 1.3rem; font-weight: 800; color: #10b981;">
                                    {format_currency(estimated_savings)}
                                </div>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                # Action items
                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown("""
                <div class="alert-info">
                    <strong>💡 Quick Actions:</strong><br>
                    <ul style="margin-top: 0.5rem; padding-left: 1.5rem;">
                        <li>Collect bills and receipts for eligible expenses</li>
                        <li>Consult with a tax advisor for personalized guidance</li>
                        <li>File revised return if within the deadline</li>
                        <li>Plan investments for next financial year</li>
                    </ul>
                </div>
                """, unsafe_allow_html=True)

            else:
                st.info("No missed deductions detected based on current data")

        except Exception as e:
            st.error(f"Error analyzing tax deductions: {str(e)}")

    with tab3:
        st.markdown("### 💡 Smart Tax Suggestions")

        try:
            suggestions_report = get_tax_suggestions_report(state)

            suggestions = suggestions_report.get('suggestions', [])
            tax_efficiency_score = suggestions_report.get('tax_efficiency_score', 0)

            # Tax efficiency score
            col1, col2, col3 = st.columns([1, 2, 1])

            with col2:
                score_color = health_score_color(tax_efficiency_score)
                grade = 'Excellent' if tax_efficiency_score >= 80 else 'Good' if tax_efficiency_score >= 60 else 'Fair' if tax_efficiency_score >= 40 else 'Poor'

                st.markdown(f"""
                <div class="gradient-card" style="text-align: center;">
                    <div style="font-size: 1.2rem; margin-bottom: 1rem;">Tax Efficiency Score</div>
                    <div style="font-size: 5rem; font-weight: 900; color: white;">
                        {tax_efficiency_score}
                    </div>
                    <div style="font-size: 1.2rem; margin-top: 1rem; opacity: 0.95;">
                        {grade}
                    </div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)

            # Display suggestions
            if suggestions:
                st.markdown('<div class="subsection-header">🎯 Personalized Recommendations</div>',
                            unsafe_allow_html=True)

                for idx, suggestion in enumerate(suggestions, 1):
                    title = suggestion.get('title', 'Tax Tip')
                    description = suggestion.get('description', '')
                    impact = suggestion.get('impact', 'Medium')
                    action_items = suggestion.get('action_items', [])

                    impact_colors = {
                        'High': 'linear-gradient(135deg, #10b981, #059669)',
                        'Medium': 'linear-gradient(135deg, #3b82f6, #1d4ed8)',
                        'Low': 'linear-gradient(135deg, #6b7280, #4b5563)'
                    }
                    impact_color = impact_colors.get(impact, impact_colors['Medium'])

                    st.markdown(f"""
                    <div class="metric-card" style="border-left: 5px solid #667eea;">
                        <div style="display: flex; gap: 1rem; margin-bottom: 1rem;">
                            <div style="background: {impact_color}; color: white; width: 50px; height: 50px; border-radius: 12px; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 1.5rem; flex-shrink: 0;">
                                {idx}
                            </div>
                            <div style="flex: 1;">
                                <div style="font-size: 1.2rem; font-weight: 800; color: #1f2937; margin-bottom: 0.5rem;">
                                    {title}
                                </div>
                                <div style="display: inline-block; background: {impact_color}; color: white; padding: 0.25rem 0.75rem; border-radius: 20px; font-size: 0.8rem; font-weight: 600;">
                                    {impact} Impact
                                </div>
                            </div>
                        </div>

                        <div style="color: #374151; font-size: 0.95rem; line-height: 1.7; margin-bottom: 1rem;">
                            {description}
                        </div>
                    """, unsafe_allow_html=True)

                    if action_items:
                        st.markdown("""
                        <div style="background: #f9fafb; border-radius: 8px; padding: 1rem; margin-top: 1rem;">
                            <div style="font-weight: 700; color: #667eea; margin-bottom: 0.75rem;">📝 Action Steps:</div>
                            <ul style="margin: 0; padding-left: 1.5rem; color: #374151;">
                        """, unsafe_allow_html=True)

                        for action in action_items:
                            st.markdown(f"<li style='margin: 0.5rem 0;'>{action}</li>", unsafe_allow_html=True)

                        st.markdown("</ul></div>", unsafe_allow_html=True)

                    st.markdown("</div>", unsafe_allow_html=True)

            # Tax calendar/deadlines
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown('<div class="subsection-header">📅 Important Tax Deadlines</div>', unsafe_allow_html=True)

            deadlines = [
                {'date': 'July 31', 'event': 'ITR Filing (Individuals)', 'status': 'Upcoming'},
                {'date': 'June 15', 'event': 'Advance Tax Q1', 'status': 'Upcoming'},
                {'date': 'September 15', 'event': 'Advance Tax Q2', 'status': 'Upcoming'},
                {'date': 'December 15', 'event': 'Advance Tax Q3', 'status': 'Upcoming'},
                {'date': 'March 15', 'event': 'Advance Tax Q4', 'status': 'Upcoming'}
            ]

            cols = st.columns(2)
            for idx, deadline in enumerate(deadlines[:4]):
                with cols[idx % 2]:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div>
                                <div style="font-size: 1.1rem; font-weight: 700; color: #667eea;">
                                    📅 {deadline['date']}
                                </div>
                                <div style="color: #6b7280; font-size: 0.9rem; margin-top: 0.25rem;">
                                    {deadline['event']}
                                </div>
                            </div>
                            <div style="background: #fef3c7; color: #f59e0b; padding: 0.5rem 1rem; border-radius: 20px; font-size: 0.85rem; font-weight: 600;">
                                {deadline['status']}
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

        except Exception as e:
            st.info("Configure your tax profile to receive personalized suggestions")


# ============================================================================
# WHAT-IF SIMULATOR PAGE
# ============================================================================

def render_simulator():
    """Render advanced financial what-if simulator."""
    st.markdown('<div class="section-header">🔮 What-If Financial Simulator</div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="alert-info">
        <strong>🎯 Scenario Planning Tool</strong><br>
        Model different financial scenarios to understand their impact on your health score, 
        stress index, savings goals, and tax liability. Make informed decisions with confidence!
    </div>
    """, unsafe_allow_html=True)

    state = st.session_state.state

    st.markdown("<br>", unsafe_allow_html=True)

    # Baseline metrics
    st.markdown('<div class="subsection-header">📊 Current Baseline</div>', unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)

    try:
        health_report = calculate_financial_health_score(state)
        baseline_health = health_report.get('health_score', 0)
    except:
        baseline_health = 0

    try:
        stress_report = calculate_financial_stress_index(state)
        baseline_stress = stress_report.get('stress_index', 0)
    except:
        baseline_stress = 0

    baseline_income = state.get('monthly_income', 0) or state.get('income', {}).get('monthly', 0)

    try:
        now = datetime.now()
        summary = monthly_expense_summary(state, now.year, now.month)
        baseline_expenses = summary.get('total_expenses', 0)
    except:
        baseline_expenses = 0

    with col1:
        st.markdown(f"""
        <div class="metric-card" style="text-align: center;">
            <div style="font-size: 2rem; font-weight: 800; color: {health_score_color(baseline_health)};">
                {baseline_health}
            </div>
            <div style="color: #6b7280; margin-top: 0.5rem; font-size: 0.9rem;">Health Score</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="metric-card" style="text-align: center;">
            <div style="font-size: 2rem; font-weight: 800; color: #ef4444;">
                {baseline_stress}
            </div>
            <div style="color: #6b7280; margin-top: 0.5rem; font-size: 0.9rem;">Stress Index</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="metric-card" style="text-align: center;">
            <div style="font-size: 1.5rem; font-weight: 800; color: #10b981;">
                {format_large_number(baseline_income)}
            </div>
            <div style="color: #6b7280; margin-top: 0.5rem; font-size: 0.9rem;">Monthly Income</div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
        <div class="metric-card" style="text-align: center;">
            <div style="font-size: 1.5rem; font-weight: 800; color: #ef4444;">
                {format_large_number(baseline_expenses)}
            </div>
            <div style="color: #6b7280; margin-top: 0.5rem; font-size: 0.9rem;">Monthly Expenses</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Simulation controls
    st.markdown('<div class="subsection-header">🎚️ Adjust Variables</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**💰 Income Changes**")
        income_change = st.slider(
            "Income Change (%)",
            min_value=-50,
            max_value=100,
            value=0,
            step=5,
            help="Simulate salary increase/decrease or bonus"
        )

        st.markdown("**💳 New EMI/Debt**")
        new_emi = st.number_input(
            "Additional Monthly EMI (₹)",
            min_value=0.0,
            max_value=100000.0,
            step=1000.0,
            help="Add new loan EMI to see impact"
        )

    with col2:
        st.markdown("**💸 Expense Changes**")
        expense_change = st.slider(
            "Expense Change (%)",
            min_value=-50,
            max_value=100,
            value=0,
            step=5,
            help="Simulate lifestyle changes or cost-cutting"
        )

        st.markdown("**💎 Investment Addition**")
        new_investment = st.number_input(
            "Monthly Investment (₹)",
            min_value=0.0,
            max_value=100000.0,
            step=1000.0,
            help="Add recurring investment amount"
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # Run simulation button
    if st.button("🚀 Run Simulation", use_container_width=True, type="primary"):
        try:
            # Build scenario parameters
            scenario = {
                'income_change': income_change,
                'expense_change': expense_change,
                'new_emi': new_emi,
                'new_investment': new_investment
            }

            # Run simulation
            simulation_result = run_simulation(state, scenario)

            # Display results
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown('<div class="subsection-header">📈 Simulation Results</div>', unsafe_allow_html=True)

            # Impact summary
            new_health = simulation_result.get('health_score', baseline_health)
            new_stress = simulation_result.get('stress_index', baseline_stress)
            new_income = simulation_result.get('new_income', baseline_income)
            new_expenses = simulation_result.get('new_expenses', baseline_expenses)

            health_change = new_health - baseline_health
            stress_change = new_stress - baseline_stress

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                health_arrow = "⬆️" if health_change > 0 else "⬇️" if health_change < 0 else "➡️"
                health_color = "#10b981" if health_change > 0 else "#ef4444" if health_change < 0 else "#6b7280"

                st.markdown(f"""
                <div class="gradient-card">
                    <div style="text-align: center;">
                        <div style="font-size: 2.5rem; font-weight: 900;">
                            {new_health}
                        </div>
                        <div style="font-size: 1rem; margin-top: 0.5rem; opacity: 0.9;">New Health Score</div>
                        <div style="font-size: 1.2rem; margin-top: 0.75rem; color: {health_color}; font-weight: 700;">
                            {health_arrow} {abs(health_change):.1f}
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

            with col2:
                stress_arrow = "⬇️" if stress_change < 0 else "⬆️" if stress_change > 0 else "➡️"
                stress_color = "#10b981" if stress_change < 0 else "#ef4444" if stress_change > 0 else "#6b7280"

                st.markdown(f"""
                <div class="gradient-card gradient-card-warning">
                    <div style="text-align: center;">
                        <div style="font-size: 2.5rem; font-weight: 900;">
                            {new_stress}
                        </div>
                        <div style="font-size: 1rem; margin-top: 0.5rem; opacity: 0.9;">New Stress Index</div>
                        <div style="font-size: 1.2rem; margin-top: 0.75rem; color: {stress_color}; font-weight: 700;">
                            {stress_arrow} {abs(stress_change):.1f}
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

            with col3:
                income_diff = new_income - baseline_income
                st.markdown(f"""
                <div class="gradient-card gradient-card-success">
                    <div style="text-align: center;">
                        <div style="font-size: 1.8rem; font-weight: 900;">
                            {format_large_number(new_income)}
                        </div>
                        <div style="font-size: 1rem; margin-top: 0.5rem; opacity: 0.9;">New Income</div>
                        <div style="font-size: 1rem; margin-top: 0.75rem; font-weight: 700;">
                            {'⬆️' if income_diff > 0 else '⬇️' if income_diff < 0 else '➡️'} {format_currency(abs(income_diff))}
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

            with col4:
                expense_diff = new_expenses - baseline_expenses
                st.markdown(f"""
                <div class="gradient-card">
                    <div style="text-align: center;">
                        <div style="font-size: 1.8rem; font-weight: 900;">
                            {format_large_number(new_expenses)}
                        </div>
                        <div style="font-size: 1rem; margin-top: 0.5rem; opacity: 0.9;">New Expenses</div>
                        <div style="font-size: 1rem; margin-top: 0.75rem; font-weight: 700;">
                            {'⬆️' if expense_diff > 0 else '⬇️' if expense_diff < 0 else '➡️'} {format_currency(abs(expense_diff))}
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

            # Detailed impact analysis
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown('<div class="subsection-header">🔍 Detailed Impact Analysis</div>', unsafe_allow_html=True)

            col1, col2 = st.columns(2)

            with col1:
                # Financial metrics
                new_savings = new_income - new_expenses
                old_savings = baseline_income - baseline_expenses
                savings_diff = new_savings - old_savings

                new_savings_rate = (new_savings / new_income * 100) if new_income > 0 else 0
                old_savings_rate = (old_savings / baseline_income * 100) if baseline_income > 0 else 0

                st.markdown(f"""
                <div class="metric-card">
                    <div style="font-weight: 700; color: #667eea; font-size: 1.2rem; margin-bottom: 1rem;">
                        💰 Financial Impact
                    </div>

                    <div style="display: flex; justify-content: space-between; margin: 0.75rem 0; padding: 0.5rem; background: #f9fafb; border-radius: 8px;">
                        <span>Monthly Savings:</span>
                        <span style="font-weight: 700; color: {'#10b981' if new_savings > 0 else '#ef4444'};">
                            {format_currency(new_savings)}
                        </span>
                    </div>

                    <div style="display: flex; justify-content: space-between; margin: 0.75rem 0; padding: 0.5rem; background: #f9fafb; border-radius: 8px;">
                        <span>Savings Rate:</span>
                        <span style="font-weight: 700; color: {'#10b981' if new_savings_rate >= 20 else '#f59e0b' if new_savings_rate >= 10 else '#ef4444'};">
                            {new_savings_rate:.1f}%
                        </span>
                    </div>

                    <div style="display: flex; justify-content: space-between; margin: 0.75rem 0; padding: 0.5rem; background: #f9fafb; border-radius: 8px;">
                        <span>Change vs Baseline:</span>
                        <span style="font-weight: 700; color: {'#10b981' if savings_diff > 0 else '#ef4444' if savings_diff < 0 else '#6b7280'};">
                            {format_currency(savings_diff)}
                        </span>
                    </div>

                    <div style="display: flex; justify-content: space-between; margin: 0.75rem 0; padding: 0.5rem; background: #f9fafb; border-radius: 8px;">
                        <span>Annual Savings:</span>
                        <span style="font-weight: 700; color: #667eea;">
                            {format_large_number(new_savings * 12)}
                        </span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

            with col2:
                # Recommendations based on simulation
                st.markdown("""
                <div class="metric-card">
                    <div style="font-weight: 700; color: #667eea; font-size: 1.2rem; margin-bottom: 1rem;">
                        💡 Key Insights
                    </div>
                """, unsafe_allow_html=True)

                insights = []

                if health_change > 5:
                    insights.append("✅ This scenario significantly improves your financial health!")
                elif health_change < -5:
                    insights.append("⚠️ Warning: This scenario may harm your financial health.")
                else:
                    insights.append("➡️ Neutral impact on overall financial health.")

                if stress_change < -10:
                    insights.append("✅ Great news! This reduces financial stress considerably.")
                elif stress_change > 10:
                    insights.append("⚠️ This scenario increases financial stress levels.")

                if new_savings_rate >= 30:
                    insights.append("🎯 Excellent savings rate! You're on track for financial independence.")
                elif new_savings_rate >= 20:
                    insights.append("👍 Good savings rate. Consider increasing slightly.")
                elif new_savings_rate < 10:
                    insights.append("📉 Low savings rate. Focus on expense reduction.")

                if new_emi > 0:
                    debt_burden = (new_emi / new_income * 100) if new_income > 0 else 0
                    if debt_burden > 40:
                        insights.append("🚨 New EMI creates high debt burden! Reconsider or increase income.")
                    else:
                        insights.append(f"💳 New EMI is manageable ({debt_burden:.1f}% of income).")

                for insight in insights:
                    st.markdown(f"""
                    <div style="padding: 0.75rem; margin: 0.5rem 0; background: #f9fafb; border-radius: 8px; border-left: 3px solid #667eea;">
                        {insight}
                    </div>
                    """, unsafe_allow_html=True)

                st.markdown("</div>", unsafe_allow_html=True)

            # Comparison chart
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown('<div class="subsection-header">📊 Before vs After Comparison</div>', unsafe_allow_html=True)

            fig = go.Figure()

            metrics = ['Health Score', 'Stress Index', 'Savings Rate']
            baseline_values = [baseline_health, baseline_stress, old_savings_rate]
            new_values = [new_health, new_stress, new_savings_rate]

            fig.add_trace(go.Bar(
                name='Current',
                x=metrics,
                y=baseline_values,
                marker_color='#6b7280',
                text=[f"{v:.1f}" for v in baseline_values],
                textposition='outside'
            ))

            fig.add_trace(go.Bar(
                name='After Simulation',
                x=metrics,
                y=new_values,
                marker_color='#667eea',
                text=[f"{v:.1f}" for v in new_values],
                textposition='outside'
            ))

            fig.update_layout(
                paper_bgcolor='rgba(255,255,255,0.95)',
                plot_bgcolor='rgba(0,0,0,0)',
                height=400,
                barmode='group',
                showlegend=True,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                font=dict(family='Inter', size=13),
                yaxis=dict(title="Score / %", gridcolor='rgba(200,200,200,0.2)'),
                xaxis=dict(showgrid=False)
            )

            st.plotly_chart(fig, use_container_width=True)

        except Exception as e:
            st.error(f"Simulation error: {str(e)}")
            st.info("Please ensure you have sufficient financial data entered for accurate simulation.")

    else:
        st.markdown("""
        <div class="metric-card" style="text-align: center; padding: 3rem;">
            <div style="font-size: 4rem; margin-bottom: 1rem;">🎯</div>
            <div style="font-size: 1.3rem; font-weight: 700; color: #1f2937;">
                Adjust the sliders above and click "Run Simulation"
            </div>
            <div style="color: #6b7280; margin-top: 0.5rem;">
                See how different financial decisions impact your future
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Pre-built scenarios
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="subsection-header">🎭 Quick Scenarios</div>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("💼 Job Switch (+20% Income)", use_container_width=True):
            st.info("Set Income Change to +20% and run simulation")

    with col2:
        if st.button("🏠 Aggressive Savings (-30% Expenses)", use_container_width=True):
            st.info("Set Expense Change to -30% and run simulation")

    with col3:
        if st.button("🚗 New Car Loan (₹25K EMI)", use_container_width=True):
            st.info("Set New EMI to 25000 and run simulation")


# ============================================================================
# MAIN APP CONTROLLER
# ============================================================================

def main():
    """Main application controller."""
    inject_global_css()
    # Render sidebar
    render_sidebar()

    # Route to appropriate page based on session state
    page = st.session_state.current_page

    if page == "Dashboard":
        render_dashboard()
    elif page == "Expenses":
        render_expenses()
    elif page == "Health":
        render_health()
    elif page == "Overspending":
        render_overspending()
    elif page == "Insights":
        render_insights()
    elif page == "Goals":
        render_goals()
    elif page == "Tax":
        render_tax()
    elif page == "Simulator":
        render_simulator()
    else:
        render_dashboard()

    # Footer
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("""
    <div style="text-align: center; opacity: 0.6; padding: 2rem 0; color: white;">
        <div style="font-size: 0.9rem; margin-bottom: 0.5rem;">
            MonetIQ - AI-Powered Financial Intelligence Platform
        </div>
        <div style="font-size: 0.8rem;">
            Made with ❤️ for smarter financial decisions
        </div>
    </div>
    """, unsafe_allow_html=True)


# ============================================================================
# RUN APPLICATION
# ============================================================================

if __name__ == "__main__":
    main()