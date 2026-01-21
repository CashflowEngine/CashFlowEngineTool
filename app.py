import streamlit as st
import pandas as pd
import ui_components as ui
import database as db
import calculations as calc

# Import page modules
import pages.login as login
import pages.landing as landing
import pages.portfolio_analytics as portfolio_analytics
import pages.portfolio_builder as portfolio_builder
import pages.monte_carlo as monte_carlo
import pages.comparison as comparison
import pages.meic_analysis as meic_analysis
import pages.meic_optimizer as meic_optimizer
import pages.ai_analyst as ai_analyst

# --- 1. CONFIGURATION ---
st.set_page_config(
    page_title="Cashflow Engine", 
    page_icon="⚡", 
    layout="wide",
    initial_sidebar_state="expanded" 
)

# --- 2. CORPORATE IDENTITY CSS ---
st.markdown("""
<style>
    /* IMPORT FONTS - FULL WEIGHTS */
    @import url('https://fonts.googleapis.com/css2?family=Exo+2:ital,wght@0,100..900;1,100..900&family=Poppins:wght@300;400;500;600;700&display=swap');

    /* --- TYPOGRAPHY --- */

    /* Force Poppins for All Body Text */
    * {
        font-family: 'Poppins', sans-serif;
    }

    html, body, [class*="css"], .stMarkdown, .stText, p, div, span, label, input, .stDataFrame, .stTable, .stSelectbox, .stNumberInput, button {
        font-family: 'Poppins', sans-serif !important;
        color: #4B5563;
    }

    /* Force Exo 2 for ALL Headings - More specific selectors */
    h1, h2, h3, h4, h5, h6,
    .card-title,
    .stHeading,
    [data-testid="stMarkdownContainer"] h1,
    [data-testid="stMarkdownContainer"] h2,
    [data-testid="stMarkdownContainer"] h3,
    .stMetricValue,
    .page-header,
    .section-title {
        font-family: 'Exo 2', sans-serif !important;
        text-transform: uppercase !important;
        letter-spacing: 0.5px !important;
        color: #4B5563 !important;
        font-weight: 800 !important;
    }

    /* Tagline styling - ensure Exo 2 */
    .tagline, .tagline h2, .tagline span {
        font-family: 'Exo 2', sans-serif !important;
        font-weight: 800 !important;
        text-transform: uppercase !important;
    }

    /* Specific overrides for Streamlit elements to ensure font sticks */
    .stMetricLabel { font-family: 'Poppins', sans-serif !important; font-weight: 600 !important; }

    /* --- SIDEBAR TOGGLE FIX --- */
    /* Hide all text in the toggle button, show only the icon */
    button[kind="header"] {
        color: transparent !important;
        overflow: hidden;
    }
    button[kind="header"] * {
        color: transparent !important;
    }
    button[kind="header"] svg {
        fill: #4B5563 !important;
        color: #4B5563 !important;
    }
    /* Ensure the collapse button doesn't show text */
    [data-testid="collapsedControl"] {
        color: transparent !important;
    }
    [data-testid="collapsedControl"] span,
    [data-testid="collapsedControl"] p {
        display: none !important;
    }

    /* --- NAVIGATION BAR REDESIGN --- */
    [data-testid="stSidebarNav"] { display: none !important; }

    section[data-testid="stSidebar"] {
        background-color: #F9FAFB;
        border-right: 1px solid #E5E7EB;
    }

    section[data-testid="stSidebar"] .stRadio div[role="radiogroup"] {
        gap: 4px;
        padding: 0 8px;
    }

    section[data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label {
        background-color: transparent;
        border: 1px solid transparent;
        border-radius: 8px;
        padding: 10px 12px;
        margin-bottom: 2px;
        color: #6B7280;
        font-family: 'Poppins', sans-serif !important;
        font-weight: 500;
        font-size: 13px;
        cursor: pointer;
        transition: all 0.2s ease;
        display: flex;
        align-items: center;
        box-shadow: none;
    }

    section[data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label:hover {
        background-color: #FFFFFF;
        color: #302BFF;
        border-color: #E5E7EB;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
    }

    /* Active/Selected menu item - improved styling */
    section[data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label[data-checked="true"],
    section[data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label[aria-checked="true"] {
        background-color: #302BFF !important;
        color: #FFFFFF !important;
        font-weight: 600 !important;
        border: none !important;
        box-shadow: 0 4px 6px rgba(48, 43, 255, 0.15) !important;
    }

    section[data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label[data-checked="true"] span,
    section[data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label[aria-checked="true"] span {
        color: #FFFFFF !important;
    }

    /* Hide the radio button circle */
    section[data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label > div:first-child {
        display: none;
    }

    section[data-testid="stSidebar"] .block-container {
        padding-top: 2rem;
        padding-bottom: 5rem;
    }

    /* Expander styling - remove icon garble */
    .streamlit-expanderHeader {
        font-family: 'Poppins', sans-serif !important;
        font-weight: 600 !important;
        font-size: 13px !important;
        color: #4B5563 !important;
    }

    /* Hide expander icons that cause garbled text */
    .streamlit-expanderHeader svg {
        display: inline-block !important;
    }

    /* Fix any material icon issues */
    .material-icons, .material-symbols-outlined {
        font-family: 'Material Icons' !important;
    }

    /* --- UI ELEMENTS --- */

    /* PRIMARY BUTTONS - Blue Background with WHITE Text (CRITICAL!) */
    div.stButton > button,
    div.stButton > button[kind="primary"],
    div.stButton > button:not([kind="tertiary"]):not([kind="secondary"]),
    .stButton button[type="primary"] {
        background-color: #302BFF !important;
        color: #FFFFFF !important;
        font-family: 'Poppins', sans-serif !important;
        font-weight: 600 !important;
        text-transform: uppercase;
        border: none !important;
        border-radius: 6px;
        padding: 0.5rem 1.0rem;
        box-shadow: 0 4px 6px rgba(48, 43, 255, 0.2);
        transition: all 0.2s ease;
        letter-spacing: 0.5px;
        font-size: 13px;
    }

    /* Force white text on ALL children of primary buttons */
    div.stButton > button span,
    div.stButton > button p,
    div.stButton > button div,
    div.stButton > button[kind="primary"] span,
    div.stButton > button[kind="primary"] p,
    div.stButton > button:not([kind="tertiary"]):not([kind="secondary"]) span,
    div.stButton > button:not([kind="tertiary"]):not([kind="secondary"]) p {
        color: #FFFFFF !important;
    }

    div.stButton > button:hover,
    div.stButton > button[kind="primary"]:hover,
    div.stButton > button:not([kind="tertiary"]):not([kind="secondary"]):hover {
        background-color: #2521c9 !important;
        box-shadow: 0 6px 12px rgba(48, 43, 255, 0.3);
        color: #FFFFFF !important;
    }

    /* TERTIARY BUTTONS - Text Links (blue, underlined on hover) */
    div.stButton > button[kind="tertiary"],
    button[kind="tertiary"] {
        background-color: transparent !important;
        border: none !important;
        color: #302BFF !important;
        box-shadow: none !important;
        text-decoration: none !important;
        padding: 8px 0 !important;
        font-weight: 500 !important;
        text-transform: none !important;
        font-size: 14px !important;
        font-family: 'Poppins', sans-serif !important;
    }

    div.stButton > button[kind="tertiary"] span,
    div.stButton > button[kind="tertiary"] p,
    button[kind="tertiary"] span {
        color: #302BFF !important;
    }

    div.stButton > button[kind="tertiary"]:hover,
    button[kind="tertiary"]:hover {
        color: #2521c9 !important;
        text-decoration: underline !important;
        background-color: transparent !important;
        box-shadow: none !important;
    }

    /* SECONDARY BUTTONS - Outlined style */
    button[kind="secondary"] {
        background-color: transparent !important;
        border: 1px solid #302BFF !important;
        color: #302BFF !important;
        box-shadow: none !important;
        padding: 0.5rem 1.0rem !important;
        font-weight: 600 !important;
        text-transform: uppercase !important;
        border-radius: 6px !important;
    }

    button[kind="secondary"]:hover {
        background-color: #302BFF !important;
        color: #FFFFFF !important;
    }

    .ghost-link {
        color: #9CA3AF;
        font-size: 12px;
        font-weight: 500;
        font-family: 'Poppins', sans-serif;
        font-style: italic;
        text-align: center;
        margin-top: 10px;
    }

    /* Coming Soon Badge */
    .coming-soon-badge {
        display: inline-block;
        background-color: #E5E7EB;
        color: #6B7280;
        font-size: 9px;
        font-weight: 600;
        padding: 2px 6px;
        border-radius: 4px;
        margin-left: 8px;
        text-transform: uppercase;
    }

    /* Beta Badge */
    .beta-badge {
        display: inline-block;
        background-color: #FEF3C7;
        color: #D97706;
        font-size: 9px;
        font-weight: 600;
        padding: 2px 6px;
        border-radius: 4px;
        margin-left: 8px;
        text-transform: uppercase;
    }

    /* --- LAYOUTS --- */

    .stApp { background-color: #FFFFFF; }

    div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #FFFFFF;
        border: 1px solid #E5E7EB;
        border-radius: 12px;
        padding: 24px;
        margin-bottom: 24px;
    }

    /* KPI Cards */
    .hero-card {
        padding: 16px 12px;
        border-radius: 8px;
        text-align: center;
        margin-bottom: 8px;
        border: 1px solid #E5E7EB;
        background-color: #FFFFFF;
        height: 140px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
    }

    .hero-label {
        font-size: 11px !important;
        text-transform: uppercase;
        letter-spacing: 1px;
        font-weight: 600 !important;
        margin-bottom: 8px;
        color: #6B7280;
        font-family: 'Poppins', sans-serif !important;
    }

    .hero-value {
        font-family: 'Exo 2', sans-serif !important;
        font-size: 28px !important;
        font-weight: 800 !important;
        color: #111827;
        margin-bottom: 4px;
    }

    .hero-sub {
        font-size: 11px;
        color: #9CA3AF;
        font-family: 'Poppins', sans-serif !important;
    }

    /* Functional Colors for Grid - USING CORRECT CI COLORS */
    .hero-cyan, .hero-teal {
        background-color: #00D2BE !important; /* Turbo Teal */
        border: none !important;
    }
    .hero-cyan .hero-label, .hero-cyan .hero-value, .hero-cyan .hero-sub,
    .hero-teal .hero-label, .hero-teal .hero-value, .hero-teal .hero-sub { color: #FFFFFF !important; }

    .hero-red, .hero-coral {
        background-color: #FF2E4D !important; /* Radical Coral */
        border: none !important;
    }
    .hero-red .hero-label, .hero-red .hero-value, .hero-red .hero-sub,
    .hero-coral .hero-label, .hero-coral .hero-value, .hero-coral .hero-sub { color: #FFFFFF !important; }

    /* Feature Tiles */
    .feature-tile {
        height: 200px;
        display: flex;
        flex-direction: column;
        justify-content: flex-start;
        align-items: center;
        text-align: center;
        padding: 5px;
    }
    .feature-title {
        font-family: 'Exo 2', sans-serif !important;
        font-size: 16px;
        font-weight: 800;
        color: #4B5563;
        margin-bottom: 12px;
        text-transform: uppercase;
        height: 40px;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .feature-desc {
        font-size: 13px;
        color: #6B7280;
        line-height: 1.4;
        font-family: 'Poppins', sans-serif !important;
    }

    /* Multiselect styling - less overwhelming */
    div[data-baseweb="select"] {
        max-height: 150px;
    }

    /* Make multiselect chips smaller */
    span[data-baseweb="tag"] {
        font-size: 11px !important;
        padding: 2px 6px !important;
        margin: 2px !important;
    }

    /* Footer */
    .footer {
        position: fixed;
        bottom: 0;
        left: 0;
        width: 100%;
        background-color: #F9FAFB;
        border-top: 1px solid #E5E7EB;
        padding: 8px;
        text-align: center;
        font-size: 10px;
        color: #9CA3AF;
        z-index: 999;
        font-family: 'Poppins', sans-serif;
    }
    .block-container {
        padding-bottom: 50px;
    }

</style>
""", unsafe_allow_html=True)

