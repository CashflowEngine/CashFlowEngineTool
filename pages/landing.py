import streamlit as st
import pandas as pd
import database as db
import calculations as calc
import ui_components as ui

def show_landing_page():
    """Landing page with file upload."""
    c1, c2, c3 = st.columns([1, 1, 1])
    with c2:
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

                loading_placeholder.empty()
                
                if 'full_df' in st.session_state:
                    st.rerun()
                else:
                    st.error("Please upload at least Backtest Data to start.")
            else:
                st.error("Please upload at least Backtest Data to start.")

    # Database load section
    if db.DB_AVAILABLE:
        saved_analyses = db.get_analysis_list()
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
                        bt_df, live_df = db.load_analysis_from_db(analysis_id)
                        if bt_df is not None:
                            st.session_state['full_df'] = bt_df
                            st.session_state['bt_filenames'] = f"DB: {selected_option}"
                            if live_df is not None:
                                st.session_state['live_df'] = live_df
                                st.session_state['live_filenames'] = "From Database"
                            db_loading.empty()
                            st.success("Loaded!")
                            st.rerun()
