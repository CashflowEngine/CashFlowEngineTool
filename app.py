import streamlit as st
import pandas as pd
import ui_components as ui
import database as db
import calculations as calc

# Import page modules
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
    
    /* Force Exo 2 for ALL Headings */
    h1, h2, h3, h4, h5, h6, .card-title, .stHeading, 
    [data-testid="stMarkdownContainer"] h1, 
    [data-testid="stMarkdownContainer"] h2, 
    [data-testid="stMarkdownContainer"] h3,
    .stMetricValue {
        font-family: 'Exo 2', sans-serif !important;
        text-transform: uppercase !important;
        letter-spacing: 0.5px !important;
        color: #4B5563 !important;
        font-weight: 800 !important;
    }
    
    /* Specific overrides for Streamlit elements to ensure font sticks */
    .stMetricLabel { font-family: 'Poppins', sans-serif !important; font-weight: 600 !important; }
    
    /* --- SIDEBAR TOGGLE FIX --- */
    button[kind="header"] { color: transparent !important; }
    button[kind="header"] svg { fill: #4B5563 !important; }
    
    /* --- NAVIGATION BAR REDESIGN --- */
    [data-testid="stSidebarNav"] { display: none !important; }
    
    section[data-testid="stSidebar"] {
        background-color: #F9FAFB;
        border-right: 1px solid #E5E7EB;
    }

    section[data-testid="stSidebar"] .stRadio div[role="radiogroup"] {
        gap: 8px;
        padding: 0 10px;
    }

    section[data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label {
        background-color: transparent;
        border: 1px solid transparent;
        border-radius: 8px;
        padding: 10px 12px;
        margin-bottom: 4px;
        color: #6B7280;
        font-family: 'Poppins', sans-serif !important;
        font-weight: 500;
        font-size: 14px;
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

    section[data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label[data-checked="true"] {
        background-color: #FFFFFF !important; 
        color: #302BFF !important; 
        font-weight: 700 !important;
        border: 1px solid #302BFF !important;
        box-shadow: 0 4px 6px rgba(48, 43, 255, 0.05) !important;
    }
    
    section[data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label > div:first-child {
        display: none;
    }

    section[data-testid="stSidebar"] .block-container {
        padding-top: 2rem;
        padding-bottom: 5rem;
    }

    /* --- UI ELEMENTS --- */
    
    div.stButton > button { 
        background-color: #302BFF !important; 
        color: #FFFFFF !important; 
        font-family: 'Poppins', sans-serif !important;
        font-weight: 600 !important; 
        text-transform: uppercase;
        border: none;
        border-radius: 6px;
        padding: 0.5rem 1.0rem; 
        box-shadow: 0 4px 6px rgba(48, 43, 255, 0.2); 
        transition: all 0.2s ease;
        letter-spacing: 0.5px;
        font-size: 13px; 
    }
    
    div.stButton > button:hover { 
        background-color: #2521c9 !important; 
        box-shadow: 0 6px 12px rgba(48, 43, 255, 0.3); 
        color: #FFFFFF !important;
    }
    
    /* Text Links for Landing Page */
    button[kind="secondary"] {
        background-color: transparent !important;
        border: none !important;
        color: #302BFF !important;
        box-shadow: none !important;
        text-decoration: none !important;
        padding: 0 !important;
        margin-top: 10px !important;
        font-weight: 600 !important;
        text-transform: none !important;
        display: inline-block !important;
        width: auto !important;
    }
    
    button[kind="secondary"]:hover {
        color: #1e1b9e !important;
        text-decoration: underline !important;
        background-color: transparent !important;
    }

    .ghost-link {
        color: #9CA3AF;
        font-size: 12px;
        font-weight: 600;
        cursor: not-allowed;
        font-family: 'Poppins', sans-serif;
        text-transform: uppercase;
        border: 1px dashed #E5E7EB;
        padding: 8px;
        border-radius: 4px;
        display: block;
        text-align: center;
        margin-top: auto;
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
    }
    
    /* Functional Colors for Grid */
    .hero-cyan { 
        background-color: #06B6D4 !important; /* Cyan-500 */
        border: none !important;
    }
    .hero-cyan .hero-label, .hero-cyan .hero-value, .hero-cyan .hero-sub { color: #FFFFFF !important; }
    
    .hero-red {
        background-color: #FF2E4D !important;
        border: none !important;
    }
    .hero-red .hero-label, .hero-red .hero-value, .hero-red .hero-sub { color: #FFFFFF !important; }

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

if 'navigate_to_page' not in st.session_state:
    st.session_state.navigate_to_page = None

# Define Menu Items
page_map = {
    "Start & Data": "Start & Data",
    "Portfolio Analytics": "Portfolio Analytics",
    "Portfolio Builder": "Portfolio Builder",
    "Monte Carlo": "Monte Carlo",
    "Reality Check": "Live vs. Backtest",
    "MEIC Analysis": "MEIC Deep Dive",
    "MEIC Optimizer": "MEIC Optimizer",
    "AI Analyst": "AI Analyst"
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
if current_page_val == "Start & Data":
    st.markdown("""
    <style>
        [data-testid="stSidebar"] { display: none !important; }
        section[data-testid="stSidebar"] { display: none !important; }
    </style>
    """, unsafe_allow_html=True)
else:
    with st.sidebar:
        ui.render_logo()
        st.write("")
        
        # Navigation
        selected_key = st.radio("Navigation", menu_items, index=menu_items.index(current_key), label_visibility="collapsed")
        
        target_val = page_map[selected_key]
        if target_val != st.session_state.navigate_to_page:
            st.session_state.navigate_to_page = target_val
            st.rerun()
            
        st.markdown("---")
        if st.button("RESET APP", use_container_width=True):
            st.session_state.clear()
            st.rerun()
            
        # Analysis Manager
        with st.expander("ANALYSIS MANAGER", expanded=False):
            ui.render_save_load_sidebar(st.session_state.get('full_df'), st.session_state.get('live_df'))

# --- 4. PAGE RENDERING ---

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