# --- 3. ROUTING & NAVIGATION ---

# Initialize authentication state
if 'is_authenticated' not in st.session_state:
    st.session_state.is_authenticated = False

if 'navigate_to_page' not in st.session_state:
    st.session_state.navigate_to_page = None

# Define Menu Items with display names
# Format: {display_name: internal_page_value}
page_map = {
    "Start & Data": "Start & Data",
    "Portfolio Analytics": "Portfolio Analytics",
    "Portfolio Builder": "Portfolio Builder",
    "Monte Carlo": "Monte Carlo",
    "Reality Check": "Live vs. Backtest",
    "MEIC Deep Dive": "MEIC Deep Dive",
    "MEIC Optimizer (Beta)": "MEIC Optimizer",
    "AI Analyst (Coming Soon)": "AI Analyst"
}
menu_items = list(page_map.keys())

# Determine current page
if st.session_state.navigate_to_page in page_map.values():
    current_key = list(page_map.keys())[list(page_map.values()).index(st.session_state.navigate_to_page)]
else:
    current_key = "Start & Data"
    st.session_state.navigate_to_page = "Start & Data"

current_page_val = st.session_state.navigate_to_page

# --- SIDEBAR LOGIC ---
# Hide sidebar on login page and landing page
if not st.session_state.is_authenticated or current_page_val == "Start & Data":
    st.markdown("""
    <style>
        [data-testid="stSidebar"] { display: none !important; }
        section[data-testid="stSidebar"] { display: none !important; }
    </style>
    """, unsafe_allow_html=True)
