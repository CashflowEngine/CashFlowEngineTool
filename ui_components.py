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

# --- FONT INJECTION ---
def inject_fonts():
    """Inject Google Fonts with JavaScript enforcement for reliable loading."""
    st.markdown("""
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Exo+2:wght@400;500;600;700;800;900&family=Poppins:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Exo+2:wght@400;500;600;700;800;900&family=Poppins:wght@300;400;500;600;700&display=swap');

        /* Force Exo 2 on all headings */
        h1, h2, h3, h4, h5, h6 {
            font-family: 'Exo 2', sans-serif !important;
            font-weight: 800 !important;
        }
    </style>
    <script>
        // Wait for fonts to load, then force apply
        document.fonts.ready.then(function() {
            // Apply Exo 2 to all headings
            document.querySelectorAll('h1, h2, h3, h4, h5, h6').forEach(function(el) {
                el.style.fontFamily = "'Exo 2', sans-serif";
                el.style.fontWeight = "800";
            });
        });

        // Also run after a short delay to catch dynamically loaded content
        setTimeout(function() {
            document.querySelectorAll('h1, h2, h3, h4, h5, h6').forEach(function(el) {
                el.style.fontFamily = "'Exo 2', sans-serif";
                el.style.fontWeight = "800";
            });
        }, 500);
    </script>
    """, unsafe_allow_html=True)

def render_page_header(title, subtitle=None):
    """Render a consistent page header with Exo 2 font - uses h1 tag like original."""
    inject_fonts()

    # Use h1 tag exactly like the original - browser renders it large automatically
    # No explicit font-size - let browser/Streamlit handle the sizing
    header_html = f"""<h1 style='color: #4B5563; font-family: "Exo 2", sans-serif; font-weight: 800;
        text-transform: uppercase; margin-bottom: 0;'>{title}</h1>"""

    if subtitle:
        header_html += f'<p style="font-family: Poppins, sans-serif; color: #6B7280; font-size: 14px; margin-top: 8px;">{subtitle}</p>'

    st.markdown(header_html, unsafe_allow_html=True)

def _get_logo_base64(logo_file="CashflowEnginelogo.png"):
    """Load logo as base64 for reliable rendering."""
    if os.path.exists(logo_file):
        try:
            with open(logo_file, "rb") as f:
                data = f.read()
                # Verify it's a valid PNG (check signature)
                if data[:4] == b'\x89PNG':
                    return base64.b64encode(data).decode()
        except Exception as e:
            pass
    return None

