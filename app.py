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
    /* IMPORT FONTS */
    @import url('https://fonts.googleapis.com/css2?family=Exo+2:wght@400;600;700;800&family=Poppins:wght@300;400;500;600;700&display=swap');
    
    /* --- TYPOGRAPHY --- */
    
    /* Body Text - Poppins - Space Grey */
    html, body, [class*="css"], .stMarkdown, .stText, p, div, span, label, input, .stDataFrame, .stTable, .stSelectbox, .stNumberInput {
        font-family: 'Poppins', sans-serif !important;
        color: #4B5563 !important; /* Space Grey */
    }
    
    /* Headlines - Exo 2 - Space Grey - Uppercase */
    h1, h2, h3, h4, h5, h6, .card-title, .stHeading {
        font-family: 'Exo 2', sans-serif !important;
        text-transform: uppercase !important;
        letter-spacing: 0.5px !important;
        color: #4B5563 !important; /* Space Grey */
        font-weight: 800 !important; /* Extra Bold */
    }
    
    /* --- NAVIGATION BAR REDESIGN (Pill Style) --- */
    
    /* Hide default Streamlit Nav */
    [data-testid="stSidebarNav"] { display: none !important; }
    
    /* Sidebar Background */
    section[data-testid="stSidebar"] {
        background-color: #F9FAFB;
        border-right: 1px solid #E5E7EB;
    }

    /* Radio Button Container */
    section[data-testid="stSidebar"] .stRadio div[role="radiogroup"] {
        gap: 6px;
        padding: 0 10px;
    }

    /* Radio Items (Pills) */
    section[data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label {
        background-color: transparent;
        border: 1px solid transparent;
        border-radius: 8px;
        padding: 10px 12px;
        margin-bottom: 2px;
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

    /* Active State (Selected Pill) */
    section[data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label[data-checked="true"] {
        background-color: #FFFFFF; 
        color: #302BFF; /* Blue */
        font-weight: 600;
        border: 1px solid #302BFF;
        box-shadow: 0 4px 6px rgba(48, 43, 255, 0.05);
    }
    
    /* Hide the radio circle */
    section[data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label > div:first-child {
        display: none;
    }

    /* Clean up sidebar padding */
    section[data-testid="stSidebar"] .block-container {
        padding-top: 2rem;
        padding-bottom: 5rem;
    }

    /* --- UI ELEMENTS --- */
    
    /* Primary Button - Electric Blue - White Text - FORCE OVERRIDE */
    div.stButton > button { 
        background-color: #302BFF !important; /* Electric Blue */
        color: #FFFFFF !important; /* Pure White Text */
        font-family: 'Poppins', sans-serif !important;
        font-weight: 600 !important; /* Medium/Bold */
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
    
    div.stButton > button:active, div.stButton > button:focus {
        color: #FFFFFF !important;
        background-color: #302BFF !important;
    }
    
    div.stButton > button p {
        color: #FFFFFF !important;
    }

    /* Secondary/Ghost Button styling for 'Coming Soon' etc */
    .ghost-link {
        color: #9CA3AF;
        text-decoration: none;
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
    }

    /* Links */
    a {
        color: #302BFF !important;
        font-weight: 600;
        text-decoration: none;
    }
    a:hover {
        color: #7B2BFF !important; 
        text-decoration: underline;
    }

    /* --- LAYOUTS --- */
    
    /* Main App Background */
    .stApp { background-color: #FFFFFF; }
    
    /* Card Styling */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #FFFFFF;
        border: 1px solid #E5E7EB;
        border-radius: 12px;
        padding: 24px;
        margin-bottom: 24px;
    }

    /* KPI Cards */
    .hero-card { 
        padding: 12px 8px; 
        border-radius: 8px; 
        text-align: center; 
        margin-bottom: 8px; 
        border: 1px solid #E5E7EB; 
        background-color: #F0F4FF; 
        height: 120px; 
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
    }
    
    /* Feature Tiles */
    .feature-tile {
        height: 100%;
        min-height: 220px; 
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        align-items: center;
        text-align: center;
    }
    .feature-title {
        font-family: 'Exo 2', sans-serif !important;
        font-size: 18px;
        font-weight: 700;
        color: #4B5563;
        margin-bottom: 12px;
        text-transform: uppercase;
    }

    /* Overlay Data Warning */
    .data-overlay {
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        height: 100vh;
        background-color: rgba(255, 255, 255, 0.98);
        z-index: 1000000;
        display: flex;
        justify-content: center;
        align-items: center;
        flex-direction: column;
        backdrop-filter: blur(5px);
    }
    .data-overlay-box {
        background: white;
        padding: 40px;
        border-radius: 16px;
        border: 1px solid #E5E7EB;
        box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
        text-align: center;
        max-width: 600px;
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
    /* Adjust main content to not hide behind footer */
    .block-container {
        padding-bottom: 50px;
    }

</style>
""", unsafe_allow_html=True)

# --- 3. ROUTING & NAVIGATION ---

# Initialize Session State
if 'navigate_to_page' not in st.session_state:
    st.session_state.navigate_to_page = None

# Define Menu Items (Clean text, no emojis)
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
    # Find key from value
    current_key = list(page_map.keys())[list(page_map.values()).index(st.session_state.navigate_to_page)]
else:
    current_key = "Start & Data"
    st.session_state.navigate_to_page = "Start & Data"

current_page_val = st.session_state.navigate_to_page

# --- SIDEBAR LOGIC ---
# If on Landing Page, we HIDE the sidebar via CSS injection
if current_page_val == "Start & Data":
    st.markdown("""
    <style>
        [data-testid="stSidebar"] { display: none !important; }
        section[data-testid="stSidebar"] { display: none !important; }
    </style>
    """, unsafe_allow_html=True)
else:
    # Render Sidebar only if NOT landing page
    with st.sidebar:
        ui.render_logo() # Brand Logo on top of Nav
        st.write("") # Spacer
        
        # Custom Radio Menu
        selected_key = st.radio("Navigation", menu_items, index=menu_items.index(current_key), label_visibility="collapsed")
        
        # Handle Navigation
        target_val = page_map[selected_key]
        if target_val != st.session_state.navigate_to_page:
            st.session_state.navigate_to_page = target_val
            st.rerun()
            
        st.markdown("---")
        if st.button("RESET APP", use_container_width=True):
            st.session_state.clear()
            st.rerun()
            
        # Analysis Manager - Expander
        with st.expander("ANALYSIS MANAGER", expanded=False):
            ui.render_save_load_sidebar(st.session_state.get('full_df'), st.session_state.get('live_df'))

# --- 4. PAGE RENDERING ---

df = st.session_state.get('full_df', pd.DataFrame())
live_df = st.session_state.get('live_df', pd.DataFrame())

if current_page_val == "Start & Data":
    landing.show_landing_page()

elif df.empty and current_page_val != "Start & Data":
    # Fallback if refresh happens on subpage without data
    st.session_state.navigate_to_page = "Start & Data"
    st.rerun()

else:
    # Module Routing
    if current_page_val == "Portfolio Analytics": portfolio_analytics.page_portfolio_analytics(df, live_df)
    elif current_page_val == "Portfolio Builder": portfolio_builder.page_portfolio_builder(df)
    elif current_page_val == "Monte Carlo": monte_carlo.page_monte_carlo(df)
    elif current_page_val == "Live vs. Backtest": comparison.page_comparison(df, live_df)
    elif current_page_val == "MEIC Deep Dive": meic_analysis.page_meic_analysis(df, live_df)
    elif current_page_val == "MEIC Optimizer": meic_optimizer.page_meic_optimizer()
    elif current_page_val == "AI Analyst": ai_analyst.page_ai_analyst(df)

# Footer
ui.render_footer()
