import streamlit as st
import pandas as pd
import database as db
import time

# Constants
COLOR_TEAL = "#00D2BE"
COLOR_CORAL = "#FF2E4D"
COLOR_BLUE = "#302BFF"
COLOR_GREY = "#4B5563"
COLOR_PURPLE = "#7B2BFF"

def section_header(title):
    """Render a styled blue header for cards."""
    st.markdown(f"<div class='card-title'>{title}</div>", unsafe_allow_html=True)

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

# --- SAVE/LOAD UI ---

def render_save_load_sidebar(bt_df, live_df):
    """Enhanced save/load system in sidebar."""
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 💾 Analysis Manager")
    
    if not db.DB_AVAILABLE:
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
    
    available_tags = ["Backtest", "Live", "MEIC", "Iron Condor", "Calendar", "Optimized", "Conservative", "Production"]
    default_tags = ["Backtest"] if bt_df is not None and not bt_df.empty else []
    if live_df is not None and not live_df.empty: default_tags.append("Live")
    
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
        
        with st.spinner("Saving..."):
            if db.save_analysis_to_db_enhanced(save_name, bt_df, live_df, save_description, selected_tags):
                st.success("✅ Saved!")
                st.balloons()

def _render_load_section():
    st.markdown("##### 📂 Load")
    saved = db.get_analysis_list_enhanced()
    if not saved:
        st.info("No saved analyses.")
        return
    
    search = st.text_input("🔍 Search", key="load_search")
    
    filtered = saved
    if search:
        filtered = [a for a in filtered if search.lower() in a['name'].lower()]
    
    if not filtered:
        st.warning("No matches.")
        return
    
    st.caption(f"Found {len(filtered)} analysis(es)")
    for a in filtered[:10]:
        with st.container(border=True):
            st.markdown(f"**{a['name']}**")
            meta = [f"📅 {a['created_at'][:10]}"]
            if a.get('trade_count'): meta.append(f"📊 {a['trade_count']}")
            st.caption(" | ".join(meta))
            if st.button("Load", key=f"load_{a['id']}", use_container_width=True):
                _load_with_feedback(a['id'], a['name'])

def _render_manage_section():
    st.markdown("##### ⚙️ Manage")
    saved = db.get_analysis_list_enhanced()
    if not saved: return
    
    options = {f"{a['name']} ({a['created_at'][:10]})": a for a in saved}
    sel = st.selectbox("Select", ["--"] + list(options.keys()), key="manage_sel")
    
    if sel == "--": return
    analysis = options[sel]
    
    action = st.radio("Action", ["✏️ Rename", "🗑️ Delete"], horizontal=True, key="manage_action")
    
    if "Rename" in action:
        new_name = st.text_input("New name", value=analysis['name'], key="new_name")
        if st.button("Apply", use_container_width=True, key="rename_btn"):
            if new_name and new_name != analysis['name']:
                if db.rename_analysis_in_db(analysis['id'], new_name):
                    st.success("Renamed!")
                    time.sleep(0.5)
                    st.rerun()
    elif "Delete" in action:
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
        st.session_state['bt_filenames'] = f"📂 {name}"
        if live_df is not None:
            st.session_state['live_df'] = live_df
            st.session_state['live_filenames'] = "Archive"
        loading.success(f"✅ Loaded!")
        time.sleep(0.5)
        st.rerun()
    else:
        loading.error("Failed to load.")
