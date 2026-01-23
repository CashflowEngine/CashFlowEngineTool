import streamlit as st
import pandas as pd
import ui_components as ui
import database as db
import calculations as calc

# Import auth module
from core.auth import (
    init_auth_session_state,
    sign_out,
    is_authenticated,
    verify_and_refresh_session,
    get_current_user
)

# Import page modules
import modules.login as login
import modules.landing as landing
import modules.portfolio_analytics as portfolio_analytics
import modules.portfolio_builder as portfolio_builder
import modules.monte_carlo as monte_carlo
import modules.comparison as comparison
import modules.meic_analysis as meic_analysis
import modules.meic_optimizer as meic_optimizer
import modules.ai_analyst as ai_analyst
import modules.privacy as privacy

# --- 1. CONFIGURATION ---
st.set_page_config(
    page_title="Cashflow Engine",
    page_icon="CashflowEngine_favicon.png",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. CORPORATE IDENTITY CSS ---
# Preload fonts for faster loading
st.markdown("""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Exo+2:wght@400;500;600;700;800;900&family=Poppins:wght@300;400;500;600;700&display=swap" rel="stylesheet">
""", unsafe_allow_html=True)

st.markdown("""
<style>
    /* IMPORT FONTS - FULL WEIGHTS (backup) */
    @import url('https://fonts.googleapis.com/css2?family=Exo+2:ital,wght@0,100..900;1,100..900&family=Poppins:wght@300;400;500;600;700&display=swap');

    /* --- HIDE STREAMLIT BRANDING & MENU --- */
    /* Hide the hamburger menu (three dots) */
    #MainMenu {visibility: hidden !important;}
    [data-testid="stToolbar"] {visibility: hidden !important; height: 0 !important;}

    /* Hide the header completely */
    header[data-testid="stHeader"] {display: none !important;}

    /* Hide "Made with Streamlit" footer */
    footer {visibility: hidden !important;}
    .viewerBadge_container__r5tak {display: none !important;}

    /* Hide deploy button */
    .stDeployButton {display: none !important;}
    [data-testid="stDecoration"] {display: none !important;}

    /* --- SIDEBAR FLASH PREVENTION (loaded first) --- */
    /* This prevents the sidebar flash during page transitions by hiding toggle buttons */
    button[kind="header"],
    [data-testid="baseButton-header"],
    [data-testid="stSidebarCollapseButton"],
    [data-testid="collapsedControl"],
    [data-testid="stSidebarCollapsedControl"] {
        display: none !important;
        visibility: hidden !important;
    }

    /* --- TYPOGRAPHY --- */

    /* Force Poppins for All Body Text */
    * {
        font-family: 'Poppins', sans-serif;
    }

    html, body, [class*="css"], .stMarkdown, .stText, p, div, span, label, input, .stDataFrame, .stTable, .stSelectbox, .stNumberInput, button {
        font-family: 'Poppins', sans-serif !important;
        color: #4B5563;
    }

    /* Force Exo 2 for ALL Headings - More specific selectors */
    /* Force Exo 2 for ALL Headings and custom classes */
    .exo2-heading,
    .card-title,
    .stHeading,
    .stMetricValue,
    .page-header,
    .section-title,
    .hero-value,
    .feature-title,
    .data-required-title,
    .loading-text {
        font-family: 'Exo 2', sans-serif !important;
        text-transform: uppercase !important;
        letter-spacing: 0.5px !important;
        color: #4B5563 !important;
        font-weight: 800 !important;
    }

    /* Tagline styling - ensure Exo 2 */
    .tagline, .tagline h2, .tagline span {
        font-family: 'Exo 2', sans-serif !important;
        font-weight: 800 !important;
        text-transform: uppercase !important;
    }

    /* Specific overrides for Streamlit elements to ensure font sticks */
    .stMetricLabel { font-family: 'Poppins', sans-serif !important; font-weight: 600 !important; }

    /* --- SIDEBAR TOGGLE - COMPLETELY HIDDEN --- */
    /* Hide the entire collapse/expand button */
    button[kind="header"],
    [data-testid="baseButton-header"],
    [data-testid="stSidebarCollapseButton"],
    [data-testid="collapsedControl"],
    [data-testid="stSidebarCollapsedControl"] {
        display: none !important;
        visibility: hidden !important;
    }

    /* Ensure sidebar is always visible and cannot be collapsed */
    section[data-testid="stSidebar"] {
        transform: none !important;
        visibility: visible !important;
        position: relative !important;
    }

    /* Fix expander text-on-text bug - hide icon text */
    .streamlit-expanderHeader span[data-testid="stExpanderToggleIcon"] {
        font-size: 0 !important;
    }
    .streamlit-expanderHeader svg {
        width: 16px !important;
        height: 16px !important;
    }
    /* Hide any arrow text in expanders */
    details summary span {
        font-family: 'Poppins', sans-serif !important;
    }
    details summary span:first-child {
        font-size: 0 !important;
    }

    /* --- NAVIGATION BAR REDESIGN --- */
    [data-testid="stSidebarNav"] { display: none !important; }

    section[data-testid="stSidebar"] {
        background-color: #F9FAFB;
        border-right: 1px solid #E5E7EB;
    }

    section[data-testid="stSidebar"] .stRadio div[role="radiogroup"] {
        gap: 4px;
        padding: 0 8px;
    }

    section[data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label {
        background-color: transparent;
        border: 1px solid transparent;
        border-radius: 8px;
        padding: 10px 12px;
        margin-bottom: 2px;
        color: #6B7280;
        font-family: 'Poppins', sans-serif !important;
        font-weight: 500;
        font-size: 13px;
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

    /* Active/Selected menu item - light gray background */
    section[data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label[data-checked="true"],
    section[data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label[aria-checked="true"],
    section[data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label:has(input:checked) {
        background-color: #E5E7EB !important;
        color: #1F2937 !important;
        font-weight: 600 !important;
        border: 1px solid #D1D5DB !important;
        border-radius: 6px !important;
        box-shadow: none !important;
    }

    section[data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label[data-checked="true"] span,
    section[data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label[aria-checked="true"] span,
    section[data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label:has(input:checked) span {
        color: #1F2937 !important;
    }

    /* Hide the radio button circle */
    section[data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label > div:first-child {
        display: none;
    }

    section[data-testid="stSidebar"] .block-container {
        padding-top: 2rem;
        padding-bottom: 5rem;
    }

    /* Expander styling - remove icon garble */
    .streamlit-expanderHeader {
        font-family: 'Poppins', sans-serif !important;
        font-weight: 600 !important;
        font-size: 13px !important;
        color: #4B5563 !important;
    }

    /* Hide expander icons that cause garbled text */
    .streamlit-expanderHeader svg {
        display: inline-block !important;
    }

    /* Fix any material icon issues */
    .material-icons, .material-symbols-outlined {
        font-family: 'Material Icons' !important;
    }

    /* --- UI ELEMENTS --- */

    /* PRIMARY BUTTONS - Blue Background with WHITE Text (CRITICAL!) */
    div.stButton > button,
    div.stButton > button[kind="primary"],
    div.stButton > button:not([kind="tertiary"]):not([kind="secondary"]),
    .stButton button[type="primary"] {
        background-color: #302BFF !important;
        color: #FFFFFF !important;
        font-family: 'Poppins', sans-serif !important;
        font-weight: 600 !important;
        text-transform: uppercase;
        border: none !important;
        border-radius: 6px;
        padding: 0.5rem 1.0rem;
        box-shadow: 0 4px 6px rgba(48, 43, 255, 0.2);
        transition: all 0.2s ease;
        letter-spacing: 0.5px;
        font-size: 13px;
    }

    /* Force white text on ALL children of primary buttons */
    div.stButton > button span,
    div.stButton > button p,
    div.stButton > button div,
    div.stButton > button[kind="primary"] span,
    div.stButton > button[kind="primary"] p,
    div.stButton > button:not([kind="tertiary"]):not([kind="secondary"]) span,
    div.stButton > button:not([kind="tertiary"]):not([kind="secondary"]) p {
        color: #FFFFFF !important;
    }

    div.stButton > button:hover,
    div.stButton > button[kind="primary"]:hover,
    div.stButton > button:not([kind="tertiary"]):not([kind="secondary"]):hover {
        background-color: #2521c9 !important;
        box-shadow: 0 6px 12px rgba(48, 43, 255, 0.3);
        color: #FFFFFF !important;
    }

    /* TERTIARY BUTTONS - Text Links (blue, underlined on hover) */
    div.stButton > button[kind="tertiary"],
    button[kind="tertiary"] {
        background-color: transparent !important;
        border: none !important;
        color: #302BFF !important;
        box-shadow: none !important;
        text-decoration: none !important;
        padding: 8px 0 !important;
        font-weight: 500 !important;
        text-transform: none !important;
        font-size: 14px !important;
        font-family: 'Poppins', sans-serif !important;
    }

    div.stButton > button[kind="tertiary"] span,
    div.stButton > button[kind="tertiary"] p,
    button[kind="tertiary"] span {
        color: #302BFF !important;
    }

    div.stButton > button[kind="tertiary"]:hover,
    button[kind="tertiary"]:hover {
        color: #2521c9 !important;
        text-decoration: underline !important;
        background-color: transparent !important;
        box-shadow: none !important;
    }

    /* SECONDARY BUTTONS - Outlined style */
    button[kind="secondary"] {
        background-color: transparent !important;
        border: 1px solid #302BFF !important;
        color: #302BFF !important;
        box-shadow: none !important;
        padding: 0.5rem 1.0rem !important;
        font-weight: 600 !important;
        text-transform: uppercase !important;
        border-radius: 6px !important;
    }

    button[kind="secondary"]:hover {
        background-color: #302BFF !important;
        color: #FFFFFF !important;
    }

    .ghost-link {
        color: #9CA3AF;
        font-size: 12px;
        font-weight: 500;
        font-family: 'Poppins', sans-serif;
        font-style: italic;
        text-align: center;
        margin-top: 10px;
    }

    /* Coming Soon Badge */
    .coming-soon-badge {
        display: inline-block;
        background-color: #E5E7EB;
        color: #6B7280;
        font-size: 9px;
        font-weight: 600;
        padding: 2px 6px;
        border-radius: 4px;
        margin-left: 8px;
        text-transform: uppercase;
    }

    /* Beta Badge */
    .beta-badge {
        display: inline-block;
        background-color: #FEF3C7;
        color: #D97706;
        font-size: 9px;
        font-weight: 600;
        padding: 2px 6px;
        border-radius: 4px;
        margin-left: 8px;
        text-transform: uppercase;
    }

    /* --- LAYOUTS --- */

    .stApp { background-color: #FFFFFF; }

    div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #FFFFFF;
        border: 1px solid #E5E7EB;
        border-radius: 12px;
        padding: 24px;
        margin-bottom: 24px;
    }

    /* KPI Cards */
    .hero-card {
        padding: 16px 12px;
        border-radius: 8px;
        text-align: center;
        margin-bottom: 8px;
        border: 1px solid #E5E7EB;
        background-color: #FFFFFF;
        height: 140px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
    }

    .hero-label {
        font-size: 11px !important;
        text-transform: uppercase;
        letter-spacing: 1px;
        font-weight: 600 !important;
        margin-bottom: 8px;
        color: #6B7280;
        font-family: 'Poppins', sans-serif !important;
    }

    .hero-value {
        font-family: 'Exo 2', sans-serif !important;
        font-size: 28px !important;
        font-weight: 800 !important;
        color: #111827;
        margin-bottom: 4px;
    }

    .hero-sub {
        font-size: 11px;
        color: #9CA3AF;
        font-family: 'Poppins', sans-serif !important;
    }

    /* Functional Colors for Grid - USING CORRECT CI COLORS */
    .hero-cyan, .hero-teal {
        background-color: #00D2BE !important; /* Turbo Teal */
        border: none !important;
    }
    .hero-cyan .hero-label, .hero-cyan .hero-value, .hero-cyan .hero-sub,
    .hero-teal .hero-label, .hero-teal .hero-value, .hero-teal .hero-sub { color: #FFFFFF !important; }

    .hero-red, .hero-coral {
        background-color: #FF2E4D !important; /* Radical Coral */
        border: none !important;
    }
    .hero-red .hero-label, .hero-red .hero-value, .hero-red .hero-sub,
    .hero-coral .hero-label, .hero-coral .hero-value, .hero-coral .hero-sub { color: #FFFFFF !important; }

    /* Feature Tiles */
    .feature-tile {
        height: 200px;
        display: flex;
        flex-direction: column;
        justify-content: flex-start;
        align-items: center;
        text-align: center;
        padding: 5px;
    }
    .feature-title {
        font-family: 'Exo 2', sans-serif !important;
        font-size: 16px;
        font-weight: 800;
        color: #4B5563;
        margin-bottom: 12px;
        text-transform: uppercase;
        height: 40px;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .feature-desc {
        font-size: 13px;
        color: #6B7280;
        line-height: 1.4;
        font-family: 'Poppins', sans-serif !important;
    }

    /* Multiselect styling - less overwhelming, gray background */
    div[data-baseweb="select"] {
        max-height: 150px;
    }

    /* Gray background for all dropdowns and selects */
    div[data-baseweb="select"] > div,
    div[data-baseweb="popover"] > div,
    .stSelectbox > div > div,
    .stMultiSelect > div > div,
    [data-baseweb="select"] [data-baseweb="input"] {
        background-color: #F3F4F6 !important;
        border-color: #D1D5DB !important;
    }

    /* Gray background for dropdown menu items */
    [data-baseweb="menu"] {
        background-color: #F9FAFB !important;
    }

    /* Make multiselect chips smaller with gray tones */
    span[data-baseweb="tag"] {
        font-size: 11px !important;
        padding: 2px 6px !important;
        margin: 2px !important;
        background-color: #E5E7EB !important;
        color: #374151 !important;
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
    .block-container {
        padding-bottom: 50px;
    }

    /* --- TOOLTIP STYLING --- */
    .tooltip-icon {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 16px;
        height: 16px;
        background-color: rgba(255,255,255,0.3);
        border-radius: 50%;
        font-size: 10px;
        font-weight: 700;
        cursor: help;
        margin-left: 4px;
        position: relative;
        vertical-align: middle;
    }
    .tooltip-icon:hover::after {
        content: attr(data-tip);
        position: absolute;
        bottom: 120%;
        left: 50%;
        transform: translateX(-50%);
        background-color: #1F2937;
        color: #FFFFFF;
        padding: 8px 12px;
        border-radius: 6px;
        font-size: 11px;
        font-weight: 400;
        white-space: normal;
        width: max-content;
        max-width: 250px;
        z-index: 10000;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        line-height: 1.4;
        text-transform: none;
        letter-spacing: normal;
    }
    .tooltip-icon:hover::before {
        content: '';
        position: absolute;
        bottom: 110%;
        left: 50%;
        transform: translateX(-50%);
        border: 6px solid transparent;
        border-top-color: #1F2937;
        z-index: 10001;
    }

    /* --- SIDEBAR EXPANDER ARROW FIX --- */
    /* Fix the Material Icons display issue */
    [data-testid="stSidebar"] button[kind="header"],
    [data-testid="collapsedControl"] button {
        font-size: 0 !important;
    }
    [data-testid="stSidebar"] button[kind="header"] svg,
    [data-testid="collapsedControl"] button svg {
        width: 24px !important;
        height: 24px !important;
    }

    /* Fix expander arrow icons showing as text */
    .streamlit-expanderHeader span[data-testid="stExpanderToggleIcon"],
    [data-testid="stExpander"] summary span {
        font-family: inherit !important;
    }

    /* Ensure expanders show proper icons */
    details summary::marker,
    details summary::-webkit-details-marker {
        display: none;
    }

    /* Fix sidebar collapse/expand button - hide text, show only icon */
    [data-testid="stSidebarCollapsedControl"] button,
    [data-testid="collapsedControl"] button,
    button[data-testid="baseButton-headerNoPadding"] {
        font-size: 0 !important;
        color: transparent !important;
    }
    [data-testid="stSidebarCollapsedControl"] button span,
    [data-testid="collapsedControl"] button span,
    button[data-testid="baseButton-headerNoPadding"] span {
        font-size: 0 !important;
        display: none !important;
    }
    [data-testid="stSidebarCollapsedControl"] button svg,
    [data-testid="collapsedControl"] button svg,
    button[data-testid="baseButton-headerNoPadding"] svg {
        width: 20px !important;
        height: 20px !important;
        display: block !important;
    }

    /* Hide any arrow_right or arrow_left text */
    [data-testid="stSidebar"] span:contains("arrow"),
    button span[class*="material"] {
        font-size: 0 !important;
        visibility: hidden !important;
    }

</style>
<script>
    // Force Exo 2 font on all headings after page load
    function applyExo2Fonts() {
        const headings = document.querySelectorAll('.exo2-heading, .hero-value, .feature-title, .section-title, .data-required-title, .loading-text');
        headings.forEach(function(el) {
            el.style.setProperty('font-family', "'Exo 2', sans-serif", 'important');
            el.style.setProperty('font-weight', '800', 'important');
            el.style.setProperty('text-transform', 'uppercase', 'important');
        });
    }

    // Run when fonts are ready
    if (document.fonts && document.fonts.ready) {
        document.fonts.ready.then(applyExo2Fonts);
    }

    // Run on DOMContentLoaded
    document.addEventListener('DOMContentLoaded', applyExo2Fonts);

    // Run after delays to catch Streamlit's dynamic content
    setTimeout(applyExo2Fonts, 100);
    setTimeout(applyExo2Fonts, 500);
    setTimeout(applyExo2Fonts, 1000);
    setTimeout(applyExo2Fonts, 2000);

    // Use MutationObserver to catch any new elements
    const observer = new MutationObserver(function(mutations) {
        applyExo2Fonts();
    });
    observer.observe(document.body, { childList: true, subtree: true });
</script>
""", unsafe_allow_html=True)

# --- 3. ROUTING & NAVIGATION ---

# Initialize authentication state (using new auth module)
init_auth_session_state()

if 'navigate_to_page' not in st.session_state:
    st.session_state.navigate_to_page = None

# Handle OAuth/Magic Link callback - check URL for tokens
# Supabase sends tokens as URL fragment (#access_token=...) which needs JS to convert
# Use components.html for reliable JS execution
import streamlit.components.v1 as components

components.html("""
<script>
    (function() {
        // Check if there's a hash fragment with tokens
        if (window.parent.location.hash && window.parent.location.hash.includes('access_token')) {
            // Parse the fragment
            const fragment = window.parent.location.hash.substring(1);
            const params = new URLSearchParams(fragment);

            const accessToken = params.get('access_token');
            const refreshToken = params.get('refresh_token');

            if (accessToken && refreshToken) {
                // Convert fragment to query string and redirect parent window
                const newUrl = window.parent.location.pathname + '?access_token=' + encodeURIComponent(accessToken) + '&refresh_token=' + encodeURIComponent(refreshToken);
                window.parent.location.replace(newUrl);
            }
        }
    })();
</script>
""", height=0)

# Check for auth tokens in query params (after JS redirect from fragment)
_query_params = st.query_params
_access_token = _query_params.get('access_token')
_refresh_token = _query_params.get('refresh_token')
_auth_code = _query_params.get('code')

# Handle PKCE code exchange (from OAuth providers)
if _auth_code and not _access_token:
    from core.auth import get_supabase_client
    client = get_supabase_client()
    if client:
        try:
            # Exchange the code for a session
            response = client.auth.exchange_code_for_session({"auth_code": _auth_code})
            if response and response.session:
                st.session_state['is_authenticated'] = True
                st.session_state['user'] = response.user
                st.session_state['user_id'] = response.user.id
                st.session_state['user_email'] = response.user.email
                st.session_state['access_token'] = response.session.access_token
                st.session_state['refresh_token'] = response.session.refresh_token
                st.query_params.clear()
                st.session_state.navigate_to_page = "Start & Data"
                st.rerun()
        except Exception as e:
            import logging
            logging.error(f"Code exchange error: {e}")
            st.query_params.clear()

# Handle direct token callback (from Magic Link or fragment conversion)
if _access_token and _refresh_token:
    from core.auth import handle_auth_callback
    if handle_auth_callback(_access_token, _refresh_token):
        st.query_params.clear()
        st.session_state.navigate_to_page = "Start & Data"
        st.rerun()

# Verify session on page load (refresh tokens if needed)
if st.session_state.get('is_authenticated') and st.session_state.get('access_token'):
    if not verify_and_refresh_session():
        # Session expired, clear auth state
        st.session_state['is_authenticated'] = False
        st.session_state['access_token'] = None
        st.session_state['refresh_token'] = None

# Define Menu Items with display names
# Format: {display_name: internal_page_value}
page_map = {
    "Start & Data": "Start & Data",
    "Portfolio Analytics": "Portfolio Analytics",
    "Portfolio Builder": "Portfolio Builder",
    "Monte Carlo": "Monte Carlo",
    "Reality Check": "Live vs. Backtest",
    "MEIC Deep Dive": "MEIC Deep Dive",
    "MEIC Optimizer (Beta)": "MEIC Optimizer",
    "AI Analyst (Coming Soon)": "AI Analyst"
}
menu_items = list(page_map.keys())

# Determine current page
if st.session_state.navigate_to_page in page_map.values():
    current_key = list(page_map.keys())[list(page_map.values()).index(st.session_state.navigate_to_page)]
else:
    current_key = "Start & Data"
    st.session_state.navigate_to_page = "Start & Data"

current_page_val = st.session_state.navigate_to_page

# --- SIDEBAR LOGIC ---
# Hide sidebar ONLY on login page (not authenticated) - show on landing and all other pages
if not st.session_state.is_authenticated:
    st.markdown("""
    <style>
        /* Aggressively hide sidebar during login - prevent flash of unstyled content */
        [data-testid="stSidebar"],
        section[data-testid="stSidebar"],
        [data-testid="stSidebarNav"],
        [data-testid="stSidebarContent"],
        .css-1d391kg,
        .css-163ttbj {
            display: none !important;
            visibility: hidden !important;
            width: 0 !important;
            min-width: 0 !important;
            max-width: 0 !important;
            opacity: 0 !important;
            transform: translateX(-100%) !important;
            position: absolute !important;
            left: -9999px !important;
        }
        /* Remove any sidebar margin/padding from main content */
        .main .block-container {
            margin-left: 0 !important;
            padding-left: 1rem !important;
            max-width: 100% !important;
        }
    </style>
    """, unsafe_allow_html=True)
else:
    # Show sidebar when authenticated (including landing page)
    with st.sidebar:
        # Logo in sidebar - at the top
        ui.render_logo_sidebar()

        st.write("")

        # Navigation with current page indicator
        selected_key = st.radio(
            "Navigation",
            menu_items,
            index=menu_items.index(current_key),
            label_visibility="collapsed",
            key="main_nav_radio"
        )

        target_val = page_map[selected_key]
        if target_val != st.session_state.navigate_to_page:
            st.session_state.navigate_to_page = target_val
            st.rerun()

        # Spacer to push content to bottom
        st.markdown("<div style='flex-grow: 1; min-height: 100px;'></div>", unsafe_allow_html=True)

        st.markdown("---")

        # Analysis Manager - simple section without expander (same size as menu items)
        st.markdown("""
            <div style="font-family: 'Poppins', sans-serif !important; font-weight: 600 !important;
                        font-size: 13px; color: #4B5563; text-transform: none;
                        letter-spacing: 0.3px; margin-bottom: 10px; padding: 10px 12px;">
                Analysis Manager
            </div>
        """, unsafe_allow_html=True)
        ui.render_save_load_sidebar(st.session_state.get('full_df'), st.session_state.get('live_df'))

        st.markdown("---")

        # Show logged in user
        if st.session_state.get('user_email'):
            st.caption(f"Logged in as: {st.session_state.user_email}")

        # Logout button at the very bottom
        if st.button("LOG OUT", use_container_width=True, type="secondary"):
            sign_out()
            st.session_state.clear()
            st.rerun()

# --- 4. PAGE RENDERING ---

# Check for privacy page request (accessible without auth)
query_params = st.query_params
if query_params.get('page') == 'privacy' or st.session_state.get('show_privacy'):
    privacy.show_privacy_page()
# Check authentication first - show login page if not authenticated
elif not st.session_state.is_authenticated:
    login.show_login_page()
else:
    # User is authenticated - show main app
    df = st.session_state.get('full_df', pd.DataFrame())
    live_df = st.session_state.get('live_df', pd.DataFrame())

    if current_page_val == "Start & Data":
        landing.show_landing_page()

    elif df.empty and current_page_val != "Start & Data":
        # Show data required overlay instead of redirecting (prevents hanging)
        ui.render_data_required_overlay()
        col_space, col_btn, col_space2 = st.columns([1, 2, 1])
        with col_btn:
            if st.button("GO TO DATA IMPORT", key="data_required_btn", use_container_width=True, type="primary"):
                st.session_state.navigate_to_page = "Start & Data"
                st.rerun()
        st.stop()  # Stop execution here - don't render page content

    else:
        if current_page_val == "Portfolio Analytics": portfolio_analytics.page_portfolio_analytics(df, live_df)
        elif current_page_val == "Portfolio Builder": portfolio_builder.page_portfolio_builder(df)
        elif current_page_val == "Monte Carlo": monte_carlo.page_monte_carlo(df)
        elif current_page_val == "Live vs. Backtest": comparison.page_comparison(df, live_df)
        elif current_page_val == "MEIC Deep Dive": meic_analysis.page_meic_analysis(df, live_df)
        elif current_page_val == "MEIC Optimizer": meic_optimizer.page_meic_optimizer()
        elif current_page_val == "AI Analyst": ai_analyst.page_ai_analyst(df)

    ui.render_footer()