elif st.session_state.is_authenticated:
    with st.sidebar:
        # Logo in sidebar
        ui.render_logo_sidebar()
        st.write("")

        # Navigation with current page indicator
        selected_key = st.radio(
            "Navigation",
            menu_items,
            index=menu_items.index(current_key),
            label_visibility="collapsed",
            key="main_nav_radio"
        )

        target_val = page_map[selected_key]
        if target_val != st.session_state.navigate_to_page:
            st.session_state.navigate_to_page = target_val
            st.rerun()

        # Spacer to push Analysis Manager to bottom
        st.markdown("<div style='flex-grow: 1; min-height: 50px;'></div>", unsafe_allow_html=True)

        st.markdown("---")

        # Analysis Manager at bottom
        st.markdown("""
            <div style="font-family: 'Poppins', sans-serif; font-weight: 600; font-size: 12px;
                        color: #6B7280; text-transform: uppercase; letter-spacing: 0.5px;
                        margin-bottom: 8px; padding-left: 8px;">
                Analysis Manager
            </div>
        """, unsafe_allow_html=True)
        ui.render_save_load_sidebar(st.session_state.get('full_df'), st.session_state.get('live_df'))

        st.markdown("---")
        # Show logged in user
        if st.session_state.get('user_email'):
            st.caption(f"Logged in as: {st.session_state.user_email}")

        # Logout button
        if st.button("LOG OUT", use_container_width=True, type="secondary"):
            st.session_state.clear()
            st.rerun()

# --- 4. PAGE RENDERING ---

# Check authentication first - show login page if not authenticated
if not st.session_state.is_authenticated:
    login.show_login_page()
else:
    # User is authenticated - show main app
    df = st.session_state.get('full_df', pd.DataFrame())
    live_df = st.session_state.get('live_df', pd.DataFrame())

    if current_page_val == "Start & Data":
        landing.show_landing_page()

    elif df.empty and current_page_val != "Start & Data":
        st.session_state.navigate_to_page = "Start & Data"
        st.rerun()

    else:
        if current_page_val == "Portfolio Analytics": portfolio_analytics.page_portfolio_analytics(df, live_df)
        elif current_page_val == "Portfolio Builder": portfolio_builder.page_portfolio_builder(df)
        elif current_page_val == "Monte Carlo": monte_carlo.page_monte_carlo(df)
        elif current_page_val == "Live vs. Backtest": comparison.page_comparison(df, live_df)
        elif current_page_val == "MEIC Deep Dive": meic_analysis.page_meic_analysis(df, live_df)
        elif current_page_val == "MEIC Optimizer": meic_optimizer.page_meic_optimizer()
        elif current_page_val == "AI Analyst": ai_analyst.page_ai_analyst(df)

    ui.render_footer()