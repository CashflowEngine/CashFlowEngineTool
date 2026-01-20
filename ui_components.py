import streamlit as st
import pandas as pd
import database as db
import time

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
    Renders the official Master-Logo according to CI construction rules.
    1. Upper Line (Electric Blue)
    2. Headline (Exo 2 Bold Uppercase)
    3. Subline (Poppins Bold Uppercase)
    4. Lower Line (Electric Blue)
    5. Signature (Poppins Light Uppercase)
    """
    st.markdown(f"""
    <div style="text-align: center; padding: 20px 0;">
        <div style="height: 2px; background-color: {COLOR_BLUE}; width: 100%; margin-bottom: 15px;"></div>
        <div style="font-family: 'Exo 2', sans-serif; font-weight: 800; font-size: 28px; color: {COLOR_GREY}; letter-spacing: 2px; line-height: 1.2;">
            CASHFLOW<br>ENGINE
        </div>
        <div style="font-family: 'Poppins', sans-serif; font-weight: 700; font-size: 10px; color: {COLOR_GREY}; letter-spacing: 3px; margin-top: 5px; margin-bottom: 15px;">
            AUTOMATED OPTIONS TRADING
        </div>
        <div style="height: 2px; background-color: {COLOR_BLUE}; width: 100%; margin-bottom: 10px;"></div>
        <div style="font-family: 'Poppins', sans-serif; font-weight: 300; font-size: 9px; color: {COLOR_BLUE}; letter-spacing: 4px; text-align: center;">
            ENGINEERED BY THOMAS MEHLITZ
        </div>
    </div>
    """, unsafe_allow_html=True)

def section_header(title):
    """Render a styled blue header for cards using Exo 2."""
    st.markdown(f"<div class='card-title' style='color: {COLOR_BLUE} !important; margin-bottom: 20px;'>{title}</div>", unsafe_allow_html=True)

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
    """Render a hero metric card with optional tooltip."""
    tooltip_html = ""
    if tooltip:
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
    """Color code monthly performance values - Turbo Teal vs Radical Coral."""
    try:
        if isinstance(val, str):
            clean_val = val.replace('$', '').replace(',', '').replace('%', '').strip()
            num_val = float(clean_val)
        else:
            num_val = float(val)
        
        if num_val > 0:
            # Green/Teal tint
            return f'background-color: rgba(0, 210, 190, 0.15); color: {COLOR_GREY}; font-weight: 600;'
        elif num_val < 0:
            # Red/Coral tint
            return f'background-color: rgba(255, 46, 77, 0.15); color: {COLOR_GREY}; font-weight: 600;'
        else:
            return 'background-color: white; color: #374151'
    except (ValueError, TypeError):
        return 'background-color: white; color: #374151'

# --- SAVE/LOAD UI ---

def render_save_load_sidebar(bt_df, live_df):
    """Enhanced save/load system in sidebar."""
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 💾 Analysis Manager")
    
    if not db.DB_AVAILABLE:
        st.sidebar.warning("☁️ Database not connected")
        return
    
    save_tab, load_tab, manage_tab = st.sidebar.tabs(["Save", "Load", "Manage"])
    
    with save_tab:
        _render_save_section(bt_df, live_df)
    
    with load_tab:
        _render_load_section()
    
    with manage_tab:
        _render_manage_section()

def _render_save_section(bt_df, live_df):
    if bt_df is None or bt_df.empty:
        st.info("📊 No data to save.")
        return
    
    strategies = bt_df['strategy'].unique().tolist() if 'strategy' in bt_df.columns else []
    date_range = ""
    if 'timestamp' in bt_df.columns:
        min_d = bt_df['timestamp'].min()
        max_d = bt_df['timestamp'].max()
        if pd.notna(min_d) and pd.notna(max_d):
            date_range = f"{min_d.strftime('%Y%m%d')}-{max_d.strftime('%Y%m%d')}"
    
    default_name = f"Analysis_{date_range}"
    if len(strategies) > 0:
        default_name = f"{strategies[0][:15]}_{date_range}"
    
    st.markdown("##### 📝 Save Current Analysis")
    save_name = st.text_input("Name", value=default_name, max_chars=100, key="save_name")
    save_description = st.text_area("Description", placeholder="Notes...", max_chars=300, height=60, key="save_desc")
    
    if st.button("💾 Save to Cloud", use_container_width=True, type="primary"):
        with st.spinner("Saving..."):
            if db.save_analysis_to_db_enhanced(save_name, bt_df, live_df, save_description):
                st.success("✅ Saved!")

def _render_load_section():
    st.markdown("##### 📂 Load Analysis")
    saved = db.get_analysis_list_enhanced()
    if not saved:
        st.info("No saved analyses.")
        return
    
    search = st.text_input("🔍 Search", key="load_search")
    
    filtered = saved
    if search:
        filtered = [a for a in filtered if search.lower() in a['name'].lower()]
    
    for a in filtered[:5]:
        with st.container(border=True):
            st.markdown(f"**{a['name']}**")
            st.caption(f"📅 {a['created_at'][:10]} | 📊 {a.get('trade_count',0)} Trades")
            if st.button("Load", key=f"load_{a['id']}", use_container_width=True):
                _load_with_feedback(a['id'], a['name'])

def _render_manage_section():
    st.markdown("##### ⚙️ Manage")
    saved = db.get_analysis_list_enhanced()
    if not saved: return
    
    options = {f"{a['name']}": a for a in saved}
    sel = st.selectbox("Select", list(options.keys()), key="manage_sel")
    if sel:
        analysis = options[sel]
        if st.button("🗑️ Delete", use_container_width=True, key="del_btn"):
            if db.delete_analysis_from_db(analysis['id']):
                st.success("Deleted!")
                time.sleep(0.5)
                st.rerun()

def _load_with_feedback(analysis_id, name):
    loading = st.empty()
    loading.info(f"Loading {name}...")
    bt_df, live_df = db.load_analysis_from_db(analysis_id)
    if bt_df is not None:
        st.session_state['full_df'] = bt_df
        if live_df is not None:
            st.session_state['live_df'] = live_df
        loading.success(f"✅ Loaded!")
        time.sleep(0.5)
        st.session_state.navigate_to_page = "📊 Portfolio Analytics"
        st.rerun()
    else:
        loading.error("Failed to load.")
