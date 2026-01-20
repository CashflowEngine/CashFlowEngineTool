import streamlit as st
import pandas as pd
import database as db
import calculations as calc
import ui_components as ui

def show_landing_page():
    """Landing page with Data Management and Feature Navigation Tiles."""
    
    # Header
    st.markdown(
        """
        <div style="text-align: center; margin-bottom: 40px;">
            <h1 style='color: #302BFF; font-size: 42px; margin-bottom: 10px;'>⚡ CASHFLOW ENGINE</h1>
            <p style='font-size: 18px; color: #6B7280;'>Advanced Portfolio Analytics & Risk Simulation for Option Traders</p>
        </div>
        """, 
        unsafe_allow_html=True
    )

    # --- SECTION 1: DATA MANAGEMENT ---
    with st.container(border=True):
        ui.section_header("📂 Data Management")
        
        # Check if data is already loaded
        has_data = 'full_df' in st.session_state and not st.session_state['full_df'].empty
        
        if has_data:
            st.success(f"✅ Data Loaded: {len(st.session_state['full_df']):,} trades active.")
            if st.button("🔄 Clear Data & Start Over"):
                st.session_state.clear()
                st.rerun()
        
        tab_upload, tab_db = st.tabs(["📤 Upload Files", "☁️ Load from Database"])
        
        with tab_upload:
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("#### 1. Backtest Data (Required)")
                st.caption("Supports Option Omega exports (.csv).")
                bt_files = st.file_uploader("Upload Backtest CSVs", accept_multiple_files=True,
                                            type=['csv'], key="bt_uploader", label_visibility="collapsed")
            with c2:
                st.markdown("#### 2. Live Data (Optional)")
                st.caption("Supports Option Omega or OptionsApp logs.")
                live_files = st.file_uploader("Upload Live Log", accept_multiple_files=True,
                                              type=['csv', 'xlsx', 'xls'], key="live_uploader", label_visibility="collapsed")

            if st.button("🚀 Process Uploaded Data", use_container_width=True, type="primary"):
                if bt_files:
                    ui.show_loading_overlay("Ingesting Data", "Parsing CSVs and normalizing formats...")
                    
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
                saved_analyses = db.get_analysis_list()
                if saved_analyses:
                    c_load1, c_load2 = st.columns([3, 1])
                    with c_load1:
                        options = {f"{entry['name']} ({entry['created_at'][:10]})": entry['id'] for entry in saved_analyses}
                        selected_option = st.selectbox("Select Analysis", ["-- Select --"] + list(options.keys()),
                                                       label_visibility="collapsed")
                    with c_load2:
                        if st.button("Load Analysis", use_container_width=True) and selected_option != "-- Select --":
                            ui.show_loading_overlay("Loading from Cloud", "Fetching portfolio data...")
                            
                            analysis_id = options[selected_option]
                            bt_df, live_df = db.load_analysis_from_db(analysis_id)
                            
                            if bt_df is not None:
                                st.session_state['full_df'] = bt_df
                                st.session_state['bt_filenames'] = f"DB: {selected_option}"
                                if live_df is not None:
                                    st.session_state['live_df'] = live_df
                                    st.session_state['live_filenames'] = "From Database"
                                
                                ui.hide_loading_overlay()
                                st.success("Loaded!")
                                st.rerun()
                else:
                    st.info("No saved analyses found in database.")
            else:
                st.warning("Database connection not configured.")

    st.write("")
    st.write("")

    # --- SECTION 2: APP MODULES (TILES) ---
    st.markdown("<h3 style='text-align:center; margin-bottom:30px;'>Select a Module</h3>", unsafe_allow_html=True)

    # Function to create a tile (Dry code)
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
                
                # Streamlit button needs to be outside the HTML div to function
                if st.button(f"Open {title.split(' ')[0]}", key=f"btn_{title}", use_container_width=True):
                    st.session_state.navigate_to_page = target_page
                    st.rerun()

    # Row 1
    r1c1, r1c2, r1c3, r1c4 = st.columns(4)
    render_tile(r1c1, "📊", "Portfolio Analytics", "Deep dive into your backtest performance. Analyze KPIs, monthly returns, and equity curves.", "📊 Portfolio Analytics")
    render_tile(r1c2, "🏗️", "Portfolio Builder", "Construct a multi-strategy portfolio. Allocate capital and optimize weights with Kelly/MART.", "🏗️ Portfolio Builder")
    render_tile(r1c3, "🎲", "Monte Carlo", "Stress test your portfolio against thousands of market scenarios and Black Swan events.", "🎲 Monte Carlo Punisher")
    render_tile(r1c4, "⚖️", "Live vs Backtest", "Compare your actual trading performance against theoretical backtest results.", "⚖️ Live vs. Backtest")

    st.write("")

    # Row 2
    r2c1, r2c2, r2c3, r2c4 = st.columns(4)
    render_tile(r2c1, "🔬", "MEIC Deep Dive", "Specialized analysis for Multiple Entry Iron Condors. Analyze entry time performance.", "🔬 MEIC Deep Dive")
    render_tile(r2c2, "🧪", "MEIC Optimizer", "Generate entry signals for Option Omega and analyze batch results.", "🧪 MEIC Optimizer")
    render_tile(r2c3, "🤖", "AI Analyst", "Chat with your portfolio data using Google Gemini AI for insights.", "🤖 AI Analyst")
    
    # Placeholder for symmetry or documentation
    with r2c4:
        st.markdown("""
        <div class="feature-tile" style="background-color: #F3F4F6; border-style: dashed;">
            <div class="feature-icon">📚</div>
            <div class="feature-title">Documentation</div>
            <div class="feature-desc">Learn how to interpret metrics and use the tools effectively.</div>
        </div>
        """, unsafe_allow_html=True)
        st.button("Coming Soon", disabled=True, use_container_width=True)
