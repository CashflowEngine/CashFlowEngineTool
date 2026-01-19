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
    @import url('https://fonts.googleapis.com/css2?family=Exo+2:wght@400;600;700;800&family=Poppins:wght@300;400;500;600&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    /* Main Background - Light Gray */
    .stApp { 
        font-family: 'Inter', sans-serif; 
        color: #1F2937; 
        background-color: #F9FAFB; /* Very light gray */
    }
    
    h1, h2, h3 { font-family: 'Exo 2', sans-serif !important; text-transform: uppercase; letter-spacing: 0.5px; color: #111827 !important; }
    
    /* HIDE NATIVE STREAMLIT NAVIGATION */
    [data-testid="stSidebarNav"] {
        display: none;
    }

    /* CUSTOM NAVIGATION STYLING (Mimic Native Look) */
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
        color: #31333F;
        font-family: "Source Sans Pro", sans-serif;
        font-size: 16px;
    }
    
    div.row-widget.stRadio > div[role="radiogroup"] > label:hover { 
        background-color: #F0F2F6; 
        color: #31333F;
    }
    
    div.row-widget.stRadio > div[role="radiogroup"] > label[data-checked="true"] {
        background-color: #E8EAF0 !important; 
        color: #31333F !important; 
        font-weight: 600;
        border: none;
        box-shadow: none;
        transform: none;
    }
    
    /* --- CARD DESIGN SYSTEM --- */
    
    /* Style st.container(border=True) as a Card */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: white;
        border-radius: 12px;
        padding: 32px;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06);
        border: 1px solid #E5E7EB; /* Gray 200 */
        margin-bottom: 24px;
    }
    
    /* Card Title Class */
    .card-title {
        font-family: 'Inter', sans-serif;
        font-size: 22px;
        font-weight: 600;
        color: #302BFF; /* Brand Blue */
        margin-bottom: 24px;
        letter-spacing: -0.025em;
    }

    /* --- HIGHLIGHT BOXES (New Design from Screenshot) --- */
    .highlight-container {
        margin-bottom: 20px;
    }
    .highlight-label {
        font-family: 'Inter', sans-serif;
        font-size: 14px;
        font-weight: 500;
        color: #374151;
        margin-bottom: 8px;
    }
    .highlight-box { 
        padding: 16px 20px; 
        border-radius: 8px; 
        text-align: left; 
        font-weight: 600; 
        font-size: 24px; 
        display: inline-block;
        min-width: 120px;
        text-align: center;
    }
    .highlight-green { background-color: #34D399; color: white; } /* Green */
    .highlight-red { background-color: #F87171; color: white; } /* Red */
    .highlight-teal { background-color: #2DD4BF; color: white; } /* Teal */
    .highlight-gray { background-color: #E5E7EB; color: #1F2937; } /* Gray */

    /* Buttons */
    div.stButton > button { background-color: #302BFF !important; color: white !important; font-family: 'Poppins', sans-serif; font-weight: 600; text-transform: uppercase; border: none; border-radius: 8px; padding: 0.6rem 1.2rem; box-shadow: 0 4px 6px rgba(48, 43, 255, 0.2); transition: all 0.2s ease; width: 100%; font-size: 15px; }
    div.stButton > button:hover { background-color: #2521c9 !important; box-shadow: 0 6px 12px rgba(48, 43, 255, 0.3); }
    
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

if 'full_df' not in st.session_state:
    landing.show_landing_page()
else:
    # Sidebar
    st.sidebar.markdown("### 🧭 NAVIGATION")
    
    # Check for programmatic navigation
    if 'navigate_to_page' in st.session_state and st.session_state.navigate_to_page:
        default_index = [
            "📊 Portfolio Analytics", 
            "🏗️ Portfolio Builder", 
            "🎲 Monte Carlo Punisher", 
            "⚖️ Live vs. Backtest", 
            "🔬 MEIC Deep Dive", 
            "🧪 MEIC Optimizer", 
            "🤖 AI Analyst"
        ].index(st.session_state.navigate_to_page)
        st.session_state.navigate_to_page = None # Reset
    else:
        default_index = 0

    page = st.sidebar.radio("Go to", [
        "📊 Portfolio Analytics", 
        "🏗️ Portfolio Builder", 
        "🎲 Monte Carlo Punisher", 
        "⚖️ Live vs. Backtest", 
        "🔬 MEIC Deep Dive", 
        "🧪 MEIC Optimizer", 
        "🤖 AI Analyst"
    ], index=default_index)
    
    # Reset Logic
    st.sidebar.markdown("---")
    if st.sidebar.button("🔄 Reset"):
        st.session_state.clear()
        st.rerun()
        
    ui.render_save_load_sidebar(st.session_state.get('full_df'), st.session_state.get('live_df'))

    # Routing
    df = st.session_state['full_df']
    live_df = st.session_state.get('live_df')

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
                <div style='font-weight: 600; color: #92400E; font-size: 14px;'>DISCLAIMER</div>
                <div style='color: #78350F; font-size: 13px;'>Educational purposes only. Not financial advice.</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
