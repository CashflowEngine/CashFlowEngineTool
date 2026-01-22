import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import os
import yfinance as yf
import json
import datetime
import logging
import time
from scipy import stats
import re
from pandas.tseries.offsets import BDay

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Cashflow Engine", page_icon="⚡", layout="wide")

# --- 2. CSS STYLING ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Exo+2:wght@400;600;700;800&family=Poppins:wght@300;400;500;600&display=swap');
    
    .stApp { font-family: 'Poppins', sans-serif; color: #4B5563; }
    h1, h2, h3 { font-family: 'Exo 2', sans-serif !important; text-transform: uppercase; letter-spacing: 1px; color: #111827 !important; }
    
  /* Navigation Styling */
    /* Verstecke den Standard-Radio-Kreis */
    div.row-widget.stRadio > div[role="radiogroup"] > label > div:first-child { display: none; }
    
    /* Basis-Stil für alle Buttons */
    div.row-widget.stRadio > div[role="radiogroup"] > label {
        background-color: transparent; 
        padding: 10px 16px; 
        border-radius: 6px; 
        margin-bottom: 4px;
        border: 1px solid transparent; 
        transition: all 0.2s ease-in-out; 
        cursor: pointer; 
        display: flex; 
        align-items: center; 
        width: 100%;
        color: #4B5563; /* Textgrau normal */
    }
    
    /* Hover-Effekt (leichtes Grau) */
    div.row-widget.stRadio > div[role="radiogroup"] > label:hover { 
        background-color: #F3F4F6; 
        color: #111827;
    }
    
    /* AKTIVER Button (Dunkelgrau/Anthrazit) */
    div.row-widget.stRadio > div[role="radiogroup"] > label[data-checked="true"] {
        background-color: #374151 !important; /* Cool Gray 700 */
        color: white !important; 
        border: 1px solid #374151 !important;
        font-weight: 500; 
        box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
        transform: translateX(2px); /* Kleiner Bewegungseffekt */
    }
    
    /* Text-Styling im Button */
    div.row-widget.stRadio > div[role="radiogroup"] > label > div {
        font-family: 'Poppins', sans-serif; 
        font-size: 14px;
        letter-spacing: 0.3px;
    }




    .stMultiSelect div[data-baseweb="select"] span, div[data-baseweb="select"] span {
        white-space: normal !important; word-wrap: break-word !important; line-height: 1.4 !important; height: auto !important;
    }

    .hero-card { padding: 20px; border-radius: 8px; text-align: center; margin-bottom: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); display: flex; flex-direction: column; justify-content: center; height: 100%; min-height: 120px; border: 1px solid rgba(0,0,0,0.05); position: relative; }
    .hero-teal { background-color: #00D2BE; color: white; border: none; }
    .hero-coral { background-color: #FF2E4D; color: white; border: none; }
    .hero-neutral { background-color: white; border: 1px solid #E5E7EB; color: #374151; }
    .hero-neutral .hero-label { color: #6B7280; font-weight: 600; }
    .hero-neutral .hero-value { color: #1F2937; }
    .hero-neutral .hero-sub { color: #9CA3AF; }
    .hero-label { font-family: 'Poppins', sans-serif; font-size: 12px; font-weight: 500; text-transform: uppercase; opacity: 0.9; margin-bottom: 5px; letter-spacing: 0.5px; display: flex; align-items: center; justify-content: center; gap: 4px; }
    .hero-value { font-family: 'Exo 2', sans-serif; font-size: 26px; font-weight: 800; margin: 0; }
    .hero-sub { font-family: 'Poppins', sans-serif; font-size: 11px; opacity: 0.8; margin-top: 5px; }
    
    /* Tooltip styling */
    .tooltip-icon { 
        cursor: help; 
        font-size: 11px; 
        opacity: 0.6; 
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 16px;
        height: 16px;
        border-radius: 50%;
        background-color: rgba(0,0,0,0.1);
        font-style: normal;
        position: relative;
    }
    .tooltip-icon:hover { opacity: 1; background-color: rgba(0,0,0,0.2); }
    .tooltip-icon:hover::after {
        content: attr(data-tip);
        position: absolute;
        bottom: 130%;
        left: 50%;
        transform: translateX(-50%);
        background-color: #1F2937;
        color: white;
        padding: 8px 12px;
        border-radius: 6px;
        font-size: 11px;
        font-weight: 400;
        white-space: normal;
        width: 220px;
        text-align: left;
        z-index: 1000;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        line-height: 1.4;
    }
    .tooltip-icon:hover::before {
        content: '';
        position: absolute;
        bottom: 115%;
        left: 50%;
        transform: translateX(-50%);
        border: 6px solid transparent;
        border-top-color: #1F2937;
        z-index: 1000;
    }
    .hero-teal .tooltip-icon, .hero-coral .tooltip-icon { background-color: rgba(255,255,255,0.2); color: white; }
    .hero-teal .tooltip-icon:hover, .hero-coral .tooltip-icon:hover { background-color: rgba(255,255,255,0.4); }
    .hero-neutral .tooltip-icon { background-color: #E5E7EB; color: #6B7280; }

    div.stButton > button { background-color: #302BFF !important; color: white !important; font-family: 'Poppins', sans-serif; font-weight: 600; text-transform: uppercase; border: none; border-radius: 6px; padding: 0.7rem 1.2rem; box-shadow: 0 4px 6px rgba(48, 43, 255, 0.2); transition: all 0.2s ease; width: 100%; font-size: 16px; }
    div.stButton > button:hover { background-color: #2521c9 !important; box-shadow: 0 6px 12px rgba(48, 43, 255, 0.3); }
    
    /* Smaller buttons in sidebar */
    section[data-testid="stSidebar"] div.stButton > button {
        padding: 0.4rem 0.8rem !important;
        font-size: 11px !important;
        min-height: 32px !important;
    }
    
    /* Small inline buttons for select all/none - targeting by column width pattern */
    [data-testid="column"] div.stButton > button {
        padding: 0.3rem 0.6rem !important;
        font-size: 11px !important;
        min-height: 28px !important;
    }
    
    .sidebar-footer { font-family: 'Poppins', sans-serif; font-size: 11px; color: #6B7280; margin-top: 20px; padding: 10px; background-color: #F3F4F6; border-radius: 8px; line-height: 1.5; }
    .landing-header { text-align: center; margin-bottom: 40px; }
    .landing-header h1 { font-family: 'Exo 2', sans-serif; font-size: 42px; color: #4B5563; margin-bottom: 10px; text-transform: uppercase; font-weight: 800; }
    .landing-header p { font-size: 18px; color: #6B7280; }
    
    /* Loading Overlay Styles */
    .loading-overlay {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(255, 255, 255, 0.95);
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        z-index: 9999;
    }
    
    .engine-container {
        text-align: center;
        animation: pulse 2s ease-in-out infinite;
    }
    
    .engine-icon {
        font-size: 80px;
        margin-bottom: 20px;
        animation: spin 3s linear infinite;
    }
    
    .gear-system {
        display: flex;
        justify-content: center;
        align-items: center;
        gap: 5px;
        margin-bottom: 20px;
    }
    
    .gear {
        font-size: 40px;
        color: #302BFF;
    }
    
    .gear-1 { animation: spin 2s linear infinite; }
    .gear-2 { animation: spin-reverse 1.5s linear infinite; font-size: 50px; }
    .gear-3 { animation: spin 2s linear infinite; }
    
    @keyframes spin {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
    }
    
    @keyframes spin-reverse {
        from { transform: rotate(360deg); }
        to { transform: rotate(0deg); }
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.7; }
    }
    
    .loading-text {
        font-family: 'Exo 2', sans-serif;
        font-size: 24px;
        font-weight: 700;
        color: #302BFF;
        text-transform: uppercase;
        letter-spacing: 2px;
        margin-bottom: 10px;
    }
    
    .loading-subtext {
        font-family: 'Poppins', sans-serif;
        font-size: 14px;
        color: #6B7280;
    }
    
    .progress-bar-container {
        width: 300px;
        height: 6px;
        background: #E5E7EB;
        border-radius: 3px;
        overflow: hidden;
        margin-top: 20px;
    }
    
    .progress-bar {
        height: 100%;
        background: linear-gradient(90deg, #302BFF, #00D2BE, #302BFF);
        background-size: 200% 100%;
        animation: progress-flow 1.5s linear infinite;
        width: 100%;
    }
    
    @keyframes progress-flow {
        0% { background-position: 100% 0; }
        100% { background-position: -100% 0; }
    }
    
    /* Data editor - highlight editable column */
    div[data-testid="stDataFrameResizable"] div[data-testid="column-header"]:last-child {
        background-color: #EEF2FF !important;
        color: #4338CA !important;
        font-weight: 600 !important;
    }
    
    /* Style editable cells in data editor */
    div[data-testid="stDataFrameResizable"] input[type="number"] {
        background-color: #EEF2FF !important;
        border: 2px solid #4338CA !important;
        border-radius: 4px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

COLOR_TEAL, COLOR_CORAL, COLOR_BLUE, COLOR_GREY, COLOR_PURPLE = "#00D2BE", "#FF2E4D", "#302BFF", "#4B5563", "#7B2BFF"

# --- 3. DATABASE SETUP (with proper error handling) ---

DB_AVAILABLE = False
supabase = None
try:
    from supabase import create_client, Client
    
    # Railway Environment Variables ODER Streamlit Secrets
    url = os.environ.get("SUPABASE_URL") or st.secrets.get("supabase", {}).get("url")
    key = os.environ.get("SUPABASE_KEY") or st.secrets.get("supabase", {}).get("key")
    
    if url and key:
        supabase = create_client(url, key)
        DB_AVAILABLE = True
        logger.info("Database connected successfully")
    else:
        logger.warning("No Supabase credentials found - database features disabled")
except ImportError:
    logger.warning("Supabase library not installed - database features disabled")
except Exception as e:
    logger.error(f"Database connection failed: {e}")



# --- 4. AI SETUP (GEMINI) ---
GEMINI_AVAILABLE = False
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    logger.warning("Gemini library not installed - AI features disabled")

# --- 5. CACHING UTILITIES ---
# Strategy DNA cache to avoid repeated inference
if 'dna_cache' not in st.session_state:
    st.session_state.dna_cache = {}

def get_cached_dna(strategy_name, strat_df=None):
    """Get strategy DNA with caching."""
    if strategy_name in st.session_state.dna_cache:
        return st.session_state.dna_cache[strategy_name]
    dna = _infer_strategy_dna(strategy_name, strat_df)
    st.session_state.dna_cache[strategy_name] = dna
    return dna

# --- 6. DATABASE HELPER FUNCTIONS ---
def clean_df_for_json(df):
    """Convert DataFrame to JSON-serializable format."""
    if df is None or df.empty:
        return []
    df_clean = df.copy()
    for col in df_clean.select_dtypes(include=['datetime64', 'datetimetz']).columns:
        df_clean[col] = df_clean[col].astype(str)
    df_clean = df_clean.replace({np.nan: None})
    return df_clean.to_dict(orient='records')


# ============================================================================
# new save function
# ============================================================================

def clean_df_for_json(df):
    """Convert DataFrame to JSON-serializable format."""
    if df is None or df.empty:
        return []
    df_clean = df.copy()
    for col in df_clean.select_dtypes(include=['datetime64', 'datetimetz']).columns:
        df_clean[col] = df_clean[col].astype(str)
    df_clean = df_clean.replace({np.nan: None})
    return df_clean.to_dict(orient='records')


def save_analysis_to_db(name, bt_df, live_df=None):
    """Save analysis to database (legacy wrapper)."""
    return save_analysis_to_db_enhanced(name, bt_df, live_df)


def save_analysis_to_db_enhanced(name, bt_df, live_df=None, description="", tags=None):
    """Enhanced save with metadata."""
    if not DB_AVAILABLE:
        st.error("Database not connected.")
        return False
    
    try:
        bt_json = clean_df_for_json(bt_df)
        live_json = clean_df_for_json(live_df)
        
        trade_count = len(bt_df) if bt_df is not None and not bt_df.empty else 0
        total_pnl = float(bt_df['pnl'].sum()) if bt_df is not None and not bt_df.empty else 0
        strategies = list(bt_df['strategy'].unique()) if bt_df is not None and not bt_df.empty else []
        
        date_start = None
        date_end = None
        if bt_df is not None and not bt_df.empty and 'timestamp' in bt_df.columns:
            date_start = str(bt_df['timestamp'].min().date())
            date_end = str(bt_df['timestamp'].max().date())
        
        payload = {
            "version": 3,
            "backtest": bt_json,
            "live": live_json,
            "metadata": {
                "description": description,
                "tags": tags or [],
                "trade_count": trade_count,
                "total_pnl": total_pnl,
                "strategies": strategies[:10],
                "date_start": date_start,
                "date_end": date_end,
                "has_live": live_df is not None and not live_df.empty
            }
        }
        
        supabase.table('analyses').insert({
            "name": name,
            "data_json": payload
        }).execute()
        
        logger.info(f"Analysis '{name}' saved successfully")
        return True
    except Exception as e:
        logger.error(f"Enhanced save error: {e}")
        st.error(f"Save Error: {e}")
        return False


def get_analysis_list():
    """Retrieve list of saved analyses (legacy wrapper)."""
    return get_analysis_list_enhanced()


def get_analysis_list_enhanced():
    """Get analysis list with metadata."""
    if not DB_AVAILABLE:
        return []
    
    try:
        response = supabase.table('analyses').select(
            "id, name, created_at, data_json"
        ).order('created_at', desc=True).execute()
        
        analyses = []
        for item in response.data:
            analysis = {
                'id': item['id'],
                'name': item['name'],
                'created_at': item['created_at']
            }
            
            data_json = item.get('data_json', {})
            if isinstance(data_json, dict):
                metadata = data_json.get('metadata', {})
                analysis['description'] = metadata.get('description', '')
                analysis['tags'] = metadata.get('tags', [])
                analysis['trade_count'] = metadata.get('trade_count', 0)
                analysis['total_pnl'] = metadata.get('total_pnl', 0)
                analysis['strategies'] = metadata.get('strategies', [])
                analysis['date_start'] = metadata.get('date_start', '')
                analysis['date_end'] = metadata.get('date_end', '')
                analysis['has_live'] = metadata.get('has_live', False)
            else:
                if isinstance(data_json, list):
                    analysis['trade_count'] = len(data_json)
                analysis['description'] = ''
                analysis['tags'] = []
            
            analyses.append(analysis)
        
        return analyses
    except Exception as e:
        logger.error(f"Failed to get enhanced list: {e}")
        return []


def delete_analysis_from_db(analysis_id):
    """Delete an analysis by ID."""
    if not DB_AVAILABLE:
        return False
    try:
        supabase.table('analyses').delete().eq('id', analysis_id).execute()
        logger.info(f"Analysis {analysis_id} deleted")
        return True
    except Exception as e:
        logger.error(f"Delete error: {e}")
        return False


def rename_analysis_in_db(analysis_id, new_name):
    """Rename an analysis."""
    if not DB_AVAILABLE:
        return False
    try:
        supabase.table('analyses').update({"name": new_name}).eq('id', analysis_id).execute()
        logger.info(f"Analysis {analysis_id} renamed to {new_name}")
        return True
    except Exception as e:
        logger.error(f"Rename error: {e}")
        return False


# ============================================================================
# SECTION B: UI FUNCTIONS (füge diese NACH den Database Functions ein)
# ============================================================================

def render_save_load_sidebar(bt_df, live_df):
    """Enhanced save/load system in sidebar."""
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 💾 Analysis Manager")
    
    if not DB_AVAILABLE:
        st.sidebar.warning("☁️ Database not connected")
        st.sidebar.caption("Save/Load requires database.")
        return
    
    save_tab, load_tab, manage_tab = st.sidebar.tabs(["💾 Save", "📂 Load", "⚙️ Manage"])
    
    with save_tab:
        _render_save_section(bt_df, live_df)
    
    with load_tab:
        _render_load_section()
    
    with manage_tab:
        _render_manage_section()


def _render_save_section(bt_df, live_df):
    """Save section with smart naming and tags."""
    
    if bt_df is None or bt_df.empty:
        st.info("📊 No data to save.")
        return
    
    # Auto-generate smart name
    strategies = bt_df['strategy'].unique().tolist() if 'strategy' in bt_df.columns else []
    date_range = ""
    if 'timestamp' in bt_df.columns:
        min_d = bt_df['timestamp'].min()
        max_d = bt_df['timestamp'].max()
        if pd.notna(min_d) and pd.notna(max_d):
            date_range = f"{min_d.strftime('%Y%m%d')}-{max_d.strftime('%Y%m%d')}"
    
    if len(strategies) == 1:
        default_name = f"{strategies[0][:20]}_{date_range}"
    elif len(strategies) <= 3:
        default_name = f"{'_'.join([s[:8] for s in strategies[:3]])}_{date_range}"
    else:
        default_name = f"Portfolio_{len(strategies)}strats_{date_range}"
    default_name = default_name.replace(" ", "_")[:60]
    
    st.markdown("##### 📝 Save")
    
    save_name = st.text_input("Name", value=default_name, max_chars=100, key="save_name")
    save_description = st.text_area("Description", placeholder="Optional notes...", max_chars=300, height=60, key="save_desc")
    
    # Tags
    available_tags = ["Backtest", "Live", "MEIC", "Iron Condor", "Calendar", "Optimized", "Conservative", "Production"]
    default_tags = ["Backtest"] if bt_df is not None and not bt_df.empty else []
    if live_df is not None and not live_df.empty:
        default_tags.append("Live")
    for strat in strategies[:5]:
        strat_upper = strat.upper()
        if "MEIC" in strat_upper and "MEIC" not in default_tags:
            default_tags.append("MEIC")
        elif ("IC" in strat_upper or "IRON" in strat_upper) and "Iron Condor" not in default_tags:
            default_tags.append("Iron Condor")
        elif ("CALENDAR" in strat_upper or "DC" in strat_upper) and "Calendar" not in default_tags:
            default_tags.append("Calendar")
    default_tags = list(set(default_tags))[:3]
    
    selected_tags = st.multiselect("Tags", options=available_tags, default=default_tags, key="save_tags")
    
    with st.expander("📊 Preview"):
        c1, c2 = st.columns(2)
        with c1:
            st.metric("Trades", f"{len(bt_df):,}")
            st.metric("Strategies", len(strategies))
        with c2:
            live_count = len(live_df) if live_df is not None and not live_df.empty else 0
            st.metric("Live Trades", f"{live_count:,}")
            st.metric("P/L", f"${bt_df['pnl'].sum():,.0f}" if 'pnl' in bt_df.columns else "N/A")
    
    if st.button("💾 Save", use_container_width=True, type="primary", key="save_btn"):
        if not save_name.strip():
            st.error("Enter a name.")
            return
        
        existing = get_analysis_list_enhanced()
        existing_names = [a['name'] for a in existing]
        
        if save_name in existing_names:
            st.warning(f"'{save_name}' exists!")
            if st.checkbox("Overwrite?", key="overwrite"):
                for a in existing:
                    if a['name'] == save_name:
                        delete_analysis_from_db(a['id'])
                        break
            else:
                return
        
        with st.spinner("Saving..."):
            if save_analysis_to_db_enhanced(save_name, bt_df, live_df, save_description, selected_tags):
                st.success("✅ Saved!")
                st.balloons()


def _render_load_section():
    """Load section with search and filter."""
    
    st.markdown("##### 📂 Load")
    
    saved = get_analysis_list_enhanced()
    if not saved:
        st.info("No saved analyses.")
        return
    
    search = st.text_input("🔍 Search", key="load_search")
    
    all_tags = set()
    for a in saved:
        all_tags.update(a.get('tags', []))
    
    filter_tags = st.multiselect("Filter", options=sorted(all_tags), key="load_tags") if all_tags else []
    
    filtered = saved
    if search:
        filtered = [a for a in filtered if search.lower() in a['name'].lower() or search.lower() in a.get('description', '').lower()]
    if filter_tags:
        filtered = [a for a in filtered if any(t in a.get('tags', []) for t in filter_tags)]
    
    if not filtered:
        st.warning("No matches.")
        return
    
    st.caption(f"Found {len(filtered)} analysis(es)")
    
    for a in filtered[:10]:
        with st.container(border=True):
            st.markdown(f"**{a['name']}**")
            meta = [f"📅 {a['created_at'][:10]}"]
            if a.get('trade_count'):
                meta.append(f"📊 {a['trade_count']}")
            if a.get('total_pnl'):
                meta.append(f"💰 ${a['total_pnl']:,.0f}")
            if a.get('has_live'):
                meta.append("⚡ Live")
            st.caption(" | ".join(meta))
            
            if a.get('description'):
                st.caption(f"📝 {a['description'][:60]}...")
            
            if a.get('tags'):
                st.markdown(" ".join([f"`{t}`" for t in a['tags'][:4]]))
            
            if st.button("Load", key=f"load_{a['id']}", use_container_width=True):
                _load_with_feedback(a['id'], a['name'])


def _render_manage_section():
    """Manage: rename, delete, export."""
    
    st.markdown("##### ⚙️ Manage")
    
    saved = get_analysis_list_enhanced()
    if not saved:
        st.info("Nothing to manage.")
        return
    
    options = {f"{a['name']} ({a['created_at'][:10]})": a for a in saved}
    sel = st.selectbox("Select", ["--"] + list(options.keys()), key="manage_sel")
    
    if sel == "--":
        return
    
    analysis = options[sel]
    
    st.markdown("---")
    st.caption(f"**Trades:** {analysis.get('trade_count', 'N/A')}")
    if analysis.get('strategies'):
        st.caption(f"**Strategies:** {', '.join(analysis['strategies'][:3])}")
    
    action = st.radio("Action", ["✏️ Rename", "🗑️ Delete", "📤 Export"], horizontal=True, key="manage_action")
    
    if "Rename" in action:
        new_name = st.text_input("New name", value=analysis['name'], key="new_name")
        if st.button("Apply", use_container_width=True, key="rename_btn"):
            if new_name and new_name != analysis['name']:
                if rename_analysis_in_db(analysis['id'], new_name):
                    st.success("Renamed!")
                    time.sleep(0.5)
                    st.rerun()
            else:
                st.warning("Enter a different name.")
    
    elif "Delete" in action:
        st.warning(f"Delete '{analysis['name']}'?")
        if st.checkbox("Confirm deletion", key="del_confirm"):
            if st.button("🗑️ Delete", use_container_width=True, key="del_btn"):
                if delete_analysis_from_db(analysis['id']):
                    st.success("Deleted!")
                    time.sleep(0.5)
                    st.rerun()
    
    elif "Export" in action:
        if st.button("📤 Export CSV", use_container_width=True, key="export_btn"):
            bt_df, _ = load_analysis_from_db(analysis['id'])
            if bt_df is not None and not bt_df.empty:
                csv = bt_df.to_csv(index=False)
                st.download_button("⬇️ Download", csv, f"{analysis['name'].replace(' ', '_')}.csv", "text/csv", use_container_width=True)
            else:
                st.error("No data to export.")


def _load_with_feedback(analysis_id, name):
    """Load with feedback."""
    loading = st.empty()
    loading.info(f"Loading {name}...")
    
    bt_df, live_df = load_analysis_from_db(analysis_id)
    
    if bt_df is not None and not bt_df.empty:
        st.session_state['full_df'] = bt_df
        st.session_state['bt_filenames'] = f"📂 {name}"
        if live_df is not None and not live_df.empty:
            st.session_state['live_df'] = live_df
            st.session_state['live_filenames'] = "Archive"
        else:
            if 'live_df' in st.session_state:
                del st.session_state['live_df']
            if 'live_filenames' in st.session_state:
                del st.session_state['live_filenames']
        loading.success(f"✅ Loaded!")
        time.sleep(0.5)
        st.rerun()
    else:
        loading.error("Failed to load.")



def repair_df_dates(df):
    """Repair and validate date columns with logging."""
    if df is None or df.empty:
        return pd.DataFrame()
    
    original_len = len(df)
    for col in ['timestamp', 'date', 'date_open', 'timestamp_open', 'timestamp_close']:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')
    
    if 'timestamp' in df.columns:
        df = df.dropna(subset=['timestamp'])
        dropped = original_len - len(df)
        if dropped > 0:
            logger.warning(f"Dropped {dropped} rows with invalid timestamps")
    
    return df

def load_analysis_from_db(analysis_id):
    """Load analysis from database."""
    if not DB_AVAILABLE:
        return None, None
    try:
        response = supabase.table('analyses').select("data_json").eq('id', analysis_id).execute()
        if response.data:
            json_data = response.data[0]['data_json']
            if isinstance(json_data, list):
                bt_df = pd.DataFrame(json_data)
                return repair_df_dates(bt_df), None
            elif isinstance(json_data, dict):
                bt_data = json_data.get('backtest', [])
                live_data = json_data.get('live', [])
                bt_df = pd.DataFrame(bt_data) if bt_data else pd.DataFrame()
                live_df = pd.DataFrame(live_data) if live_data else None
                return repair_df_dates(bt_df), repair_df_dates(live_df) if live_df is not None else None
        return None, None
    except Exception as e:
        logger.error(f"Load Error: {e}")
        st.error(f"Load Error: {e}")
        return None, None
# --- 7. DATA LOADING FUNCTIONS ---

@st.cache_data(show_spinner=False)
def load_and_clean(_file_content, file_name):
    """
    Load and clean uploaded file.
    Note: We pass file content instead of file object for proper caching.
    """
    try:
        import io
        if file_name.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(io.BytesIO(_file_content))
        else:
            df = pd.read_csv(io.BytesIO(_file_content))

        df.columns = df.columns.str.strip()
        
        # Build column mapping efficiently
        col_map = {}
        for col in df.columns:
            c_low = col.lower()
            if c_low in ['profit/loss', 'p/l', 'net profit', 'pnl', 'profit']:
                col_map[col] = 'pnl'
            elif c_low in ['margin', 'margin req', 'margin req.', 'margin requirement']:
                col_map[col] = 'margin'
            elif 'no. of contracts' in c_low or c_low in ['contracts', 'quantity', 'qty', 'size']:
                col_map[col] = 'contracts'
            elif 'time closed' in c_low:
                col_map[col] = 'time'
            elif c_low in ['date closed', 'exit date', 'close date', 'date/time', 'date']:
                col_map[col] = 'date'
            elif 'time opened' in c_low:
                col_map[col] = 'time_open'
            elif c_low in ['date opened', 'entry date', 'open date']:
                col_map[col] = 'date_open'
            elif 'strategy' in c_low:
                col_map[col] = 'strategy'
            elif 'legs' in c_low:
                col_map[col] = 'legs'

        df.rename(columns=col_map, inplace=True)

        # Options App specific columns
        if 'Entry Time' in df.columns:
            df.rename(columns={'Entry Time': 'timestamp_open'}, inplace=True)
        if 'Close Time' in df.columns:
            df.rename(columns={'Close Time': 'timestamp_close'}, inplace=True)
        if 'Profit' in df.columns and 'pnl' not in df.columns:
            df.rename(columns={'Profit': 'pnl'}, inplace=True)

        if 'Strategy' in df.columns and 'strategy' not in df.columns:
            df['strategy'] = df['Strategy'].astype(str).str.replace('SPX: ', '', regex=False)
        elif 'Name' in df.columns and 'strategy' not in df.columns:
            df['strategy'] = df['Name']

        if 'pnl' not in df.columns:
            logger.warning(f"No PnL column found in {file_name}")
            return None

        # Clean numeric columns efficiently
        for col in ['pnl', 'margin']:
            if col in df.columns and df[col].dtype == object:
                df[col] = pd.to_numeric(
                    df[col].astype(str).str.replace(r'[$,]', '', regex=True),
                    errors='coerce'
                )

        if 'margin' not in df.columns:
            df['margin'] = 0.0
        else:
            df['margin'] = df['margin'].abs().fillna(0)

        # Date handling
        if 'timestamp_open' in df.columns:
            df['timestamp_open'] = pd.to_datetime(df['timestamp_open'], errors='coerce')

        if 'timestamp_close' in df.columns:
            df['timestamp_close'] = pd.to_datetime(df['timestamp_close'], errors='coerce')
            df['timestamp'] = df['timestamp_close'].fillna(df.get('timestamp_open', df['timestamp_close']))
        elif 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'], errors='coerce')
            if 'time' in df.columns:
                df['timestamp_close'] = pd.to_datetime(
                    df['date'].astype(str) + ' ' + df['time'].astype(str), errors='coerce'
                ).fillna(df['date'])
            else:
                df['timestamp_close'] = df['date']
            df['timestamp'] = df['timestamp_close']

            if 'date_open' in df.columns:
                df['date_open'] = pd.to_datetime(df['date_open'], errors='coerce')
                if 'time_open' in df.columns:
                    df['timestamp_open'] = pd.to_datetime(
                        df['date_open'].astype(str) + ' ' + df['time_open'].astype(str), errors='coerce'
                    ).fillna(df['date_open'])
                else:
                    df['timestamp_open'] = df['date_open']
            else:
                df['timestamp_open'] = df['timestamp_close']
        else:
            df['timestamp'] = pd.to_datetime(df.index)

        if not np.issubdtype(df['timestamp'].dtype, np.datetime64):
            df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')

        df = df.dropna(subset=['timestamp'])

        if 'strategy' not in df.columns:
            df['strategy'] = file_name.rsplit('.', 1)[0]

        cols = ['pnl', 'margin', 'contracts', 'timestamp', 'timestamp_open', 'timestamp_close', 'strategy']
        optional = ['legs', 'date', 'Open']
        cols.extend([c for c in optional if c in df.columns])
        
        return df[[c for c in cols if c in df.columns]]

    except Exception as e:
        logger.error(f"Error loading file {file_name}: {e}")
        return None


@st.cache_data(ttl=3600, show_spinner=False)  # Cache for 1 hour
def fetch_spx_benchmark(start_date, end_date):
    """Fetch S&P 500 data with TTL caching."""
    try:
        # Extend start date by a few days to ensure we have data for alignment
        s_date = start_date - pd.Timedelta(days=5)
        s_str = s_date.strftime('%Y-%m-%d')
        e_str = end_date.strftime('%Y-%m-%d')
        
        data = yf.download("^GSPC", start=s_str, end=e_str, progress=False, auto_adjust=True)
        if data.empty:
            logger.warning("Empty SPX data returned from yfinance")
            return None
        
        # Handle MultiIndex columns (happens with some yfinance versions)
        if isinstance(data.columns, pd.MultiIndex):
            # Try to get Close column
            if 'Close' in data.columns.get_level_values(0):
                close_data = data['Close']
                if isinstance(close_data, pd.DataFrame):
                    close_data = close_data.iloc[:, 0]  # Get first column if still DataFrame
                return close_data
            else:
                return data.iloc[:, 0]  # Return first column
        else:
            if 'Close' in data.columns:
                return data['Close']
            return data.iloc[:, 0]  # Return first column if no Close
    except Exception as e:
        logger.error(f"Failed to fetch SPX data: {e}")
        return None


# --- 8. OPTIMIZED CALCULATION FUNCTIONS ---

def generate_daily_margin_series_optimized(df_strat):
    """
    OPTIMIZED: Generate daily margin series using vectorized cumsum approach.
    ~40-80x faster than original loop-based implementation.
    """
    if df_strat.empty or 'margin' not in df_strat.columns:
        return pd.Series(dtype=float)
    
    if 'timestamp_open' not in df_strat.columns or 'timestamp_close' not in df_strat.columns:
        return pd.Series(dtype=float)

    df = df_strat.copy()
    df['margin'] = df['margin'].fillna(0)

    # Build smart trades list (put/call netting)
    smart_trades = []
    
    for t_open, group in df.groupby('timestamp_open'):
        if pd.isna(t_open):
            continue
            
        put_m, call_m, unk_m = 0.0, 0.0, 0.0
        
        for _, row in group.iterrows():
            m = row['margin'] if not pd.isna(row['margin']) else 0
            legs = str(row.get('legs', '')).upper()
            
            if any(x in legs for x in [' P ', ' PUT ', ' P:']):
                put_m += m
            elif any(x in legs for x in [' C ', ' CALL ', ' C:']):
                call_m += m
            else:
                unk_m += m
        
        smart_margin = max(put_m, call_m) + unk_m
        
        if smart_margin > 0:
            t_close = group['timestamp_close'].max()
            if pd.isna(t_close):
                t_close = t_open
            smart_trades.append({
                'start': pd.Timestamp(t_open).normalize(),
                'end': pd.Timestamp(t_close).normalize(),
                'margin': smart_margin
            })

    if not smart_trades:
        return pd.Series(dtype=float)

    trades_df = pd.DataFrame(smart_trades)
    min_date = trades_df['start'].min()
    max_date = trades_df['end'].max()
    
    # OPTIMIZED: Use event-based cumsum instead of slice assignment
    date_range = pd.date_range(start=min_date, end=max_date, freq='D')
    margin_changes = pd.Series(0.0, index=date_range)
    
    for _, trade in trades_df.iterrows():
        if trade['start'] in margin_changes.index:
            margin_changes.loc[trade['start']] += trade['margin']
        end_plus_one = trade['end'] + pd.Timedelta(days=1)
        if end_plus_one in margin_changes.index:
            margin_changes.loc[end_plus_one] -= trade['margin']

    return margin_changes.cumsum()


def calculate_streaks_optimized(pnl_values):
    """
    OPTIMIZED: Calculate win/loss streaks using NumPy vectorization.
    """
    if len(pnl_values) == 0:
        return 0, 0

    pnl = np.asarray(pnl_values)
    wins = pnl > 0
    losses = pnl <= 0

    def max_streak(arr):
        if len(arr) == 0 or not arr.any():
            return 0
        padded = np.concatenate([[False], arr, [False]])
        changes = np.diff(padded.astype(int))
        starts = np.where(changes == 1)[0]
        ends = np.where(changes == -1)[0]
        if len(starts) == 0:
            return 0
        return int(np.max(ends - starts))

    return max_streak(wins), max_streak(losses)


def run_monte_carlo_optimized(trades, n_simulations, n_steps, start_capital, batch_size=1000, 
                               stress_injections=None, n_stress_per_sim=0, n_years=1, injection_mode='distributed'):
    """
    OPTIMIZED: Fully vectorized Monte Carlo simulation with batched processing.
    Handles large numbers of simulations without running out of memory.
    
    Args:
        trades: Array of trade P&L values to sample from
        n_simulations: Number of simulation paths to generate
        n_steps: Number of trades per simulation
        start_capital: Starting portfolio value
        batch_size: Batch size for memory-efficient processing
        stress_injections: Array of worst-case trade values to inject (if stress testing)
        n_stress_per_sim: Number of stress events to inject per simulation
        n_years: Number of years in simulation (for distributing events evenly)
        injection_mode: 'distributed' (black swan - one per year) or 'random' (historical - anywhere)
    """
    
    def get_distributed_positions(n_steps, n_events, n_years):
        """Distribute events evenly across years - one per year max (for Black Swan)."""
        if n_events == 0:
            return []
        
        steps_per_year = n_steps / n_years
        positions = []
        
        for i in range(n_events):
            # Which year does this event belong to?
            year_idx = i % int(n_years)
            year_start = int(year_idx * steps_per_year)
            year_end = int((year_idx + 1) * steps_per_year)
            
            # Random position within this year
            if year_end > year_start:
                pos = np.random.randint(year_start, year_end)
                positions.append(pos)
        
        return positions
    
    def get_random_positions(n_steps, n_events):
        """Get completely random positions (for Historical worst days)."""
        if n_events == 0:
            return []
        return np.random.choice(n_steps, size=min(n_events, n_steps), replace=False).tolist()
    
    def inject_stress_events(random_trades, sim_idx, stress_injections, n_stress_per_sim, n_steps, n_years, mode):
        """Inject stress events into a simulation based on mode."""
        if mode == 'random':
            # HISTORICAL: Inject from the array of separate strategy worst days at random positions
            positions = get_random_positions(n_steps, len(stress_injections))
            for i, pos in enumerate(positions):
                if i < len(stress_injections):
                    random_trades[sim_idx, pos] = stress_injections[i]
        else:
            # DISTRIBUTED (Black Swan): Inject the combined value distributed across years
            positions = get_distributed_positions(n_steps, n_stress_per_sim, n_years)
            for pos in positions:
                random_trades[sim_idx, pos] = stress_injections[0]
    
    # For smaller simulations, run all at once
    if n_simulations <= batch_size:
        random_trades = np.random.choice(trades, size=(n_simulations, n_steps), replace=True)
        
        # Inject stress events based on mode
        if stress_injections is not None and n_stress_per_sim > 0 and len(stress_injections) > 0:
            for sim_idx in range(n_simulations):
                inject_stress_events(random_trades, sim_idx, stress_injections, n_stress_per_sim, n_steps, n_years, injection_mode)
        
        cumsum = np.cumsum(random_trades, axis=1)
        paths = np.zeros((n_simulations, n_steps + 1), dtype=np.float32)
        paths[:, 0] = start_capital
        paths[:, 1:] = start_capital + cumsum
        return paths
    
    # For larger simulations, process in batches
    n_batches = (n_simulations + batch_size - 1) // batch_size
    
    # We'll store a subset of paths for visualization (max 500) plus all end values and drawdowns
    max_paths_to_store = min(500, n_simulations)
    stored_paths = np.zeros((max_paths_to_store, n_steps + 1), dtype=np.float32)
    all_end_vals = np.zeros(n_simulations, dtype=np.float32)
    all_max_dds = np.zeros(n_simulations, dtype=np.float32)
    
    paths_stored = 0
    sims_processed = 0
    
    for batch_idx in range(n_batches):
        batch_start = batch_idx * batch_size
        batch_end = min(batch_start + batch_size, n_simulations)
        current_batch_size = batch_end - batch_start
        
        # Generate batch
        random_trades = np.random.choice(trades, size=(current_batch_size, n_steps), replace=True)
        
        # Inject stress events based on mode
        if stress_injections is not None and n_stress_per_sim > 0 and len(stress_injections) > 0:
            for sim_idx in range(current_batch_size):
                inject_stress_events(random_trades, sim_idx, stress_injections, n_stress_per_sim, n_steps, n_years, injection_mode)
        
        cumsum = np.cumsum(random_trades, axis=1)
        
        batch_paths = np.zeros((current_batch_size, n_steps + 1), dtype=np.float32)
        batch_paths[:, 0] = start_capital
        batch_paths[:, 1:] = start_capital + cumsum
        
        # Store end values
        all_end_vals[batch_start:batch_end] = batch_paths[:, -1]
        
        # Calculate drawdowns for this batch
        running_max = np.maximum.accumulate(batch_paths, axis=1)
        with np.errstate(divide='ignore', invalid='ignore'):
            drawdowns = (running_max - batch_paths) / running_max
            drawdowns = np.nan_to_num(drawdowns, nan=0.0, posinf=0.0, neginf=0.0)
        all_max_dds[batch_start:batch_end] = np.max(drawdowns, axis=1)
        
        # Store some paths for visualization
        paths_to_add = min(current_batch_size, max_paths_to_store - paths_stored)
        if paths_to_add > 0:
            stored_paths[paths_stored:paths_stored + paths_to_add] = batch_paths[:paths_to_add]
            paths_stored += paths_to_add
        
        sims_processed += current_batch_size
    
    # Return stored paths (for visualization) and attach metadata
    result_paths = stored_paths[:paths_stored]
    
    # Attach additional data as attributes (will be extracted later)
    return result_paths, all_end_vals, all_max_dds


def calculate_max_drawdown_batch(paths, precomputed_dds=None):
    """
    OPTIMIZED: Calculate max drawdown for all paths at once.
    Can accept precomputed drawdowns from batched processing.
    """
    if precomputed_dds is not None:
        return precomputed_dds
    
    # Running maximum for each path (along axis=1)
    running_max = np.maximum.accumulate(paths, axis=1)
    
    # Drawdown percentage
    with np.errstate(divide='ignore', invalid='ignore'):
        drawdowns = (running_max - paths) / running_max
        drawdowns = np.nan_to_num(drawdowns, nan=0.0, posinf=0.0, neginf=0.0)
    
    # Max drawdown per path
    return np.max(drawdowns, axis=1)


def get_top_drawdowns_optimized(equity_curve, initial_capital):
    """
    OPTIMIZED: Calculate top drawdowns using vectorized operations.
    ~50-100x faster than row iteration.
    """
    if equity_curve.empty:
        return pd.DataFrame()

    equity = equity_curve.values
    dates = equity_curve.index
    
    # Vectorized peak calculation
    peak = np.maximum.accumulate(equity)
    dd_from_peak = equity - peak
    
    # Find drawdown periods by detecting transitions
    in_dd = dd_from_peak < 0
    
    # Find boundaries: start when entering DD, end when exiting
    dd_diff = np.diff(np.concatenate([[False], in_dd, [False]]).astype(int))
    starts_idx = np.where(dd_diff == 1)[0]
    ends_idx = np.where(dd_diff == -1)[0]
    
    drawdowns = []
    for i in range(len(starts_idx)):
        if i >= len(ends_idx):
            break
            
        start_idx = max(0, starts_idx[i] - 1)  # Day before DD began
        end_idx = min(ends_idx[i], len(equity) - 1)
        
        period_equity = equity[start_idx:end_idx + 1]
        period_peak = peak[start_idx:end_idx + 1]
        
        valley_idx_local = np.argmin(period_equity)
        valley_idx = start_idx + valley_idx_local
        
        dd_usd = period_peak[0] - period_equity[valley_idx_local]
        dd_pct_peak = (dd_usd / period_peak[0]) * 100 if period_peak[0] > 0 else 0
        dd_pct_initial = (dd_usd / initial_capital) * 100
        
        is_recovered = end_idx < len(equity) - 1 or not in_dd[-1] if len(in_dd) > 0 else True
        
        drawdowns.append({
            "Start Date": dates[start_idx].date() if hasattr(dates[start_idx], 'date') else dates[start_idx],
            "Bottom Date": dates[valley_idx].date() if hasattr(dates[valley_idx], 'date') else dates[valley_idx],
            "Recovery Date": dates[end_idx].date() if is_recovered and hasattr(dates[end_idx], 'date') else "Not yet",
            "Depth ($)": dd_usd,
            "Drop from Peak (%)": dd_pct_peak,
            "Drop of Init. Cap (%)": dd_pct_initial,
            "Duration (Days)": (dates[end_idx] - dates[start_idx]).days if hasattr(dates[end_idx] - dates[start_idx], 'days') else 0
        })

    df_dd = pd.DataFrame(drawdowns)
    if not df_dd.empty:
        df_dd = df_dd.sort_values(by="Depth ($)", ascending=False).head(10)
    
    return df_dd


def _infer_strategy_dna(strategy_name, strat_df=None):
    """
    Infer strategy Greek exposure from name and optionally trade data.
    Results are cached via get_cached_dna().
    """
    n = strategy_name.upper()
    dna = {"Type": "Custom", "Delta": "Neutral", "Vega": "Neutral", "Theta": "Neutral", "Gamma": "Neutral"}

    # Explicit name-based checks (fastest)
    if "LONG PUT" in n or (" P " in n and "LONG" in n):
        return {"Type": "Long Put", "Delta": "Short", "Vega": "Long", "Theta": "Short", "Gamma": "Long"}
    if "SHORT PUT" in n or (" P " in n and "SHORT" in n):
        return {"Type": "Short Put", "Delta": "Long", "Vega": "Short", "Theta": "Long", "Gamma": "Short"}
    if "LONG CALL" in n:
        return {"Type": "Long Call", "Delta": "Long", "Vega": "Long", "Theta": "Short", "Gamma": "Long"}

    # Check legs data if available (sample only first 20 trades)
    if strat_df is not None and not strat_df.empty and 'legs' in strat_df.columns:
        if 'timestamp_open' in strat_df.columns:
            # OPTIMIZED: Sample first, don't create all groups
            sample = strat_df.head(100)
            grouped = sample.groupby('timestamp_open')
            ic_count = 0
            
            for i, (_, group) in enumerate(grouped):
                if i >= 20:
                    break
                legs = " | ".join(group['legs'].dropna().astype(str).tolist()).upper()
                if (" C STO" in legs or " CALL STO" in legs) and (" P STO" in legs or " PUT STO" in legs):
                    ic_count += 1
            
            if ic_count > 0:
                if "MEIC" in n:
                    return {"Type": "MEIC (Iron Condor)", "Delta": "Neutral", "Vega": "Short", "Theta": "Long", "Gamma": "Short"}
                return {"Type": "Iron Condor", "Delta": "Neutral", "Vega": "Short", "Theta": "Long", "Gamma": "Short"}

    # Fallback pattern matching
    if "METF CALL" in n:
        return {"Type": "Bear Call Spread", "Delta": "Short", "Vega": "Short", "Theta": "Long", "Gamma": "Short"}
    if "METF PUT" in n:
        return {"Type": "Bull Put Spread", "Delta": "Long", "Vega": "Short", "Theta": "Long", "Gamma": "Short"}
    if "DC" in n or "DOUBLE CALENDAR" in n:
        return {"Type": "Double Calendar", "Delta": "Neutral", "Vega": "Long", "Theta": "Long", "Gamma": "Short"}
    if "RIC" in n or "REVERSE IRON" in n:
        return {"Type": "Reverse Iron Condor", "Delta": "Neutral", "Vega": "Long", "Theta": "Short", "Gamma": "Long"}
    if "BCS" in n:
        return {"Type": "Bull Call Spread", "Delta": "Long", "Vega": "Long", "Theta": "Short", "Gamma": "Long"}
    if "BPS" in n:
        return {"Type": "Bull Put Spread", "Delta": "Long", "Vega": "Short", "Theta": "Long", "Gamma": "Short"}
    if any(x in n for x in ["BUTTERFLY", "FLY", "BWB"]):
        return {"Type": "Butterfly", "Delta": "Neutral", "Vega": "Short", "Theta": "Long", "Gamma": "Short"}

    return dna
# --- 9. ADVANCED METRICS CALCULATION ---

def calculate_advanced_metrics(daily_returns_series, trades_df=None, benchmark_series=None, account_size=100000):
    """
    Calculate comprehensive portfolio metrics.
    FIXED: Division by zero bugs and edge cases.
    """
    # Initialize with defaults
    metrics = {
        "CAGR": 0, "Vol": 0, "Sharpe": 0, "Sortino": 0,
        "MaxDD": 0, "MaxDD_USD": 0, "MAR": 0, "MART": 0,
        "WinRate": 0, "PF": 0, "Alpha": 0, "Beta": 0, "Kelly": 0,
        "WinStreak": 0, "LossStreak": 0, "AvgRetMargin": 0, "Trades": 0,
        "SPX_CAGR": 0, "SPX_MaxDD": 0, "SPX_Vol": 0, "SPX_Sharpe": 0, "SPX_TotalRet": 0
    }

    n_days = len(daily_returns_series)
    if n_days < 2:
        return metrics

    # Basic return metrics
    total_ret = (1 + daily_returns_series).prod() - 1
    # CAGR: Annualize using 365 since we're using calendar days (not 252 trading days)
    # Formula: (1 + total_return)^(365/calendar_days) - 1
    cagr = (1 + total_ret) ** (365 / n_days) - 1 if total_ret > -1 else 0
    volatility = daily_returns_series.std() * np.sqrt(252)  # Volatility still uses 252 trading days

    rf = 0.04  # Risk-free rate
    excess_ret = daily_returns_series.mean() * 252 - rf
    sharpe = excess_ret / volatility if volatility > 0 else 0

    neg_ret = daily_returns_series[daily_returns_series < 0]
    downside_std = neg_ret.std() * np.sqrt(252) if len(neg_ret) > 0 else 0
    sortino = excess_ret / downside_std if downside_std > 0 else 0

    # Drawdown metrics (vectorized)
    equity_curve = account_size * (1 + daily_returns_series).cumprod()
    peak_eq = equity_curve.cummax()
    dd_pct = (equity_curve - peak_eq) / peak_eq
    dd_usd = equity_curve - peak_eq

    max_dd_pct = dd_pct.min()
    max_dd_val = dd_usd.min()

    # Risk-adjusted ratios (with zero protection)
    mar = cagr / abs(max_dd_pct) if max_dd_pct != 0 else 0
    mart = cagr / (abs(max_dd_val) / account_size) if max_dd_val != 0 else 0

    # Trade-based metrics
    if trades_df is not None and not trades_df.empty:
        num_trades = len(trades_df)
        pnl = trades_df['pnl'].values

        wins = pnl[pnl > 0]
        losses = pnl[pnl <= 0]

        win_rate = len(wins) / num_trades if num_trades > 0 else 0
        pf = wins.sum() / abs(losses.sum()) if losses.sum() != 0 else 999

        # Kelly criterion - FIXED: proper zero protection
        avg_win = wins.mean() if len(wins) > 0 else 0
        avg_loss = abs(losses.mean()) if len(losses) > 0 else 0

        kelly = 0
        if avg_loss > 0 and avg_win > 0:
            b = avg_win / avg_loss
            if b > 0:  # Additional protection
                p = win_rate
                q = 1 - p
                kelly = (p * b - q) / b

        # Average return on margin
        avg_ret_margin = 0
        if 'margin' in trades_df.columns:
            valid_m = trades_df[trades_df['margin'] > 0]
            if not valid_m.empty:
                avg_ret_margin = (valid_m['pnl'] / valid_m['margin']).mean()

        # Streaks - OPTIMIZED
        max_w_streak, max_l_streak = calculate_streaks_optimized(pnl)

        metrics.update({
            "Trades": num_trades,
            "WinRate": win_rate,
            "PF": pf,
            "Kelly": kelly,
            "AvgRetMargin": avg_ret_margin,
            "WinStreak": max_w_streak,
            "LossStreak": max_l_streak
        })

    # Benchmark comparison
    if benchmark_series is not None and not benchmark_series.empty:
        # Clean the benchmark series
        benchmark_clean = benchmark_series.dropna()
        
        if len(benchmark_clean) > 0:
            aligned = pd.concat([daily_returns_series, benchmark_clean], axis=1).dropna()

            if len(aligned) > 20:
                y = aligned.iloc[:, 0].values
                x = aligned.iloc[:, 1].values
                # Filter out any remaining NaN or inf values
                mask = np.isfinite(x) & np.isfinite(y)
                if mask.sum() > 20:
                    slope, intercept, _, _, _ = stats.linregress(x[mask], y[mask])
                    metrics["Beta"] = slope
                    metrics["Alpha"] = intercept * 252

            spx_tot = (1 + benchmark_clean).prod() - 1
            spx_cagr = (1 + spx_tot) ** (365 / len(benchmark_clean)) - 1 if len(benchmark_clean) > 0 and spx_tot > -1 else 0

            spx_cum = (1 + benchmark_clean).cumprod()
            spx_peak = spx_cum.cummax()
            spx_dd = (spx_cum - spx_peak) / spx_peak
            
            # SPX Volatility
            spx_vol = benchmark_clean.std() * np.sqrt(252) if len(benchmark_clean) > 0 else 0
            
            # SPX Sharpe
            spx_excess = benchmark_clean.mean() * 252 - rf
            spx_sharpe = spx_excess / spx_vol if spx_vol > 0 else 0
            
            # SPX Total Return (dollar equivalent for comparison)
            spx_total_ret_pct = spx_tot

            metrics["SPX_CAGR"] = spx_cagr
            metrics["SPX_MaxDD"] = spx_dd.min() if len(spx_dd) > 0 else 0
            metrics["SPX_Vol"] = spx_vol
            metrics["SPX_Sharpe"] = spx_sharpe
            metrics["SPX_TotalRet"] = spx_total_ret_pct

    metrics.update({
        "CAGR": cagr, "Vol": volatility, "Sharpe": sharpe, "Sortino": sortino,
        "MaxDD": max_dd_pct, "MaxDD_USD": max_dd_val, "MAR": mar, "MART": mart
    })

    return metrics


# --- 10. UI HELPER FUNCTIONS ---

def show_loading_overlay(message="Processing", submessage="The engine is running..."):
    """Display a custom loading overlay with animated gears."""
    loading_html = f"""
    <div class="loading-overlay" id="loadingOverlay">
        <div class="engine-container">
            <div class="gear-system">
                <span class="gear gear-1">⚙️</span>
                <span class="gear gear-2">⚙️</span>
                <span class="gear gear-3">⚙️</span>
            </div>
            <div class="loading-text">{message}</div>
            <div class="loading-subtext">{submessage}</div>
            <div class="progress-bar-container">
                <div class="progress-bar"></div>
            </div>
        </div>
    </div>
    """
    return st.markdown(loading_html, unsafe_allow_html=True)


def hide_loading_overlay():
    """Hide the loading overlay using JavaScript."""
    hide_js = """
    <script>
        var overlay = document.getElementById('loadingOverlay');
        if (overlay) {
            overlay.style.display = 'none';
        }
    </script>
    """
    st.markdown(hide_js, unsafe_allow_html=True)


def render_hero_metric(label, value, subtext="", color_class="hero-neutral", tooltip=""):
    """Render a hero metric card with optional tooltip shown via question mark icon."""
    tooltip_html = ""
    if tooltip:
        # Escape single quotes and double quotes in tooltip
        tooltip_escaped = tooltip.replace("'", "&#39;").replace('"', '&quot;')
        tooltip_html = f"<span class='tooltip-icon' data-tip='{tooltip_escaped}'>?</span>"
    
    st.markdown(
        f"<div class='hero-card {color_class}'>"
        f"<div class='hero-label'>{label} {tooltip_html}</div>"
        f"<div class='hero-value'>{value}</div>"
        f"<div class='hero-sub'>{subtext}</div>"
        f"</div>",
        unsafe_allow_html=True
    )


def render_standard_metric(label, value, subtext="", value_color=COLOR_GREY):
    """Render a standard metric card."""
    st.markdown(
        f"<div class='metric-card'>"
        f"<div class='metric-label'>{label}</div>"
        f"<div class='metric-value' style='color: {value_color}'>{value}</div>"
        f"<div class='metric-sub'>{subtext}</div>"
        f"</div>",
        unsafe_allow_html=True
    )


def color_monthly_performance(val):
    """Color code monthly performance values - green for positive, red for negative."""
    try:
        # Handle string values with $ or %
        if isinstance(val, str):
            clean_val = val.replace('$', '').replace(',', '').replace('%', '').strip()
            num_val = float(clean_val)
        else:
            num_val = float(val)
        
        if num_val > 0:
            # Green gradient based on magnitude
            intensity = min(abs(num_val) / 5000, 1) if abs(num_val) > 100 else min(abs(num_val) / 10, 1)
            green_intensity = int(200 + (55 * (1 - intensity)))
            return f'background-color: rgba(0, 210, 190, {0.1 + intensity * 0.4}); color: #065F46'
        elif num_val < 0:
            # Red gradient based on magnitude
            intensity = min(abs(num_val) / 5000, 1) if abs(num_val) > 100 else min(abs(num_val) / 10, 1)
            return f'background-color: rgba(255, 46, 77, {0.1 + intensity * 0.4}); color: #991B1B'
        else:
            return 'background-color: white; color: #374151'
    except (ValueError, TypeError):
        return 'background-color: white; color: #374151'


def load_file_with_caching(uploaded_file):
    """
    Helper to load file with proper caching.
    Reads file content once, then passes to cached function.
    """
    content = uploaded_file.read()
    uploaded_file.seek(0)  # Reset file pointer
    return load_and_clean(content, uploaded_file.name)
# ==========================================
# MEIC OPTIMIZER HELPER FUNCTIONS
# ==========================================
import re
from pandas.tseries.offsets import BDay

def parse_meic_filename(filename):
    """
    Extrahiert Parameter aus dem Dateinamen für den 4D Analyzer.
    Erwartet Format: MEIC_W{width}_SL{sl}_P{premium}.csv
    Beispiel: MEIC_W50_SL100_P2.5.csv
    """
    # Regex für W, SL, P (Premium kann Dezimalpunkt haben)
    width_match = re.search(r'W(\d+)', filename, re.IGNORECASE)
    sl_match = re.search(r'SL(\d+)', filename, re.IGNORECASE)
    prem_match = re.search(r'P(\d+\.?\d*)', filename, re.IGNORECASE)
    
    return {
        'Width': int(width_match.group(1)) if width_match else None,
        'SL': int(sl_match.group(1)) if sl_match else None,
        'Premium': float(prem_match.group(1)) if prem_match else None,
        'Filename': filename
    }

def generate_oo_signals(start_date, end_date, start_time="09:35", end_time="15:55", interval_min=5):
    """
    Generiert CSV für Option Omega Custom Signals.
    Format entspricht 'signals_open_only.csv': Header 'OPEN_DATETIME', Format 'YYYY-MM-DD HH:MM'
    """
    # Business Days Only
    dates = pd.date_range(start=start_date, end=end_date, freq='B') 
    
    signal_rows = []
    
    # Zeit-Range erstellen
    t_start = pd.to_datetime(start_time).time()
    t_end = pd.to_datetime(end_time).time()
    
    for d in dates:
        # Simple Holiday Skip (Hardcoded für die wichtigsten)
        if d.month == 12 and d.day == 25: continue # Christmas
        if d.month == 1 and d.day == 1: continue   # New Year
        if d.month == 7 and d.day == 4: continue   # Independence Day
        
        # Erstelle Zeitpunkte für den Tag
        current_ts = pd.Timestamp.combine(d.date(), t_start)
        end_ts = pd.Timestamp.combine(d.date(), t_end)
        
        while current_ts <= end_ts:
            signal_rows.append(current_ts)
            current_ts += pd.Timedelta(minutes=interval_min)
            
    df_signals = pd.DataFrame(signal_rows, columns=['OPEN_DATETIME'])
    # Formatierung exakt wie im Template
    df_signals['OPEN_DATETIME'] = df_signals['OPEN_DATETIME'].dt.strftime('%Y-%m-%d %H:%M')
    return df_signals

def analyze_meic_group(df, account_size):
    """Berechnet Metriken (MAR, CAGR, DD) für eine Gruppe von Trades."""
    if df.empty:
        return {'MAR': 0, 'CAGR': 0, 'MaxDD': 0, 'Trades': 0, 'WinRate': 0, 'P/L': 0}
    
    # Ensure datetime sorting
    df = df.sort_values('timestamp')
    
    # Daily PnL
    daily_pnl = df.set_index('timestamp').resample('D')['pnl'].sum()
    
    # Equity Curve
    equity = account_size + daily_pnl.cumsum()
    peak = equity.cummax()
    dd_series = (equity - peak) / peak
    max_dd = dd_series.min()
    
    # CAGR (approx)
    days = (df['timestamp'].max() - df['timestamp'].min()).days
    if days < 1: days = 1
    total_ret = daily_pnl.sum() / account_size
    cagr = (1 + total_ret) ** (365 / days) - 1
    
    # MAR
    mar = cagr / abs(max_dd) if max_dd != 0 else 0
    
    # Win Rate
    win_rate = (df['pnl'] > 0).mean()
    
    return {
        'MAR': mar,
        'CAGR': cagr,
        'MaxDD': max_dd,
        'Trades': len(df),
        'WinRate': win_rate,
        'P/L': daily_pnl.sum()
    }







# --- 11. PAGE FUNCTIONS ---

def page_monte_carlo(full_df):
    """Monte Carlo simulation page - OPTIMIZED with error handling."""
    if 'sim_run' not in st.session_state:
        st.session_state.sim_run = False
    if 'mc_results' not in st.session_state:
        st.session_state.mc_results = None

    st.markdown(
        """<h1 style='color: #4B5563; font-family: "Exo 2", sans-serif; font-weight: 800; 
        text-transform: uppercase; margin-bottom: 0;'>MONTE CARLO PUNISHER</h1>""",
        unsafe_allow_html=True
    )
    st.write("")
    
    # Check if we have portfolio data from Portfolio Builder
    from_builder = st.session_state.get('mc_from_builder', False)
    portfolio_daily_pnl = st.session_state.get('mc_portfolio_daily_pnl', None)
    
    # Reset results when coming from builder with fresh data
    if from_builder and st.session_state.get('mc_new_from_builder', False):
        st.session_state.sim_run = False
        st.session_state.mc_results = None
        st.session_state.mc_new_from_builder = False
    
    if from_builder and portfolio_daily_pnl is not None:
        st.success("📦 **Using Assembled Portfolio from Portfolio Builder**")
        st.caption(f"Portfolio has {len(portfolio_daily_pnl)} days of data | Click 'Run Simulation' to stress test")
        
        # Option to clear and use raw data instead
        if st.button("🔄 Use Raw Trade Data Instead", type="secondary"):
            st.session_state.mc_from_builder = False
            st.session_state.mc_portfolio_daily_pnl = None
            st.session_state.sim_run = False
            st.session_state.mc_results = None
            st.rerun()
        
        st.write("")

    st.subheader("Simulation Parameters")
    c1, c2, c3 = st.columns(3)
    with c1:
        n_sims = st.number_input("Number of Simulations", value=5000, step=500, min_value=100, max_value=10000)
    with c2:
        sim_months = st.number_input("Simulation Period (Months)", value=60, step=6, min_value=1, max_value=120)
    with c3:
        if from_builder and portfolio_daily_pnl is not None:
            start_cap = st.number_input("Initial Capital ($)", 
                                        value=st.session_state.get('mc_portfolio_account_size', 100000), 
                                        step=1000, min_value=1000)
        else:
            start_cap = st.number_input("Initial Capital ($)", value=100000, step=1000, min_value=1000)

    st.write("")

    # Get available strategies for the dropdown
    available_strategies = []
    if full_df is not None and not full_df.empty and 'strategy' in full_df.columns:
        available_strategies = sorted(full_df['strategy'].dropna().unique().tolist())
    
    with st.expander("🎯 Stress Test (Worst-Case Injection)", expanded=False):
        stress_mode = st.radio(
            "Stress Test Mode:",
            ["Historical Max Loss (Real)", "Theoretical Max Risk (Black Swan)"],
            index=1,
            help="Historical: Uses actual worst days from data. Theoretical: Uses margin-based black swan calculation."
        )
        
        if "Historical" in stress_mode:
            st.markdown("""
            <div style='background-color: #DBEAFE; padding: 10px; border-radius: 6px; font-size: 12px; margin-bottom: 8px;'>
            <b>Historical Max Loss:</b> Injects each strategy's <b>actual worst day P&L</b> from your backtest data.<br>
            • Events are injected <b>separately</b> for each strategy<br>
            • Events occur at <b>random times</b> throughout the simulation (not simultaneously)<br>
            • All strategies are included automatically
            </div>
            """, unsafe_allow_html=True)
            stress_val = st.slider("Frequency (times per year)", 0, 12, 0, 1, format="%d x/Year",
                                  help="How many worst-day events per year per strategy", key="hist_stress_slider")
            stress_type = "freq"
            stress_strategies = available_strategies  # Use all for Historical
            if stress_val > 0:
                n_events = int(np.ceil(stress_val * (sim_months / 12.0)))
                n_strats = len(available_strategies)
                st.caption(f"📊 {n_events} worst-day events per strategy × {n_strats} strategies = {n_events * n_strats} total events per simulation, randomly distributed")
        else:
            st.markdown("""
            <div style='background-color: #FEE2E2; padding: 10px; border-radius: 6px; font-size: 12px; margin-bottom: 8px;'>
            <b>Theoretical Max Risk (Black Swan):</b> Simulates a market crash hitting <b>ALL selected strategies at once</b>.<br>
            • Loss = PUT-side margin <b>minus premium received</b><br>
            • Events are <b>distributed evenly</b> across years (max 1 per year)<br>
            • Deselect strategies that profit from crashes (bear call spreads, long puts)
            </div>
            """, unsafe_allow_html=True)
            
            # Strategy selector ONLY for Theoretical mode
            if len(available_strategies) > 0:
                st.markdown("**Select strategies to include in black swan:**")
                stress_strategies = st.multiselect(
                    "Strategies at risk during crash:",
                    options=available_strategies,
                    default=available_strategies,  # All selected by default
                    key="stress_test_strategies",
                    help="Only selected strategies will be hit simultaneously. Deselect strategies that profit from crashes."
                )
            else:
                stress_strategies = []
            
            stress_val = st.slider("Frequency (times per year)", 0, 12, 0, 1, format="%d x/Year",
                                  help="How many combined crash events per year", key="theo_stress_slider")
            stress_type = "freq"
            if stress_val > 0:
                n_events = int(np.ceil(stress_val * (sim_months / 12.0)))
                st.caption(f"⚠️ {n_events} event(s) distributed across {max(1, sim_months//12)} year(s)")
        
        # Store selected strategies in session state for use during simulation
        st.session_state.stress_test_selected_strategies = stress_strategies

    st.write("")

    if st.button("🎲 Run Simulation", type="primary", use_container_width=True):
        st.session_state.sim_run = True
        st.session_state.mc_results = None  # Clear previous results

    if st.session_state.sim_run:
        # Check if we need to run simulation or just display results
        if st.session_state.mc_results is None:
            try:
                # Show custom loading overlay for Monte Carlo
                mc_loading = st.empty()
                mc_loading.markdown("""
                <div class="loading-overlay">
                    <div class="engine-container">
                        <div class="gear-system">
                            <span class="gear gear-1">⚙️</span>
                            <span class="gear gear-2">🎰</span>
                            <span class="gear gear-3">⚙️</span>
                        </div>
                        <div class="loading-text">🎲 Running Simulations</div>
                        <div class="loading-subtext">Crunching thousands of possible futures...</div>
                        <div class="progress-bar-container">
                            <div class="progress-bar"></div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Initialize stress injection variables
                stress_injections = []
                
                # Determine data source
                if from_builder and portfolio_daily_pnl is not None:
                    # Use portfolio daily P&L from builder
                    daily_pnl_values = portfolio_daily_pnl.dropna().values
                    daily_pnl_values = daily_pnl_values[daily_pnl_values != 0]  # Remove zero days
                    
                    if len(daily_pnl_values) < 10:
                        mc_loading.empty()
                        st.error("Not enough non-zero days for simulation.")
                        return
                    
                    # For portfolio, we sample daily returns
                    final_trades_pool = list(daily_pnl_values)
                    days = len(portfolio_daily_pnl)
                    auto_trades_per_year = 252  # Trading days per year for daily data
                    
                    debug_msg = []
                    injected_count = 0
                    
                    # Stress test injection for portfolio - collect separately
                    if stress_val > 0:
                        worst_day = np.min(daily_pnl_values)
                        if worst_day < 0:
                            n = int(np.ceil(stress_val * (sim_months / 12.0)))
                            
                            if n > 0:
                                stress_injections.append((worst_day, n))
                                injected_count += n
                                debug_msg.append(f"**Portfolio**: {n}x **${worst_day:,.0f}** per sim (Worst Day)")
                else:
                    # Use raw trade data
                    if full_df.empty:
                        mc_loading.empty()
                        st.error("No trade data available.")
                        return
                        
                    active_df = full_df.sort_values('timestamp')

                    if len(active_df) < 2:
                        mc_loading.empty()
                        st.error("Not enough data for simulation.")
                        return

                    days = (active_df['timestamp'].iloc[-1] - active_df['timestamp'].iloc[0]).days
                    days = max(days, 1)

                    auto_trades_per_year = len(active_df) / (days / 365.25)

                    final_trades_pool = []
                    debug_msg = []
                    injected_count = 0
                    
                    # Get user-selected strategies for stress test (only used for Theoretical)
                    stress_selected_strategies = st.session_state.get('stress_test_selected_strategies', [])
                    
                    # HISTORICAL: Collect each strategy's worst day SEPARATELY
                    # THEORETICAL: Collect and SUM selected strategies' margin into ONE combined event
                    historical_worst_days = []  # List of (strategy_name, worst_day_value)
                    combined_theoretical_wc = 0
                    strategy_wc_details = []

                    for strat_name, group in active_df.groupby('strategy'):
                        strat_pnl = group['pnl'].dropna().values
                        if len(strat_pnl) == 0:
                            continue
                        final_trades_pool.extend(strat_pnl)

                        if stress_val > 0:
                            # Calculate historical worst day for ALL strategies
                            daily_pnl = group.groupby(group['timestamp'].dt.date)['pnl'].sum()
                            hist_worst_day = daily_pnl.min() if len(daily_pnl) > 0 else np.min(strat_pnl)
                            
                            if hist_worst_day < 0:
                                historical_worst_days.append((strat_name, hist_worst_day))
                            
                            # THEORETICAL: Only include if strategy is SELECTED by user
                            if strat_name in stress_selected_strategies:
                                strat_theoretical_wc = 0
                                avg_daily_premium = 0
                                
                                if 'margin' in group.columns and 'legs' in group.columns:
                                    # Calculate average daily premium received
                                    daily_premium = group.groupby(group['timestamp'].dt.date)['pnl'].sum()
                                    avg_daily_premium = daily_premium.mean() if len(daily_premium) > 0 else 0
                                    
                                    # Smart margin: only count PUT-side risk, ignore CALL-side
                                    daily_put_margins = []
                                    
                                    for entry_date, day_group in group.groupby(group['timestamp_open'].dt.date if 'timestamp_open' in group.columns else group['timestamp'].dt.date):
                                        day_put_margin = 0
                                        
                                        for _, row in day_group.iterrows():
                                            m = row['margin'] if not pd.isna(row['margin']) else 0
                                            legs = str(row.get('legs', '')).upper()
                                            
                                            # Check if this is a PUT-side position (has downside crash risk)
                                            is_put_side = any(x in legs for x in [' P ', ' PUT ', ' P:', '/P', '-P', 'PUT SPREAD', 'BULL PUT'])
                                            is_call_side = any(x in legs for x in [' C ', ' CALL ', ' C:', '/C', '-C', 'CALL SPREAD', 'BEAR CALL'])
                                            is_long_put = 'LONG PUT' in legs or 'BUY PUT' in legs
                                            
                                            # For iron condors (has both P and C), only count PUT margin
                                            if is_put_side and is_call_side:
                                                day_put_margin += m / 2  # Half the margin is PUT side
                                            elif is_put_side and not is_long_put:
                                                day_put_margin += m
                                            elif is_call_side or is_long_put:
                                                pass  # Profits from crash, skip
                                            else:
                                                day_put_margin += m  # Unknown - conservatively include
                                        
                                        if day_put_margin > 0:
                                            daily_put_margins.append(day_put_margin)
                                    
                                    max_daily_put_margin = max(daily_put_margins) if daily_put_margins else 0
                                    
                                    # Theoretical worst = margin at risk MINUS premium received
                                    if max_daily_put_margin > 0:
                                        strat_theoretical_wc = -(max_daily_put_margin - abs(avg_daily_premium))
                                
                                # Accumulate theoretical for selected strategies
                                if strat_theoretical_wc < 0:
                                    combined_theoretical_wc += strat_theoretical_wc
                                    strategy_wc_details.append(f"**{strat_name}**: ${abs(strat_theoretical_wc):,.0f}")
                                elif hist_worst_day < 0:
                                    # Fallback to historical if no margin data
                                    combined_theoretical_wc += hist_worst_day
                                    strategy_wc_details.append(f"**{strat_name}**: ${abs(hist_worst_day):,.0f} (hist)")
                    
                    # Now create stress injections based on mode
                    if stress_val > 0:
                        n_events_per_year = stress_val
                        n_years = max(1, sim_months / 12)
                        
                        if "Historical" in stress_mode:
                            # HISTORICAL: Each strategy's worst day injected SEPARATELY at RANDOM times
                            # Total events = n_events_per_year * n_years, distributed across all strategies
                            total_events = int(np.ceil(n_events_per_year * n_years))
                            
                            if len(historical_worst_days) > 0 and total_events > 0:
                                # Create separate injection entries for each strategy
                                # Events per strategy = total_events (each strategy gets its worst day injected)
                                for strat_name, worst_day in historical_worst_days:
                                    stress_injections.append((worst_day, total_events, 'random'))
                                    injected_count += total_events
                                    debug_msg.append(f"**{strat_name}**: {total_events}x **${worst_day:,.0f}** (worst day)")
                                
                                debug_msg.insert(0, f"**Historical Worst Days**: {total_events} events per strategy, randomly distributed")
                                debug_msg.insert(1, "---")
                        else:
                            # THEORETICAL (Black Swan): All selected strategies hit SIMULTANEOUSLY
                            # Events distributed evenly - one per year max
                            n_events = int(np.ceil(n_events_per_year * n_years))
                            
                            combined_wc = combined_theoretical_wc
                            
                            if combined_wc < 0 and n_events > 0:
                                stress_injections.append((combined_wc, n_events, 'distributed'))
                                injected_count = n_events
                                debug_msg.append(f"**COMBINED Black Swan**: {n_events}x **${combined_wc:,.0f}** per sim")
                                debug_msg.append("---")
                                debug_msg.append(f"**Included strategies** ({len(stress_selected_strategies)} selected):")
                                for detail in strategy_wc_details:
                                    debug_msg.append(f"  - {detail}")
                            elif n_events > 0 and len(stress_selected_strategies) == 0:
                                debug_msg.append("⚠️ No strategies selected for stress test")
                            elif n_events > 0 and combined_wc >= 0:
                                debug_msg.append("⚠️ Selected strategies have no downside risk (combined loss = $0)")

                if len(final_trades_pool) == 0:
                    mc_loading.empty()
                    st.error("No valid data found for simulation.")
                    return

                n_steps = max(int((sim_months / 12) * auto_trades_per_year), 10)
                
                # Calculate number of years for event distribution
                n_years = max(1, sim_months / 12)
                
                # Prepare stress injection parameters based on mode
                # stress_injections contains tuples of (value, count, mode)
                # mode = 'random' for Historical, 'distributed' for Theoretical
                stress_inj_list = []
                injection_mode = 'distributed'  # default
                total_injections = 0
                
                if len(stress_injections) > 0:
                    # Check the mode from first entry
                    injection_mode = stress_injections[0][2] if len(stress_injections[0]) > 2 else 'distributed'
                    
                    if injection_mode == 'random':
                        # HISTORICAL: Multiple separate values, each injected at random times
                        for entry in stress_injections:
                            val, count = entry[0], entry[1]
                            stress_inj_list.extend([val] * count)
                            total_injections += count
                    else:
                        # THEORETICAL: Single combined value, distributed across years
                        val, count = stress_injections[0][0], stress_injections[0][1]
                        stress_inj_list = [val]
                        total_injections = count
                
                stress_inj_array = np.array(stress_inj_list) if stress_inj_list else None

                # OPTIMIZED: Vectorized Monte Carlo with stress injections
                mc_result = run_monte_carlo_optimized(
                    np.array(final_trades_pool), int(n_sims), n_steps, start_cap,
                    stress_injections=stress_inj_array, 
                    n_stress_per_sim=total_injections,
                    n_years=n_years,
                    injection_mode=injection_mode
                )
                
                # Handle both return formats (small sims return just paths, large return tuple)
                if isinstance(mc_result, tuple):
                    mc_paths, end_vals, dds = mc_result
                else:
                    mc_paths = mc_result
                    end_vals = mc_paths[:, -1]
                    dds = calculate_max_drawdown_batch(mc_paths)
                
                profit = np.mean(end_vals) - start_cap
                cagr = ((np.mean(end_vals) / start_cap) ** (12 / sim_months)) - 1

                dd_mean = np.mean(dds)
                mar = cagr / dd_mean if dd_mean > 0 else 0

                p95, p50, p05 = np.percentile(end_vals, [95, 50, 5])
                d05, d50, d95 = np.percentile(dds, [5, 50, 95])
                
                # Calculate CAGR for each percentile
                cagr_p95 = ((p95 / start_cap) ** (12 / sim_months)) - 1
                cagr_p50 = ((p50 / start_cap) ** (12 / sim_months)) - 1
                cagr_p05 = ((p05 / start_cap) ** (12 / sim_months)) - 1
                
                # Calculate MART = CAGR / (MaxDD% as ratio)
                mart = cagr / dd_mean if dd_mean > 0 else 0
                
                # Calculate Probability of Profit
                profitable_sims = np.sum(end_vals > start_cap)
                prob_profit = profitable_sims / len(end_vals)

                # Store results in session state
                st.session_state.mc_results = {
                    'mc_paths': mc_paths,
                    'end_vals': end_vals,
                    'profit': profit,
                    'cagr': cagr,
                    'dds': dds,
                    'dd_mean': dd_mean,
                    'mar': mar,
                    'mart': mart,
                    'p95': p95, 'p50': p50, 'p05': p05,
                    'cagr_p95': cagr_p95, 'cagr_p50': cagr_p50, 'cagr_p05': cagr_p05,
                    'd05': d05, 'd50': d50, 'd95': d95,
                    'start_cap': start_cap,
                    'sim_months': sim_months,
                    'n_sims': int(n_sims),
                    'n_steps': n_steps,
                    'prob_profit': prob_profit,
                    'injected_count': injected_count,
                    'n_stress_per_sim': total_injections,
                    'injection_mode': injection_mode,
                    'debug_msg': debug_msg
                }
                
                # Hide loading overlay
                mc_loading.empty()

            except Exception as e:
                mc_loading.empty()
                st.error(f"Simulation error: {str(e)}")
                logger.error(f"Monte Carlo error: {e}")
                st.session_state.sim_run = False
                return

        # Display results from session state
        if st.session_state.mc_results is not None:
            r = st.session_state.mc_results
            
            n_stress = r.get('n_stress_per_sim', 0)
            n_steps = r.get('n_steps', 0)
            sim_months = r.get('sim_months', 12)
            n_years = max(1, sim_months / 12)
            injection_mode = r.get('injection_mode', 'distributed')
            
            if n_stress > 0:
                if injection_mode == 'random':
                    # HISTORICAL MODE - not a black swan
                    with st.expander(f"✅ Historical Worst Days Stress Test Active", expanded=True):
                        st.markdown(f"""
                        <div style='background-color: #DBEAFE; padding: 12px; border-radius: 8px; font-size: 13px;'>
                        <b>Every simulation</b> ({r['n_sims']:,} total) includes historical worst-day events.<br>
                        Each strategy's worst day is injected <b>separately</b> at <b>random times</b> throughout the simulation.<br>
                        Events do NOT happen simultaneously - they are distributed randomly.
                        </div>
                        """, unsafe_allow_html=True)
                        for msg in r['debug_msg']:
                            if msg.startswith("---"):
                                st.markdown("---")
                            elif msg.startswith("**Historical"):
                                st.markdown(f"📊 {msg}")
                            elif msg.startswith("⚠️"):
                                st.warning(msg)
                            else:
                                st.markdown(f"  • {msg}")
                else:
                    # THEORETICAL MODE - black swan
                    with st.expander(f"✅ Black Swan Stress Test: {n_stress} event(s) per simulation", expanded=True):
                        st.markdown(f"""
                        <div style='background-color: #FEE2E2; padding: 12px; border-radius: 8px; font-size: 13px;'>
                        <b>Every simulation</b> ({r['n_sims']:,} total) includes exactly <b>{n_stress} black swan event(s)</b>.<br>
                        Events are <b>distributed evenly</b> across {n_years:.0f} year(s) - max 1 event per year.<br>
                        Each event hits <b>all selected strategies simultaneously</b> (like a real market crash).
                        </div>
                        """, unsafe_allow_html=True)
                        for msg in r['debug_msg']:
                            if msg.startswith("---"):
                                st.markdown("---")
                            elif msg.startswith("**Included") or msg.startswith("**COMBINED"):
                                st.markdown(f"🎯 {msg}")
                            elif msg.startswith("  -"):
                                st.markdown(msg)
                            elif msg.startswith("⚠️"):
                                st.warning(msg)
                            else:
                                st.markdown(msg)

            st.subheader("Key Metrics")
            k1, k2, k3, k4, k5 = st.columns(5)
            with k1:
                render_hero_metric("Avg. Net Profit", f"${r['profit']:,.0f}", "Mean Result", "hero-teal" if r['profit'] > 0 else "hero-coral",
                                  tooltip="Average ending portfolio value minus initial capital across all simulations")
            with k2:
                render_hero_metric("CAGR", f"{r['cagr']*100:.1f}%", "Ann. Growth", "hero-teal" if r['cagr'] > 0 else "hero-coral",
                                  tooltip="Compound Annual Growth Rate based on average ending value")
            with k3:
                render_hero_metric("Expected DD", f"{r['dd_mean']*100:.1f}%", "Avg. Drawdown", "hero-coral",
                                  tooltip="Average maximum drawdown across all simulations - the expected worst-case decline")
            with k4:
                mar_val = r.get('mar', r['cagr'] / r['dd_mean'] if r['dd_mean'] > 0 else 0)
                render_hero_metric("MAR Ratio", f"{mar_val:.2f}", "CAGR/DD", "hero-teal" if mar_val > 1 else "hero-coral",
                                  tooltip="CAGR divided by Expected Drawdown. Above 0.5 is acceptable, above 1.0 is good")
            with k5:
                prob_profit = r.get('prob_profit', 1.0)
                n_sims = r.get('n_sims', 1000)
                render_hero_metric("Prob. of Profit", f"{prob_profit*100:.1f}%", f"Out of {n_sims:,} sims", 
                                  "hero-teal" if prob_profit > 0.9 else ("hero-coral" if prob_profit < 0.7 else "hero-neutral"),
                                  tooltip="Percentage of simulations that ended with profit (ending value > starting capital)")

            st.write("")
            st.subheader("Return Scenarios (CAGR)")
            r1, r2, r3 = st.columns(3)
            with r1:
                cagr_best = r.get('cagr_p95', ((r['p95']/r['start_cap']) ** (12 / r.get('sim_months', 36))) - 1)
                render_hero_metric("Best Case (95%)", f"{cagr_best*100:.1f}%", f"${r['p95']:,.0f}", "hero-neutral",
                                  tooltip="95th percentile CAGR - only 5% of simulations performed better")
            with r2:
                cagr_likely = r.get('cagr_p50', ((r['p50']/r['start_cap']) ** (12 / r.get('sim_months', 36))) - 1)
                render_hero_metric("Most Likely (50%)", f"{cagr_likely*100:.1f}%", f"${r['p50']:,.0f}", "hero-neutral",
                                  tooltip="Median CAGR - 50% of simulations were better, 50% were worse")
            with r3:
                cagr_worst = r.get('cagr_p05', ((r['p05']/r['start_cap']) ** (12 / r.get('sim_months', 36))) - 1)
                render_hero_metric("Worst Case (5%)", f"{cagr_worst*100:.1f}%", f"${r['p05']:,.0f}", "hero-neutral",
                                  tooltip="5th percentile CAGR - only 5% of simulations performed worse")

            st.write("")
            st.subheader("Drawdown Scenarios")
            d1, d2, d3 = st.columns(3)
            with d1:
                render_hero_metric("Best Case DD", f"{r['d05']*100:.1f}%", "Top 5%", "hero-neutral",
                                  tooltip="5th percentile drawdown - only 5% of simulations had smaller drawdowns")
            with d2:
                render_hero_metric("Typical DD", f"{r['d50']*100:.1f}%", "Median", "hero-neutral",
                                  tooltip="Median drawdown - 50% of simulations had larger, 50% smaller drawdowns")
            with d3:
                render_hero_metric("Worst Case DD", f"{r['d95']*100:.1f}%", "Bottom 5%", "hero-neutral",
                                  tooltip="95th percentile drawdown - only 5% of simulations had larger drawdowns")

            st.write("")
            st.subheader("Portfolio Growth")
            show_paths = st.checkbox("Show individual paths", value=True)

            mc_paths = r['mc_paths']
            end_vals = r['end_vals']
            dds = r['dds']
            
            x = np.arange(mc_paths.shape[1])
            fig = go.Figure()

            if show_paths:
                n_display = min(50, mc_paths.shape[0])
                # Use fixed seed for consistent display
                np.random.seed(42)
                random_indices = np.random.choice(mc_paths.shape[0], n_display, replace=False)

                for idx in random_indices:
                    fig.add_trace(go.Scatter(
                        x=x, y=mc_paths[idx], mode='lines',
                        line=dict(color='rgba(200, 200, 200, 0.15)', width=1),
                        showlegend=False, hoverinfo='skip'
                    ))

                # Find best/worst within the stored paths (not all end_vals)
                stored_end_vals = mc_paths[:, -1]
                stored_dds = calculate_max_drawdown_batch(mc_paths)
                
                best_idx = np.argmax(stored_end_vals)
                worst_idx = np.argmin(stored_end_vals)
                max_dd_idx = np.argmax(stored_dds)

                fig.add_trace(go.Scatter(x=x, y=mc_paths[best_idx], mode='lines',
                                         line=dict(color=COLOR_TEAL, width=2), name='Best Path'))
                fig.add_trace(go.Scatter(x=x, y=mc_paths[worst_idx], mode='lines',
                                         line=dict(color=COLOR_CORAL, width=2), name='Worst Path'))
                if max_dd_idx != worst_idx:
                    fig.add_trace(go.Scatter(x=x, y=mc_paths[max_dd_idx], mode='lines',
                                             line=dict(color=COLOR_PURPLE, width=2, dash='dot'), name='Max DD Path'))

            pp95, pp05 = np.percentile(mc_paths, [95, 5], axis=0)
            fig.add_trace(go.Scatter(
                x=np.concatenate([x, x[::-1]]),
                y=np.concatenate([pp95, pp05[::-1]]),
                fill='toself', fillcolor='rgba(0, 210, 190, 0.05)',
                line=dict(width=0), name='5-95% Conf.', showlegend=True
            ))

            pp50 = np.percentile(mc_paths, 50, axis=0)
            fig.add_trace(go.Scatter(x=x, y=pp50, mode='lines',
                                     line=dict(color=COLOR_BLUE, width=3), name='Median'))

            fig.add_shape(type="line", x0=0, y0=r['start_cap'], x1=len(x), y1=r['start_cap'],
                          line=dict(color="gray", width=1, dash="dash"))

            fig.update_layout(
                template="plotly_white", height=600,
                margin=dict(l=20, r=20, t=40, b=20),
                legend=dict(orientation="h", y=1.02, x=1, xanchor="right")
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Distribution Charts
            st.write("")
            dist_col1, dist_col2 = st.columns(2)
            
            with dist_col1:
                st.subheader("Return Distribution")
                # Calculate returns as percentage of starting capital
                returns_pct = ((end_vals - r['start_cap']) / r['start_cap']) * 100
                
                fig_return_dist = go.Figure()
                fig_return_dist.add_trace(go.Histogram(
                    x=returns_pct,
                    nbinsx=30,
                    marker_color=COLOR_BLUE,
                    opacity=0.8,
                    name="Returns"
                ))
                
                # Add percentile lines
                p5_ret = np.percentile(returns_pct, 5)
                p50_ret = np.percentile(returns_pct, 50)
                p95_ret = np.percentile(returns_pct, 95)
                
                fig_return_dist.add_vline(x=p5_ret, line_dash="dash", line_color="red", 
                                          annotation_text=f"P5: {p5_ret:.1f}%", annotation_position="top left")
                fig_return_dist.add_vline(x=p50_ret, line_dash="dash", line_color="blue",
                                          annotation_text=f"P50: {p50_ret:.1f}%", annotation_position="top")
                fig_return_dist.add_vline(x=p95_ret, line_dash="dash", line_color="green",
                                          annotation_text=f"P95: {p95_ret:.1f}%", annotation_position="top right")
                
                fig_return_dist.update_layout(
                    template="plotly_white",
                    height=350,
                    margin=dict(l=20, r=20, t=40, b=40),
                    xaxis_title="Cumulative Return (%)",
                    yaxis_title="Frequency",
                    showlegend=False
                )
                st.plotly_chart(fig_return_dist, use_container_width=True, key="mc_return_dist")
            
            with dist_col2:
                st.subheader("Drawdown Analysis")
                # Convert dds to percentage
                dds_pct = dds * 100
                
                fig_dd_dist = go.Figure()
                fig_dd_dist.add_trace(go.Histogram(
                    x=dds_pct,
                    nbinsx=30,
                    marker_color=COLOR_CORAL,
                    opacity=0.8,
                    name="Drawdowns"
                ))
                
                # Add percentile lines
                d5_pct = np.percentile(dds_pct, 5)
                d50_pct = np.percentile(dds_pct, 50)
                d95_pct = np.percentile(dds_pct, 95)
                
                fig_dd_dist.add_vline(x=d5_pct, line_dash="dash", line_color="red",
                                      annotation_text=f"P5: {d5_pct:.1f}%", annotation_position="top left")
                fig_dd_dist.add_vline(x=d50_pct, line_dash="dash", line_color="blue",
                                      annotation_text=f"P50: {d50_pct:.1f}%", annotation_position="top")
                fig_dd_dist.add_vline(x=d95_pct, line_dash="dash", line_color="green",
                                      annotation_text=f"P95: {d95_pct:.1f}%", annotation_position="top right")
                
                fig_dd_dist.update_layout(
                    template="plotly_white",
                    height=350,
                    margin=dict(l=20, r=20, t=40, b=40),
                    xaxis_title="Drawdown (%)",
                    yaxis_title="Frequency",
                    showlegend=False
                )
                st.plotly_chart(fig_dd_dist, use_container_width=True, key="mc_dd_dist")


def categorize_strategy(strategy_name, strat_df=None):
    """
    Categorize strategy into Workhorse, Airbag, or Opportunist based on name and trade data.
    
    - Workhorse: Iron condors, credit spreads, premium selling strategies
    - Airbag: Double calendars, long puts, strangles, protective strategies  
    - Opportunist: Bull call spreads, long calls, directional plays
    """
    n = strategy_name.upper()
    
    # Check for explicit patterns
    # WORKHORSE: Premium sellers, iron condors, credit strategies
    workhorse_patterns = ['IC', 'IRON CONDOR', 'MEIC', 'PUT SPREAD', 'CALL SPREAD', 
                          'BPS', 'BCS', 'CREDIT', 'BUTTERFLY', 'FLY', 'BWB',
                          'SHORT PUT', 'SHORT CALL', 'NAKED', 'COVERED']
    
    # AIRBAG: Protective strategies, calendars, long puts
    airbag_patterns = ['CALENDAR', 'DC', 'DOUBLE CALENDAR', 'LONG PUT', 'STRANGLE',
                       'STRADDLE', 'PROTECTIVE', 'COLLAR', 'HEDGE', 'VIX', 'UVXY']
    
    # OPPORTUNIST: Directional plays, long calls, debit spreads
    opportunist_patterns = ['LONG CALL', 'DEBIT', 'BULL CALL', 'BEAR PUT', 'DIRECTIONAL',
                            'MOMENTUM', 'BREAKOUT', 'TREND']
    
    for pattern in workhorse_patterns:
        if pattern in n:
            return 'Workhorse'
    
    for pattern in airbag_patterns:
        if pattern in n:
            return 'Airbag'
    
    for pattern in opportunist_patterns:
        if pattern in n:
            return 'Opportunist'
    
    # Default based on common naming conventions
    if 'METF' in n or 'SPREAD' in n:
        return 'Workhorse'
    
    return 'Workhorse'  # Default to workhorse


def calculate_lots_from_trades(strat_df):
    """
    Calculate the number of lots from trade data.
    A lot = 1 iron condor or 1 contract entry.
    
    Multiple entries per day = multiple lots.
    If quantity column exists, use it.
    """
    if strat_df.empty:
        return 0, 0  # total_lots, avg_lots_per_day
    
    # Check for quantity column
    qty_col = None
    for col in strat_df.columns:
        if col.lower() in ['quantity', 'qty', 'contracts', 'size']:
            qty_col = col
            break
    
    if 'timestamp_open' in strat_df.columns:
        # Group by entry timestamp
        if qty_col:
            # Sum quantities per entry
            lots_per_entry = strat_df.groupby('timestamp_open')[qty_col].sum()
        else:
            # Count legs per entry (for spreads, an IC has 4 legs = 1 lot)
            entries_per_open = strat_df.groupby('timestamp_open').size()
            # Assume 4 legs = 1 IC lot, 2 legs = 1 spread lot, 1 leg = 1 lot
            # This is approximate - each unique timestamp_open is 1 lot
            lots_per_entry = pd.Series(1, index=entries_per_open.index)
        
        total_lots = len(lots_per_entry)
        
        # Calculate avg lots per trading day
        trading_days = strat_df['timestamp_open'].dt.date.nunique()
        avg_lots_per_day = total_lots / trading_days if trading_days > 0 else 0
        
    else:
        # Fallback: use timestamp
        if qty_col:
            total_lots = strat_df[qty_col].sum()
        else:
            # Each row is approximately 1 leg, estimate lots
            total_lots = len(strat_df)
        
        trading_days = strat_df['timestamp'].dt.date.nunique()
        avg_lots_per_day = total_lots / trading_days if trading_days > 0 else 0
    
    return int(total_lots), avg_lots_per_day


def page_portfolio_builder(full_df):
    """
    Enhanced Portfolio Builder with:
    - 1 Lot = 1 contract per day (average daily contracts)
    - Strategy categorization using Greek DNA logic
    - Manual calculation trigger (no auto-calculation)
    - Greek & Risk Exposure section
    """
    st.markdown(
        """<h1 style='color: #4B5563; font-family: "Exo 2", sans-serif; font-weight: 800; 
        text-transform: uppercase; margin-bottom: 0;'>🏗️ PORTFOLIO BUILDER</h1>""",
        unsafe_allow_html=True
    )
    st.caption("INTERACTIVE CONTRACT ALLOCATION — 1 LOT = 1 CONTRACT/DAY")

    if full_df.empty:
        st.info("👆 Please upload CSV files to start building your portfolio.")
        return

    # === SECTION 1: CONFIGURATION ===
    st.markdown("### ⚙️ Configuration")
    
    with st.expander("📊 Account & Risk Settings", expanded=True):
        config_r1_c1, config_r1_c2, config_r1_c3 = st.columns(3)
        
        with config_r1_c1:
            account_size = st.number_input(
                "Account Size ($)", 
                value=100000, 
                step=5000, 
                min_value=1000,
                key="builder_account",
                help="Your total trading capital"
            )
        with config_r1_c2:
            target_margin_pct = st.slider(
                "Target Margin (%)",
                min_value=10,
                max_value=100,
                value=80,
                step=5,
                help="Maximum % of account for margin"
            )
        with config_r1_c3:
            target_margin = account_size * (target_margin_pct / 100)
            st.metric("Margin Budget", f"${target_margin:,.0f}")
    
    # Strategy Type Allocation
    with st.expander("🎯 Strategy Type Allocation", expanded=True):
        st.caption("Define target allocation percentages for each strategy category")
        
        type_c1, type_c2, type_c3, type_c4 = st.columns(4)
        with type_c1:
            workhorse_pct = st.slider(
                "🐴 Workhorse %",
                min_value=0,
                max_value=100,
                value=60,
                step=5,
                help="Iron Condors, Credit Spreads, Premium Selling"
            )
        with type_c2:
            airbag_pct = st.slider(
                "🛡️ Airbag %",
                min_value=0,
                max_value=100,
                value=25,
                step=5,
                help="Double Calendars, Long Puts, Strangles - Protection"
            )
        with type_c3:
            opportunist_pct = st.slider(
                "🎯 Opportunist %",
                min_value=0,
                max_value=100,
                value=15,
                step=5,
                help="Bull Call Spreads, Long Calls, Directional Plays"
            )
        with type_c4:
            total_type_pct = workhorse_pct + airbag_pct + opportunist_pct
            if total_type_pct != 100:
                st.warning(f"⚠️ Total: {total_type_pct}%")
            else:
                st.success(f"✅ Total: {total_type_pct}%")
    
    # Evaluation Period - at the top
    st.markdown("### 📅 Evaluation Period")
    min_d = full_df['timestamp'].min().date()
    max_d = full_df['timestamp'].max().date()
    
    date_c1, date_c2 = st.columns(2)
    with date_c1:
        selected_dates = st.date_input(
            "Select Date Range",
            [min_d, max_d],
            min_value=min_d,
            max_value=max_d,
            key="builder_dates"
        )
    
    if len(selected_dates) != 2:
        st.warning("Please select a date range.")
        return
    
    # Filter data
    filtered_df = full_df[
        (full_df['timestamp'].dt.date >= selected_dates[0]) &
        (full_df['timestamp'].dt.date <= selected_dates[1])
    ].copy()
    
    if filtered_df.empty:
        st.warning("No data in selected date range.")
        return
    
    strategies = sorted(filtered_df['strategy'].unique().tolist())
    full_date_range = pd.date_range(start=selected_dates[0], end=selected_dates[1], freq='D')
    trading_days = len(full_date_range)
    
    # === CALCULATE MAX DAILY LOSS for entire portfolio ===
    # Sum all P&L by day across all strategies
    all_daily_pnl = filtered_df.set_index('timestamp').resample('D')['pnl'].sum()
    all_daily_pnl = all_daily_pnl[all_daily_pnl != 0]  # Remove zero days
    
    if len(all_daily_pnl) > 0:
        max_daily_loss = all_daily_pnl.min()  # Worst single day
        worst_10_days = all_daily_pnl.nsmallest(10)
        avg_worst_10 = worst_10_days.mean()
    else:
        max_daily_loss = 0
        avg_worst_10 = 0
    
    # === SECTION 2: PRE-CALCULATE STRATEGY METRICS ===
    strategy_base_stats = {}
    strategy_daily_pnl = {}
    
    for strat in strategies:
        strat_data = filtered_df[filtered_df['strategy'] == strat].copy()
        if strat_data.empty:
            continue
        
        # Get DNA for category classification
        dna = get_cached_dna(strat, strat_data)
        
        # IMPROVED Category assignment based on strategy name, legs, and patterns
        strat_lower = strat.lower()
        strat_upper = strat.upper()
        dna_type = dna.get('Type', 'Custom').upper()
        
        # Analyze leg structure if available
        sample_leg = strat_data['legs'].iloc[0] if 'legs' in strat_data.columns and len(strat_data) > 0 else ""
        leg_lower = sample_leg.lower() if sample_leg else ""
        
        has_call_short = ' c sto' in leg_lower or ' c sbo' in leg_lower
        has_call_long = ' c bto' in leg_lower or ' c btc' in leg_lower
        has_put_short = ' p sto' in leg_lower or ' p sbo' in leg_lower
        has_put_long = ' p bto' in leg_lower or ' p btc' in leg_lower
        
        # Determine strategy type and category
        category = 'Workhorse'  # Default
        
        # 1. Check for hedging/airbag strategies
        if 'long put' in strat_lower or (has_put_long and not has_put_short and not has_call_short):
            category = 'Airbag'
        elif 'hedge' in strat_lower or 'protection' in strat_lower:
            category = 'Airbag'
        elif 'vix up' in strat_lower or 'vix spike' in strat_lower:
            category = 'Airbag'
        elif 'calendar' in strat_lower or 'dc ' in strat_lower or 'dc5' in strat_lower or 'dc6' in strat_lower:
            category = 'Airbag'
        elif 'ric' in strat_lower or 'reverse iron' in strat_lower:
            category = 'Airbag'
        elif 'bull call' in strat_lower or 'bcs' in strat_lower:
            # BCS is opportunist (betting on upward move)
            category = 'Opportunist'
        
        # 2. Check for opportunist strategies
        elif 'orb' in strat_lower and 'bcs' not in strat_lower:
            category = 'Opportunist'  # Opening Range Breakout
        elif 'momentum' in strat_lower or 'breakout' in strat_lower:
            category = 'Opportunist'
        elif 'long call' in strat_lower or (has_call_long and not has_call_short and not has_put_short):
            category = 'Opportunist'
        elif 'fomc' in strat_lower or 'event' in strat_lower:
            category = 'Opportunist'
        
        # 3. Workhorse strategies (credit-based, steady income)
        elif 'meic' in strat_lower or 'multi entry' in strat_lower:
            category = 'Workhorse'
        elif 'metf' in strat_lower:
            category = 'Workhorse'
        elif 'iron condor' in strat_lower or ' ic ' in strat_lower or strat_lower.endswith(' ic'):
            category = 'Workhorse'
        elif 'bull put' in strat_lower or 'bps' in strat_lower:
            category = 'Workhorse'  # Bull Put Spreads are steady income
        elif 'bear call' in strat_lower:
            category = 'Workhorse'
        elif 'butterfly' in strat_lower or 'fly' in strat_lower or 'bwb' in strat_lower:
            category = 'Workhorse'
        elif has_call_short and has_call_long and has_put_short and has_put_long:
            category = 'Workhorse'  # Iron Condor structure
        elif (has_call_short and has_call_long) or (has_put_short and has_put_long):
            category = 'Workhorse'  # Credit spread
        
        # 4. Fallback based on DNA Greeks
        else:
            if dna.get('Theta') == 'Long' and dna.get('Vega') == 'Short':
                category = 'Workhorse'  # Theta positive strategies
            elif dna.get('Vega') == 'Long':
                category = 'Airbag'  # Long vega = volatility hedge
            else:
                category = 'Workhorse'
        
        # === IRON CONDOR FIX: Count lots by unique entry times ===
        if 'timestamp_open' in strat_data.columns:
            unique_entries = strat_data.groupby('timestamp_open').first()
            total_lots = len(unique_entries)
            
            if 'contracts' in strat_data.columns:
                contracts_per_entry = strat_data.groupby('timestamp_open')['contracts'].first()
                total_contracts = int(contracts_per_entry.sum())
            else:
                total_contracts = total_lots
        else:
            if 'contracts' in strat_data.columns:
                total_contracts = int(strat_data['contracts'].sum())
            else:
                total_contracts = len(strat_data)
            total_lots = total_contracts
        
        if total_lots == 0:
            total_lots = 1
        if total_contracts == 0:
            total_contracts = 1
        
        # Trading days and entries for this strategy
        strat_trading_days = strat_data['timestamp'].dt.date.nunique()
        
        # Number of unique entries (trades)
        if 'timestamp_open' in strat_data.columns:
            num_entries = strat_data['timestamp_open'].nunique()
        else:
            num_entries = len(strat_data)
        
        if num_entries == 0:
            num_entries = 1
        
        # CONTRACTS PER DAY calculation (for MEICs and other multi-entry strategies)
        # If strategy trades 6 times per day, contracts_per_day = 6
        contracts_per_day = num_entries / strat_trading_days if strat_trading_days > 0 else 1
        contracts_per_day = max(0.5, round(contracts_per_day * 2) / 2)  # Round to nearest 0.5
        
        # Margin per contract (per entry)
        if 'margin' in strat_data.columns and 'timestamp_open' in strat_data.columns:
            margin_per_entry = strat_data.groupby('timestamp_open')['margin'].first()
            avg_margin = margin_per_entry.mean()
            if 'contracts' in strat_data.columns:
                contracts_per_entry = strat_data.groupby('timestamp_open')['contracts'].first()
                avg_contracts = contracts_per_entry.mean()
                margin_per_contract = avg_margin / avg_contracts if avg_contracts > 0 else avg_margin
            else:
                margin_per_contract = avg_margin
        elif 'margin' in strat_data.columns:
            margin_per_contract = strat_data['margin'].mean()
        else:
            margin_per_contract = 0
        
        # Calculate PEAK MARGIN (max margin used on any single day)
        # IMPORTANT: For Iron Condors, margin is only charged on ONE side
        # So we take first margin per entry (not sum of all legs)
        if 'margin' in strat_data.columns and 'timestamp_open' in strat_data.columns:
            # Group by date and entry, take first margin per entry, then sum per day
            strat_data['_date'] = strat_data['timestamp'].dt.date
            margin_per_entry_per_day = strat_data.groupby(['_date', 'timestamp_open'])['margin'].first()
            daily_margin = margin_per_entry_per_day.groupby(level=0).sum()
            peak_margin = daily_margin.max() if len(daily_margin) > 0 else margin_per_contract * contracts_per_day
        elif 'margin' in strat_data.columns:
            daily_margin = strat_data.groupby(strat_data['timestamp'].dt.date)['margin'].sum()
            peak_margin = daily_margin.max() if len(daily_margin) > 0 else margin_per_contract * contracts_per_day
        else:
            peak_margin = margin_per_contract * contracts_per_day
        
        # P&L calculations
        total_pnl = strat_data['pnl'].sum()
        
        # P&L per contract/day
        # If you set lots=contracts_per_day, you get total_pnl
        pnl_per_contract = total_pnl / contracts_per_day if contracts_per_day > 0 else total_pnl
        
        # Profit per Margin = Total P&L / Total Margin used over entire period
        total_margin_used = margin_per_contract * total_lots
        profit_per_margin = (total_pnl / total_margin_used) if total_margin_used > 0 else 0
        
        # Win rate by entry
        if 'timestamp_open' in strat_data.columns:
            pnl_per_entry = strat_data.groupby('timestamp_open')['pnl'].sum()
            wins = (pnl_per_entry > 0).sum()
            losses_entries = pnl_per_entry[pnl_per_entry <= 0]
            wins_entries = pnl_per_entry[pnl_per_entry > 0]
            num_trades = len(pnl_per_entry)
        else:
            wins_entries = strat_data[strat_data['pnl'] > 0]['pnl']
            losses_entries = strat_data[strat_data['pnl'] <= 0]['pnl']
            wins = len(wins_entries)
            num_trades = len(strat_data)
        win_rate = wins / num_trades if num_trades > 0 else 0
        
        # Kelly Criterion calculation
        # Kelly = (W * R - L) / R where W = win rate, L = loss rate, R = win/loss ratio
        avg_win = wins_entries.mean() if len(wins_entries) > 0 else 0
        avg_loss = abs(losses_entries.mean()) if len(losses_entries) > 0 else 0
        
        kelly = 0
        if avg_loss > 0 and avg_win > 0:
            win_loss_ratio = avg_win / avg_loss
            kelly = (win_rate * win_loss_ratio - (1 - win_rate)) / win_loss_ratio
            kelly = max(0, min(kelly, 1))  # Clamp between 0 and 1
        
        # Daily PnL series
        daily_pnl = strat_data.set_index('timestamp').resample('D')['pnl'].sum()
        daily_pnl_aligned = daily_pnl.reindex(full_date_range, fill_value=0)
        strategy_daily_pnl[strat] = daily_pnl_aligned
        
        # Max drawdown per contract - divide by contracts_per_day
        cumsum = daily_pnl_aligned.cumsum() / contracts_per_day if contracts_per_day > 0 else daily_pnl_aligned.cumsum()
        peak = cumsum.cummax()
        dd = (cumsum - peak).min()
        
        # MAR ratio per strategy
        strat_cagr = 0
        if strat_trading_days > 30:
            total_ret = total_pnl / (margin_per_contract * contracts_per_day) if margin_per_contract > 0 else 0
            strat_cagr = (1 + total_ret) ** (252 / strat_trading_days) - 1 if total_ret > -1 else 0
        mar_ratio = strat_cagr / abs(dd / margin_per_contract) if dd != 0 and margin_per_contract > 0 else 0
        
        # Margin series for charting
        # IMPORTANT: For Iron Condors, margin is only charged on ONE side
        # So we take first margin per entry (not sum of all legs)
        if 'margin' in strat_data.columns and 'timestamp_open' in strat_data.columns:
            strat_data['_date'] = strat_data['timestamp'].dt.date
            margin_per_entry_per_day = strat_data.groupby(['_date', 'timestamp_open'])['margin'].first()
            daily_margin = margin_per_entry_per_day.groupby(level=0).sum()
            margin_series = pd.Series(daily_margin.values, index=pd.to_datetime(daily_margin.index))
            margin_series = margin_series.reindex(full_date_range, fill_value=0)
        elif 'margin' in strat_data.columns:
            daily_margin = strat_data.groupby(strat_data['timestamp'].dt.date)['margin'].sum()
            margin_series = pd.Series(daily_margin.values, index=pd.to_datetime(daily_margin.index))
            margin_series = margin_series.reindex(full_date_range, fill_value=0)
        else:
            margin_series = pd.Series(0.0, index=full_date_range)
        
        strategy_base_stats[strat] = {
            'category': category,
            'dna': dna,
            'contracts_per_day': contracts_per_day,  # Historical contracts per day
            'total_lots': total_lots,
            'num_entries': num_entries,
            'strat_trading_days': strat_trading_days,
            'trades': num_trades,
            'margin_per_contract': margin_per_contract,  # Margin per single entry/contract
            'peak_margin': peak_margin,  # Peak daily margin (for charting)
            'pnl_per_contract': pnl_per_contract,
            'total_pnl': total_pnl,
            'profit_per_margin': profit_per_margin,
            'win_rate': win_rate,
            'kelly': kelly,
            'max_dd': abs(dd) if dd < 0 else 0,  # Max drawdown in $ for historical level
            'mar_ratio': mar_ratio,
            'daily_pnl_series': daily_pnl_aligned,
            'margin_series': margin_series
        }

    # === SECTION 3: ALLOCATION TABLE ===
    st.markdown("### 📊 Strategy Allocation")
    st.caption("**Lots Multiplier**: 1 = historical level, 0.5 = half, 2 = double. Margin/Lot shows margin per contract.")
    
    # Initialize session state ONCE
    if 'portfolio_allocation' not in st.session_state:
        st.session_state.portfolio_allocation = {}
    if 'category_overrides' not in st.session_state:
        st.session_state.category_overrides = {}
    if 'calculate_kpis' not in st.session_state:
        st.session_state.calculate_kpis = False
    if 'kelly_pct' not in st.session_state:
        st.session_state.kelly_pct = 20
    if 'last_mar' not in st.session_state:
        st.session_state.last_mar = 0
    
    # Prefill with 1 (multiplier = 1 means historical level)
    for strat in strategies:
        if strat not in st.session_state.portfolio_allocation:
            st.session_state.portfolio_allocation[strat] = 1.0

    # Build allocation data
    allocation_data = []
    total_pnl = 0
    total_margin = 0
    total_margin_opt = 0
    total_dd = 0
    
    for strat in strategies:
        if strat not in strategy_base_stats:
            continue
        strat_stats = strategy_base_stats[strat]
        category = st.session_state.category_overrides.get(strat, strat_stats['category'])
        
        kelly = strat_stats.get('kelly', 0)
        hist_lots = strat_stats['contracts_per_day']
        
        # Per-multiplier values (what you get/need for multiplier=1, i.e., historical level)
        # P&L for entire period at historical level
        pnl_historical = strat_stats['total_pnl']
        # Margin per contract (single entry)
        margin_per_contract = strat_stats['margin_per_contract']
        # DD at historical level
        dd_historical = strat_stats['max_dd']
        
        current_multiplier = st.session_state.portfolio_allocation.get(strat, 1.0)
        
        # Margin after optimization = margin_per_contract * hist_lots * multiplier
        margin_opt = margin_per_contract * hist_lots * current_multiplier
        
        allocation_data.append({
            'Category': category,
            'Strategy': strat,
            'Hist': hist_lots,
            'P&L': pnl_historical,  # P&L at historical level (multiplier=1)
            'Margin/Lot': margin_per_contract,  # Margin per single contract
            'Margin After Mult': margin_opt,  # Margin after applying multiplier
            'DD After Mult': dd_historical * current_multiplier,  # DD after applying multiplier
            'Kelly%': kelly * 100,
            'Multiplier': current_multiplier
        })
        
        # Accumulate totals based on current multiplier
        total_pnl += pnl_historical * current_multiplier
        total_margin += margin_per_contract * hist_lots  # Base margin (multiplier=1)
        total_margin_opt += margin_opt
        total_dd += dd_historical * current_multiplier
    
    alloc_df = pd.DataFrame(allocation_data)
    
    # Sort by category
    category_order = {'Workhorse': 0, 'Airbag': 1, 'Opportunist': 2}
    alloc_df['_sort'] = alloc_df['Category'].map(category_order).fillna(3)
    alloc_df = alloc_df.sort_values(['_sort', 'Strategy']).drop('_sort', axis=1)
    
    # Add TOTAL row
    total_row = pd.DataFrame([{
        'Category': '📊 TOTAL',
        'Strategy': '',
        'Hist': None,
        'P&L': total_pnl,
        'Margin/Lot': None,
        'Margin After Mult': total_margin_opt,
        'DD After Mult': total_dd,
        'Kelly%': None,
        'Multiplier': None
    }])
    alloc_df = pd.concat([alloc_df, total_row], ignore_index=True)
    
    # Layout
    alloc_col, action_col = st.columns([5, 1])
    
    with alloc_col:
        # Calculate height for 18 rows (35px per row + header)
        num_rows = min(len(alloc_df), 18)
        editor_height = 35 * num_rows + 40  # 35px per row + 40px header
        
        edited_alloc = st.data_editor(
            alloc_df,
            column_config={
                "Category": st.column_config.SelectboxColumn(
                    "🎨 Type",
                    options=["Workhorse", "Airbag", "Opportunist"],
                    help="🐴 Workhorse | 🛡️ Airbag | 🎯 Opportunist - CLICK TO CHANGE",
                    width="small"
                ),
                "Strategy": st.column_config.TextColumn("Strategy", disabled=True, width="medium"),
                "Hist": st.column_config.NumberColumn("Hist", disabled=True, format="%.1f", help="Historical contracts per day"),
                "P&L": st.column_config.NumberColumn("P&L", disabled=True, format="$%.0f", help="P&L at historical level (multiplier=1)"),
                "Margin/Lot": st.column_config.NumberColumn("Margin/Lot", disabled=True, format="$%.0f", help="Margin per single contract"),
                "Margin After Mult": st.column_config.NumberColumn("Margin", disabled=True, format="$%.0f", help="Margin after applying multiplier"),
                "DD After Mult": st.column_config.NumberColumn("DD", disabled=True, format="$%.0f", help="Max drawdown after applying multiplier"),
                "Kelly%": st.column_config.NumberColumn("Kelly%", disabled=True, format="%.1f%%", help="Kelly Criterion optimal allocation"),
                "Multiplier": st.column_config.NumberColumn(
                    "🎨 MULT",
                    min_value=0.0,
                    max_value=10.0,
                    step=0.1,
                    format="%.2f",
                    help="Lots Multiplier: 1=historical, 0.5=half, 2=double. CLICK TO EDIT."
                ),
            },
            use_container_width=True,
            hide_index=True,
            height=editor_height,
            disabled=["Strategy", "Hist", "P&L", "Margin/Lot", "Margin After Mult", "DD After Mult", "Kelly%"],
            key="allocation_editor_v16"
        )
        
        # Update session state and trigger rerun if changed
        allocation_changed = False
        for _, row in edited_alloc.iterrows():
            if row['Category'] == '📊 TOTAL' or row['Strategy'] == '':
                continue  # Skip total row
            try:
                new_mult = float(row['Multiplier']) if row['Multiplier'] != '' and pd.notna(row['Multiplier']) else 1.0
            except:
                new_mult = 1.0
            old_mult = st.session_state.portfolio_allocation.get(row['Strategy'], 1.0)
            if abs(new_mult - old_mult) > 0.01:
                allocation_changed = True
            st.session_state.portfolio_allocation[row['Strategy']] = new_mult
            st.session_state.category_overrides[row['Strategy']] = row['Category']
        
        # Immediate rerun when allocation changes
        if allocation_changed:
            st.session_state.calculate_kpis = True
            st.rerun()
    
    with action_col:
        st.markdown("##### Actions")
        
        if st.button("🧮 CALCULATE", use_container_width=True, type="primary", help="Calculate KPIs"):
            st.session_state.calculate_kpis = True
            st.rerun()
        
        st.markdown("---")
        
        if st.button("🔄 Reset", use_container_width=True, help="Reset all multipliers to 1"):
            for strat in strategies:
                st.session_state.portfolio_allocation[strat] = 1.0
            st.rerun()
        
        if st.button("❌ Clear", use_container_width=True, help="Set all to 0"):
            for strat in strategies:
                st.session_state.portfolio_allocation[strat] = 0
            st.rerun()
        
        st.markdown("---")
        
        # Kelly optimization with input
        kelly_input = st.number_input(
            "Kelly %",
            min_value=5,
            max_value=100,
            value=st.session_state.kelly_pct,
            step=5,
            help="""**Portfolio Kelly %**
            
The Kelly Criterion suggests what percentage of your target margin to allocate based on each strategy's historical edge.

**How it works:**
• Each strategy has its own Kelly % based on win rate and profit/loss ratio
• Your Portfolio Kelly % determines how much of your target margin to use
• Strategies with higher Kelly % get proportionally more allocation within their category

**Guidelines:**
• Conservative: 10-15%
• Moderate: 20-25%  
• Aggressive: 30%+

**Note:** Full Kelly (100%) is mathematically optimal but very aggressive. Most traders use "fractional Kelly" (10-25%) for smoother equity curves."""
        )
        st.session_state.kelly_pct = kelly_input
        
        if st.button("⚡ Kelly Opt", use_container_width=True, type="primary", help="Allocate using Kelly Criterion"):
            # Store current MAR before optimization
            st.session_state.last_mar = st.session_state.get('current_mar', 0)
            
            optimized = kelly_optimize_allocation(
                strategy_base_stats,
                target_margin,
                kelly_input / 100,
                workhorse_pct / 100,
                airbag_pct / 100,
                opportunist_pct / 100,
                st.session_state.category_overrides,
                3.0  # max_multiplier
            )
            st.session_state.portfolio_allocation = optimized
            st.session_state.calculate_kpis = True
            st.session_state.kelly_optimized = True
            st.rerun()
        
        st.markdown("---")
        
        # MART Optimization with Min P&L input
        min_total_pnl = st.number_input(
            "Min Total P&L ($)",
            min_value=0,
            max_value=10000000,
            value=int(account_size * 3),
            step=10000,
            help="Minimum total P&L target (default: 3x account size)",
            key="mart_min_pnl"
        )
        
        if st.button("🎯 MART Opt", use_container_width=True, type="primary", help="Optimize for maximum MART ratio"):
            # Store current MAR before optimization
            st.session_state.last_mar = st.session_state.get('current_mar', 0)
            
            with st.spinner("Optimizing for MART..."):
                optimized = mart_optimize_allocation(
                    strategy_base_stats,
                    target_margin,
                    account_size,
                    st.session_state.category_overrides,
                    full_date_range,
                    filtered_df,
                    min_total_pnl=min_total_pnl
                )
            st.session_state.portfolio_allocation = optimized
            st.session_state.calculate_kpis = True
            st.session_state.mart_optimized = True
            st.rerun()
    
    # === SECTION 4: KPI CALCULATION ===
    st.divider()
    
    if not st.session_state.calculate_kpis:
        st.info("👆 Adjust allocations above, then click **🧮 CALCULATE** to see portfolio KPIs.")
        return
    
    # DEBUG: Print allocation info
    print("=" * 60)
    print("KPI CALCULATION DEBUG")
    print("=" * 60)
    print(f"portfolio_allocation keys: {list(st.session_state.portfolio_allocation.keys())[:3]}...")
    print(f"portfolio_allocation values: {list(st.session_state.portfolio_allocation.values())[:5]}...")
    print(f"strategy_base_stats keys: {list(strategy_base_stats.keys())[:3]}...")
    
    # Check for matches
    matches = 0
    for strat in st.session_state.portfolio_allocation.keys():
        if strat in strategy_base_stats:
            matches += 1
    print(f"Matching strategies: {matches} / {len(st.session_state.portfolio_allocation)}")
    
    # Calculate portfolio metrics
    portfolio_daily_pnl = pd.Series(0.0, index=full_date_range)
    portfolio_margin = pd.Series(0.0, index=full_date_range)
    
    total_contracts = 0
    total_margin_required = 0
    total_projected_pnl = 0
    
    category_margin = {'Workhorse': 0, 'Airbag': 0, 'Opportunist': 0}
    category_pnl = {'Workhorse': 0, 'Airbag': 0, 'Opportunist': 0}
    
    strategy_contributions = []
    active_strategy_returns = []
    
    for strat, multiplier in st.session_state.portfolio_allocation.items():
        if strat not in strategy_base_stats or multiplier <= 0:
            continue
        
        strat_stats = strategy_base_stats[strat]
        hist_lots = strat_stats['contracts_per_day']
        
        # multiplier is now direct: 1 = historical, 0.5 = half, 2 = double
        
        # Scale daily P&L series
        scaled_pnl = strat_stats['daily_pnl_series'] * multiplier
        portfolio_daily_pnl = portfolio_daily_pnl.add(scaled_pnl, fill_value=0)
        
        # Scale margin series
        strat_margin_series = strat_stats['margin_series'] * multiplier
        portfolio_margin = portfolio_margin.add(strat_margin_series, fill_value=0)
        
        if scaled_pnl.std() > 0:
            active_strategy_returns.append({
                'name': strat,
                'returns': scaled_pnl
            })
        
        category = st.session_state.category_overrides.get(strat, strat_stats['category'])
        
        # P&L calculation: scale historical P&L by multiplier
        strat_actual_pnl = filtered_df[filtered_df['strategy'] == strat]['pnl'].sum()
        strat_pnl = strat_actual_pnl * multiplier
        
        # Margin = margin_per_contract * hist_lots * multiplier
        strat_margin = strat_stats['margin_per_contract'] * hist_lots * multiplier
        
        total_contracts += hist_lots * multiplier
        total_margin_required += strat_margin
        total_projected_pnl += strat_pnl
        
        if category in category_margin:
            category_margin[category] += strat_margin
            category_pnl[category] += strat_pnl
        
        strategy_contributions.append({
            'Strategy': strat,
            'Category': category,
            'Multiplier': multiplier,
            'Margin': strat_margin,
            'Projected P&L': strat_pnl,
            'Weight': 0
        })
    
    # FIXED: Peak margin = maximum daily margin across entire evaluation period
    # This is the actual worst-case margin requirement from historical data
    portfolio_peak_margin = portfolio_margin.max() if len(portfolio_margin) > 0 and portfolio_margin.max() > 0 else total_margin_required
    
    # Mean margin across the evaluation period
    mean_margin = portfolio_margin.mean() if len(portfolio_margin) > 0 else total_margin_required
    
    for sc in strategy_contributions:
        sc['Weight'] = (sc['Margin'] / total_margin_required * 100) if total_margin_required > 0 else 0

    # Portfolio metrics
    portfolio_equity = account_size + portfolio_daily_pnl.cumsum()
    portfolio_returns = portfolio_equity.pct_change().fillna(0)
    
    # Fetch SPX benchmark
    spx_data = None
    spx_returns = pd.Series(dtype=float)
    try:
        spx_data = fetch_spx_benchmark(pd.to_datetime(selected_dates[0]), pd.to_datetime(selected_dates[1]))
        if spx_data is not None and not spx_data.empty:
            spx_aligned = spx_data.reindex(full_date_range, method='ffill')
            spx_returns = spx_aligned.pct_change().fillna(0)
    except Exception as e:
        logger.warning(f"Failed to fetch SPX benchmark: {e}")
    
    # Alpha and Beta calculation
    alpha_val, beta_val = 0, 0
    spx_sharpe, spx_sortino = 0, 0
    try:
        if len(spx_returns) > 20 and len(portfolio_returns) > 20:
            # Ensure both series have the same index
            common_idx = portfolio_returns.index.intersection(spx_returns.index)
            if len(common_idx) > 20:
                port_ret = portfolio_returns.loc[common_idx]
                spx_ret = spx_returns.loc[common_idx]
                
                # Remove any NaN or inf values
                valid_mask = np.isfinite(port_ret) & np.isfinite(spx_ret) & (spx_ret != 0)
                if valid_mask.sum() > 20:
                    y = port_ret[valid_mask].values
                    x = spx_ret[valid_mask].values
                    
                    from scipy import stats as scipy_stats
                    slope, intercept, r_value, p_value, std_err = scipy_stats.linregress(x, y)
                    beta_val = slope
                    alpha_val = intercept * 252  # Annualize
                    
                    # Calculate SPX Sharpe
                    spx_vol = spx_ret[valid_mask].std() * np.sqrt(252)
                    spx_mean_ret = spx_ret[valid_mask].mean() * 252
                    spx_sharpe = (spx_mean_ret - 0.04) / spx_vol if spx_vol > 0 else 0
                    
                    # Calculate SPX Sortino
                    spx_neg = spx_ret[valid_mask][spx_ret[valid_mask] < 0]
                    spx_downside = spx_neg.std() * np.sqrt(252) if len(spx_neg) > 0 else 0
                    spx_sortino = (spx_mean_ret - 0.04) / spx_downside if spx_downside > 0 else 0
    except Exception as e:
        logger.warning(f"Alpha/Beta calculation failed: {e}")
    
    # Correlation matrix
    correlation_matrix = None
    avg_correlation = 0
    if len(active_strategy_returns) > 1:
        corr_df = pd.DataFrame({s['name']: s['returns'] for s in active_strategy_returns})
        correlation_matrix = corr_df.corr()
        corr_mask = np.triu(np.ones_like(correlation_matrix, dtype=bool), k=1)
        avg_correlation = correlation_matrix.where(corr_mask).stack().mean()
        if np.isnan(avg_correlation):
            avg_correlation = 0
    
    # Performance metrics
    if len(portfolio_returns) > 1 and portfolio_returns.std() > 0:
        days = len(portfolio_returns)
        total_ret = (1 + portfolio_returns).prod() - 1
        # CAGR: Annualize using 365 since we're using calendar days
        cagr = (1 + total_ret) ** (365 / days) - 1 if days > 0 and total_ret > -1 else 0
        volatility = portfolio_returns.std() * np.sqrt(252)  # Volatility uses trading days
        sharpe = (portfolio_returns.mean() * 252 - 0.04) / volatility if volatility > 0 else 0
        
        neg_returns = portfolio_returns[portfolio_returns < 0]
        downside_std = neg_returns.std() * np.sqrt(252) if len(neg_returns) > 0 else 0
        sortino = (portfolio_returns.mean() * 252 - 0.04) / downside_std if downside_std > 0 else 0
        
        peak = portfolio_equity.cummax()
        dd = (portfolio_equity - peak) / peak
        max_dd = dd.min()
        max_dd_usd = (portfolio_equity - peak).min()
        
        # DD vs Account Size (percentage of initial account)
        dd_vs_account = abs(max_dd_usd) / account_size if account_size > 0 else 0
        
        mar = cagr / abs(max_dd) if max_dd != 0 else 0
        # MART = CAGR / (MaxDD$ / Account)
        mart = cagr / dd_vs_account if dd_vs_account > 0 else 0
        # MAR on Margin = CAGR / (MaxDD$ / MeanMargin)
        mar_on_margin = cagr / (abs(max_dd_usd) / mean_margin) if max_dd_usd != 0 and mean_margin > 0 else 0
    else:
        cagr, volatility, sharpe, sortino, max_dd, max_dd_usd, mar, mart, mar_on_margin, dd_vs_account = 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
        dd = pd.Series(0.0, index=full_date_range)

    # Store current MAR for comparison
    st.session_state.current_mar = mar
    
    # Calculate monthly returns for chart
    monthly_pnl = portfolio_daily_pnl.resample('M').sum()
    monthly_returns_pct = (monthly_pnl / account_size) * 100
    
    # Calculate actual total P&L: sum of (strategy_pnl * multiplier)
    actual_total_pnl = 0
    for strat, multiplier in st.session_state.portfolio_allocation.items():
        if multiplier <= 0:
            continue
        strat_pnl = filtered_df[filtered_df['strategy'] == strat]['pnl'].sum()
        actual_total_pnl += strat_pnl * multiplier

    # === SECTION 5: KPI DASHBOARD (matching Portfolio Analytics layout) ===
    st.markdown("### 📈 Portfolio KPIs")
    
    # Calculate ACTUAL max daily loss and avg worst 10 from portfolio P&L (with multipliers applied)
    portfolio_daily_pnl_nonzero = portfolio_daily_pnl[portfolio_daily_pnl != 0]
    if len(portfolio_daily_pnl_nonzero) > 0:
        actual_max_daily_loss = portfolio_daily_pnl_nonzero.min()  # Worst single day
        worst_10 = portfolio_daily_pnl_nonzero.nsmallest(10)
        actual_avg_worst_10 = worst_10.mean() if len(worst_10) > 0 else 0
    else:
        actual_max_daily_loss = 0
        actual_avg_worst_10 = 0
    
    # Show Kelly optimization warning if MAR decreased
    if st.session_state.get('kelly_optimized', False):
        last_mar = st.session_state.get('last_mar', 0)
        if last_mar > 0 and mar < last_mar:
            st.warning(f"⚠️ **Kelly Optimization Warning**: MAR decreased from {last_mar:.2f} to {mar:.2f}. Consider adjusting the Kelly % or category allocations.")
        st.session_state.kelly_optimized = False  # Reset flag
    
    # ROW 1: Primary metrics (6 columns like Portfolio Analytics)
    kpi_r1 = st.columns(6)
    with kpi_r1[0]:
        render_hero_metric("Total P/L", f"${actual_total_pnl:,.0f}", "", "hero-teal" if actual_total_pnl > 0 else "hero-coral",
                          tooltip="Total profit/loss across all strategies with applied multipliers")
    with kpi_r1[1]:
        render_hero_metric("CAGR", f"{cagr:.1%}", "", "hero-teal" if cagr > 0 else "hero-coral",
                          tooltip="Compound Annual Growth Rate - annualized return assuming reinvestment")
    with kpi_r1[2]:
        render_hero_metric("Max DD (%)", f"{max_dd:.1%}", "", "hero-coral",
                          tooltip="Maximum Drawdown - largest peak-to-trough decline as percentage")
    with kpi_r1[3]:
        render_hero_metric("Max DD ($)", f"${abs(max_dd_usd):,.0f}", "", "hero-coral",
                          tooltip="Maximum Drawdown in dollars - largest peak-to-trough decline")
    with kpi_r1[4]:
        render_hero_metric("MAR Ratio", f"{mar:.2f}", "", "hero-teal" if mar > 1 else "hero-coral",
                          tooltip="CAGR divided by Max Drawdown %. Above 1.0 is good, above 2.0 is excellent")
    with kpi_r1[5]:
        render_hero_metric("MART Ratio", f"{mart:.2f}", "", "hero-teal" if mart > 1 else "hero-coral",
                          tooltip="CAGR divided by (MaxDD$ / Account Size). Measures return vs account-relative risk")

    st.write("")
    
    # ROW 2: Secondary metrics (neutral/black & white)
    kpi_r2 = st.columns(6)
    with kpi_r2[0]:
        # Peak Margin = maximum daily margin across entire evaluation period
        peak_margin_util = (portfolio_peak_margin / account_size) * 100 if account_size > 0 else 0
        render_hero_metric("Peak Margin", f"${portfolio_peak_margin:,.0f}", f"{peak_margin_util:.0f}% of account", "hero-neutral",
                          tooltip="Maximum margin requirement reached during evaluation period")
    with kpi_r2[1]:
        # Mean Margin
        mean_margin_util = (mean_margin / account_size) * 100 if account_size > 0 else 0
        render_hero_metric("Mean Margin", f"${mean_margin:,.0f}", f"{mean_margin_util:.0f}% of account", "hero-neutral",
                          tooltip="Average margin requirement over the evaluation period")
    with kpi_r2[2]:
        active_strats = len([s for s, c in st.session_state.portfolio_allocation.items() if c > 0])
        render_hero_metric("Active Strats", f"{active_strats}", f"{total_contracts:.1f} contracts/day", "hero-neutral",
                          tooltip="Number of strategies with multiplier > 0")
    with kpi_r2[3]:
        spx_sharpe_txt = f"SPX: {spx_sharpe:.2f}" if spx_sharpe != 0 else ""
        render_hero_metric("Sharpe", f"{sharpe:.2f}", spx_sharpe_txt, "hero-neutral",
                          tooltip="Risk-adjusted return: (Return - Risk-free rate) / Volatility. Above 1.0 is good, above 2.0 is excellent")
    with kpi_r2[4]:
        spx_sortino_txt = f"SPX: {spx_sortino:.2f}" if spx_sortino != 0 else ""
        render_hero_metric("Sortino", f"{sortino:.2f}", spx_sortino_txt, "hero-neutral",
                          tooltip="Like Sharpe but only penalizes downside volatility. Above 1.5 is good, above 2.0 is excellent")
    with kpi_r2[5]:
        render_hero_metric("DD vs Account", f"{dd_vs_account:.1%}", f"${abs(max_dd_usd):,.0f} of ${account_size:,.0f}", "hero-neutral",
                          tooltip="Maximum drawdown as percentage of account size")

    st.write("")
    
    # ROW 3: Alpha/Beta, Max Daily Loss, Correlation (neutral/black & white)
    kpi_r3 = st.columns(6)
    with kpi_r3[0]:
        render_hero_metric("Alpha", f"{alpha_val:.1%}", "vs SPX", "hero-neutral",
                          tooltip="Excess return above what beta would predict. Positive alpha = outperforming the market")
    with kpi_r3[1]:
        render_hero_metric("Beta", f"{beta_val:.2f}", "vs SPX", "hero-neutral",
                          tooltip="Sensitivity to market movements. Beta < 1 = less volatile than market")
    with kpi_r3[2]:
        render_hero_metric("MAR on Margin", f"{mar_on_margin:.2f}", "CAGR/(DD/AvgMargin)", "hero-neutral",
                          tooltip="CAGR divided by (MaxDD$ / Average Margin). Shows return efficiency relative to margin used")
    with kpi_r3[3]:
        render_hero_metric("Max Daily Loss", f"-${abs(actual_max_daily_loss):,.0f}", f"Avg 10 worst: -${abs(actual_avg_worst_10):,.0f}", "hero-neutral",
                          tooltip="Worst single-day loss in the portfolio. Avg 10 worst shows average of the 10 worst days")
    with kpi_r3[4]:
        render_hero_metric("Avg Correlation", f"{avg_correlation:.2f}", "Lower = better", "hero-neutral",
                          tooltip="Average pairwise correlation between strategies. Lower = better diversification")
    with kpi_r3[5]:
        render_hero_metric("Profit Factor", f"{(actual_total_pnl / abs(max_dd_usd)) if max_dd_usd != 0 else 0:.2f}", "P&L / Max DD", "hero-neutral",
                          tooltip="Total P&L divided by Maximum Drawdown. Higher = better reward for risk taken")

    # Monte Carlo Stress Test button
    st.write("")
    mc_col1, mc_col2, mc_col3 = st.columns([1, 2, 1])
    with mc_col2:
        if st.button("🎲 Stress Test with Monte Carlo →", use_container_width=True, type="primary", 
                     help="Run Monte Carlo simulation on the assembled portfolio"):
            # Save portfolio data to session state for Monte Carlo page
            st.session_state.mc_portfolio_daily_pnl = portfolio_daily_pnl
            st.session_state.mc_portfolio_account_size = account_size
            st.session_state.mc_portfolio_name = "Assembled Portfolio"
            st.session_state.mc_from_builder = True
            st.session_state.mc_new_from_builder = True  # Flag to reset MC state
            st.session_state.navigate_to_page = "🎲  Monte Carlo Punisher"
            st.rerun()

    st.divider()
    
    # === SECTION 6: VISUALIZATION TABS ===
    viz_tab1, viz_tab2, viz_tab3, viz_tab4, viz_tab5 = st.tabs(["📈 Equity & DD", "📊 Allocation", "💰 Margin", "🔗 Correlation", "🧬 Greek Exposure"])
    
    with viz_tab1:
        # Equity curve with SPX
        fig_equity = go.Figure()
        fig_equity.add_trace(go.Scatter(
            x=portfolio_equity.index, y=portfolio_equity.values,
            mode='lines', name='Portfolio',
            line=dict(color=COLOR_BLUE, width=3),
            fill='tozeroy', fillcolor='rgba(48, 43, 255, 0.1)'
        ))
        
        if spx_data is not None and not spx_data.empty:
            spx_aligned = spx_data.reindex(full_date_range, method='ffill')
            if not spx_aligned.empty and spx_aligned.iloc[0] > 0:
                spx_normalized = (spx_aligned / spx_aligned.iloc[0]) * account_size
                fig_equity.add_trace(go.Scatter(
                    x=spx_normalized.index, y=spx_normalized.values,
                    mode='lines', name='S&P 500',
                    line=dict(color='gray', width=2, dash='dot')
                ))
        
        fig_equity.add_hline(y=account_size, line_dash="dash", line_color="lightgray")
        fig_equity.update_layout(template="plotly_white", height=400, title="Portfolio vs S&P 500",
                                legend=dict(orientation="h", y=1.02, x=1, xanchor="right"))
        st.plotly_chart(fig_equity, use_container_width=True)
        
        # Drawdown toggle
        dd_view = st.radio("Drawdown:", ["Percentage", "Dollar"], horizontal=True, key="dd_toggle_builder")
        fig_dd = go.Figure()
        if "Percentage" in dd_view:
            fig_dd.add_trace(go.Scatter(x=dd.index, y=dd.values, fill='tozeroy', line=dict(color=COLOR_CORAL, width=1)))
            fig_dd.update_layout(template="plotly_white", height=250, title=f"Drawdown (Max: {max_dd:.1%})", yaxis_tickformat='.1%')
        else:
            dd_dollars = portfolio_equity - portfolio_equity.cummax()
            fig_dd.add_trace(go.Scatter(x=dd_dollars.index, y=dd_dollars.values, fill='tozeroy', line=dict(color=COLOR_CORAL, width=1)))
            fig_dd.update_layout(template="plotly_white", height=250, title=f"Drawdown (Max: ${abs(max_dd_usd):,.0f})", yaxis_tickformat='$,.0f')
        st.plotly_chart(fig_dd, use_container_width=True)
        
        # Monthly Returns TABLE (Year x Month format)
        st.markdown("##### Monthly Returns")
        if len(monthly_pnl) > 0:
            # Create monthly P&L DataFrame
            monthly_df = pd.DataFrame({'pnl': monthly_pnl})
            monthly_df['Year'] = monthly_df.index.year
            monthly_df['Month'] = monthly_df.index.month
            
            # Pivot to Year x Month format
            month_names = {1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr', 5: 'May', 6: 'Jun',
                          7: 'Jul', 8: 'Aug', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dec'}
            
            pivot = monthly_df.pivot_table(index='Year', columns='Month', values='pnl', aggfunc='sum').fillna(0)
            pivot.columns = [month_names.get(c, c) for c in pivot.columns]
            
            # Add row totals (Year Total)
            pivot['Total'] = pivot.sum(axis=1)
            
            # Add column totals (Monthly Average)
            avg_row = pivot.mean()
            avg_row.name = 'Average'
            pivot = pd.concat([pivot, pd.DataFrame([avg_row])])
            
            # Style the table with color coding
            def color_monthly(val):
                try:
                    num_val = float(val) if not isinstance(val, str) else float(val.replace('$', '').replace(',', ''))
                    if num_val > 0:
                        intensity = min(abs(num_val) / 5000, 1)
                        return f'background-color: rgba(0, 210, 190, {0.1 + intensity * 0.4}); color: #065F46'
                    elif num_val < 0:
                        intensity = min(abs(num_val) / 5000, 1)
                        return f'background-color: rgba(255, 46, 77, {0.1 + intensity * 0.4}); color: #991B1B'
                    else:
                        return 'background-color: white; color: #374151'
                except:
                    return 'background-color: white; color: #374151'
            
            # Display styled table
            st.dataframe(
                pivot.style.applymap(color_monthly).format("${:,.0f}"),
                use_container_width=True
            )
            
            # Monthly summary stats
            pos_months = (monthly_pnl > 0).sum()
            neg_months = (monthly_pnl <= 0).sum()
            avg_month = monthly_pnl.mean()
            best_month = monthly_pnl.max()
            worst_month = monthly_pnl.min()
            
            m_col1, m_col2, m_col3, m_col4, m_col5 = st.columns(5)
            with m_col1:
                st.metric("Positive Months", f"{pos_months}")
            with m_col2:
                st.metric("Negative Months", f"{neg_months}")
            with m_col3:
                st.metric("Avg Month", f"${avg_month:,.0f}")
            with m_col4:
                st.metric("Best Month", f"${best_month:,.0f}")
            with m_col5:
                st.metric("Worst Month", f"${worst_month:,.0f}")
    
    with viz_tab2:
        alloc_view = st.radio("View:", ["Margin by Category", "P&L by Category"], horizontal=True, key="alloc_toggle")
        col_pie1, col_pie2 = st.columns(2)
        
        with col_pie1:
            if "Margin" in alloc_view:
                fig_cat = go.Figure(data=[go.Pie(
                    labels=['🐴 Workhorse', '🛡️ Airbag', '🎯 Opportunist'],
                    values=[category_margin['Workhorse'], category_margin['Airbag'], category_margin['Opportunist']],
                    hole=0.4, marker_colors=[COLOR_BLUE, COLOR_TEAL, COLOR_PURPLE]
                )])
                fig_cat.update_layout(title="Margin by Category", height=350)
            else:
                fig_cat = go.Figure(data=[go.Pie(
                    labels=['🐴 Workhorse', '🛡️ Airbag', '🎯 Opportunist'],
                    values=[max(0, category_pnl['Workhorse']), max(0, category_pnl['Airbag']), max(0, category_pnl['Opportunist'])],
                    hole=0.4, marker_colors=[COLOR_BLUE, COLOR_TEAL, COLOR_PURPLE]
                )])
                fig_cat.update_layout(title="P&L by Category", height=350)
            st.plotly_chart(fig_cat, use_container_width=True)
        
        with col_pie2:
            if strategy_contributions:
                contrib_df = pd.DataFrame(strategy_contributions)
                fig_strat = go.Figure(data=[go.Pie(
                    labels=contrib_df['Strategy'],
                    values=contrib_df['Margin'] if "Margin" in alloc_view else contrib_df['Projected P&L'].abs(),
                    hole=0.4
                )])
                fig_strat.update_layout(title="By Strategy", height=350)
                st.plotly_chart(fig_strat, use_container_width=True)
        
        if strategy_contributions:
            st.markdown("##### Strategy Contributions")
            st.dataframe(pd.DataFrame(strategy_contributions)[['Category', 'Strategy', 'Multiplier', 'Margin', 'Projected P&L', 'Weight']].style.format({
                'Multiplier': '{:.1f}x', 'Margin': '${:,.0f}', 'Projected P&L': '${:,.0f}', 'Weight': '{:.1f}%'
            }), use_container_width=True, hide_index=True)
    
    with viz_tab3:
        st.markdown("##### Margin Usage Over Time")
        
        # Calculate actual daily margin from CSV data with proper scaling
        margin_usage = pd.Series(0.0, index=full_date_range)
        for strat, multiplier in st.session_state.portfolio_allocation.items():
            if strat not in strategy_base_stats or multiplier <= 0:
                continue
            strat_stats = strategy_base_stats[strat]
            
            # multiplier is already the scaling factor
            strat_data = filtered_df[filtered_df['strategy'] == strat].copy()
            if 'margin' in strat_data.columns and 'timestamp_open' in strat_data.columns:
                # For Iron Condors: only count one side per entry
                strat_data['_date'] = strat_data['timestamp'].dt.date
                margin_per_entry = strat_data.groupby(['_date', 'timestamp_open'])['margin'].first()
                daily_margin = margin_per_entry.groupby(level=0).sum()
                for date, margin_val in daily_margin.items():
                    date_ts = pd.Timestamp(date)
                    if date_ts in margin_usage.index:
                        margin_usage.loc[date_ts] += margin_val * multiplier
            elif 'margin' in strat_data.columns:
                daily_margin = strat_data.groupby(strat_data['timestamp'].dt.date)['margin'].sum()
                for date, margin_val in daily_margin.items():
                    date_ts = pd.Timestamp(date)
                    if date_ts in margin_usage.index:
                        margin_usage.loc[date_ts] += margin_val * multiplier
        
        margin_usage_filled = margin_usage.replace(0, np.nan).ffill().fillna(0)
        avg_chart_margin = margin_usage_filled[margin_usage_filled > 0].mean() if (margin_usage_filled > 0).any() else 0
        
        fig_margin = go.Figure()
        fig_margin.add_trace(go.Scatter(x=margin_usage_filled.index, y=margin_usage_filled.values, fill='tozeroy', line=dict(color=COLOR_PURPLE, width=2), name='Daily Margin'))
        fig_margin.add_hline(y=target_margin, line_dash="dash", line_color="orange", annotation_text="Target")
        fig_margin.add_hline(y=account_size, line_dash="dash", line_color="red", annotation_text="Account")
        fig_margin.add_hline(y=portfolio_peak_margin, line_dash="dot", line_color="blue", annotation_text=f"Peak: ${portfolio_peak_margin:,.0f}")
        fig_margin.update_layout(template="plotly_white", height=400, title="Margin Over Time", xaxis=dict(rangeslider=dict(visible=True)))
        st.plotly_chart(fig_margin, use_container_width=True)
        
        # Explanation of margin
        with st.expander("ℹ️ Understanding Peak Margin"):
            st.markdown(f"""
            **KPI "Peak Margin" = ${portfolio_peak_margin:,.0f}**  
            This is the **maximum margin used on any single day** across the entire evaluation period, scaled by your multipliers.
            This represents the **worst-case margin requirement** you should plan for.
            
            **Chart Average = ${avg_chart_margin:,.0f}**  
            This shows the **average daily margin** actually used.
            
            **Why Peak > Average:**
            - **Overlapping positions**: Multiple trades open simultaneously (e.g., daily trades with 20+ DTE = ~20 overlapping positions)
            - **Varying activity**: Some days have more entries than others
            - **Use Peak for planning**: Ensure your account can handle the worst-case margin day
            """)
    
    with viz_tab4:
        if correlation_matrix is not None and len(correlation_matrix) > 1:
            # Truncate names but store full names for hover
            full_names = list(correlation_matrix.columns)
            short_names = [s[:12] + '...' if len(s) > 12 else s for s in full_names]
            
            # Create custom hover text with full strategy names
            hover_text = []
            for i, row_name in enumerate(full_names):
                row_hover = []
                for j, col_name in enumerate(full_names):
                    row_hover.append(f"{row_name}<br>vs<br>{col_name}<br>Corr: {correlation_matrix.iloc[i, j]:.2f}")
                hover_text.append(row_hover)
            
            fig_corr = go.Figure(data=go.Heatmap(
                z=correlation_matrix.values,
                x=short_names,
                y=short_names,
                colorscale='RdBu_r',
                zmin=-1, zmax=1,
                text=np.round(correlation_matrix.values, 2),
                texttemplate="%{text}",
                textfont={"size": 9},
                hovertext=hover_text,
                hovertemplate="%{hovertext}<extra></extra>"
            ))
            n_strats = len(correlation_matrix)
            chart_height = max(500, min(900, 150 + n_strats * 35))
            fig_corr.update_layout(title="Strategy Correlation", height=chart_height,
                                   xaxis=dict(tickangle=45, tickfont=dict(size=9)),
                                   yaxis=dict(tickfont=dict(size=9)),
                                   margin=dict(l=120, r=20, t=50, b=120))
            st.plotly_chart(fig_corr, use_container_width=True)
            st.caption(f"**Avg Correlation: {avg_correlation:.2f}** — Hover for full strategy names")
        else:
            st.info("Need 2+ active strategies for correlation matrix.")
    
    with viz_tab5:
        # === GREEK & RISK EXPOSURE (moved from Portfolio Construction) ===
        st.markdown("##### Greek Exposure Analysis")
        
        greek_stats = {'Delta': {'Long': 0, 'Short': 0, 'Neutral': 0},
                       'Vega': {'Long': 0, 'Short': 0, 'Neutral': 0},
                       'Theta': {'Long': 0, 'Short': 0, 'Neutral': 0}}
        profit_greek = {'Delta': {'Long': 0, 'Short': 0, 'Neutral': 0},
                        'Vega': {'Long': 0, 'Short': 0, 'Neutral': 0},
                        'Theta': {'Long': 0, 'Short': 0, 'Neutral': 0}}
        greek_data = []
        
        for strat, multiplier in st.session_state.portfolio_allocation.items():
            if strat not in strategy_base_stats or multiplier <= 0:
                continue
            strat_stats = strategy_base_stats[strat]
            dna = strat_stats['dna']
            scaled_pnl = strat_stats['total_pnl'] * multiplier
            
            greek_stats['Delta'][dna['Delta']] += 1
            greek_stats['Vega'][dna['Vega']] += 1
            greek_stats['Theta'][dna['Theta']] += 1
            
            profit_greek['Delta'][dna['Delta']] += scaled_pnl
            profit_greek['Vega'][dna['Vega']] += scaled_pnl
            profit_greek['Theta'][dna['Theta']] += scaled_pnl
            
            greek_data.append({
                'Strategy': strat, 'Type': dna['Type'], 'Multiplier': multiplier,
                'Delta': dna['Delta'], 'Vega': dna['Vega'], 'Theta': dna['Theta'],
                'Scaled P&L': scaled_pnl
            })
        
        def make_donut(title, data_dict):
            fig = go.Figure(data=[go.Pie(labels=list(data_dict.keys()), values=list(data_dict.values()), hole=.5)])
            fig.update_layout(title_text=title, height=280, margin=dict(l=10, r=10, t=40, b=10))
            return fig
        
        g1, g2, g3 = st.columns(3)
        with g1:
            st.plotly_chart(make_donut("Delta", greek_stats['Delta']), use_container_width=True)
        with g2:
            st.plotly_chart(make_donut("Vega", greek_stats['Vega']), use_container_width=True)
        with g3:
            st.plotly_chart(make_donut("Theta", greek_stats['Theta']), use_container_width=True)
        
        st.markdown("##### P&L by Greek Stance")
        st.dataframe(pd.DataFrame(profit_greek).style.format("${:,.0f}"), use_container_width=True)
        
        with st.expander("Strategy Greek Details"):
            if greek_data:
                st.dataframe(pd.DataFrame(greek_data).style.format({'Scaled P&L': '${:,.0f}'}), use_container_width=True, hide_index=True)

def kelly_optimize_allocation(strategy_stats, target_margin, kelly_pct,
                              workhorse_target, airbag_target, opportunist_target,
                              category_overrides=None, max_multiplier=3.0):
    """
    Kelly Criterion-based optimization that:
    - Uses Portfolio Kelly % to determine total capital to allocate
    - Respects category allocation targets (Workhorse/Airbag/Opportunist)
    - Allocates within each category proportionally to strategy Kelly %
    - Returns MULTIPLIERS (1 = historical level)
    - Uses proper lot fractions (e.g., 1/6 for 6-lot strategy)
    """
    if category_overrides is None:
        category_overrides = {}
    
    # Available capital = target_margin * kelly_pct
    available_capital = target_margin * kelly_pct
    
    # Category budgets
    category_budgets = {
        'Workhorse': available_capital * workhorse_target,
        'Airbag': available_capital * airbag_target,
        'Opportunist': available_capital * opportunist_target
    }
    
    # Group strategies by category and calculate Kelly totals
    category_strategies = {'Workhorse': [], 'Airbag': [], 'Opportunist': []}
    category_kelly_totals = {'Workhorse': 0, 'Airbag': 0, 'Opportunist': 0}
    
    for strat, stats in strategy_stats.items():
        category = category_overrides.get(strat, stats.get('category', 'Workhorse'))
        kelly = max(0, stats.get('kelly', 0))  # Ignore negative Kelly
        hist_lots = stats.get('contracts_per_day', 1)
        
        # Margin at historical level = margin_per_contract * hist_lots
        margin_historical = stats.get('margin_per_contract', 0) * hist_lots
        
        if margin_historical <= 0:
            continue
        
        if category in category_strategies:
            category_strategies[category].append({
                'strategy': strat,
                'kelly': kelly,
                'margin_historical': margin_historical,
                'hist_lots': hist_lots,
                'margin_per_contract': stats.get('margin_per_contract', 0)
            })
            category_kelly_totals[category] += kelly
    
    # Allocate within each category based on relative Kelly %
    allocation = {}
    
    for category, strategies in category_strategies.items():
        budget = category_budgets.get(category, 0)
        kelly_total = category_kelly_totals.get(category, 0)
        
        for s in strategies:
            if kelly_total > 0 and s['kelly'] > 0:
                # Relative weight within category
                weight = s['kelly'] / kelly_total
                allocated_margin = budget * weight
                
                # Convert to multiplier: how much of historical level?
                multiplier = allocated_margin / s['margin_historical'] if s['margin_historical'] > 0 else 0
                
                # Proper lot fractions based on hist_lots
                hist_lots = s['hist_lots']
                if hist_lots <= 1:
                    # Only whole numbers allowed: 0, 1, 2, 3
                    multiplier = round(multiplier)
                else:
                    # Step size = 1 / hist_lots (e.g., 1/6 = 0.1667 for 6-lot strategy)
                    step = 1.0 / hist_lots
                    # Round to nearest valid step
                    multiplier = round(multiplier / step) * step
                
                # Cap at max_multiplier
                multiplier = min(multiplier, max_multiplier)
                multiplier = max(0, multiplier)  # No negative
            else:
                multiplier = 0
            
            allocation[s['strategy']] = round(multiplier, 4)
    
    return allocation


def mart_optimize_allocation(strategy_stats, target_margin, account_size,
                             category_overrides=None, full_date_range=None,
                             filtered_df=None, min_total_pnl=0, max_iterations=100):
    """
    MART Ratio optimization that:
    - Maximizes MART = CAGR / (MaxDD$ / Account)
    - Stays within target margin constraint
    - Tries to meet min_total_pnl target
    - Returns MULTIPLIERS (1 = historical level)
    """
    
    if category_overrides is None:
        category_overrides = {}
    
    # Build strategy info
    strategies = []
    for strat, stats in strategy_stats.items():
        hist_lots = stats['contracts_per_day']
        margin_per_mult = stats['margin_per_contract'] * hist_lots
        total_pnl_at_1x = stats.get('total_pnl', 0)
        
        if margin_per_mult <= 0 or hist_lots <= 0:
            continue
        
        daily_pnl = stats.get('daily_pnl_series', None)
        if daily_pnl is None:
            continue
        
        # Step size based on hist_lots
        if hist_lots <= 1:
            step = 1.0
            allowed_values = [0, 1]
        else:
            step = max(0.1, round(1 / hist_lots, 1))
            allowed_values = None
        
        strategies.append({
            'name': strat,
            'hist_lots': hist_lots,
            'margin_per_mult': margin_per_mult,
            'total_pnl_at_1x': total_pnl_at_1x,
            'daily_pnl': daily_pnl,
            'step': step,
            'allowed_values': allowed_values,
            'max_mult': 3.0
        })
    
    if not strategies or full_date_range is None:
        return {s['name']: 1.0 for s in strategies}
    
    # Initialize allocation at 0
    allocation = {s['name']: 0.0 for s in strategies}
    
    def calculate_metrics(alloc):
        """Calculate MART and P&L for allocation."""
        portfolio_pnl = pd.Series(0.0, index=full_date_range)
        total_margin = 0
        total_pnl = 0
        
        for s in strategies:
            mult = alloc.get(s['name'], 0)
            if mult <= 0:
                continue
            
            portfolio_pnl = portfolio_pnl.add(s['daily_pnl'] * mult, fill_value=0)
            total_margin += s['margin_per_mult'] * mult
            total_pnl += s['total_pnl_at_1x'] * mult
        
        if total_margin == 0:
            return 0, 0, 0
        
        portfolio_equity = account_size + portfolio_pnl.cumsum()
        
        if len(portfolio_equity) < 2:
            return 0, total_margin, total_pnl
        
        days = len(portfolio_pnl)
        total_ret = portfolio_pnl.sum() / account_size
        # CAGR: Annualize using 365 since portfolio_pnl uses calendar days
        cagr = (1 + total_ret) ** (365 / days) - 1 if days > 0 and total_ret > -1 else 0
        
        peak = portfolio_equity.cummax()
        dd_dollars = (portfolio_equity - peak).min()
        max_dd_usd = abs(dd_dollars)
        
        dd_vs_account = max_dd_usd / account_size if account_size > 0 else 1
        mart = cagr / dd_vs_account if dd_vs_account > 0 else 0
        
        return mart, total_margin, total_pnl
    
    # Greedy optimization - maximize MART within margin constraint
    best_mart = 0
    
    for iteration in range(max_iterations):
        best_improvement = 0
        best_change = None
        
        for s in strategies:
            current_mult = allocation[s['name']]
            
            # Get next multiplier value
            if s['allowed_values']:
                if current_mult in s['allowed_values']:
                    idx = s['allowed_values'].index(current_mult)
                else:
                    idx = 0
                if idx < len(s['allowed_values']) - 1:
                    new_mult = s['allowed_values'][idx + 1]
                else:
                    continue
            else:
                new_mult = round(current_mult + s['step'], 1)
                if new_mult > s['max_mult']:
                    continue
            
            # Test this change
            test_alloc = allocation.copy()
            test_alloc[s['name']] = new_mult
            
            mart, margin, pnl = calculate_metrics(test_alloc)
            
            # Check margin constraint
            if margin > target_margin * 1.05:
                continue
            
            improvement = mart - best_mart
            if improvement > best_improvement:
                best_improvement = improvement
                best_change = (s['name'], new_mult, mart)
        
        if best_change and best_improvement > 0.001:
            allocation[best_change[0]] = best_change[1]
            best_mart = best_change[2]
        else:
            break
    
    # If min_total_pnl not met, keep adding best P&L strategies
    if min_total_pnl > 0:
        _, _, current_pnl = calculate_metrics(allocation)
        
        # Sort by P&L efficiency
        strategies_by_pnl = sorted(strategies, 
            key=lambda s: s['total_pnl_at_1x'] / max(1, s['margin_per_mult']), 
            reverse=True)
        
        for _ in range(max_iterations):
            _, current_margin, current_pnl = calculate_metrics(allocation)
            
            if current_pnl >= min_total_pnl:
                break
            if current_margin >= target_margin * 1.05:
                break
            
            added = False
            for s in strategies_by_pnl:
                current_mult = allocation[s['name']]
                
                if s['allowed_values']:
                    if current_mult in s['allowed_values']:
                        idx = s['allowed_values'].index(current_mult)
                    else:
                        idx = 0
                    if idx < len(s['allowed_values']) - 1:
                        new_mult = s['allowed_values'][idx + 1]
                    else:
                        continue
                else:
                    new_mult = round(current_mult + s['step'], 1)
                    if new_mult > s['max_mult']:
                        continue
                
                test_alloc = allocation.copy()
                test_alloc[s['name']] = new_mult
                _, test_margin, _ = calculate_metrics(test_alloc)
                
                if test_margin <= target_margin * 1.05:
                    allocation[s['name']] = new_mult
                    added = True
                    break
            
            if not added:
                break
    
    return allocation


def auto_optimize_allocation_v2(strategy_stats, target_margin, account_size,
                                 workhorse_target, airbag_target, opportunist_target,
                                 category_overrides=None):
    """
    Enhanced optimization that considers:
    - Category allocation targets (Workhorse/Airbag/Opportunist)
    - Risk-adjusted returns (P&L/DD ratio)
    - Margin budget per category
    """
    if category_overrides is None:
        category_overrides = {}
    
    # Calculate category budgets
    category_budgets = {
        'Workhorse': target_margin * workhorse_target,
        'Airbag': target_margin * airbag_target,
        'Opportunist': target_margin * opportunist_target
    }
    category_used = {'Workhorse': 0, 'Airbag': 0, 'Opportunist': 0}
    
    # Score each strategy
    scored_strategies = []
    for strat, strat_stats in strategy_stats.items():
        # Handle both old and new field names
        margin_per_lot = strat_stats.get('margin_per_contract', strat_stats.get('margin_per_lot', 0))
        pnl_per_lot = strat_stats.get('pnl_per_contract', strat_stats.get('pnl_per_lot', 0))
        dd_per_lot = strat_stats.get('max_dd_per_contract', strat_stats.get('max_dd_per_lot', 0))
        worst_day = strat_stats.get('worst_day_per_contract', strat_stats.get('worst_day_per_lot', 0))
        
        # Use override if exists
        category = category_overrides.get(strat, strat_stats['category'])
        
        if margin_per_lot <= 0:
            continue
        
        # Calculate max lots based on risk (cap at 20)
        max_lots = 20
        if worst_day > 0:
            # Limit based on reasonable daily loss (2% of account)
            max_lots = min(max_lots, max(1, int(account_size * 0.02 / worst_day)))
        
        # Efficiency score
        pnl_per_margin = pnl_per_lot / margin_per_lot if margin_per_lot > 0 else 0
        dd_penalty = 1 / (1 + dd_per_lot / margin_per_lot) if margin_per_lot > 0 else 1
        efficiency = pnl_per_margin * dd_penalty * strat_stats['win_rate']
        
        scored_strategies.append({
            'strategy': strat,
            'category': category,
            'efficiency': efficiency,
            'margin_per_lot': margin_per_lot,
            'pnl_per_lot': pnl_per_lot,
            'max_lots': max_lots
        })
    
    # Sort by efficiency within each category
    scored_strategies.sort(key=lambda x: (x['category'], -x['efficiency']))
    
    # Allocate within category budgets
    allocation = {s['strategy']: 0 for s in scored_strategies}
    
    # First pass: allocate 1 lot to each strategy if budget allows
    for s in scored_strategies:
        cat = s['category']
        if cat in category_used and category_used[cat] + s['margin_per_lot'] <= category_budgets.get(cat, 0):
            allocation[s['strategy']] = 1
            category_used[cat] += s['margin_per_lot']
    
    # Second pass: add more lots to best performers within budget
    for _ in range(50):  # Max iterations
        added = False
        for s in sorted(scored_strategies, key=lambda x: -x['efficiency']):
            cat = s['category']
            current_lots = allocation[s['strategy']]
            
            if current_lots >= s['max_lots']:
                continue
            
            if cat in category_used and category_used[cat] + s['margin_per_lot'] <= category_budgets.get(cat, 0):
                allocation[s['strategy']] += 1
                category_used[cat] += s['margin_per_lot']
                added = True
                break
        
        if not added:
            break
    
    return allocation



def page_portfolio_analytics(full_df, live_df=None):
    """Portfolio Analytics page - IMPROVED LAYOUT."""
    st.markdown(
        """<h1 style='color: #4B5563; font-family: "Exo 2", sans-serif; font-weight: 800; 
        text-transform: uppercase; margin-bottom: 0;'>PORTFOLIO ANALYTICS</h1>""",
        unsafe_allow_html=True
    )

    data_source = "Backtest Data"
    if live_df is not None and not live_df.empty:
        c_toggle, _ = st.columns([1, 4])
        with c_toggle:
            data_source = st.radio("Source:", ["Backtest Data", "Live Data"], label_visibility="collapsed")

    target_df = live_df if data_source == "Live Data" and live_df is not None else full_df
    st.caption(f"Showing {'LIVE TRADING' if data_source == 'Live Data' else 'BACKTEST simulation'} performance")

    if target_df.empty:
        st.warning("Selected data source is empty.")
        return

    col_cap, col_date = st.columns(2)
    with col_cap:
        account_size = st.number_input("Account Size ($)", value=100000, step=1000, key="analytics_account")

    if not np.issubdtype(target_df['timestamp'].dtype, np.datetime64):
        target_df = target_df.copy()
        target_df['timestamp'] = pd.to_datetime(target_df['timestamp'], errors='coerce')
        target_df = target_df.dropna(subset=['timestamp'])

    min_ts, max_ts = target_df['timestamp'].min(), target_df['timestamp'].max()

    if pd.isna(min_ts) or pd.isna(max_ts):
        st.warning("No valid dates found.")
        return

    with col_date:
        selected_dates = st.date_input("Analysis Period", [min_ts.date(), max_ts.date()],
                                       min_value=min_ts.date(), max_value=max_ts.date())
    st.divider()

    if len(selected_dates) != 2:
        return

    filt_df = target_df[
        (target_df['timestamp'].dt.date >= selected_dates[0]) &
        (target_df['timestamp'].dt.date <= selected_dates[1])
    ].copy()

    if filt_df.empty:
        st.warning("No data in selected range.")
        return

    full_date_range = pd.date_range(start=selected_dates[0], end=selected_dates[1], freq='D')
    daily_pnl = filt_df.set_index('timestamp').resample('D')['pnl'].sum().reindex(full_date_range, fill_value=0)
    port_equity = account_size + daily_pnl.cumsum()
    port_returns = port_equity.pct_change().fillna(0)

    spx_data = fetch_spx_benchmark(pd.to_datetime(selected_dates[0]), pd.to_datetime(selected_dates[1]))
    spx_returns = pd.Series(dtype=float)
    if spx_data is not None and not spx_data.empty:
        spx_aligned = spx_data.reindex(full_date_range, method='ffill')
        spx_returns = spx_aligned.pct_change().fillna(0)

    m = calculate_advanced_metrics(port_returns, filt_df, spx_returns, account_size)
    
    # Calculate SPX equivalent P/L for comparison
    spx_pnl_equivalent = account_size * m['SPX_TotalRet'] if m['SPX_TotalRet'] != 0 else 0

    # ============================================
    # CALCULATE MARGIN METRICS FOR ALL STRATEGIES
    # ============================================
    portfolio_margin_series = pd.Series(0.0, index=full_date_range)
    strategy_metrics = []
    
    all_strategies = sorted(filt_df['strategy'].unique().tolist())
    
    for strat in all_strategies:
        strat_data = filt_df[filt_df['strategy'] == strat].copy()
        if strat_data.empty:
            continue
        
        # P/L
        strat_pnl = strat_data['pnl'].sum()
        
        # Count contracts (unique entries/trades)
        if 'timestamp_open' in strat_data.columns:
            num_contracts = strat_data['timestamp_open'].nunique()
        else:
            num_contracts = len(strat_data)
        
        # Max DD for strategy
        strat_daily_pnl = strat_data.set_index('timestamp').resample('D')['pnl'].sum()
        strat_daily_pnl = strat_daily_pnl.reindex(full_date_range, fill_value=0)
        strat_equity = account_size + strat_daily_pnl.cumsum()
        strat_peak = strat_equity.cummax()
        strat_dd = (strat_equity - strat_peak).min()
        
        # Strategy CAGR for MAR
        strat_total_ret = strat_daily_pnl.sum() / account_size
        strat_days = len(full_date_range)
        strat_cagr = (1 + strat_total_ret) ** (365 / strat_days) - 1 if strat_total_ret > -1 and strat_days > 0 else 0
        strat_mar = strat_cagr / (abs(strat_dd) / account_size) if strat_dd != 0 else 0
        
        # Margin series for this strategy
        strat_margin_series = generate_daily_margin_series_optimized(strat_data)
        if not strat_margin_series.empty:
            strat_margin_aligned = strat_margin_series.reindex(full_date_range, fill_value=0)
            portfolio_margin_series = portfolio_margin_series.add(strat_margin_aligned, fill_value=0)
            strat_max_margin = strat_margin_aligned.max()
            strat_avg_margin = strat_margin_aligned[strat_margin_aligned > 0].mean() if (strat_margin_aligned > 0).any() else 0
        else:
            strat_max_margin = 0
            strat_avg_margin = 0
        
        strategy_metrics.append({
            'Strategy': strat,
            'Contracts': num_contracts,
            'P/L': strat_pnl,
            'Max DD ($)': abs(strat_dd),
            'MAR': strat_mar,
            'Peak Margin': strat_max_margin,
            'Avg Margin': strat_avg_margin
        })
    
    # Portfolio-level margin metrics
    portfolio_max_margin = portfolio_margin_series.max()
    portfolio_avg_margin = portfolio_margin_series[portfolio_margin_series > 0].mean() if (portfolio_margin_series > 0).any() else 0
    max_margin_pct = (portfolio_max_margin / account_size) * 100
    avg_margin_pct = (portfolio_avg_margin / account_size) * 100

    # ============================================
    # SECTION 1: KPI GRID
    # ============================================
    st.markdown("### Portfolio KPI Grid")

    # ROW 1: Primary metrics with colors AND SPX comparisons
    r1c1, r1c2, r1c3, r1c4, r1c5, r1c6 = st.columns(6)
    with r1c1:
        spx_pnl_txt = f"SPX: ${spx_pnl_equivalent:,.0f}" if spx_pnl_equivalent != 0 else "SPX: N/A"
        render_hero_metric("Total P/L", f"${filt_df['pnl'].sum():,.0f}", spx_pnl_txt, "hero-teal",
                          tooltip="Total profit/loss from all trades. Compared to equivalent SPX buy-and-hold")
    with r1c2:
        spx_cagr_txt = f"SPX: {m['SPX_CAGR']:.1%}" if m['SPX_CAGR'] != 0 else "SPX: N/A"
        render_hero_metric("CAGR", f"{m['CAGR']:.1%}", spx_cagr_txt, "hero-teal",
                          tooltip="Compound Annual Growth Rate - annualized return assuming reinvestment")
    with r1c3:
        spx_dd_txt = f"SPX: {m['SPX_MaxDD']:.1%}" if m['SPX_MaxDD'] != 0 else "SPX: N/A"
        render_hero_metric("Max DD (%)", f"{m['MaxDD']:.1%}", spx_dd_txt, "hero-coral",
                          tooltip="Maximum Drawdown - largest peak-to-trough decline as percentage")
    with r1c4:
        # Calculate SPX max DD in dollars
        spx_dd_usd = account_size * abs(m['SPX_MaxDD']) if m['SPX_MaxDD'] != 0 else 0
        spx_dd_usd_txt = f"SPX: ${spx_dd_usd:,.0f}" if spx_dd_usd != 0 else "SPX: N/A"
        render_hero_metric("Max DD ($)", f"${abs(m['MaxDD_USD']):,.0f}", spx_dd_usd_txt, "hero-coral",
                          tooltip="Maximum Drawdown in dollars - largest peak-to-trough decline")
    with r1c5:
        # SPX MAR = SPX_CAGR / abs(SPX_MaxDD)
        spx_mar = m['SPX_CAGR'] / abs(m['SPX_MaxDD']) if m['SPX_MaxDD'] != 0 else 0
        spx_mar_txt = f"SPX: {spx_mar:.2f}" if spx_mar != 0 else "SPX: N/A"
        render_hero_metric("MAR Ratio", f"{m['MAR']:.2f}", spx_mar_txt, "hero-teal",
                          tooltip="CAGR divided by Max Drawdown %. Above 1.0 is good, above 2.0 is excellent")
    with r1c6:
        render_hero_metric("MART Ratio", f"{m['MART']:.2f}", "", "hero-teal",
                          tooltip="CAGR divided by (MaxDD$ / Account Size). Measures return vs account-relative risk")

    st.write("")

    # ROW 2: Secondary metrics (neutral) with SPX comparisons where relevant
    r2c1, r2c2, r2c3, r2c4, r2c5, r2c6 = st.columns(6)
    with r2c1:
        render_hero_metric("Total Trades", f"{m['Trades']}", "", "hero-neutral",
                          tooltip="Total number of trades executed in the period")
    with r2c2:
        render_hero_metric("Win Rate", f"{m['WinRate']:.1%}", "", "hero-neutral",
                          tooltip="Percentage of trades that were profitable")
    with r2c3:
        render_hero_metric("Profit Factor", f"{m['PF']:.2f}", "", "hero-neutral",
                          tooltip="Gross profits divided by gross losses. Above 1.5 is good, above 2.0 is excellent")
    with r2c4:
        spx_sharpe_txt = f"SPX: {m['SPX_Sharpe']:.2f}" if m['SPX_Sharpe'] != 0 else ""
        render_hero_metric("Sharpe", f"{m['Sharpe']:.2f}", spx_sharpe_txt, "hero-neutral",
                          tooltip="Risk-adjusted return: (Return - Risk-free rate) / Volatility. Above 1.0 is good")
    with r2c5:
        render_hero_metric("Sortino", f"{m['Sortino']:.2f}", "", "hero-neutral",
                          tooltip="Like Sharpe but only penalizes downside volatility. Above 1.5 is good")
    with r2c6:
        spx_vol_txt = f"SPX: {m['SPX_Vol']:.1%}" if m['SPX_Vol'] != 0 else ""
        render_hero_metric("Volatility", f"{m['Vol']:.1%}", spx_vol_txt, "hero-neutral",
                          tooltip="Annualized standard deviation of daily returns. Lower = more consistent")

    st.write("")

    # ROW 3: More secondary metrics (neutral)
    r3c1, r3c2, r3c3, r3c4, r3c5, r3c6 = st.columns(6)
    with r3c1:
        render_hero_metric("Alpha (vs SPX)", f"{m['Alpha']:.1%}", "Excess return", "hero-neutral",
                          tooltip="Excess return above what beta would predict. Positive = outperforming market")
    with r3c2:
        render_hero_metric("Beta (vs SPX)", f"{m['Beta']:.2f}", "Market sensitivity", "hero-neutral",
                          tooltip="Sensitivity to market movements. Beta < 1 = less volatile than market")
    with r3c3:
        render_hero_metric("Avg Ret/Marg", f"{m['AvgRetMargin']:.1%}", "", "hero-neutral",
                          tooltip="Average return per dollar of margin used")
    with r3c4:
        render_hero_metric("Kelly", f"{m['Kelly']:.1%}", "", "hero-neutral",
                          tooltip="Kelly Criterion - optimal bet size based on win rate and win/loss ratio")
    with r3c5:
        render_hero_metric("Peak Margin", f"${portfolio_max_margin:,.0f}", f"{max_margin_pct:.0f}% of Account", "hero-neutral",
                          tooltip="Maximum margin used at any point during the period")
    with r3c6:
        render_hero_metric("Avg Margin", f"${portfolio_avg_margin:,.0f}", f"{avg_margin_pct:.0f}% of Account", "hero-neutral",
                          tooltip="Average margin used when positions are open")

    st.write("")

    # ROW 4: Streak metrics (neutral)
    r4c1, r4c2, r4c3, r4c4, r4c5 = st.columns(5)
    with r4c1:
        render_hero_metric("Win Streak", f"{m['WinStreak']}", "Best run", "hero-neutral",
                          tooltip="Maximum consecutive winning trades")
    with r4c2:
        render_hero_metric("Loss Streak", f"{m['LossStreak']}", "Worst run", "hero-neutral",
                          tooltip="Maximum consecutive losing trades")
    with r4c3:
        avg_win = filt_df[filt_df['pnl'] > 0]['pnl'].mean() if len(filt_df[filt_df['pnl'] > 0]) > 0 else 0
        render_hero_metric("Avg Win", f"${avg_win:,.0f}", "", "hero-neutral",
                          tooltip="Average profit from winning trades")
    with r4c4:
        avg_loss = filt_df[filt_df['pnl'] <= 0]['pnl'].mean() if len(filt_df[filt_df['pnl'] <= 0]) > 0 else 0
        render_hero_metric("Avg Loss", f"${avg_loss:,.0f}", "", "hero-neutral",
                          tooltip="Average loss from losing trades")
    with r4c5:
        best_trade = filt_df['pnl'].max() if len(filt_df) > 0 else 0
        worst_trade = filt_df['pnl'].min() if len(filt_df) > 0 else 0
        render_hero_metric("Best/Worst", f"${best_trade:,.0f} / ${worst_trade:,.0f}", "", "hero-neutral",
                          tooltip="Best single trade / Worst single trade")

    st.divider()

    # ============================================
    # SECTION 2: EQUITY CURVE (moved to position 2)
    # ============================================
    st.markdown("### Equity Curve vs SPX")
    
    # Strategy selector above the chart
    eq_sel_col1, eq_sel_col2 = st.columns([1, 5])
    with eq_sel_col1:
        if st.button("Select All", key="eq_select_all", use_container_width=True):
            st.session_state.equity_curve_strategies = all_strategies
            st.rerun()
    
    # Get default from session state
    default_eq_strats = st.session_state.get('equity_curve_strategies', None)
    if default_eq_strats is None:
        default_eq_strats = []
    else:
        default_eq_strats = [s for s in default_eq_strats if s in all_strategies]
    
    selected_strategies = st.multiselect(
        "Add strategy lines to chart:",
        options=all_strategies,
        default=default_eq_strats,
        key="equity_curve_strats_select",
        placeholder="Select strategies to compare..."
    )
    st.session_state.equity_curve_strategies = selected_strategies

    fig_eq = go.Figure()
    
    # Always show total portfolio
    fig_eq.add_trace(go.Scatter(
        x=port_equity.index, 
        y=port_equity, 
        mode='lines',
        name='📊 Total Portfolio', 
        line=dict(color=COLOR_BLUE, width=3)
    ))

    # Add SPX benchmark if available
    if spx_data is not None and not spx_data.empty:
        spx_aligned = spx_data.reindex(full_date_range, method='ffill')
        if not spx_aligned.empty and spx_aligned.iloc[0] > 0:
            spx_norm = (spx_aligned / spx_aligned.iloc[0]) * account_size
            fig_eq.add_trace(go.Scatter(
                x=spx_norm.index, 
                y=spx_norm, 
                mode='lines',
                name='📈 S&P 500', 
                line=dict(color='gray', width=2, dash='dot')
            ))

    # Color palette for strategies
    strategy_colors = px.colors.qualitative.Set2 + px.colors.qualitative.Pastel1 + px.colors.qualitative.Dark2

    # Only add selected strategies
    for i, strat in enumerate(selected_strategies):
        strat_data = filt_df[filt_df['strategy'] == strat]
        if not strat_data.empty:
            s_pnl = strat_data.set_index('timestamp').resample('D')['pnl'].sum()
            s_pnl = s_pnl.reindex(full_date_range, fill_value=0)
            s_equity = account_size + s_pnl.cumsum()
            color = strategy_colors[i % len(strategy_colors)]
            fig_eq.add_trace(go.Scatter(
                x=s_equity.index, 
                y=s_equity, 
                mode='lines', 
                name=f'🔹 {strat}',
                line=dict(color=color, width=2)
            ))

    # Calculate dynamic height based on number of selected strategies
    # More strategies = more legend space needed
    num_legend_items = 2 + len(selected_strategies)  # Portfolio + SPX + strategies
    legend_rows = (num_legend_items + 2) // 3  # ~3 items per row
    extra_height = max(0, (legend_rows - 2) * 25)  # Extra height for more rows
    
    # Update layout - legend BELOW chart with proper spacing
    fig_eq.update_layout(
        template="plotly_white", 
        height=500 + extra_height,
        legend=dict(
            orientation="h", 
            yanchor="top",
            y=-0.12,
            xanchor="center",
            x=0.5,
            bgcolor="rgba(255,255,255,0.95)",
            bordercolor="rgba(0,0,0,0.1)",
            borderwidth=1,
            font=dict(size=9),
            itemsizing='constant',
            traceorder='normal'
        ),
        margin=dict(l=20, r=20, t=40, b=20 + (legend_rows * 30)),
        hovermode='x unified',
        yaxis_title="Portfolio Value ($)"
    )
    
    st.plotly_chart(fig_eq, use_container_width=True)

    st.divider()

    # ============================================
    # SECTION 3: MARGIN USAGE CHART
    # ============================================
    st.markdown("### Margin Usage")
    
    fig_margin = go.Figure()
    fig_margin.add_trace(go.Scatter(
        x=portfolio_margin_series.index, 
        y=portfolio_margin_series.values,
        fill='tozeroy', 
        mode='lines',
        line=dict(color=COLOR_PURPLE, width=2), 
        name='Margin Usage ($)',
        fillcolor='rgba(123, 43, 255, 0.2)'
    ))
    
    # Add account size line
    fig_margin.add_shape(
        type="line", 
        x0=portfolio_margin_series.index[0], 
        y0=account_size,
        x1=portfolio_margin_series.index[-1], 
        y1=account_size,
        line=dict(color="red", width=2, dash="dash"),
        name="Account Size"
    )
    
    # Add peak margin line
    fig_margin.add_shape(
        type="line", 
        x0=portfolio_margin_series.index[0], 
        y0=portfolio_max_margin,
        x1=portfolio_margin_series.index[-1], 
        y1=portfolio_max_margin,
        line=dict(color=COLOR_BLUE, width=1, dash="dot"),
    )
    
    fig_margin.add_annotation(
        x=portfolio_margin_series.index[-1],
        y=account_size,
        text="Account Size",
        showarrow=False,
        yshift=10,
        font=dict(color="red", size=10)
    )
    
    fig_margin.add_annotation(
        x=portfolio_margin_series.index[-1],
        y=portfolio_max_margin,
        text=f"Peak: ${portfolio_max_margin:,.0f}",
        showarrow=False,
        yshift=10,
        font=dict(color=COLOR_BLUE, size=10)
    )
    
    fig_margin.update_layout(
        template="plotly_white", 
        height=350,
        margin=dict(l=20, r=20, t=40, b=20),
        xaxis=dict(rangeslider=dict(visible=True), rangeselector=dict(
            buttons=list([
                dict(count=1, label="1m", step="month", stepmode="backward"),
                dict(count=3, label="3m", step="month", stepmode="backward"),
                dict(count=6, label="6m", step="month", stepmode="backward"),
                dict(count=1, label="YTD", step="year", stepmode="todate"),
                dict(step="all", label="All")
            ])
        )),
        yaxis_title="Margin ($)",
        showlegend=False
    )
    st.plotly_chart(fig_margin, use_container_width=True)

    st.divider()

    # ============================================
    # SECTION 4: STRATEGY BREAKDOWN TABLE
    # ============================================
    st.markdown("### Strategy Breakdown")
    
    if strategy_metrics:
        strat_df = pd.DataFrame(strategy_metrics)
        strat_df = strat_df.sort_values('P/L', ascending=False)
        
        # Calculate total contracts
        total_contracts = strat_df['Contracts'].sum()
        
        # Add totals row
        totals = {
            'Strategy': 'TOTAL',
            'Contracts': total_contracts,
            'P/L': strat_df['P/L'].sum(),
            'Max DD ($)': abs(m['MaxDD_USD']),  # Portfolio max DD, not sum
            'MAR': m['MAR'],  # Portfolio MAR
            'Peak Margin': portfolio_max_margin,
            'Avg Margin': portfolio_avg_margin
        }
        strat_df = pd.concat([strat_df, pd.DataFrame([totals])], ignore_index=True)
        
        st.dataframe(
            strat_df.style.format({
                'Contracts': '{:,.0f}',
                'P/L': '${:,.0f}',
                'Max DD ($)': '${:,.0f}',
                'MAR': '{:.2f}',
                'Peak Margin': '${:,.0f}',
                'Avg Margin': '${:,.0f}'
            }).apply(lambda x: ['font-weight: bold' if x.name == len(strat_df) - 1 else '' for _ in x], axis=1),
            use_container_width=True,
            hide_index=True,
            height=min(400, 35 * (len(strat_df) + 1))
        )

    st.divider()

    # ============================================
    # SECTION 5: MONTHLY PERFORMANCE
    # ============================================
    st.markdown("### Monthly Performance")
    matrix_mode = st.radio("Display:", ["Dollar P/L", "Percent Return"], horizontal=True, label_visibility="collapsed")

    filt_df['Year'] = filt_df['timestamp'].dt.year
    filt_df['Month'] = filt_df['timestamp'].dt.month

    # Month name mapping for columns
    month_names = {1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr', 5: 'May', 6: 'Jun',
                   7: 'Jul', 8: 'Aug', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dec'}

    if "Dollar" in matrix_mode:
        pivot = filt_df.pivot_table(index='Year', columns='Month', values='pnl', aggfunc='sum').fillna(0)
        pivot['Total'] = pivot.sum(axis=1)
        pivot.loc['Average'] = pivot.mean()
        pivot.columns = [month_names.get(c, c) for c in pivot.columns]
        
        # Apply color styling
        styled_pivot = pivot.style.applymap(color_monthly_performance).format("${:,.0f}")
        st.dataframe(styled_pivot, use_container_width=True)
    else:
        pivot = (filt_df.pivot_table(index='Year', columns='Month', values='pnl', aggfunc='sum').fillna(0) / account_size) * 100
        pivot['Total'] = pivot.sum(axis=1)
        pivot.loc['Average'] = pivot.mean()
        pivot.columns = [month_names.get(c, c) for c in pivot.columns]
        
        # Apply color styling
        styled_pivot = pivot.style.applymap(color_monthly_performance).format("{:.1f}%")
        st.dataframe(styled_pivot, use_container_width=True)

    st.divider()

    c_day, c_chart = st.columns(2)
    with c_day:
        st.markdown("### Day of Week Analysis")
        filt_df['Day'] = filt_df['timestamp'].dt.day_name()
        days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
        day_stats = filt_df.groupby('Day')['pnl'].agg(['sum', 'count', 'mean'])
        day_stats = day_stats.reindex(days_order).dropna()
        day_stats.columns = ['Total P/L', 'Trades', 'Avg P/L']
        win_rates = filt_df.groupby('Day')['pnl'].apply(lambda x: (x > 0).mean())
        day_stats['Win Rate'] = win_rates.reindex(days_order)
        st.dataframe(day_stats.style.format({
            'Total P/L': "${:,.0f}", 'Avg P/L': "${:,.0f}", 'Win Rate': "{:.1%}"
        }), use_container_width=True)

    with c_chart:
        fig_days = px.bar(day_stats, x=day_stats.index, y='Total P/L', title="PnL by Weekday", template="plotly_white")
        st.plotly_chart(fig_days, use_container_width=True)


# ================================================================================
# ENHANCED MEIC DEEP DIVE PAGE
# ================================================================================
# 
# This is a complete replacement for the page_meic_analysis function.
# 
# NEW FEATURES:
# 1. Entry Time Multi-Select Filter - Filter trades by selected entry times
# 2. KPI Summary - Shows CAGR, MAR, Max DD for filtered data
# 3. MAR column in Entry Time table (with color coding)
# 4. Monthly Performance Table (Year × Month matrix with color coding)
# 5. Equity Curve by Strategy (with strategy selector)
# 6. Entry Time × Day of Week Heatmap
#
# DEPENDENCIES (already in app_optimized.py):
# - render_hero_metric()
# - COLOR_TEAL, COLOR_CORAL, COLOR_BLUE (color constants)
# - plotly.express as px
# - plotly.graph_objects as go
# - pandas as pd
# - numpy as np
#
# NOTE: If color_monthly_performance() is not in your version, add this helper:
#
# def color_monthly_performance(val):
#     """Color code monthly performance values - green for positive, red for negative."""
#     try:
#         if isinstance(val, str):
#             clean_val = val.replace('$', '').replace(',', '').replace('%', '').strip()
#             num_val = float(clean_val)
#         else:
#             num_val = float(val)
#         
#         if num_val > 0:
#             intensity = min(abs(num_val) / 5000, 1) if abs(num_val) > 100 else min(abs(num_val) / 10, 1)
#             return f'background-color: rgba(0, 210, 190, {0.1 + intensity * 0.4}); color: #065F46'
#         elif num_val < 0:
#             intensity = min(abs(num_val) / 5000, 1) if abs(num_val) > 100 else min(abs(num_val) / 10, 1)
#             return f'background-color: rgba(255, 46, 77, {0.1 + intensity * 0.4}); color: #991B1B'
#         else:
#             return 'background-color: white; color: #374151'
#     except (ValueError, TypeError):
#         return 'background-color: white; color: #374151'
#
# ================================================================================


def page_meic_analysis(bt_df, live_df=None):
    """MEIC Deep Dive page - Enhanced with Entry Time Filter, Monthly Performance, and Equity Curves."""
    st.markdown(
        """<h1 style='color: #4B5563; font-family: "Exo 2", sans-serif; font-weight: 800; 
        text-transform: uppercase; margin-bottom: 0;'>🔬 MEIC DEEP DIVE</h1>""",
        unsafe_allow_html=True
    )
    st.caption("ENTRY TIME ANALYSIS & OPTIMIZATION")

    # === DATA SOURCE TOGGLE ===
    data_source = "Backtest Data"
    if live_df is not None and not live_df.empty:
        c_toggle, _ = st.columns([1, 4])
        with c_toggle:
            data_source = st.radio("Source:", ["Backtest Data", "Live Data"], label_visibility="collapsed", key="meic_source")

    target_df = live_df if data_source == "Live Data" and live_df is not None else bt_df

    if target_df.empty:
        st.warning("No data available.")
        return

    # === SECTION 1: CONFIGURATION ===
    st.markdown("### ⚙️ Configuration")
    
    # Date range
    min_ts, max_ts = target_df['timestamp'].min(), target_df['timestamp'].max()
    
    config_c1, config_c2, config_c3 = st.columns([1, 1, 1])
    with config_c1:
        sel_dates = st.date_input("📅 Period", [min_ts.date(), max_ts.date()],
                                  min_value=min_ts.date(), max_value=max_ts.date(), key="meic_dates")

    if len(sel_dates) != 2:
        return

    # Filter by date first
    target_df = target_df[
        (target_df['timestamp'].dt.date >= sel_dates[0]) &
        (target_df['timestamp'].dt.date <= sel_dates[1])
    ].copy()

    # Strategy selector
    all_strats = sorted(list(target_df['strategy'].unique()))
    default_meics = [s for s in all_strats if "MEIC" in s.upper()]

    with config_c2:
        selected_meics = st.multiselect("📊 Select Strategies:", options=all_strats, default=default_meics, key="meic_strats")
    
    with config_c3:
        account_size = st.number_input("💰 Account Size ($)", value=100000, step=5000, min_value=1000, key="meic_account")

    if not selected_meics:
        st.error("Please select at least one strategy.")
        return

    # Filter by strategy
    meic_df = target_df[target_df['strategy'].isin(selected_meics)].copy()
    
    # Check for entry time data
    if 'timestamp_open' not in meic_df.columns:
        st.error("No 'Entry Time' data available. Make sure your data contains 'timestamp_open' column.")
        return
    
    # Create entry time string
    meic_df['EntryTimeStr'] = meic_df['timestamp_open'].dt.strftime('%H:%M')
    
    # === ENTRY TIME FILTER (NEW FEATURE) ===
    st.divider()
    st.markdown("### 🎯 Entry Time Filter")
    
    # Get all available entry times
    all_entry_times = sorted(meic_df['EntryTimeStr'].unique().tolist())
    
    # Calculate stats for each entry time to help user decide
    time_quick_stats = meic_df.groupby('EntryTimeStr')['pnl'].agg(['count', 'sum', 'mean'])
    time_quick_stats.columns = ['trades', 'total_pnl', 'avg_pnl']
    
    # Get times with positive P/L as default suggestion
    positive_times = time_quick_stats[time_quick_stats['total_pnl'] > 0].index.tolist()
    
    filter_col1, filter_col2 = st.columns([3, 1])
    
    with filter_col1:
        # Entry time multi-select
        selected_entry_times = st.multiselect(
            "Select Entry Times to Analyze:",
            options=all_entry_times,
            default=all_entry_times,  # Default: all times selected
            key="meic_entry_time_filter",
            help="Filter trades by entry time. Only selected times will be included in analysis."
        )
    
    with filter_col2:
        st.markdown("##### Quick Actions")
        qa_col1, qa_col2 = st.columns(2)
        with qa_col1:
            if st.button("✅ All", key="meic_select_all", use_container_width=True, help="Select all entry times"):
                st.session_state.meic_entry_time_filter = all_entry_times
                st.rerun()
        with qa_col2:
            if st.button("❌ None", key="meic_select_none", use_container_width=True, help="Clear all selections"):
                st.session_state.meic_entry_time_filter = []
                st.rerun()
        
        if st.button("💚 Profitable Only", key="meic_select_profitable", use_container_width=True, 
                     help="Select only entry times with positive total P/L"):
            st.session_state.meic_entry_time_filter = positive_times
            st.rerun()

    if not selected_entry_times:
        st.warning("Please select at least one entry time.")
        return

    # Apply entry time filter
    meic_df_filtered = meic_df[meic_df['EntryTimeStr'].isin(selected_entry_times)].copy()
    
    # Show filter summary
    filter_summary_col1, filter_summary_col2, filter_summary_col3 = st.columns(3)
    with filter_summary_col1:
        st.metric("Selected Times", f"{len(selected_entry_times)} / {len(all_entry_times)}")
    with filter_summary_col2:
        st.metric("Filtered Trades", f"{len(meic_df_filtered):,}")
    with filter_summary_col3:
        filtered_pnl = meic_df_filtered['pnl'].sum()
        unfiltered_pnl = meic_df['pnl'].sum()
        pnl_retained = (filtered_pnl / unfiltered_pnl * 100) if unfiltered_pnl != 0 else 0
        st.metric("P/L Retained", f"{pnl_retained:.1f}%", delta=f"${filtered_pnl:,.0f}")

    st.divider()

    # === SECTION 2: KPI SUMMARY (for filtered data) ===
    st.markdown("### 📈 Performance Summary")
    
    # Calculate metrics for filtered data
    full_date_range = pd.date_range(start=sel_dates[0], end=sel_dates[1], freq='D')
    daily_pnl = meic_df_filtered.set_index('timestamp').resample('D')['pnl'].sum().reindex(full_date_range, fill_value=0)
    
    port_equity = account_size + daily_pnl.cumsum()
    port_returns = port_equity.pct_change().fillna(0)
    
    # Basic metrics
    total_pnl = meic_df_filtered['pnl'].sum()
    num_trades = len(meic_df_filtered)
    win_trades = (meic_df_filtered['pnl'] > 0).sum()
    win_rate = win_trades / num_trades if num_trades > 0 else 0
    
    # Calculate CAGR and Max DD
    days = len(port_returns)
    if days > 1:
        total_ret = daily_pnl.sum() / account_size
        cagr = (1 + total_ret) ** (365 / days) - 1 if total_ret > -1 else 0
        
        peak = port_equity.cummax()
        dd = (port_equity - peak) / peak
        max_dd = dd.min()
        max_dd_usd = (port_equity - peak).min()
        
        mar = cagr / abs(max_dd) if max_dd != 0 else 0
    else:
        cagr, max_dd, max_dd_usd, mar = 0, 0, 0, 0
    
    # KPI Row
    kpi_c1, kpi_c2, kpi_c3, kpi_c4, kpi_c5 = st.columns(5)
    with kpi_c1:
        render_hero_metric("Total P/L", f"${total_pnl:,.0f}", "", "hero-teal" if total_pnl > 0 else "hero-coral")
    with kpi_c2:
        render_hero_metric("CAGR", f"{cagr:.1%}", "", "hero-teal" if cagr > 0 else "hero-coral")
    with kpi_c3:
        render_hero_metric("Max DD", f"{max_dd:.1%}", f"${abs(max_dd_usd):,.0f}", "hero-coral")
    with kpi_c4:
        render_hero_metric("MAR Ratio", f"{mar:.2f}", "", "hero-teal" if mar > 1 else "hero-coral")
    with kpi_c5:
        render_hero_metric("Win Rate", f"{win_rate:.1%}", f"{num_trades} trades", "hero-neutral")

    st.divider()

    # === SECTION 3: ENTRY TIME PERFORMANCE TABLE ===
    st.markdown("### ⏰ Performance by Entry Time")
    st.caption("Analysis based on filtered entry times. Times with < 10 trades are hidden.")

    # Calculate stats for filtered times only
    time_stats = meic_df_filtered.groupby('EntryTimeStr').agg({
        'pnl': ['count', 'sum', 'mean'],
        'strategy': lambda x: ", ".join(sorted(set(x)))
    })
    time_stats.columns = ['Trades', 'Total P/L', 'Avg P/L', 'Strategies']

    win_counts = meic_df_filtered.groupby('EntryTimeStr').apply(lambda x: (x['pnl'] > 0).sum())
    trade_counts = meic_df_filtered.groupby('EntryTimeStr').size()
    time_stats['Win Rate'] = win_counts / trade_counts
    
    # Calculate MAR for each entry time
    time_mars = {}
    for entry_time in meic_df_filtered['EntryTimeStr'].unique():
        et_df = meic_df_filtered[meic_df_filtered['EntryTimeStr'] == entry_time]
        et_daily_pnl = et_df.set_index('timestamp').resample('D')['pnl'].sum().reindex(full_date_range, fill_value=0)
        et_equity = account_size + et_daily_pnl.cumsum()
        et_peak = et_equity.cummax()
        et_dd = ((et_equity - et_peak) / et_peak).min()
        et_total_ret = et_daily_pnl.sum() / account_size
        et_cagr = (1 + et_total_ret) ** (365 / len(full_date_range)) - 1 if et_total_ret > -1 else 0
        time_mars[entry_time] = et_cagr / abs(et_dd) if et_dd != 0 else 0
    
    time_stats['MAR'] = pd.Series(time_mars)

    filtered_stats = time_stats[time_stats['Trades'] >= 10].sort_values('MAR', ascending=False)

    if filtered_stats.empty:
        st.warning("No entry times found with >= 10 trades.")
    else:
        tbl_col, chart_col = st.columns([1, 1])
        
        with tbl_col:
            # Style the dataframe
            def color_mar(val):
                try:
                    if val >= 2:
                        return 'background-color: rgba(0, 210, 190, 0.3)'
                    elif val >= 1:
                        return 'background-color: rgba(255, 193, 7, 0.3)'
                    else:
                        return 'background-color: rgba(255, 46, 77, 0.3)'
                except:
                    return ''
            
            styled_stats = filtered_stats.style.format({
                'Total P/L': '${:,.0f}', 
                'Avg P/L': '${:,.0f}', 
                'Win Rate': '{:.1%}',
                'MAR': '{:.2f}'
            }).applymap(color_mar, subset=['MAR'])
            
            st.dataframe(styled_stats, use_container_width=True, height=450)
        
        with chart_col:
            chart_metric = st.radio("Chart Metric:", ["MAR", "Total P/L", "Avg P/L", "Win Rate"], horizontal=True, key="meic_chart_metric")
            
            # Create bar chart with color based on value
            if chart_metric == "MAR":
                colors = [COLOR_TEAL if v >= 2 else (COLOR_CORAL if v < 1 else '#FFC107') for v in filtered_stats['MAR']]
            elif chart_metric == "Total P/L":
                colors = [COLOR_TEAL if v > 0 else COLOR_CORAL for v in filtered_stats['Total P/L']]
            elif chart_metric == "Avg P/L":
                colors = [COLOR_TEAL if v > 0 else COLOR_CORAL for v in filtered_stats['Avg P/L']]
            else:
                colors = [COLOR_TEAL if v >= 0.5 else COLOR_CORAL for v in filtered_stats['Win Rate']]
            
            fig_bar = go.Figure(data=[go.Bar(
                x=filtered_stats.index,
                y=filtered_stats[chart_metric],
                marker_color=colors
            )])
            fig_bar.update_layout(
                title=f"{chart_metric} by Entry Time",
                template="plotly_white",
                height=400,
                xaxis_title="Entry Time",
                yaxis_title=chart_metric
            )
            st.plotly_chart(fig_bar, use_container_width=True)

    st.divider()

    # === SECTION 4: MONTHLY PERFORMANCE ===
    st.markdown("### 📅 Monthly Performance")
    
    meic_df_filtered['Year'] = meic_df_filtered['timestamp'].dt.year
    meic_df_filtered['Month'] = meic_df_filtered['timestamp'].dt.month
    
    monthly_mode = st.radio("Display:", ["Dollar P/L", "Percent Return"], horizontal=True, key="meic_monthly_mode", label_visibility="collapsed")
    
    month_names = {1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr', 5: 'May', 6: 'Jun',
                   7: 'Jul', 8: 'Aug', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dec'}
    
    # Helper function for styling (in case it's not available globally)
    def _color_monthly(val):
        try:
            if isinstance(val, str):
                clean_val = val.replace('$', '').replace(',', '').replace('%', '').strip()
                num_val = float(clean_val)
            else:
                num_val = float(val)
            
            if num_val > 0:
                intensity = min(abs(num_val) / 5000, 1) if abs(num_val) > 100 else min(abs(num_val) / 10, 1)
                return f'background-color: rgba(0, 210, 190, {0.1 + intensity * 0.4}); color: #065F46'
            elif num_val < 0:
                intensity = min(abs(num_val) / 5000, 1) if abs(num_val) > 100 else min(abs(num_val) / 10, 1)
                return f'background-color: rgba(255, 46, 77, {0.1 + intensity * 0.4}); color: #991B1B'
            else:
                return 'background-color: white; color: #374151'
        except (ValueError, TypeError):
            return 'background-color: white; color: #374151'
    
    if "Dollar" in monthly_mode:
        pivot = meic_df_filtered.pivot_table(index='Year', columns='Month', values='pnl', aggfunc='sum').fillna(0)
        pivot['Total'] = pivot.sum(axis=1)
        pivot.loc['Average'] = pivot.mean()
        pivot.columns = [month_names.get(c, c) for c in pivot.columns]
        styled_pivot = pivot.style.applymap(_color_monthly).format("${:,.0f}")
    else:
        pivot = (meic_df_filtered.pivot_table(index='Year', columns='Month', values='pnl', aggfunc='sum').fillna(0) / account_size) * 100
        pivot['Total'] = pivot.sum(axis=1)
        pivot.loc['Average'] = pivot.mean()
        pivot.columns = [month_names.get(c, c) for c in pivot.columns]
        styled_pivot = pivot.style.applymap(_color_monthly).format("{:.1f}%")
    
    st.dataframe(styled_pivot, use_container_width=True)

    st.divider()

    # === SECTION 5: EQUITY CURVES BY STRATEGY ===
    st.markdown("### 📈 Equity Curve by Strategy")
    
    # Strategy selector for equity curves
    eq_strat_col1, eq_strat_col2 = st.columns([1, 5])
    with eq_strat_col1:
        if st.button("Select All", key="meic_eq_select_all", use_container_width=True):
            st.session_state.meic_equity_strategies = selected_meics
            st.rerun()
    
    default_eq_strats = st.session_state.get('meic_equity_strategies', None)
    if default_eq_strats is None:
        default_eq_strats = []
    else:
        default_eq_strats = [s for s in default_eq_strats if s in selected_meics]
    
    selected_eq_strategies = st.multiselect(
        "Add strategy lines to chart:",
        options=selected_meics,
        default=default_eq_strats,
        key="meic_equity_strats_select",
        placeholder="Select strategies to compare..."
    )
    st.session_state.meic_equity_strategies = selected_eq_strategies
    
    # Create equity curve figure
    fig_eq = go.Figure()
    
    # Total portfolio equity (for filtered data)
    fig_eq.add_trace(go.Scatter(
        x=port_equity.index,
        y=port_equity,
        mode='lines',
        name='📊 Combined Portfolio',
        line=dict(color=COLOR_BLUE, width=3)
    ))
    
    # Add starting line
    fig_eq.add_hline(y=account_size, line_dash="dash", line_color="lightgray")
    
    # Color palette for strategies
    strategy_colors = px.colors.qualitative.Set2 + px.colors.qualitative.Pastel1 + px.colors.qualitative.Dark2
    
    # Add individual strategy equity curves
    for i, strat in enumerate(selected_eq_strategies):
        strat_data = meic_df_filtered[meic_df_filtered['strategy'] == strat]
        if not strat_data.empty:
            s_daily_pnl = strat_data.set_index('timestamp').resample('D')['pnl'].sum()
            s_daily_pnl = s_daily_pnl.reindex(full_date_range, fill_value=0)
            s_equity = account_size + s_daily_pnl.cumsum()
            color = strategy_colors[i % len(strategy_colors)]
            fig_eq.add_trace(go.Scatter(
                x=s_equity.index,
                y=s_equity,
                mode='lines',
                name=f'🔹 {strat}',
                line=dict(color=color, width=2)
            ))
    
    # Calculate dynamic height based on legend items
    num_legend_items = 1 + len(selected_eq_strategies)
    legend_rows = (num_legend_items + 2) // 3
    extra_height = max(0, (legend_rows - 2) * 25)
    
    fig_eq.update_layout(
        template="plotly_white",
        height=500 + extra_height,
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.12,
            xanchor="center",
            x=0.5,
            bgcolor="rgba(255,255,255,0.95)",
            bordercolor="rgba(0,0,0,0.1)",
            borderwidth=1,
            font=dict(size=9)
        ),
        margin=dict(l=20, r=20, t=40, b=20 + (legend_rows * 30)),
        hovermode='x unified',
        yaxis_title="Portfolio Value ($)"
    )
    
    st.plotly_chart(fig_eq, use_container_width=True)
    
    # Strategy performance table below equity curve
    if selected_eq_strategies:
        st.markdown("##### Strategy Performance Comparison")
        strat_perf = []
        for strat in selected_eq_strategies:
            strat_data = meic_df_filtered[meic_df_filtered['strategy'] == strat]
            if not strat_data.empty:
                s_pnl = strat_data['pnl'].sum()
                s_trades = len(strat_data)
                s_win_rate = (strat_data['pnl'] > 0).mean()
                s_avg_pnl = strat_data['pnl'].mean()
                strat_perf.append({
                    'Strategy': strat,
                    'Total P/L': s_pnl,
                    'Trades': s_trades,
                    'Win Rate': s_win_rate,
                    'Avg Trade': s_avg_pnl
                })
        
        if strat_perf:
            perf_df = pd.DataFrame(strat_perf)
            st.dataframe(
                perf_df.style.format({
                    'Total P/L': '${:,.0f}',
                    'Win Rate': '{:.1%}',
                    'Avg Trade': '${:,.0f}'
                }),
                use_container_width=True,
                hide_index=True
            )

    st.divider()

    # === SECTION 6: ENTRY TIME HEATMAP (Day × Time) ===
    st.markdown("### 🗓️ Entry Time × Day of Week Heatmap")
    
    meic_df_filtered['DayOfWeek'] = meic_df_filtered['timestamp_open'].dt.day_name()
    
    heatmap_metric = st.radio("Heatmap Metric:", ["Total P/L", "Avg P/L", "Win Rate", "Trade Count"], horizontal=True, key="meic_heatmap_metric")
    
    # Create pivot table
    if heatmap_metric == "Total P/L":
        heat_pivot = meic_df_filtered.pivot_table(index='EntryTimeStr', columns='DayOfWeek', values='pnl', aggfunc='sum').fillna(0)
        colorscale = 'RdYlGn'
    elif heatmap_metric == "Avg P/L":
        heat_pivot = meic_df_filtered.pivot_table(index='EntryTimeStr', columns='DayOfWeek', values='pnl', aggfunc='mean').fillna(0)
        colorscale = 'RdYlGn'
    elif heatmap_metric == "Win Rate":
        heat_pivot = meic_df_filtered.pivot_table(index='EntryTimeStr', columns='DayOfWeek', values='pnl', aggfunc=lambda x: (x > 0).mean()).fillna(0)
        colorscale = 'RdYlGn'
    else:
        heat_pivot = meic_df_filtered.pivot_table(index='EntryTimeStr', columns='DayOfWeek', values='pnl', aggfunc='count').fillna(0)
        colorscale = 'Blues'
    
    # Reorder days
    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    heat_pivot = heat_pivot.reindex(columns=[d for d in day_order if d in heat_pivot.columns])
    
    # Only show times with data
    heat_pivot = heat_pivot[heat_pivot.sum(axis=1) != 0]
    
    if not heat_pivot.empty:
        # Determine text format based on metric
        if heatmap_metric in ["Total P/L", "Avg P/L"]:
            text_template = "%{text:.0f}"
        elif heatmap_metric == "Win Rate":
            text_template = "%{text:.1%}"
        else:
            text_template = "%{text:.0f}"
        
        fig_heat = go.Figure(data=go.Heatmap(
            z=heat_pivot.values,
            x=heat_pivot.columns,
            y=heat_pivot.index,
            colorscale=colorscale,
            text=heat_pivot.values,
            texttemplate=text_template,
            textfont={"size": 8},
            hovertemplate="Time: %{y}<br>Day: %{x}<br>Value: %{z:.2f}<extra></extra>"
        ))
        
        fig_heat.update_layout(
            template="plotly_white",
            height=max(400, len(heat_pivot) * 18),
            xaxis_title="Day of Week",
            yaxis_title="Entry Time",
            margin=dict(l=80, r=20, t=40, b=60)
        )
        
        st.plotly_chart(fig_heat, use_container_width=True)
    else:
        st.warning("Not enough data to generate heatmap.")
def page_meic_optimizer():
    st.markdown(
        """<h1 style='color: #4B5563; font-family: "Exo 2", sans-serif; font-weight: 800; 
        text-transform: uppercase; margin-bottom: 0;'>🧪 MEIC OPTIMIZER (4D)</h1>""",
        unsafe_allow_html=True
    )
    st.caption("ENTRY TIMES • PREMIUM • WIDTH • STOP LOSS")
    
    tab_gen, tab_ana = st.tabs(["1️⃣ Signal Generator (für Option Omega)", "2️⃣ 4D Analyzer (Ergebnisse)"])
    
    # --- TAB 1: GENERATOR ---
    with tab_gen:
        st.markdown("### Erstelle Entry-Signale für Option Omega")
        st.info("Lade diese Datei bei Option Omega unter **'Custom Signals'** hoch (Open Only), um Backtests zu jeder möglichen Uhrzeit zu erzwingen.")
        
        c1, c2 = st.columns(2)
        with c1:
            # Standard: SPX Dailies Start bis Heute
            gen_start = st.date_input("Start Datum", value=pd.to_datetime("2022-05-16"))
            gen_end = st.date_input("End Datum", value=pd.Timestamp.now())
        with c2:
            gen_interval = st.number_input("Intervall (Minuten)", value=5, min_value=1, max_value=60)
            
        if st.button("CSV Generieren", type="primary"):
            df_signals = generate_oo_signals(gen_start, gen_end, interval_min=gen_interval)
            
            # Convert to CSV string
            csv = df_signals.to_csv(index=False)
            
            st.success(f"Generiert: {len(df_signals):,} Entry Signale ({gen_interval}min Intervall)")
            st.download_button(
                label="⬇️ Download signals_open_only.csv",
                data=csv,
                file_name="signals_open_only.csv",
                mime="text/csv"
            )

    # --- TAB 2: ANALYZER ---
    with tab_ana:
        st.markdown("### Dimensionale Analyse")
        st.markdown("""
        **Workflow:**
        1. Führe Backtests in Option Omega durch (nutze die Signal-CSV von Tab 1).
        2. Benenne die Ergebnis-Dateien strikt nach dem Schema: `MEIC_W{Width}_SL{StopLoss}_P{Premium}.csv`
           *(Beispiel: MEIC_W50_SL100_P2.5.csv)*
        3. Lade alle Ergebnisse hier hoch.
        """)
        
        uploaded_files = st.file_uploader("Upload OO Backtest CSVs (Mehrfachauswahl)", accept_multiple_files=True, type=['csv'])
        
        account_size = st.number_input("Account Size ($)", value=100000, step=10000, key="opt_acc_size")
        
        if uploaded_files:
            all_trades = []
            file_stats = []
            
            # Progress Bar initialisieren
            progress_text = "Verarbeite Dateien..."
            my_bar = st.progress(0, text=progress_text)
            
            for i, uploaded_file in enumerate(uploaded_files):
                # 1. Parse Metadaten aus Dateinamen
                meta = parse_meic_filename(uploaded_file.name)
                
                # 2. Lade Content
                try:
                    # Wir nutzen die existierende load_file_with_caching Funktion
                    df = load_file_with_caching(uploaded_file)
                    
                    if df is None or df.empty: 
                        continue
                    
                    # 3. Entry Time extrahieren (Format HH:MM)
                    if 'timestamp_open' in df.columns:
                        df['EntryTime'] = df['timestamp_open'].dt.strftime('%H:%M')
                    else:
                        continue # Skip if no time info
                    
                    # 4. Dimensionen anfügen (wenn im Dateinamen gefunden, sonst 'Unknown')
                    df['Width'] = meta['Width'] if meta['Width'] else 0
                    df['SL'] = meta['SL'] if meta['SL'] else 0
                    df['Premium'] = meta['Premium'] if meta['Premium'] else 0.0
                    df['SourceFile'] = meta['Filename']
                    
                    all_trades.append(df)
                    file_stats.append(meta)
                    
                except Exception as e:
                    logger.error(f"Error parsing {uploaded_file.name}: {e}")
                
                # Update Progress
                my_bar.progress((i + 1) / len(uploaded_files), text=f"Lade {uploaded_file.name}")
            
            my_bar.empty()
            
            if not all_trades:
                st.error("Keine validen Trades gefunden. Bitte prüfe die CSV-Dateien.")
                return
                
            master_df = pd.concat(all_trades, ignore_index=True)
            st.success(f"Daten geladen: {len(master_df):,} Trades aus {len(uploaded_files)} Dateien.")
            
            # --- ANALYSE LOGIK ---
            st.divider()
            
            # Datumsgrenze für "Letzte 6 Monate"
            max_date = master_df['timestamp'].max()
            date_6m = max_date - pd.DateOffset(months=6)
            
            st.markdown(f"#### 🏆 Strategie-Ranking")
            st.caption(f"Vergleich: Full History vs. Letzte 6 Monate (ab {date_6m.date()})")

            with st.spinner("Berechne 4D-Metriken (Width x SL x Premium x EntryTime)..."):
                combinations = []
                
                # Gruppieren nach ALLEN Dimensionen
                groups = master_df.groupby(['Width', 'SL', 'Premium', 'EntryTime'])
                
                for name, group in groups:
                    width, sl, prem, entry_time = name
                    
                    # Filter: Nur Einträge mit sinnvollen Parametern berücksichtigen
                    if width == 0 and sl == 0 and prem == 0:
                        continue 

                    # Split in 6M und Total
                    df_6m = group[group['timestamp'] >= date_6m]
                    
                    # Wenn in den letzten 6M keine Trades, überspringen (Strategy stopped working?)
                    if df_6m.empty:
                        continue

                    # Stats berechnen
                    stats_total = analyze_meic_group(group, account_size)
                    stats_6m = analyze_meic_group(df_6m, account_size)
                    
                    combinations.append({
                        'Width': width,
                        'SL': sl,
                        'Premium': prem,
                        'EntryTime': entry_time,
                        'MAR (6M)': stats_6m['MAR'],
                        'MAR (Total)': stats_total['MAR'],
                        'CAGR (6M)': stats_6m['CAGR'],
                        'MaxDD (6M)': stats_6m['MaxDD'],
                        'Trades (6M)': stats_6m['Trades'],
                        'WinRate (6M)': stats_6m['WinRate'],
                        'P/L (6M)': stats_6m['P/L']
                    })
                
                results_df = pd.DataFrame(combinations)
                
            if results_df.empty:
                st.warning("Keine Kombinationen gefunden. Bitte Dateinamen prüfen (z.B. MEIC_W50...).")
                return

            # --- INTERACTIVE FILTERING ---
            col_f1, col_f2 = st.columns([1, 3])
            
            with col_f1:
                st.markdown("##### Filter")
                min_mar_6m = st.slider("Min MAR (6M)", 0.0, 5.0, 1.5, 0.1)
                min_mar_total = st.slider("Min MAR (Total)", 0.0, 3.0, 0.5, 0.1)
                min_trades = st.slider("Min Trades (6M)", 0, 100, 20, 5)
                
            # Filter anwenden
            filtered_res = results_df[
                (results_df['MAR (6M)'] >= min_mar_6m) &
                (results_df['MAR (Total)'] >= min_mar_total) &
                (results_df['Trades (6M)'] >= min_trades)
            ].sort_values('MAR (6M)', ascending=False)
            
            with col_f2:
                st.markdown(f"##### Ergebnisse ({len(filtered_res)} Kombos gefunden)")
                
                # Farb-Formatierung für MAR
                def color_mar(val):
                    if val >= 3: return 'background-color: #065F46; color: white' # Excellent
                    if val >= 2: return 'background-color: #10B981; color: white' # Good
                    if val >= 1: return 'background-color: #FBBF24; color: black' # Okay
                    return 'background-color: #EF4444; color: white' # Bad

                st.dataframe(
                    filtered_res.style.format({
                        'MAR (6M)': '{:.2f}',
                        'MAR (Total)': '{:.2f}',
                        'CAGR (6M)': '{:.1%}',
                        'MaxDD (6M)': '{:.1%}',
                        'WinRate (6M)': '{:.1%}',
                        'P/L (6M)': '${:,.0f}',
                        'Premium': '${:.2f}'
                    }).map(color_mar, subset=['MAR (6M)', 'MAR (Total)']),
                    use_container_width=True,
                    height=500
                )
            
            # --- DEEP DIVE VISUALISIERUNG ---
            st.divider()
            st.markdown("### 🔬 Deep Dive: Parameter Impact")
            
            viz_c1, viz_c2 = st.columns(2)
            
            with viz_c1:
                st.markdown("**Beste Entry Times (Top 50 Kombos)**")
                if not filtered_res.empty:
                    top_times = filtered_res.head(50)['EntryTime'].value_counts().sort_index()
                    fig_times = px.bar(x=top_times.index, y=top_times.values, 
                                     labels={'x': 'Entry Time', 'y': 'Häufigkeit in Top 50'},
                                     template="plotly_white")
                    fig_times.update_traces(marker_color='#00D2BE')
                    st.plotly_chart(fig_times, use_container_width=True)
            
            with viz_c2:
                st.markdown("**Robustheit: 6M vs Total**")
                if not filtered_res.empty:
                    fig_scat = px.scatter(
                        filtered_res, 
                        x="MAR (Total)", 
                        y="MAR (6M)", 
                        color="Width",
                        size="Premium",
                        hover_data=["EntryTime", "SL"],
                        template="plotly_white",
                        title="Konsistenz-Check (Größe = Premium, Farbe = Width)"
                    )
                    # Grüne Zone einzeichnen
                    fig_scat.add_shape(type="rect",
                        x0=1.0, y0=2.0, x1=5.0, y1=10.0,
                        line=dict(color="Green", width=1, dash="dot"),
                        fillcolor="rgba(0,255,0,0.1)"
                    )
                    st.plotly_chart(fig_scat, use_container_width=True)

            # --- DOWNLOAD BEST ---
            st.markdown("### 📥 Export")
            if not filtered_res.empty:
                csv_export = filtered_res.to_csv(index=False)
                st.download_button("Download Top Ergebnisse (.csv)", csv_export, "meic_optimized_results.csv", "text/csv")

# --- 13. FINAL PAGE FUNCTIONS AND MAIN APP ---

def page_comparison():
    """Live vs Backtest comparison page - COMPLETE."""
    st.markdown(
        """<h1 style='color: #4B5563; font-family: "Exo 2", sans-serif; font-weight: 800; 
        text-transform: uppercase; margin-bottom: 0;'>⚖️ REALITY CHECK</h1>""",
        unsafe_allow_html=True
    )

    if 'full_df' not in st.session_state or 'live_df' not in st.session_state:
        st.warning("⚠️ Please upload both Backtest and Live data.")
        return

    bt_df = st.session_state['full_df'].copy()
    live_df = st.session_state['live_df'].copy()

    if live_df.empty:
        st.warning("⚠️ Live data is empty.")
        return

    # Ensure timestamps are datetime
    if not np.issubdtype(live_df['timestamp'].dtype, np.datetime64):
        live_df['timestamp'] = pd.to_datetime(live_df['timestamp'], errors='coerce')
    if not np.issubdtype(bt_df['timestamp'].dtype, np.datetime64):
        bt_df['timestamp'] = pd.to_datetime(bt_df['timestamp'], errors='coerce')

    # Get date range from live data
    live_min_ts = live_df['timestamp'].min()
    live_max_ts = live_df['timestamp'].max()
    
    # Evaluation period selector
    st.markdown("### 📅 Evaluation Period")
    col_preset, col_dates = st.columns(2)
    
    with col_preset:
        data_start = live_min_ts.date() if pd.notna(live_min_ts) else pd.Timestamp.now().date()
        data_end = live_max_ts.date() if pd.notna(live_max_ts) else pd.Timestamp.now().date()
        
        # Use data_end as reference point for presets, not today
        comp_presets = {
            "Full Period": (data_start, data_end),
            "Last Month": (max((pd.Timestamp(data_end) - pd.DateOffset(months=1)).date(), data_start), data_end),
            "Last Quarter": (max((pd.Timestamp(data_end) - pd.DateOffset(months=3)).date(), data_start), data_end),
            "Last 6 Months": (max((pd.Timestamp(data_end) - pd.DateOffset(months=6)).date(), data_start), data_end),
            "Year to Date": (max(pd.Timestamp(data_end.year, 1, 1).date(), data_start), data_end),
            "Custom": None
        }
        
        comp_preset = st.selectbox("Quick Select:", list(comp_presets.keys()), key="comp_date_preset")
        
    with col_dates:
        if comp_preset != "Custom" and comp_presets[comp_preset] is not None:
            preset_start, preset_end = comp_presets[comp_preset]
            default_comp_dates = [preset_start, preset_end]
        else:
            default_comp_dates = [data_start, data_end]
        
        selected_comp_dates = st.date_input("Analysis Period", default_comp_dates,
                                            min_value=data_start, max_value=data_end, key="comp_dates_input")
    
    st.divider()
    
    # Filter data by selected dates
    if len(selected_comp_dates) == 2:
        live_df = live_df[
            (live_df['timestamp'].dt.date >= selected_comp_dates[0]) &
            (live_df['timestamp'].dt.date <= selected_comp_dates[1])
        ].copy()
        bt_df = bt_df[
            (bt_df['timestamp'].dt.date >= selected_comp_dates[0]) &
            (bt_df['timestamp'].dt.date <= selected_comp_dates[1])
        ].copy()

    bt_strategies = sorted(bt_df['strategy'].unique())
    live_strategies = sorted(live_df['strategy'].unique())

    st.markdown("### 1. Strategy Mapping")
    with st.expander("🔗 Configuration", expanded=True):
        c1, c2 = st.columns(2)
        mapping = {}

        for i, live_s in enumerate(live_strategies):
            default_ix = 0
            for k, bt_s in enumerate(bt_strategies):
                if bt_s in live_s or live_s in bt_s:
                    default_ix = k + 1
                    break

            col = c1 if i % 2 == 0 else c2
            with col:
                options = ["-- Ignore --"] + list(bt_strategies)
                selection = st.selectbox(f"Live: **{live_s}**", options=options, index=default_ix, key=f"map_{i}")
                if selection != "-- Ignore --":
                    mapping[live_s] = selection

    if not mapping:
        st.warning("Please map at least one strategy.")
        return

    st.divider()
    st.markdown("### 2. Detailed Breakdown")

    tabs = st.tabs(["📊 TOTAL PORTFOLIO"] + [f"🔎 {live} vs {bt}" for live, bt in mapping.items()])

    with tabs[0]:
        mapped_live = live_df[live_df['strategy'].isin(mapping.keys())].copy()
        mapped_bt_list = []
        global_start_date = mapped_live['timestamp'].min()

        for live_s, bt_s in mapping.items():
            temp = bt_df[bt_df['strategy'] == bt_s].copy()
            temp['strategy'] = live_s
            mapped_bt_list.append(temp)

        mapped_bt = pd.concat(mapped_bt_list, ignore_index=True)
        if pd.notna(global_start_date):
            mapped_bt = mapped_bt[mapped_bt['timestamp'] >= global_start_date]

        daily_live = mapped_live.set_index('timestamp').resample('D')['pnl'].sum().fillna(0).cumsum()
        daily_bt = mapped_bt.set_index('timestamp').resample('D')['pnl'].sum().fillna(0).cumsum()

        tot_live = daily_live.iloc[-1] if not daily_live.empty else 0
        tot_bt = daily_bt.iloc[-1] if not daily_bt.empty else 0
        diff = tot_live - tot_bt
        real_rate = (tot_live / tot_bt * 100) if tot_bt != 0 else 0

        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.metric("Live Net Profit", f"${tot_live:,.0f}")
        with m2:
            st.metric("Backtest Net Profit", f"${tot_bt:,.0f}")
        with m3:
            st.metric("Net Slippage", f"${diff:,.0f}", delta_color="normal" if diff >= 0 else "inverse")
        with m4:
            st.metric("Realization Rate", f"{real_rate:.1f}%")

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=daily_bt.index, y=daily_bt, name="Backtest (Ideal)",
                                 line=dict(color='gray', dash='dot')))
        fig.add_trace(go.Scatter(x=daily_live.index, y=daily_live, name="Live (Real)",
                                 line=dict(color=COLOR_BLUE, width=3)))
        fig.update_layout(template="plotly_white", height=500)
        st.plotly_chart(fig, use_container_width=True)

    for i, (live_s, bt_s) in enumerate(mapping.items()):
        with tabs[i + 1]:
            s_live = live_df[live_df['strategy'] == live_s].copy().sort_values('timestamp')
            if s_live.empty:
                st.write("No live trades.")
                continue

            s_start = s_live['timestamp'].min()
            s_bt = bt_df[bt_df['strategy'] == bt_s].copy()
            if pd.notna(s_start):
                s_bt = s_bt[s_bt['timestamp'] >= s_start].sort_values('timestamp')

            if s_bt.empty:
                st.warning("Backtest has no data from start date.")
                continue

            pl_live = s_live['pnl'].sum()
            pl_bt = s_bt['pnl'].sum()
            s_diff = pl_live - pl_bt
            s_real = (pl_live / pl_bt * 100) if pl_bt != 0 else 0

            st.metric("P/L Difference", f"${s_diff:,.0f}", f"{s_real:.1f}% Realization")

            cum_l = s_live.set_index('timestamp').resample('D')['pnl'].sum().cumsum()
            cum_b = s_bt.set_index('timestamp').resample('D')['pnl'].sum().cumsum()

            fig_s = go.Figure()
            fig_s.add_trace(go.Scatter(x=cum_b.index, y=cum_b, name=f"Backtest: {bt_s}",
                                       line=dict(color='gray', dash='dot')))
            fig_s.add_trace(go.Scatter(x=cum_l.index, y=cum_l, name=f"Live: {live_s}",
                                       line=dict(color=COLOR_TEAL, width=3)))
            fig_s.update_layout(template="plotly_white", height=450)
            st.plotly_chart(fig_s, use_container_width=True, key=f"chart_{i}")


def page_ai_analyst(full_df):
    """AI Analyst page."""
    st.markdown(
        """<h1 style='color: #4B5563; font-family: "Exo 2", sans-serif; font-weight: 800; 
        text-transform: uppercase; margin-bottom: 0;'>AI ANALYST</h1>""",
        unsafe_allow_html=True
    )

    if not GEMINI_AVAILABLE:
        st.error("Google Generative AI library not installed.")
        return

    api_key = None
    try:
        if "GOOGLE_API_KEY" in st.secrets:
            api_key = st.secrets["GOOGLE_API_KEY"]
    except:
        pass

    if not api_key:
        api_key = st.sidebar.text_input("Google API Key", type="password")

    if not api_key:
        st.warning("Please enter a Google API Key.")
        return

    try:
        genai.configure(api_key=api_key)
        # Using Gemini 2.5 Pro - the most capable model
        model = genai.GenerativeModel("gemini-2.5-pro-preview-06-05")
    except Exception as e:
        st.error(f"Config Error: {e}")
        return

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Ask about your portfolio..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        strat_summary = full_df.groupby('strategy')['pnl'].sum().to_markdown()
        context_prompt = f"Portfolio Summary:\n{strat_summary}\nUser: {prompt}"

        try:
            response = model.generate_content(context_prompt)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
            with st.chat_message("assistant"):
                st.markdown(response.text)
        except Exception as e:
            st.error(f"API Error: {e}")


def show_landing_page():
    """Landing page with file upload."""
    c1, c2, c3 = st.columns([1, 1, 1])
    with c2:
        try:
            st.image("logo1.png", use_container_width=True)
        except:
            st.markdown("# ⚡ CASHFLOW ENGINE")

    st.markdown(
        """<div class='landing-header'>
        <h1>Advanced Portfolio Analytics &<br>Risk Simulation for Option Traders</h1>
        </div>""",
        unsafe_allow_html=True
    )

    with st.container(border=True):
        st.markdown("### 📂 Upload Data")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("#### 1. Backtest Data (Required)")
            st.caption("Option Omega portfolio or single strategy backtest results.")
            bt_files = st.file_uploader("Upload Backtest CSVs", accept_multiple_files=True,
                                        type=['csv'], key="bt_uploader", label_visibility="collapsed")
        with c2:
            st.markdown("#### 2. Live Data (Optional)")
            st.caption("Option Omega or OptionsApp live trading reporting file.")
            live_files = st.file_uploader("Upload Live Log", accept_multiple_files=True,
                                          type=['csv', 'xlsx', 'xls'], key="live_uploader", label_visibility="collapsed")

        st.write("")
        if st.button("🚀 LAUNCH ENGINE", use_container_width=True):
            if bt_files:
                # Show custom loading overlay
                loading_placeholder = st.empty()
                loading_placeholder.markdown("""
                <div class="loading-overlay">
                    <div class="engine-container">
                        <div class="gear-system">
                            <span class="gear gear-1">⚙️</span>
                            <span class="gear gear-2">⚙️</span>
                            <span class="gear gear-3">⚙️</span>
                        </div>
                        <div class="loading-text">🔥 Firing Up The Engine</div>
                        <div class="loading-subtext">Processing your trading data...</div>
                        <div class="progress-bar-container">
                            <div class="progress-bar"></div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                dfs = []
                for f in bt_files:
                    d = load_file_with_caching(f)
                    if d is not None:
                        dfs.append(d)
                if dfs:
                    st.session_state['full_df'] = pd.concat(dfs, ignore_index=True)
                    st.session_state['bt_filenames'] = ", ".join([f.name for f in bt_files])

                if live_files:
                    dfs_live = []
                    for f in live_files:
                        d = load_file_with_caching(f)
                        if d is not None:
                            dfs_live.append(d)
                    if dfs_live:
                        st.session_state['live_df'] = pd.concat(dfs_live, ignore_index=True)
                        st.session_state['live_filenames'] = ", ".join([f.name for f in live_files])

                loading_placeholder.empty()
                
                if 'full_df' in st.session_state:
                    st.rerun()
                else:
                    st.error("Please upload at least Backtest Data to start.")
            else:
                st.error("Please upload at least Backtest Data to start.")

    # Database load section
    if DB_AVAILABLE:
        saved_analyses = get_analysis_list()
        if saved_analyses:
            st.write("---")
            st.markdown("<h4 style='text-align: center; color: #6B7280;'>📂 OR LOAD FROM ARCHIVE</h4>",
                        unsafe_allow_html=True)
            c_load1, c_load2, c_load3 = st.columns([1, 2, 1])
            with c_load2:
                options = {f"{entry['name']} ({entry['created_at'][:10]})": entry['id'] for entry in saved_analyses}
                selected_option = st.selectbox("Select Analysis", ["-- Select --"] + list(options.keys()),
                                               label_visibility="collapsed")
                if selected_option != "-- Select --":
                    if st.button("Load Analysis", use_container_width=True):
                        # Show loading overlay
                        db_loading = st.empty()
                        db_loading.markdown("""
                        <div class="loading-overlay">
                            <div class="engine-container">
                                <div class="gear-system">
                                    <span class="gear gear-1">⚙️</span>
                                    <span class="gear gear-2">💾</span>
                                    <span class="gear gear-3">⚙️</span>
                                </div>
                                <div class="loading-text">📂 Loading From Archive</div>
                                <div class="loading-subtext">Retrieving your saved analysis...</div>
                                <div class="progress-bar-container">
                                    <div class="progress-bar"></div>
                                </div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        analysis_id = options[selected_option]
                        bt_df, live_df = load_analysis_from_db(analysis_id)
                        if bt_df is not None:
                            st.session_state['full_df'] = bt_df
                            st.session_state['bt_filenames'] = f"DB: {selected_option}"
                            if live_df is not None:
                                st.session_state['live_df'] = live_df
                                st.session_state['live_filenames'] = "From Database"
                            db_loading.empty()
                            st.success("Loaded!")
                            st.rerun()


# --- 14. MAIN APP ROUTING ---
if 'full_df' not in st.session_state:
    show_landing_page()
else:
    st.sidebar.markdown("### 🧭 NAVIGATION")
    
    # Get page list - reordered as requested

    page_list = [
        "📊  Portfolio Analytics", 
        "🏗️  Portfolio Builder", 
        "🎲  Monte Carlo Punisher",
        "⚖️  Live vs. Backtest", 
        "🔬  MEIC Deep Dive", 
        "🧪  MEIC Optimizer", 
        "🤖  AI Analyst"
    ]


    # Check if we need to navigate to a specific page (e.g., from Portfolio Builder button)
    navigate_to = st.session_state.get('navigate_to_page', None)
    
    if navigate_to:
        # Map old names to new names
        name_map = {
            "Monte Carlo Punisher": "🎲  Monte Carlo Punisher",
            "Live vs. Backtest": "⚖️  Live vs. Backtest",
            "MEIC Deep Dive": "🔬  MEIC Deep Dive",
            "AI Analyst": "🤖  AI Analyst"
        }
        navigate_to = name_map.get(navigate_to, navigate_to)
        if navigate_to in page_list:
            st.session_state['main_nav_radio'] = navigate_to
            st.session_state.navigate_to_page = None
    
    # Render radio - Streamlit will use the stored state from the key
    page = st.sidebar.radio(
        "Go to",
        page_list,
        label_visibility="collapsed",
        key="main_nav_radio"
    )

    bt_df = st.session_state.get('full_df', pd.DataFrame())
    live_df = st.session_state.get('live_df', pd.DataFrame())

    bt_strats = list(bt_df['strategy'].unique()) if not bt_df.empty and 'strategy' in bt_df.columns else []
    live_strats = list(live_df['strategy'].unique()) if not live_df.empty and 'strategy' in live_df.columns else []
    all_strats = sorted(list(set(bt_strats + live_strats)))

    st.sidebar.markdown("---")
    with st.sidebar.expander("🎯 Select Strategies", expanded=False):
        # Add Select All button
        if st.button("✅ Select All", key="select_all_strats", use_container_width=True):
            st.session_state.selected_strategies = all_strats
            st.rerun()
        
        # Get default from session state or use all
        # Use None check, not falsy check, so empty list [] is preserved
        default_strats = st.session_state.get('selected_strategies', None)
        if default_strats is None:
            default_strats = all_strats
        else:
            # Filter to only valid strategies
            default_strats = [s for s in default_strats if s in all_strats]
        
        selected_strats = st.multiselect("Active Strategies:", options=all_strats, default=default_strats,
                                         placeholder="Select strategies...", key="strat_multiselect")
        st.session_state.selected_strategies = selected_strats

    if selected_strats:
        filtered_bt = bt_df[bt_df['strategy'].isin(selected_strats)] if not bt_df.empty else pd.DataFrame()
        filtered_live = live_df[live_df['strategy'].isin(selected_strats)] if not live_df.empty else pd.DataFrame()
    else:
        filtered_bt = pd.DataFrame()
        filtered_live = pd.DataFrame()

    st.sidebar.markdown("---")

    # Sidebar info
    if not filtered_bt.empty:
        min_date = filtered_bt['timestamp'].min()
        max_date = filtered_bt['timestamp'].max()
        d_start = min_date.date() if hasattr(min_date, 'date') else "N/A"
        d_end = max_date.date() if hasattr(max_date, 'date') else "N/A"
        file_info = st.session_state.get('bt_filenames', 'Backtest Data')
        st.sidebar.markdown(
            f"<div class='sidebar-footer'><b>🧬 {file_info}</b><br>"
            f"📅 {d_start} to {d_end}<br>📊 {len(filtered_bt)} Trades</div>",
            unsafe_allow_html=True
        )

    if not filtered_live.empty:
        l_info = st.session_state.get('live_filenames', 'Live Data')
        min_ts = filtered_live['timestamp'].min()
        l_min_str = str(min_ts.date()) if hasattr(min_ts, 'date') else "N/A"
        st.sidebar.markdown(
            f"<div class='sidebar-footer' style='background-color: #E0F2FE; margin-top: 5px;'>"
            f"<b>⚡ {l_info}</b><br>📅 Since: {l_min_str}<br>📊 {len(filtered_live)} Trades</div>",
            unsafe_allow_html=True
        )

    # Late live data upload
    if live_df.empty:
        st.sidebar.markdown("---")
        st.sidebar.caption("⚡ Add Live Data:")
        late_live = st.sidebar.file_uploader("Upload Live Log", type=['csv', 'xlsx', 'xls'],
                                             key="late_live", label_visibility="collapsed")
        if late_live:
            d = load_file_with_caching(late_live)
            if d is not None:
                st.session_state['live_df'] = d
                st.session_state['live_filenames'] = late_live.name
                st.rerun()

   
     # Enhanced Save/Load System
    if not filtered_bt.empty or not filtered_live.empty:
        render_save_load_sidebar(filtered_bt, filtered_live)

    # Reset button
    st.sidebar.markdown("---")
    if st.sidebar.button("🔄 Reset / Change Files"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

    # Track page changes for loading indicator
    if 'current_page' not in st.session_state:
        st.session_state.current_page = page
    
    page_changed = st.session_state.current_page != page
    st.session_state.current_page = page
    
    # Show brief loading indicator when page changes
    if page_changed:
        loading_messages = {
            "📊  Portfolio Analytics": ("📊 Loading Analytics", "Crunching your portfolio numbers..."),
            "🔬  MEIC Deep Dive": ("🔍 Loading MEIC Analysis", "Analyzing entry times..."),
            "⚖️  Live vs. Backtest": ("⚖️ Loading Comparison", "Comparing live vs backtest..."),
            "🏗️  Portfolio Builder": ("🏗️ Loading Portfolio Builder", "Preparing interactive allocation tools..."),
            "🎲  Monte Carlo Punisher": ("🎲 Loading Monte Carlo", "Preparing simulation engine..."),
            "🤖  AI Analyst": ("🤖 Loading AI Analyst", "Warming up the AI...")
        }
        msg, submsg = loading_messages.get(page, ("Loading...", "Please wait..."))
        
        page_loading = st.empty()
        page_loading.markdown(f"""
        <div class="loading-overlay">
            <div class="engine-container">
                <div class="gear-system">
                    <span class="gear gear-1">⚙️</span>
                    <span class="gear gear-2">⚙️</span>
                    <span class="gear gear-3">⚙️</span>
                </div>
                <div class="loading-text">{msg}</div>
                <div class="loading-subtext">{submsg}</div>
                <div class="progress-bar-container">
                    <div class="progress-bar"></div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Small delay to show loading
        import time
        time.sleep(0.3)
        page_loading.empty()

    # Page routing
    if page == "📊  Portfolio Analytics":
        page_portfolio_analytics(filtered_bt, filtered_live if not filtered_live.empty else None)
    elif page == "🔬  MEIC Deep Dive":
        page_meic_analysis(filtered_bt, filtered_live if not filtered_live.empty else None)
    elif page == "🧪  MEIC Optimizer":
        page_meic_optimizer()
    elif page == "⚖️  Live vs. Backtest":
        page_comparison()
    elif page == "🏗️  Portfolio Builder":
        page_portfolio_builder(filtered_bt)
    elif page == "🎲  Monte Carlo Punisher":
        page_monte_carlo(filtered_bt)
    elif page == "🤖  AI Analyst":
        page_ai_analyst(filtered_bt)
    
    # Disclaimer footer
    st.markdown("---")
    st.markdown("""
    <div style='background: linear-gradient(135deg, #FEF3C7 0%, #FDE68A 100%); 
                padding: 16px 24px; 
                border-radius: 12px; 
                margin-top: 40px;
                border-left: 4px solid #F59E0B;
                box-shadow: 0 2px 8px rgba(245, 158, 11, 0.15);'>
        <div style='display: flex; align-items: center; gap: 12px;'>
            <span style='font-size: 24px;'>⚠️</span>
            <div>
                <div style='font-family: Poppins, sans-serif; font-weight: 600; color: #92400E; font-size: 14px; margin-bottom: 4px;'>
                    DISCLAIMER
                </div>
                <div style='font-family: Poppins, sans-serif; color: #78350F; font-size: 13px; line-height: 1.5;'>
                    This tool is for educational and informational purposes only. It does not constitute financial, investment, tax, or legal advice. 
                    Past performance is not indicative of future results. Always consult a qualified financial advisor before making investment decisions.
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)








