import streamlit as st
import pandas as pd
import database as db
import calculations as calc
import ui_components as ui

def show_landing_page():
    """
    Landing Page: Data Management & Feature Hub.
    No Sidebar navigation here.
    """
    
    # 1. RENDER LOGO (Centered for Landing Page impact)
    ui.render_logo()
    
    st.markdown(
        """<div style="text-align: center; margin-bottom: 40px; font-size: 18px; color: #4B5563;">
        ADVANCED PORTFOLIO ANALYTICS & RISK SIMULATION FOR OPTION TRADERS
        </div>""", 
        unsafe_allow_html=True
    )

    # --- DATA CHECK OVERLAY ---
    # If the user tried to navigate but had no data, show this warning box
    if st.session_state.get('show_data_warning', False):
        st.markdown("""
        <div class="data-warning">
            <h3 style="color: #B45309; margin: 0;">⚠️ DATA REQUIRED</h3>
            <p style="margin: 5px 0 0 0; color: #92400E;">To access the analytics engine, you must first upload backtest files or load an analysis from the database below.</p>
        </div>
        """, unsafe_allow_html=True)
        # Reset flag after showing
        st.session_state.show_data_warning = False

    # --- SECTION 1: DATA MANAGEMENT (The Gatekeeper) ---
    with st.container(border=True):
        ui.section_header("📂 1. DATA INGESTION")
        
        # Check status
        has_data = 'full_df' in st.session_state and not st.session_state['full_df'].empty
        
        if has_data:
            c_stat1, c_stat2 = st.columns([3, 1])
            with c_stat1:
                st.success(f"✅ **ENGINE READY:** {len(st.session_state['full_df']):,} trades loaded.")
            with c_stat2:
                if st.button("🔄 Reset Data", use_container_width=True):
                    st.session_state.clear()
                    st.rerun()
        
        tab_upload, tab_db = st.tabs(["📤 Upload New Files", "☁️ Load from Database"])
        
        with tab_upload:
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("**Backtest Data** (Required)")
                st.caption("Option Omega exports (.csv)")
                bt_files = st.file_uploader("Upload Backtest CSVs", accept_multiple_files=True,
                                            type=['csv'], key="bt_uploader", label_visibility="collapsed")
            with c2:
                st.markdown("**Live Data** (Optional)")
                st.caption("Execution logs")
                live_files = st.file_uploader("Upload Live Log", accept_multiple_files=True,
                                              type=['csv', 'xlsx', 'xls'], key="live_uploader", label_visibility="collapsed")

            if st.button("🚀 INGEST DATA", use_container_width=True, type="primary"):
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

    # --- SECTION 2: MODULE SELECTION (Feature Tiles) ---
    st.markdown("<h3 style='text-align:center; margin-bottom:30px; color:#4B5563;'>2. SELECT MODULE</h3>", unsafe_allow_html=True)

    def render_tile(col, icon, title, desc, target_page):
        with col:
            with st.container():
                st.markdown(f"""
                <div class="feature-tile">
                    <div class="feature-icon">{icon}</div>
                    <div class="feature-title">{title}</div>
                    <div class="feature-desc">{desc}</div>
                </div>
                """, unsafe_allow_html=True)
                
                # Logic: Button triggers navigation ONLY if data exists
                if st.button(f"OPEN {title.split(' ')[0].upper()}", key=f"btn_{title}", use_container_width=True):
                    has_data = 'full_df' in st.session_state and not st.session_state['full_df'].empty
                    
                    if has_data:
                        st.session_state.navigate_to_page = target_page
                        st.rerun()
                    else:
                        # Trigger warning overlay
                        st.session_state.show_data_warning = True
                        st.rerun()

    # Grid Layout
    r1c1, r1c2, r1c3, r1c4 = st.columns(4)
    render_tile(r1c1, "📊", "Portfolio Analytics", "Deep dive into KPIs, monthly returns, and equity curves.", "📊 Portfolio Analytics")
    render_tile(r1c2, "🏗️", "Portfolio Builder", "Allocate capital and optimize weights (Kelly/MART).", "🏗️ Portfolio Builder")
    render_tile(r1c3, "🎲", "Monte Carlo", "Stress test against Black Swan events.", "🎲 Monte Carlo Punisher")
    render_tile(r1c4, "⚖️", "Live vs Backtest", "Reality check your execution performance.", "⚖️ Live vs. Backtest")

    st.write("")

    r2c1, r2c2, r2c3, r2c4 = st.columns(4)
    render_tile(r2c1, "🔬", "MEIC Deep Dive", "Analyze entry time performance for Iron Condors.", "🔬 MEIC Deep Dive")
    render_tile(r2c2, "🧪", "MEIC Optimizer", "Generate signals for Option Omega.", "🧪 MEIC Optimizer")
    render_tile(r2c3, "🤖", "AI Analyst", "Chat with your portfolio data using Gemini AI.", "🤖 AI Analyst")
    
    with r2c4:
        st.markdown("""
        <div class="feature-tile" style="background-color: white; border-style: dashed;">
            <div class="feature-icon">📚</div>
            <div class="feature-title">DOCUMENTATION</div>
            <div class="feature-desc">Learn how to interpret metrics and use the tools.</div>
        </div>
        """, unsafe_allow_html=True)
        st.button("COMING SOON", disabled=True, use_container_width=True)
