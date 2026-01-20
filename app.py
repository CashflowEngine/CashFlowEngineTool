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
st.set_page_config(page_title="Cashflow Engine", page_icon="⚡", layout="wide")

# --- 2. CORPORATE IDENTITY CSS ---
st.markdown("""
<style>
    /* IMPORT FONTS */
    @import url('https://fonts.googleapis.com/css2?family=Exo+2:wght@400;600;700;800&family=Poppins:wght@300;400;500;600;700&display=swap');
    
    /* --- TYPOGRAPHY --- */
    
    /* Body Text - Poppins - Space Grey */
    html, body, [class*="css"], .stMarkdown, .stText, p, div, span, label, input, .stDataFrame, .stTable {
        font-family: 'Poppins', sans-serif !important;
        color: #4B5563 !important; /* Space Grey */
    }
    
    /* Headlines - Exo 2 - Space Grey - Uppercase */
    h1, h2, h3, h4, h5, h6, .card-title {
        font-family: 'Exo 2', sans-serif !important;
        text-transform: uppercase !important;
        letter-spacing: 0.5px !important;
        color: #4B5563 !important; /* Space Grey */
        font-weight: 800 !important; /* Extra Bold */
    }
    
    /* --- COLORS & BACKGROUNDS --- */
    
    /* Main App Background - Pure White */
    .stApp { 
        background-color: #FFFFFF; 
    }
    
    /* Cards/Containers */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #FFFFFF;
        border: 1px solid #E5E7EB; /* Light Grey Border */
        border-radius: 12px;
        padding: 24px;
        box-shadow: none; /* Clean look */
        margin-bottom: 24px;
    }
    
    /* --- UI ELEMENTS --- */
    
    /* Primary Button - Electric Blue - White Text */
    div.stButton > button { 
        background-color: #302BFF !important; /* Electric Blue */
        color: #FFFFFF !important; /* Pure White Text - CRITICAL FIX */
        font-family: 'Poppins', sans-serif !important;
        font-weight: 600 !important; /* Medium/Bold */
        text-transform: uppercase;
        border: none;
        border-radius: 6px;
        padding: 0.6rem 1.2rem;
        box-shadow: 0 4px 6px rgba(48, 43, 255, 0.2); /* Blue Glow */
        transition: all 0.2s ease;
        letter-spacing: 0.5px;
    }
    
    div.stButton > button:hover { 
        background-color: #2521c9 !important; /* Darker Blue */
        box-shadow: 0 6px 12px rgba(48, 43, 255, 0.3); 
        color: #FFFFFF !important;
    }
    
    div.stButton > button:active {
        color: #FFFFFF !important;
    }

    /* Links */
    a {
        color: #302BFF !important;
        font-weight: 600;
        text-decoration: none;
    }
    a:hover {
        color: #7B2BFF !important; /* Electric Violet */
        text-decoration: underline;
    }

    /* --- LANDING PAGE TILES --- */
    .feature-tile {
        background-color: #F0F4FF; /* Ice Tint */
        border: 1px solid #E5E7EB;
        border-radius: 12px;
        padding: 24px;
        height: 100%;
        transition: all 0.3s ease;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    .feature-tile:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 15px -3px rgba(48, 43, 255, 0.1);
        border-color: #302BFF;
    }
    .feature-icon {
        font-size: 32px;
        margin-bottom: 16px;
        color: #302BFF;
    }
    .feature-title {
        font-family: 'Exo 2', sans-serif !important;
        font-size: 18px;
        font-weight: 700;
        color: #4B5563; /* Space Grey */
        margin-bottom: 8px;
        text-transform: uppercase;
    }
    .feature-desc {
        font-size: 14px;
        color: #6B7280;
        margin-bottom: 16px;
        line-height: 1.5;
    }

    /* --- KPI CARDS --- */
    .hero-card { 
        padding: 16px; 
        border-radius: 10px; 
        text-align: center; 
        margin-bottom: 8px; 
        border: 1px solid #E5E7EB; 
        background-color: #F0F4FF; /* Ice Tint */
        height: 100%;
    }
    
    /* Functional Colors */
    .hero-teal { background-color: #00D2BE !important; border: none; }
    .hero-coral { background-color: #FF2E4D !important; border: none; }
    
    /* Text colors inside colored cards must be white */
    .hero-teal .hero-label, .hero-coral .hero-label, 
    .hero-teal .hero-value, .hero-coral .hero-value, 
    .hero-teal .hero-sub, .hero-coral .hero-sub { 
        color: #FFFFFF !important; 
    }

    .hero-label { font-size: 12px; font-weight: 600; text-transform: uppercase; margin-bottom: 4px; letter-spacing: 0.5px; opacity: 0.9; }
    .hero-value { font-family: 'Exo 2', sans-serif !important; font-size: 22px; font-weight: 700; margin: 0; }
    .hero-sub { font-size: 11px; opacity: 0.8; margin-top: 2px; }

    /* HIDE NATIVE NAV */
    [data-testid="stSidebarNav"] {
        display: none;
    }
    
    /* Warning Overlay */
    .data-warning {
        background-color: #FFFBEB;
        border-left: 4px solid #FFAB00; /* Amber Flux */
        padding: 20px;
        border-radius: 4px;
        margin-bottom: 20px;
        animation: pulse 2s infinite;
    }
    @keyframes pulse { 0% { opacity: 1; } 50% { opacity: 0.8; } 100% { opacity: 1; } }

</style>
""", unsafe_allow_html=True)

