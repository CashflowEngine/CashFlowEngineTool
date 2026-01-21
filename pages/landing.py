import streamlit as st
import pandas as pd
import database as db
import calculations as calc
import ui_components as ui

def show_landing_page():
    """
    Landing Page: Data Management & Feature Hub.
    """

    # --- DATA CHECK OVERLAY (Full screen) ---
    if st.session_state.get('show_data_warning', False):
        ui.render_data_required_overlay()
        col_ack = st.columns([1, 2, 1])[1]
        with col_ack:
            if st.button("ACKNOWLEDGE & IMPORT DATA", key="ack_btn_overlay", use_container_width=True):
                st.session_state.show_data_warning = False
                st.rerun()
        return

    # --- LOGO (Using actual image file) ---
    ui.render_logo(width=350, centered=True)

    # --- MAIN HEADLINE ---
    st.markdown(f"""
        <div style="text-align: center; margin: 30px 0 20px 0;">
            <h1 style="font-family: 'Exo 2', sans-serif !important; font-weight: 800 !important; font-size: 32px !important;
                        color: {ui.COLOR_GREY} !important; text-transform: uppercase !important; letter-spacing: 2px !important;
                        margin-bottom: 15px !important; line-height: 1.3 !important;">
                Advanced Portfolio Analytics &<br>Risk Simulation for Option Traders
            </h1>
            <p style="font-family: 'Poppins', sans-serif; font-size: 15px; color: #6B7280; max-width: 700px;
                      margin: 0 auto; line-height: 1.6;">
                Analyze your options trading performance with professional-grade tools. Import your backtest
                or live trading data to unlock comprehensive analytics, Monte Carlo simulations, and portfolio optimization.
            </p>
        </div>
    """, unsafe_allow_html=True)

    # --- SECTION 1: DATA IMPORT ---
    with st.container(border=True):
        st.markdown(f"""
            <h2 style="font-family: 'Exo 2', sans-serif !important; font-weight: 800 !important; font-size: 22px !important;
                       color: {ui.COLOR_GREY} !important; text-transform: uppercase !important; letter-spacing: 1px !important;
                       margin-bottom: 10px !important;">
                1. Data Import
            </h2>
            <p style="font-family: 'Poppins', sans-serif; font-size: 13px; color: #6B7280; margin-bottom: 20px;">
                Start by importing your trading data. You can upload new CSV files from Option Omega or load
                a previously saved analysis from the cloud database.
            </p>
        """, unsafe_allow_html=True)

        has_data = 'full_df' in st.session_state and not st.session_state['full_df'].empty

        if has_data:
            c_stat1, c_stat2 = st.columns([3, 1])
            with c_stat1:
                st.success(f"ENGINE READY: {len(st.session_state['full_df']):,} trades loaded.")
            with c_stat2:
                if st.button("RESET DATA", use_container_width=True, type="secondary"):
                    st.session_state.clear()
                    st.rerun()

        tab_upload, tab_db = st.tabs(["Upload New Files", "Load from Database"])

        with tab_upload:
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("**Backtest Data** (Required)")
                st.caption("Option Omega portfolio exports or single strategy backtest results (.csv)")
                bt_files = st.file_uploader("Upload Backtest CSVs", accept_multiple_files=True,
                                            type=['csv'], key="bt_uploader", label_visibility="collapsed")
            with c2:
                st.markdown("**Live Data** (Optional)")
                st.caption("Option Omega Automation logs or OptionsApp trade exports (.csv, .xlsx)")
                live_files = st.file_uploader("Upload Live Log", accept_multiple_files=True,
                                              type=['csv', 'xlsx', 'xls'], key="live_uploader", label_visibility="collapsed")

            if st.button("IMPORT DATA", use_container_width=True, type="primary"):
                if bt_files:
                    ui.show_loading_overlay("IGNITION SEQUENCE", "Parsing CSVs and normalizing formats...")

                    dfs = []
                    for f in bt_files:
                        d = calc.load_file_with_caching(f)
                        if d is not None:
                            dfs.append(d)
                    if dfs:
                        st.session_state['full_df'] = pd.concat(dfs, ignore_index=True)
                        st.session_state['bt_filenames'] = ", ".join([f.name for f in bt_files])

                    if live_files:
                        dfs_live = []
                        for f in live_files:
                            d = calc.load_file_with_caching(f)
                            if d is not None:
                                dfs_live.append(d)
                        if dfs_live:
                            st.session_state['live_df'] = pd.concat(dfs_live, ignore_index=True)
                            st.session_state['live_filenames'] = ", ".join([f.name for f in live_files])

                    ui.hide_loading_overlay()
                    st.rerun()
                else:
                    st.error("Please upload at least Backtest Data.")

        with tab_db:
            if db.DB_AVAILABLE:
                saved_analyses = db.get_analysis_list_enhanced()
                if saved_analyses:
                    c_load1, c_load2 = st.columns([3, 1])
                    with c_load1:
                        options = {f"{entry['name']} ({entry['created_at'][:10]})": entry['id'] for entry in saved_analyses}
                        selected_option = st.selectbox("Select Analysis", ["-- Select --"] + list(options.keys()),
                                                       label_visibility="collapsed")
                    with c_load2:
                        if st.button("LOAD ANALYSIS", use_container_width=True) and selected_option != "-- Select --":
                            ui.show_loading_overlay("LOADING FROM CLOUD", "Fetching portfolio data...")

                            analysis_id = options[selected_option]
                            bt_df, live_df = db.load_analysis_from_db(analysis_id)

                            if bt_df is not None:
                                st.session_state['full_df'] = bt_df
                                if live_df is not None:
                                    st.session_state['live_df'] = live_df

                                ui.hide_loading_overlay()
                                st.rerun()
                else:
                    st.info("No saved analyses found.")
            else:
                st.warning("Database connection not configured.")

    st.write("")
    st.write("")

    # --- SECTION 2: MODULE SELECTION (Feature Tiles with Text Links) ---
    st.markdown(f"""
        <div style='text-align:center; margin-bottom:30px;'>
            <h2 style="font-family: 'Exo 2', sans-serif !important; font-weight: 800 !important; font-size: 22px !important;
                       color: {ui.COLOR_GREY} !important; text-transform: uppercase !important; letter-spacing: 1px !important;
                       margin-bottom: 10px !important;">
                2. Select Module
            </h2>
            <p style="font-family: 'Poppins', sans-serif; font-size: 13px; color: #6B7280;">
                Choose an analysis module below. Data must be imported first to access most features.
            </p>
        </div>
    """, unsafe_allow_html=True)

    def render_tile(col, title, desc, target_page, coming_soon=False):
        """Render a feature tile with a styled text link."""
        with col:
            with st.container(border=True):
                st.markdown(f"""
                <div class="feature-tile">
                    <div class="feature-title" style="font-family: 'Exo 2', sans-serif !important; font-weight: 800 !important; text-transform: uppercase;">{title}</div>
                    <div class="feature-desc">{desc}</div>
                </div>
                """, unsafe_allow_html=True)

                if coming_soon:
                    st.markdown(f"""
                        <div style='text-align: center; margin-top: 10px; color: #9CA3AF;
                                    font-size: 12px; font-style: italic; font-family: Poppins, sans-serif;'>
                            Coming Soon
                        </div>
                    """, unsafe_allow_html=True)
                elif target_page:
                    # Create a unique key for this link
                    link_key = f"link_{title.replace(' ', '_').replace('-', '_')}"
                    short_title = title.replace(' Deep Dive', '').replace(' Optimizer', '').replace('Portfolio ', '')

                    # Check if data exists
                    has_data = 'full_df' in st.session_state and not st.session_state['full_df'].empty

                    link_clicked = st.button(
                        f"LAUNCH {short_title}",
                        key=link_key,
                        type="tertiary",
                        use_container_width=True
                    )

                    if link_clicked:
                        if has_data:
                            st.session_state.navigate_to_page = target_page
                            st.rerun()
                        else:
                            st.session_state.show_data_warning = True
                            st.rerun()
                else:
                    st.markdown(f"""
                        <div style='text-align: center; margin-top: 10px; color: #9CA3AF;
                                    font-size: 12px; font-style: italic; font-family: Poppins, sans-serif;'>
                            Coming Soon
                        </div>
                    """, unsafe_allow_html=True)

    # Grid Layout - Row 1
    r1c1, r1c2, r1c3, r1c4 = st.columns(4)
    render_tile(r1c1, "Portfolio Analytics",
                "Comprehensive deep dive into your portfolio performance. Analyze backtest and live trade data, key performance indicators, monthly return matrices, and equity growth curves.",
                "Portfolio Analytics")
    render_tile(r1c2, "Portfolio Builder",
                "Construct and balance a multi-strategy portfolio. Allocate capital efficiently, simulate margin requirements, and optimize strategy weights using Kelly Criterion or MART ratios.",
                "Portfolio Builder")
    render_tile(r1c3, "Monte Carlo",
                "Stress test your portfolio against thousands of market scenarios. Simulate Black Swan events, analyze drawdown probabilities, and ensure your strategy survives extreme volatility.",
                "Monte Carlo")
    render_tile(r1c4, "Reality Check",
                "Compare your actual live trading execution against your theoretical backtest results. Identify slippage, deviation, and performance gaps to refine your execution.",
                "Live vs. Backtest")

    st.write("")

    # Grid Layout - Row 2
    r2c1, r2c2, r2c3, r2c4 = st.columns(4)
    render_tile(r2c1, "MEIC Deep Dive",
                "Specialized analysis for Multiple Entry Iron Condors. Visualize performance based on entry times, market conditions, and specific trade parameters to optimize your MEIC strategy.",
                "MEIC Deep Dive")
    render_tile(r2c2, "MEIC Optimizer",
                "Generate entry signals for Option Omega based on your optimization criteria. Analyze batch results and find the most robust parameter sets for your strategy.",
                None, coming_soon=True)
    render_tile(r2c3, "AI Analyst",
                "Interact with your portfolio data using advanced AI. Ask questions about your performance, get insights on risk factors, and receive data-driven suggestions for improvement.",
                None, coming_soon=True)
    render_tile(r2c4, "Documentation",
                "Access comprehensive guides on how to interpret metrics, use the tools effectively, and understand the mathematical models behind the calculations.",
                None, coming_soon=True)
