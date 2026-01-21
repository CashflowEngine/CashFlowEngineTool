import streamlit as st
import pandas as pd
import database as db
import time
import os
import base64

# --- CORPORATE IDENTITY COLORS ---
COLOR_BLUE = "#302BFF"   # Electric Blue
COLOR_TEAL = "#00D2BE"   # Turbo Teal (Profit)
COLOR_CORAL = "#FF2E4D"  # Radical Coral (Loss)
COLOR_GREY = "#4B5563"   # Space Grey
COLOR_ICE = "#F0F4FF"    # Ice Tint (Backgrounds)
COLOR_AMBER = "#FFAB00"  # Amber Flux (Warning)
COLOR_PURPLE = "#7B2BFF" # Electric Violet (Hover)

@st.cache_data(show_spinner=False)
def _get_logo_base64():
    """Load logo as base64 for reliable rendering."""
    logo_file = "CashflowEnginelogo.png"
    if os.path.exists(logo_file):
        try:
            with open(logo_file, "rb") as f:
                data = f.read()
                # Verify it's a PNG (check for PNG signature anywhere in first 16 bytes)
                if b'PNG' in data[:16]:
                    return base64.b64encode(data).decode()
        except Exception:
            pass
    return None

def render_logo(width=200, centered=True):
    """
    Renders the official Logo using base64 encoding for reliability.
    """
    logo_b64 = _get_logo_base64()

    if logo_b64:
        align = "center" if centered else "left"
        st.markdown(f"""
            <div style="text-align: {align}; padding: 10px 0;">
                <img src="data:image/png;base64,{logo_b64}" width="{width}" alt="Cashflow Engine Logo" />
            </div>
        """, unsafe_allow_html=True)
    else:
        _render_text_fallback(centered)

def render_logo_sidebar():
    """Render logo for sidebar (smaller)."""
    render_logo(width=180, centered=True)

def _render_text_fallback(centered=True):
    align = "center" if centered else "left"
    st.markdown(f"""
        <div style="text-align: {align}; padding: 10px 0;">
            <div style="font-family: 'Exo 2', sans-serif; font-weight: 800; font-size: 24px; color: {COLOR_BLUE}; letter-spacing: 1px;">
                CASHFLOW ENGINE
            </div>
        </div>
    """, unsafe_allow_html=True)

def render_data_required_overlay():
    """Render a full-screen overlay for data required warning."""
    st.markdown(f"""
        <style>
            .data-required-overlay {{
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background-color: rgba(255, 255, 255, 0.95);
                z-index: 9999;
                display: flex;
                justify-content: center;
                align-items: center;
            }}
            .data-required-box {{
                background: white;
                padding: 60px 80px;
                border-radius: 16px;
                box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
                text-align: center;
                max-width: 500px;
            }}
            .data-required-icon {{
                font-size: 64px;
                margin-bottom: 20px;
            }}
            .data-required-title {{
                font-family: 'Exo 2', sans-serif;
                font-weight: 800;
                font-size: 28px;
                color: {COLOR_GREY};
                text-transform: uppercase;
                margin-bottom: 16px;
            }}
            .data-required-text {{
                font-family: 'Poppins', sans-serif;
                font-size: 16px;
                color: #6B7280;
                line-height: 1.6;
            }}
        </style>
        <div class="data-required-overlay" id="dataRequiredOverlay">
            <div class="data-required-box">
                <div class="data-required-icon">📊</div>
                <div class="data-required-title">Data Required</div>
                <div class="data-required-text">
                    To access the analytics engine, please import your trading data first via the Landing Page.
                </div>
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

def section_header(title, description=None):
    """Render a styled blue header using Exo 2 with optional description."""
    st.markdown(f"""
        <div style="margin-bottom: 20px;">
            <div style="font-family: 'Exo 2', sans-serif !important; font-weight: 800 !important; font-size: 18px !important;
                        color: {COLOR_BLUE} !important; text-transform: uppercase !important; letter-spacing: 1px !important;">
                {title}
            </div>
        </div>
    """, unsafe_allow_html=True)
    if description:
        st.markdown(f"""
            <div style="font-family: 'Poppins', sans-serif !important; font-size: 14px !important; color: #6B7280 !important;
                        margin-top: -12px; margin-bottom: 16px; line-height: 1.6 !important;">
                {description}
            </div>
        """, unsafe_allow_html=True)

def show_loading_overlay(message="Processing", submessage="The engine is running..."):
    """Display a full-screen loading overlay."""
    loading_html = f"""
    <style>
        .loading-overlay {{
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(255, 255, 255, 0.95);
            z-index: 10000;
            display: flex;
            justify-content: center;
            align-items: center;
        }}
        .engine-container {{
            text-align: center;
            padding: 40px;
        }}
        .gear-system {{
            margin-bottom: 30px;
        }}
        .gear {{
            display: inline-block;
            font-size: 48px;
            animation: spin 2s linear infinite;
        }}
        .gear-1 {{ animation-duration: 3s; }}
        .gear-2 {{ animation-duration: 2s; animation-direction: reverse; margin: 0 -10px; }}
        .gear-3 {{ animation-duration: 2.5s; }}
        @keyframes spin {{
            from {{ transform: rotate(0deg); }}
            to {{ transform: rotate(360deg); }}
        }}
        .loading-text {{
            font-family: 'Exo 2', sans-serif;
            font-weight: 800;
            font-size: 28px;
            text-transform: uppercase;
            letter-spacing: 2px;
            margin-bottom: 10px;
        }}
        .loading-subtext {{
            font-family: 'Poppins', sans-serif;
            font-size: 14px;
            color: #6B7280;
        }}
        .progress-bar-container {{
            width: 200px;
            height: 4px;
            background: #E5E7EB;
            border-radius: 2px;
            margin: 20px auto 0;
            overflow: hidden;
        }}
        .progress-bar {{
            width: 40%;
            height: 100%;
            background: {COLOR_BLUE};
            border-radius: 2px;
            animation: progress 1.5s ease-in-out infinite;
        }}
        @keyframes progress {{
            0% {{ transform: translateX(-100%); }}
            100% {{ transform: translateX(350%); }}
        }}
    </style>
    <div class="loading-overlay" id="loadingOverlay">
        <div class="engine-container">
            <div class="gear-system">
                <span class="gear gear-1">&#9881;</span>
                <span class="gear gear-2">&#9881;</span>
                <span class="gear gear-3">&#9881;</span>
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
    """Hide the loading overlay via JavaScript."""
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