# --- 3. ROUTING & NAVIGATION ---

# Initialize Session State
if 'navigate_to_page' not in st.session_state:
    st.session_state.navigate_to_page = None

# Determine current page
page_options = [
    "🏠 Start & Data",
    "📊 Portfolio Analytics", 
    "🏗️ Portfolio Builder", 
    "🎲 Monte Carlo Punisher", 
    "⚖️ Live vs. Backtest", 
    "🔬 MEIC Deep Dive", 
    "🧪 MEIC Optimizer", 
    "🤖 AI Analyst"
]

# Handle programmatic navigation (from Tiles)
if st.session_state.navigate_to_page in page_options:
    current_page = st.session_state.navigate_to_page
else:
    current_page = "🏠 Start & Data"

# Sidebar Logic (Hidden on Landing Page, visible elsewhere)
if current_page != "🏠 Start & Data":
    with st.sidebar:
        ui.render_logo() # Brand Logo
        st.markdown("---")
        
        # Navigation
        st.markdown("### 🧭 MENU")
        selected_page = st.radio("Go to", page_options, index=page_options.index(current_page), label_visibility="collapsed")
        
        # If user clicks sidebar, update state
        if selected_page != current_page:
            st.session_state.navigate_to_page = selected_page
            st.rerun()
            
        # Reset Button
        st.markdown("---")
        if st.button("🔄 Reset App", use_container_width=True):
            st.session_state.clear()
            st.rerun()
            
        # Save/Load
        ui.render_save_load_sidebar(st.session_state.get('full_df'), st.session_state.get('live_df'))
else:
    # On landing page, ensure no sidebar distraction, but keep variable for logic
    selected_page = "🏠 Start & Data"

# --- 4. PAGE RENDERING ---

df = st.session_state.get('full_df', pd.DataFrame())
live_df = st.session_state.get('live_df', pd.DataFrame())

if current_page == "🏠 Start & Data":
    landing.show_landing_page()

elif df.empty and current_page != "🏠 Start & Data":
    # Safety fallback if user somehow gets here without data
    st.session_state.navigate_to_page = "🏠 Start & Data"
    st.session_state.show_data_warning = True
    st.rerun()

else:
    # Module Routing
    if current_page == "📊 Portfolio Analytics": portfolio_analytics.page_portfolio_analytics(df, live_df)
    elif current_page == "🏗️ Portfolio Builder": portfolio_builder.page_portfolio_builder(df)
    elif current_page == "🎲 Monte Carlo Punisher": monte_carlo.page_monte_carlo(df)
    elif current_page == "⚖️ Live vs. Backtest": comparison.page_comparison(df, live_df)
    elif current_page == "🔬 MEIC Deep Dive": meic_analysis.page_meic_analysis(df, live_df)
    elif current_page == "🧪 MEIC Optimizer": meic_optimizer.page_meic_optimizer()
    elif current_page == "🤖 AI Analyst": ai_analyst.page_ai_analyst(df)

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #9CA3AF; font-size: 12px; font-family: "Poppins", sans-serif;'>
    ENGINEERED BY THOMAS MEHLITZ
</div>
""", unsafe_allow_html=True)
