import streamlit as st
import pandas as pd
import database as db
import time
import os

# --- CORPORATE IDENTITY COLORS ---
COLOR_BLUE = "#302BFF"   # Electric Blue
COLOR_TEAL = "#00D2BE"   # Turbo Teal (Profit)
COLOR_CORAL = "#FF2E4D"  # Radical Coral (Loss)
COLOR_GREY = "#4B5563"   # Space Grey
COLOR_ICE = "#F0F4FF"    # Ice Tint (Backgrounds)
COLOR_AMBER = "#FFAB00"  # Amber Flux (Warning)
COLOR_PURPLE = "#7B2BFF" # Electric Violet (Hover)

def render_logo():
    """
    Renders the official Logo.
    """
    # Simple direct render to avoid complex error catching that might be false-positive
    if os.path.exists("CashflowEnginelogo.png"):
        st.image("CashflowEnginelogo.png", width=350)
    else:
        st.markdown(f"""
        <div style="text-align: center; padding: 10px 0;">
            <div style="font-family: 'Exo 2', sans-serif; font-weight: 800; font-size: 30px; color: {COLOR_GREY}; letter-spacing: 1px;">
                ⚡ CASHFLOW ENGINE
            </div>
        </div>
        """, unsafe_allow_html=True)

def render_footer():
    """
    Renders the disclaimer footer.
    """
    st.markdown("""
    <div class="footer">
        <strong>DISCLAIMER:</strong> This application is for educational and entertainment purposes only. 
        It does not constitute financial advice. Option trading involves significant risk and is not suitable for all investors. 
        Past performance is not indicative of future results.
    </div>
    """, unsafe_allow_html=True)

def section_header(title):
    """Render a styled blue header using Exo 2."""
    st.markdown(f"<div class='card-title' style='color: {COLOR_BLUE} !important; margin-bottom: 20px;'>{title}</div>", unsafe_allow_html=True)

def show_loading_overlay(message="Processing", submessage="The engine is running..."):
    """Display a custom loading overlay."""
    loading_html = f"""
    <div class="loading-overlay" id="loadingOverlay">
        <div class="engine-container">
            <div class="gear-system">
                <span class="gear gear-1">⚙️</span>
                <span class="gear gear-2">⚙️</span>
                <span class="gear gear-3">⚙️</span>
            </div>
            <div class="loading-text" style="color: {COLOR_BLUE};">{message}</div>
            <div class="loading-subtext">{submessage}</div>
            <div class="progress-bar-container">
                <div class="progress-bar"></div>
            </div>
        </div>
    </div>
    """
    return st.markdown(loading_html, unsafe_allow_html=True)

def hide_loading_overlay():
    """Hide the loading overlay."""
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
    """Render a hero metric card."""
    tooltip_html = ""
    if tooltip:
        tooltip_escaped = tooltip.replace("'", "&#39;").replace('"', '&quot;')
        tooltip_html = f"<span class='tooltip-icon' data-tip='{tooltip_escaped}'>?</span>"
    
    # Apply color classes. 'hero-cyan' and 'hero-red' are defined in app.py CSS
    st.markdown(
        f"<div class='hero-card {color_class}'>"
        f"<div class='hero-label'>{label} {tooltip_html}</div>"
        f"<div class='hero-value'>{value}</div>"
        f"<div class='hero-sub'>{subtext}</div>"
        f"</div>",
        unsafe_allow_html=True
    )

def color_monthly_performance(val):
    """Color code monthly performance values."""
    try:
        if isinstance(val, str):
            clean_val = val.replace('$', '').replace(',', '').replace('%', '').strip()
            num_val = float(clean_val)
        else:
            num_val = float(val)
        
        if num_val > 0:
            return f'background-color: rgba(0, 210, 190, 0.15); color: {COLOR_GREY}; font-weight: 600;'
        elif num_val < 0:
            return f'background-color: rgba(255, 46, 77, 0.15); color: {COLOR_GREY}; font-weight: 600;'
        else:
            return 'background-color: white; color: #374151'
    except (ValueError, TypeError):
        return 'background-color: white; color: #374151'

# --- SAVE/LOAD UI ---

def render_save_load_sidebar(bt_df, live_df):
    """Enhanced save/load system inside sidebar."""
    
    if not db.DB_AVAILABLE:
        st.warning("DB not connected")
        return
    
    # Simple Tabs to save space
    save_tab, load_tab = st.tabs(["Save", "Load"])
    
    with save_tab:
        if bt_df is None or bt_df.empty:
            st.caption("No data to save.")
        else:
            strategies = bt_df['strategy'].unique().tolist() if 'strategy' in bt_df.columns else []
            default_name = f"Analysis {len(strategies)} Strat"
            
            save_name = st.text_input("Name", value=default_name, key="save_name_input", label_visibility="collapsed", placeholder="Name")
            save_desc = st.text_area("Desc", height=60, key="save_desc_input", label_visibility="collapsed", placeholder="Notes")
            
            if st.button("SAVE", use_container_width=True):
                if db.save_analysis_to_db_enhanced(save_name, bt_df, live_df, save_desc):
                    st.success("Saved!")

    with load_tab:
        saved = db.get_analysis_list_enhanced()
        if not saved:
            st.caption("No saves.")
        else:
            # Dropdown for compact view
            opts = {f"{a['name']} ({a['created_at'][:10]})": a['id'] for a in saved}
            sel_name = st.selectbox("Select", options=list(opts.keys()), label_visibility="collapsed", key="load_sel_sb")
            
            if sel_name:
                aid = opts[sel_name]
                if st.button("LOAD", key=f"load_btn_sb", use_container_width=True):
                    _load_with_feedback(aid, sel_name)
                    
                if st.button("DELETE", key=f"del_btn_sb", use_container_width=True):
                    if db.delete_analysis_from_db(aid):
                        st.rerun()

def _load_with_feedback(analysis_id, name):
    loading = st.empty()
    loading.info(f"Loading...")
    bt_df, live_df = db.load_analysis_from_db(analysis_id)
    if bt_df is not None:
        st.session_state['full_df'] = bt_df
        if live_df is not None:
            st.session_state['live_df'] = live_df
        loading.success(f"Loaded!")
        time.sleep(0.5)
        st.session_state.navigate_to_page = "Portfolio Analytics"
        st.rerun()
