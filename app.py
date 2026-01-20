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

# --- 2. CSS STYLING ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Exo+2:wght@400;500;600;700;800&family=Poppins:wght@300;400;500;600&display=swap');
    
    /* --- CORPORATE IDENTITY FONTS --- */
    
    /* General Body Text - Poppins */
    html, body, [class*="css"], .stMarkdown, .stText, p, div, span, label, button, input {
        font-family: 'Poppins', sans-serif !important;
        color: #1F2937;
    }
    
    /* Headings - Exo 2 */
    h1, h2, h3, h4, h5, h6, .card-title, .landing-header h1 {
        font-family: 'Exo 2', sans-serif !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        color: #111827 !important;
    }
    
    /* Main Background - Light Gray */
    .stApp { 
        background-color: #F9FAFB; /* Very light gray */
    }
    
    /* --- NAVIGATION --- */
    
    /* Hide Native Sidebar Nav */
    [data-testid="stSidebarNav"] {
        display: none;
    }

    /* Custom Radio Buttons (Sidebar) */
    div.row-widget.stRadio > div[role="radiogroup"] > label {
        background-color: transparent; 
        padding: 8px 12px; 
        border-radius: 4px; 
        margin-bottom: 2px;
        border: none;
        transition: background-color 0.2s; 
        cursor: pointer; 
        display: flex; 
        align-items: center; 
        width: 100%; 
        color: #4B5563;
        font-family: 'Poppins', sans-serif !important;
        font-size: 15px;
        font-weight: 500;
    }
    
    div.row-widget.stRadio > div[role="radiogroup"] > label:hover { 
        background-color: #F3F4F6; 
        color: #111827;
    }
    
    div.row-widget.stRadio > div[role="radiogroup"] > label[data-checked="true"] {
        background-color: #E0E7FF !important; 
        color: #302BFF !important; 
        font-weight: 600;
    }
    
    /* --- CARD DESIGN SYSTEM --- */
    
    /* Standard Card (Bordered Container) */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: white;
        border-radius: 12px;
        padding: 24px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
        border: 1px solid #E5E7EB;
        margin-bottom: 24px;
    }
    
    /* Card Title */
    .card-title {
        font-size: 20px;
        font-weight: 700;
        color: #302BFF !important;
        margin-bottom: 20px;
    }

    /* --- LANDING PAGE TILES --- */
    .feature-tile {
        background-color: #FFFFFF;
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
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
        border-color: #302BFF;
    }
    .feature-icon {
        font-size: 32px;
        margin-bottom: 16px;
    }
    .feature-title {
        font-family: 'Exo 2', sans-serif !important;
        font-size: 18px;
        font-weight: 700;
        color: #111827;
        margin-bottom: 8px;
    }
    .feature-desc {
        font-size: 14px;
        color: #6B7280;
        margin-bottom: 16px;
        line-height: 1.5;
    }

    /* --- KPI CARDS (Restored) --- */
    .hero-card { 
        padding: 16px; 
        border-radius: 10px; 
        text-align: center; 
        margin-bottom: 8px; 
        border: 1px solid #F3F4F6; 
        background-color: #F9FAFB;
        height: 100%;
    }
    .hero-teal { background-color: #00D2BE; color: white !important; border: none; }
    .hero-coral { background-color: #FF2E4D; color: white !important; border: none; }
    
    .hero-teal .hero-label, .hero-coral .hero-label, 
    .hero-teal .hero-value, .hero-coral .hero-value, 
    .hero-teal .hero-sub, .hero-coral .hero-sub { color: white !important; }

    .hero-label { font-size: 12px; font-weight: 600; text-transform: uppercase; margin-bottom: 4px; letter-spacing: 0.5px; opacity: 0.9; }
    .hero-value { font-family: 'Exo 2', sans-serif !important; font-size: 22px; font-weight: 700; margin: 0; }
    .hero-sub { font-size: 11px; opacity: 0.8; margin-top: 2px; }

    /* Buttons */
    div.stButton > button { 
        background-color: #302BFF !important; 
        color: white !important; 
        font-family: 'Exo 2', sans-serif !important; 
        font-weight: 600; 
        text-transform: uppercase; 
        border: none; 
        border-radius: 8px; 
        padding: 0.5rem 1rem; 
        box-shadow: 0 4px 6px rgba(48, 43, 255, 0.2); 
        transition: all 0.2s ease;
        letter-spacing: 0.5px;
    }
    div.stButton > button:hover { 
        background-color: #2521c9 !important; 
        box-shadow: 0 6px 12px rgba(48, 43, 255, 0.3); 
    }
    
    /* Loading Overlay */
    .loading-overlay { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(255, 255, 255, 0.95); display: flex; flex-direction: column; justify-content: center; align-items: center; z-index: 9999; }
    .engine-container { text-align: center; animation: pulse 2s ease-in-out infinite; }
    .gear-system { display: flex; justify-content: center; align-items: center; gap: 5px; margin-bottom: 20px; }
    .gear { font-size: 40px; color: #302BFF; }
    .gear-1 { animation: spin 2s linear infinite; }
    .gear-2 { animation: spin-reverse 1.5s linear infinite; font-size: 50px; }
    .gear-3 { animation: spin 2s linear infinite; }
    @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
    @keyframes spin-reverse { from { transform: rotate(360deg); } to { transform: rotate(0deg); } }
    @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.7; } }
    .loading-text { font-family: 'Exo 2', sans-serif; font-size: 24px; font-weight: 700; color: #302BFF; text-transform: uppercase; letter-spacing: 2px; margin-bottom: 10px; }
    .progress-bar-container { width: 300px; height: 6px; background: #E5E7EB; border-radius: 3px; overflow: hidden; margin-top: 20px; }
    .progress-bar { height: 100%; background: linear-gradient(90deg, #302BFF, #00D2BE, #302BFF); background-size: 200% 100%; animation: progress-flow 1.5s linear infinite; width: 100%; }
    @keyframes progress-flow { 0% { background-position: 100% 0; } 100% { background-position: -100% 0; } }
</style>
""", unsafe_allow_html=True)

# --- 3. MAIN ROUTER ---

# Determine which page to show
# We handle programmatic navigation (e.g. from Landing Page tiles) via session state
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

if 'navigate_to_page' in st.session_state and st.session_state.navigate_to_page in page_options:
    default_index = page_options.index(st.session_state.navigate_to_page)
    # Clear the navigation request so subsequent reloads don't get stuck
    st.session_state.navigate_to_page = None
else:
    default_index = 0

# Sidebar Navigation
st.sidebar.markdown("### 🧭 NAVIGATION")
page = st.sidebar.radio("Go to", page_options, index=default_index)

# Reset Logic
st.sidebar.markdown("---")
if st.sidebar.button("🔄 Reset App"):
    st.session_state.clear()
    st.rerun()

# Save/Load Sidebar (only show if data exists or user wants to load)
ui.render_save_load_sidebar(st.session_state.get('full_df'), st.session_state.get('live_df'))

# Routing Logic
df = st.session_state.get('full_df', pd.DataFrame())
live_df = st.session_state.get('live_df', pd.DataFrame())

if page == "🏠 Start & Data":
    landing.show_landing_page()
    
elif df.empty and page != "🏠 Start & Data":
    # Fallback if user tries to navigate without data
    st.info("👆 Please go to 'Start & Data' to upload or load data first.")
    landing.show_landing_page()
    
else:
    # Render main pages
    if page == "📊 Portfolio Analytics": portfolio_analytics.page_portfolio_analytics(df, live_df)
    elif page == "🏗️ Portfolio Builder": portfolio_builder.page_portfolio_builder(df)
    elif page == "🎲 Monte Carlo Punisher": monte_carlo.page_monte_carlo(df)
    elif page == "⚖️ Live vs. Backtest": comparison.page_comparison(df, live_df)
    elif page == "🔬 MEIC Deep Dive": meic_analysis.page_meic_analysis(df, live_df)
    elif page == "🧪 MEIC Optimizer": meic_optimizer.page_meic_optimizer()
    elif page == "🤖 AI Analyst": ai_analyst.page_ai_analyst(df)

# Footer
st.markdown("---")
st.markdown("""
<div style='background: linear-gradient(135deg, #FEF3C7 0%, #FDE68A 100%); padding: 16px 24px; border-radius: 12px; margin-top: 40px; border-left: 4px solid #F59E0B;'>
    <div style='display: flex; align-items: center; gap: 12px;'>
        <span style='font-size: 24px;'>⚠️</span>
        <div>
            <div style='font-weight: 600; color: #92400E; font-size: 14px; font-family: "Exo 2", sans-serif;'>DISCLAIMER</div>
            <div style='color: #78350F; font-size: 13px;'>Educational purposes only. Not financial advice. Past performance is not indicative of future results.</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)