def render_logo(width=200, centered=True, logo_file="CashflowEnginelogo.png"):
    """
    Renders the official Logo using base64 encoding for reliability.
    """
    logo_b64 = _get_logo_base64(logo_file)

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
    """Render grey logo for sidebar (matches gray background). 20% larger for better visibility."""
    render_logo(width=260, centered=False, logo_file="CashflowEnginelogogrey.png")

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
    """Render a full-screen overlay for data required warning with close button."""
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
                position: relative;
            }}
            .data-required-icon {{
                font-size: 64px;
                margin-bottom: 20px;
            }}
            .data-required-title {{
                font-family: 'Exo 2', sans-serif !important;
                font-weight: 800 !important;
                font-size: 28px;
                color: {COLOR_GREY};
                text-transform: uppercase;
                margin-bottom: 16px;
                letter-spacing: 1px;
            }}
            .data-required-text {{
                font-family: 'Poppins', sans-serif !important;
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
    title_style = "font-family: 'Exo 2', sans-serif !important; font-weight: 800 !important; font-size: 18px !important; color: #302BFF !important; text-transform: uppercase !important; letter-spacing: 1px !important; margin-bottom: 10px;"
    st.markdown(f'<div class="exo2-heading" style="{title_style}">{title}</div>', unsafe_allow_html=True)
    if description:
        desc_style = "font-family: 'Poppins', sans-serif !important; font-size: 14px !important; color: #6B7280 !important; margin-bottom: 16px; line-height: 1.6 !important;"
        st.markdown(f'<p style="{desc_style}">{description}</p>', unsafe_allow_html=True)

def show_loading_overlay(message="Processing", submessage="The engine is running...", placeholder=None):
    """Display a full-screen loading overlay with animated gears (like original design)."""
    loading_html = f"""
    <style>
        .loading-overlay {{
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
        }}
        .engine-container {{
            text-align: center;
            animation: pulse 2s ease-in-out infinite;
        }}
        .gear-system {{
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 5px;
            margin-bottom: 20px;
        }}
        .gear {{
            font-size: 40px;
            color: {COLOR_BLUE};
        }}
        .gear-1 {{ animation: spin 2s linear infinite; }}
        .gear-2 {{ animation: spin-reverse 1.5s linear infinite; font-size: 50px; }}
        .gear-3 {{ animation: spin 2s linear infinite; }}
        @keyframes spin {{
            from {{ transform: rotate(0deg); }}
            to {{ transform: rotate(360deg); }}
        }}
        @keyframes spin-reverse {{
            from {{ transform: rotate(360deg); }}
            to {{ transform: rotate(0deg); }}
        }}
        @keyframes pulse {{
            0%, 100% {{ opacity: 1; }}
            50% {{ opacity: 0.7; }}
        }}
        .loading-text {{
            font-family: 'Exo 2', sans-serif;
            font-size: 24px;
            font-weight: 700;
            color: {COLOR_BLUE};
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
            width: 300px;
            height: 6px;
            background: #E5E7EB;
            border-radius: 3px;
            overflow: hidden;
            margin-top: 20px;
        }}
        .progress-bar {{
            height: 100%;
            background: linear-gradient(90deg, {COLOR_BLUE}, {COLOR_TEAL}, {COLOR_BLUE});
            background-size: 200% 100%;
            animation: progress-flow 1.5s linear infinite;
            width: 100%;
        }}
        @keyframes progress-flow {{
            0% {{ background-position: 100% 0; }}
            100% {{ background-position: -100% 0; }}
        }}
    </style>
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
    if placeholder is not None:
        placeholder.markdown(loading_html, unsafe_allow_html=True)
        return placeholder
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

            if st.button("Save Analysis", use_container_width=True, type="tertiary"):
                _save_with_feedback(save_name, bt_df, live_df, save_desc)

    with load_tab:
        saved = db.get_analysis_list()  # Use wrapper that passes user_id for cache
        if not saved:
            st.caption("No saves.")
        else:
            # Dropdown for compact view
            opts = {f"{a['name']} ({a['created_at'][:10]})": a['id'] for a in saved}
            sel_name = st.selectbox("Select", options=list(opts.keys()), label_visibility="collapsed", key="load_sel_sb")
            
            if sel_name:
                aid = opts[sel_name]
                # Use text links (tertiary buttons) for Load and Delete
                link_col1, link_col2 = st.columns(2)
                with link_col1:
                    if st.button("Load", key=f"load_btn_sb", use_container_width=True, type="tertiary"):
                        _load_with_feedback(aid, sel_name)
                with link_col2:
                    if st.button("Delete", key=f"del_btn_sb", use_container_width=True, type="tertiary"):
                        if db.delete_analysis_from_db(aid):
                            st.rerun()

def _save_with_feedback(name, bt_df, live_df, description):
    """Save analysis with loading overlay feedback."""
    # Show saving overlay
    show_loading_overlay("SAVING TO CLOUD", "Uploading your analysis data...")

    # Perform save
    success = db.save_analysis_to_db_enhanced(name, bt_df, live_df, description)

    # Hide overlay
    hide_loading_overlay()

    if success:
        st.success(f"✓ Saved '{name}' successfully!")
        time.sleep(1)
        st.rerun()
    else:
        st.error("Failed to save. Please try again.")


def _load_with_feedback(analysis_id, name):
    """Load analysis with loading overlay feedback."""
    show_loading_overlay("LOADING FROM CLOUD", "Fetching your analysis data...")

    user_id = db.get_current_user_id()
    bt_df, live_df = db.load_analysis_from_db(analysis_id, _user_id=user_id)

    hide_loading_overlay()

    if bt_df is not None:
        st.session_state['full_df'] = bt_df
        if live_df is not None:
            st.session_state['live_df'] = live_df
        st.success(f"✓ Loaded successfully!")
        time.sleep(0.5)
        st.session_state.navigate_to_page = "Portfolio Analytics"
        st.rerun()
    else:
        st.error("Failed to load. Please try again.")