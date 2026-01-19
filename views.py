import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import time
import utils
import calc

# Constants from utils
COLOR_TEAL = utils.COLOR_TEAL
COLOR_CORAL = utils.COLOR_CORAL
COLOR_BLUE = utils.COLOR_BLUE
COLOR_GREY = utils.COLOR_GREY
COLOR_PURPLE = utils.COLOR_PURPLE

# AI Setup
GEMINI_AVAILABLE = False
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    pass

# --- UI HELPERS ---

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
        # Escape single quotes and double quotes in tooltip
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
        # Handle string values with $ or %
        if isinstance(val, str):
            clean_val = val.replace('$', '').replace(',', '').replace('%', '').strip()
            num_val = float(clean_val)
        else:
            num_val = float(val)
        
        if num_val > 0:
            # Green gradient based on magnitude
            intensity = min(abs(num_val) / 5000, 1) if abs(num_val) > 100 else min(abs(num_val) / 10, 1)
            return f'background-color: rgba(0, 210, 190, {0.1 + intensity * 0.4}); color: #065F46'
        elif num_val < 0:
            # Red gradient based on magnitude
            intensity = min(abs(num_val) / 5000, 1) if abs(num_val) > 100 else min(abs(num_val) / 10, 1)
            return f'background-color: rgba(255, 46, 77, {0.1 + intensity * 0.4}); color: #991B1B'
        else:
            return 'background-color: white; color: #374151'
    except (ValueError, TypeError):
        return 'background-color: white; color: #374151'

def get_cached_dna(strategy_name, strat_df=None):
    """Get strategy DNA with caching."""
    if 'dna_cache' not in st.session_state: st.session_state.dna_cache = {}
    if strategy_name in st.session_state.dna_cache:
        return st.session_state.dna_cache[strategy_name]
    dna = calc._infer_strategy_dna(strategy_name, strat_df)
    st.session_state.dna_cache[strategy_name] = dna
    return dna

# --- DB UI ---

def render_save_load_sidebar(bt_df, live_df):
    """Enhanced save/load system in sidebar."""
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 💾 Analysis Manager")
    
    if not utils.DB_AVAILABLE:
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
    """Save section with smart naming and tags."""
    if bt_df is None or bt_df.empty:
        st.info("📊 No data to save.")
        return
    
    # Auto-generate smart name
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
    
    # Tags
    available_tags = ["Backtest", "Live", "MEIC", "Iron Condor", "Calendar", "Optimized", "Conservative", "Production"]
    default_tags = ["Backtest"] if bt_df is not None and not bt_df.empty else []
    if live_df is not None and not live_df.empty:
        default_tags.append("Live")
    for strat in strategies[:5]:
        strat_upper = strat.upper()
        if "MEIC" in strat_upper and "MEIC" not in default_tags:
            default_tags.append("MEIC")
        elif ("IC" in strat_upper or "IRON" in strat_upper) and "Iron Condor" not in default_tags:
            default_tags.append("Iron Condor")
        elif ("CALENDAR" in strat_upper or "DC" in strat_upper) and "Calendar" not in default_tags:
            default_tags.append("Calendar")
    default_tags = list(set(default_tags))[:3]
    
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
        
        existing = utils.get_analysis_list_enhanced()
        existing_names = [a['name'] for a in existing]
        
        if save_name in existing_names:
            st.warning(f"'{save_name}' exists!")
            if st.checkbox("Overwrite?", key="overwrite"):
                for a in existing:
                    if a['name'] == save_name:
                        utils.delete_analysis_from_db(a['id'])
                        break
            else:
                return
        
        with st.spinner("Saving..."):
            if utils.save_analysis_to_db_enhanced(save_name, bt_df, live_df, save_description, selected_tags):
                st.success("✅ Saved!")
                st.balloons()


def _render_load_section():
    """Load section with search and filter."""
    st.markdown("##### 📂 Load")
    
    saved = utils.get_analysis_list_enhanced()
    if not saved:
        st.info("No saved analyses.")
        return
    
    search = st.text_input("🔍 Search", key="load_search")
    
    all_tags = set()
    for a in saved:
        all_tags.update(a.get('tags', []))
    
    filter_tags = st.multiselect("Filter", options=sorted(all_tags), key="load_tags") if all_tags else []
    
    filtered = saved
    if search:
        filtered = [a for a in filtered if search.lower() in a['name'].lower() or search.lower() in a.get('description', '').lower()]
    if filter_tags:
        filtered = [a for a in filtered if any(t in a.get('tags', []) for t in filter_tags)]
    
    if not filtered:
        st.warning("No matches.")
        return
    
    st.caption(f"Found {len(filtered)} analysis(es)")
    
    for a in filtered[:10]:
        with st.container(border=True):
            st.markdown(f"**{a['name']}**")
            meta = [f"📅 {a['created_at'][:10]}"]
            if a.get('trade_count'):
                meta.append(f"📊 {a['trade_count']}")
            if a.get('total_pnl'):
                meta.append(f"💰 ${a['total_pnl']:,.0f}")
            if a.get('has_live'):
                meta.append("⚡ Live")
            st.caption(" | ".join(meta))
            
            if a.get('description'):
                st.caption(f"📝 {a['description'][:60]}...")
            
            if a.get('tags'):
                st.markdown(" ".join([f"`{t}`" for t in a['tags'][:4]]))
            
            if st.button("Load", key=f"load_{a['id']}", use_container_width=True):
                _load_with_feedback(a['id'], a['name'])


def _render_manage_section():
    """Manage: rename, delete, export."""
    st.markdown("##### ⚙️ Manage")
    
    saved = utils.get_analysis_list_enhanced()
    if not saved:
        st.info("Nothing to manage.")
        return
    
    options = {f"{a['name']} ({a['created_at'][:10]})": a for a in saved}
    sel = st.selectbox("Select", ["--"] + list(options.keys()), key="manage_sel")
    
    if sel == "--":
        return
    
    analysis = options[sel]
    
    st.markdown("---")
    st.caption(f"**Trades:** {analysis.get('trade_count', 'N/A')}")
    if analysis.get('strategies'):
        st.caption(f"**Strategies:** {', '.join(analysis['strategies'][:3])}")
    
    action = st.radio("Action", ["✏️ Rename", "🗑️ Delete", "📤 Export"], horizontal=True, key="manage_action")
    
    if "Rename" in action:
        new_name = st.text_input("New name", value=analysis['name'], key="new_name")
        if st.button("Apply", use_container_width=True, key="rename_btn"):
            if new_name and new_name != analysis['name']:
                if utils.rename_analysis_in_db(analysis['id'], new_name):
                    st.success("Renamed!")
                    time.sleep(0.5)
                    st.rerun()
            else:
                st.warning("Enter a different name.")
    
    elif "Delete" in action:
        st.warning(f"Delete '{analysis['name']}'?")
        if st.checkbox("Confirm deletion", key="del_confirm"):
            if st.button("🗑️ Delete", use_container_width=True, key="del_btn"):
                if utils.delete_analysis_from_db(analysis['id']):
                    st.success("Deleted!")
                    time.sleep(0.5)
                    st.rerun()
    
    elif "Export" in action:
        if st.button("📤 Export CSV", use_container_width=True, key="export_btn"):
            bt_df, _ = utils.load_analysis_from_db(analysis['id'])
            if bt_df is not None and not bt_df.empty:
                csv = bt_df.to_csv(index=False)
                st.download_button("⬇️ Download", csv, f"{analysis['name'].replace(' ', '_')}.csv", "text/csv", use_container_width=True)
            else:
                st.error("No data to export.")


def _load_with_feedback(analysis_id, name):
    """Load with feedback."""
    loading = st.empty()
    loading.info(f"Loading {name}...")
    
    bt_df, live_df = utils.load_analysis_from_db(analysis_id)
    
    if bt_df is not None and not bt_df.empty:
        st.session_state['full_df'] = bt_df
        st.session_state['bt_filenames'] = f"📂 {name}"
        if live_df is not None and not live_df.empty:
            st.session_state['live_df'] = live_df
            st.session_state['live_filenames'] = "Archive"
        else:
            if 'live_df' in st.session_state:
                del st.session_state['live_df']
            if 'live_filenames' in st.session_state:
                del st.session_state['live_filenames']
        loading.success(f"✅ Loaded!")
        time.sleep(0.5)
        st.rerun()
    else:
        loading.error("Failed to load.")

# --- PAGES ---

def page_monte_carlo(full_df):
    """Monte Carlo simulation page - OPTIMIZED with error handling."""
    if 'sim_run' not in st.session_state:
        st.session_state.sim_run = False
    if 'mc_results' not in st.session_state:
        st.session_state.mc_results = None

    st.markdown(
        """<h1 style='color: #4B5563; font-family: "Exo 2", sans-serif; font-weight: 800; 
        text-transform: uppercase; margin-bottom: 0;'>MONTE CARLO PUNISHER</h1>""",
        unsafe_allow_html=True
    )
    st.write("")
    
    # Check if we have portfolio data from Portfolio Builder
    from_builder = st.session_state.get('mc_from_builder', False)
    portfolio_daily_pnl = st.session_state.get('mc_portfolio_daily_pnl', None)
    
    # Reset results when coming from builder with fresh data
    if from_builder and st.session_state.get('mc_new_from_builder', False):
        st.session_state.sim_run = False
        st.session_state.mc_results = None
        st.session_state.mc_new_from_builder = False
    
    if from_builder and portfolio_daily_pnl is not None:
        st.success("📦 **Using Assembled Portfolio from Portfolio Builder**")
        st.caption(f"Portfolio has {len(portfolio_daily_pnl)} days of data | Click 'Run Simulation' to stress test")
        
        # Option to clear and use raw data instead
        if st.button("🔄 Use Raw Trade Data Instead", type="secondary"):
            st.session_state.mc_from_builder = False
            st.session_state.mc_portfolio_daily_pnl = None
            st.session_state.sim_run = False
            st.session_state.mc_results = None
            st.rerun()
        
        st.write("")

    st.subheader("Simulation Parameters")
    c1, c2, c3 = st.columns(3)
    with c1:
        n_sims = st.number_input("Number of Simulations", value=5000, step=500, min_value=100, max_value=10000)
    with c2:
        sim_months = st.number_input("Simulation Period (Months)", value=60, step=6, min_value=1, max_value=120)
    with c3:
        if from_builder and portfolio_daily_pnl is not None:
            start_cap = st.number_input("Initial Capital ($)", 
                                        value=st.session_state.get('mc_portfolio_account_size', 100000), 
                                        step=1000, min_value=1000)
        else:
            start_cap = st.number_input("Initial Capital ($)", value=100000, step=1000, min_value=1000)

    st.write("")

    # Get available strategies for the dropdown
    available_strategies = []
    if full_df is not None and not full_df.empty and 'strategy' in full_df.columns:
        available_strategies = sorted(full_df['strategy'].dropna().unique().tolist())
    
    with st.expander("🎯 Stress Test (Worst-Case Injection)", expanded=False):
        stress_mode = st.radio(
            "Stress Test Mode:",
            ["Historical Max Loss (Real)", "Theoretical Max Risk (Black Swan)"],
            index=1,
            help="Historical: Uses actual worst days from data. Theoretical: Uses margin-based black swan calculation."
        )
        
        if "Historical" in stress_mode:
            st.markdown("""
            <div style='background-color: #DBEAFE; padding: 10px; border-radius: 6px; font-size: 12px; margin-bottom: 8px;'>
            <b>Historical Max Loss:</b> Injects each strategy's <b>actual worst day P&L</b> from your backtest data.<br>
            • Events are injected <b>separately</b> for each strategy<br>
            • Events occur at <b>random times</b> throughout the simulation (not simultaneously)<br>
            • All strategies are included automatically
            </div>
            """, unsafe_allow_html=True)
            stress_val = st.slider("Frequency (times per year)", 0, 12, 0, 1, format="%d x/Year",
                                  help="How many worst-day events per year per strategy", key="hist_stress_slider")
            stress_type = "freq"
            stress_strategies = available_strategies  # Use all for Historical
            if stress_val > 0:
                n_events = int(np.ceil(stress_val * (sim_months / 12.0)))
                n_strats = len(available_strategies)
                st.caption(f"📊 {n_events} worst-day events per strategy × {n_strats} strategies = {n_events * n_strats} total events per simulation, randomly distributed")
        else:
            st.markdown("""
            <div style='background-color: #FEE2E2; padding: 10px; border-radius: 6px; font-size: 12px; margin-bottom: 8px;'>
            <b>Theoretical Max Risk (Black Swan):</b> Simulates a market crash hitting <b>ALL selected strategies at once</b>.<br>
            • Loss = PUT-side margin <b>minus premium received</b><br>
            • Events are <b>distributed evenly</b> across years (max 1 per year)<br>
            • Deselect strategies that profit from crashes (bear call spreads, long puts)
            </div>
            """, unsafe_allow_html=True)
            
            # Strategy selector ONLY for Theoretical mode
            if len(available_strategies) > 0:
                st.markdown("**Select strategies to include in black swan:**")
                stress_strategies = st.multiselect(
                    "Strategies at risk during crash:",
                    options=available_strategies,
                    default=available_strategies,  # All selected by default
                    key="stress_test_strategies",
                    help="Only selected strategies will be hit simultaneously. Deselect strategies that profit from crashes."
                )
            else:
                stress_strategies = []
            
            stress_val = st.slider("Frequency (times per year)", 0, 12, 0, 1, format="%d x/Year",
                                  help="How many combined crash events per year", key="theo_stress_slider")
            stress_type = "freq"
            if stress_val > 0:
                n_events = int(np.ceil(stress_val * (sim_months / 12.0)))
                st.caption(f"⚠️ {n_events} event(s) distributed across {max(1, sim_months//12)} year(s)")
        
        # Store selected strategies in session state for use during simulation
        st.session_state.stress_test_selected_strategies = stress_strategies

    st.write("")

    if st.button("🎲 Run Simulation", type="primary", use_container_width=True):
        st.session_state.sim_run = True
        st.session_state.mc_results = None  # Clear previous results

    if st.session_state.sim_run:
        # Check if we need to run simulation or just display results
        if st.session_state.mc_results is None:
            try:
                # Show custom loading overlay for Monte Carlo
                mc_loading = st.empty()
                mc_loading.markdown("""
                <div class="loading-overlay">
                    <div class="engine-container">
                        <div class="gear-system">
                            <span class="gear gear-1">⚙️</span>
                            <span class="gear gear-2">🎰</span>
                            <span class="gear gear-3">⚙️</span>
                        </div>
                        <div class="loading-text">🎲 Running Simulations</div>
                        <div class="loading-subtext">Crunching thousands of possible futures...</div>
                        <div class="progress-bar-container">
                            <div class="progress-bar"></div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Initialize stress injection variables
                stress_injections = []
                
                # Determine data source
                if from_builder and portfolio_daily_pnl is not None:
                    # Use portfolio daily P&L from builder
                    daily_pnl_values = portfolio_daily_pnl.dropna().values
                    daily_pnl_values = daily_pnl_values[daily_pnl_values != 0]  # Remove zero days
                    
                    if len(daily_pnl_values) < 10:
                        mc_loading.empty()
                        st.error("Not enough non-zero days for simulation.")
                        return
                    
                    # For portfolio, we sample daily returns
                    final_trades_pool = list(daily_pnl_values)
                    days = len(portfolio_daily_pnl)
                    auto_trades_per_year = 252  # Trading days per year for daily data
                    
                    debug_msg = []
                    injected_count = 0
                    
                    # Stress test injection for portfolio - collect separately
                    if stress_val > 0:
                        worst_day = np.min(daily_pnl_values)
                        if worst_day < 0:
                            n = int(np.ceil(stress_val * (sim_months / 12.0)))
                            
                            if n > 0:
                                stress_injections.append((worst_day, n))
                                injected_count += n
                                debug_msg.append(f"**Portfolio**: {n}x **${worst_day:,.0f}** per sim (Worst Day)")
                else:
                    # Use raw trade data
                    if full_df.empty:
                        mc_loading.empty()
                        st.error("No trade data available.")
                        return
                        
                    active_df = full_df.sort_values('timestamp')

                    if len(active_df) < 2:
                        mc_loading.empty()
                        st.error("Not enough data for simulation.")
                        return

                    days = (active_df['timestamp'].iloc[-1] - active_df['timestamp'].iloc[0]).days
                    days = max(days, 1)

                    auto_trades_per_year = len(active_df) / (days / 365.25)

                    final_trades_pool = []
                    debug_msg = []
                    injected_count = 0
                    
                    # Get user-selected strategies for stress test (only used for Theoretical)
                    stress_selected_strategies = st.session_state.get('stress_test_selected_strategies', [])
                    
                    # HISTORICAL: Collect each strategy's worst day SEPARATELY
                    # THEORETICAL: Collect and SUM selected strategies' margin into ONE combined event
                    historical_worst_days = []  # List of (strategy_name, worst_day_value)
                    combined_theoretical_wc = 0
                    strategy_wc_details = []

                    for strat_name, group in active_df.groupby('strategy'):
                        strat_pnl = group['pnl'].dropna().values
                        if len(strat_pnl) == 0:
                            continue
                        final_trades_pool.extend(strat_pnl)

                        if stress_val > 0:
                            # Calculate historical worst day for ALL strategies
                            daily_pnl = group.groupby(group['timestamp'].dt.date)['pnl'].sum()
                            hist_worst_day = daily_pnl.min() if len(daily_pnl) > 0 else np.min(strat_pnl)
                            
                            if hist_worst_day < 0:
                                historical_worst_days.append((strat_name, hist_worst_day))
                            
                            # THEORETICAL: Only include if strategy is SELECTED by user
                            if strat_name in stress_selected_strategies:
                                strat_theoretical_wc = 0
                                avg_daily_premium = 0
                                
                                if 'margin' in group.columns and 'legs' in group.columns:
                                    # Calculate average daily premium received
                                    daily_premium = group.groupby(group['timestamp'].dt.date)['pnl'].sum()
                                    avg_daily_premium = daily_premium.mean() if len(daily_premium) > 0 else 0
                                    
                                    # Smart margin: only count PUT-side risk, ignore CALL-side
                                    daily_put_margins = []
                                    
                                    for entry_date, day_group in group.groupby(group['timestamp_open'].dt.date if 'timestamp_open' in group.columns else group['timestamp'].dt.date):
                                        day_put_margin = 0
                                        
                                        for _, row in day_group.iterrows():
                                            m = row['margin'] if not pd.isna(row['margin']) else 0
                                            legs = str(row.get('legs', '')).upper()
                                            
                                            # Check if this is a PUT-side position (has downside crash risk)
                                            is_put_side = any(x in legs for x in [' P ', ' PUT ', ' P:', '/P', '-P', 'PUT SPREAD', 'BULL PUT'])
                                            is_call_side = any(x in legs for x in [' C ', ' CALL ', ' C:', '/C', '-C', 'CALL SPREAD', 'BEAR CALL'])
                                            is_long_put = 'LONG PUT' in legs or 'BUY PUT' in legs
                                            
                                            # For iron condors (has both P and C), only count PUT margin
                                            if is_put_side and is_call_side:
                                                day_put_margin += m / 2  # Half the margin is PUT side
                                            elif is_put_side and not is_long_put:
                                                day_put_margin += m
                                            elif is_call_side or is_long_put:
                                                pass  # Profits from crash, skip
                                            else:
                                                day_put_margin += m  # Unknown - conservatively include
                                        
                                        if day_put_margin > 0:
                                            daily_put_margins.append(day_put_margin)
                                    
                                    max_daily_put_margin = max(daily_put_margins) if daily_put_margins else 0
                                    
                                    # Theoretical worst = margin at risk MINUS premium received
                                    if max_daily_put_margin > 0:
                                        strat_theoretical_wc = -(max_daily_put_margin - abs(avg_daily_premium))
                                
                                # Accumulate theoretical for selected strategies
                                if strat_theoretical_wc < 0:
                                    combined_theoretical_wc += strat_theoretical_wc
                                    strategy_wc_details.append(f"**{strat_name}**: ${abs(strat_theoretical_wc):,.0f}")
                                elif hist_worst_day < 0:
                                    # Fallback to historical if no margin data
                                    combined_theoretical_wc += hist_worst_day
                                    strategy_wc_details.append(f"**{strat_name}**: ${abs(hist_worst_day):,.0f} (hist)")
                    
                    # Now create stress injections based on mode
                    if stress_val > 0:
                        n_events_per_year = stress_val
                        n_years = max(1, sim_months / 12)
                        
                        if "Historical" in stress_mode:
                            # HISTORICAL: Each strategy's worst day injected SEPARATELY at RANDOM times
                            # Total events = n_events_per_year * n_years, distributed across all strategies
                            total_events = int(np.ceil(n_events_per_year * n_years))
                            
                            if len(historical_worst_days) > 0 and total_events > 0:
                                # Create separate injection entries for each strategy
                                # Events per strategy = total_events (each strategy gets its worst day injected)
                                for strat_name, worst_day in historical_worst_days:
                                    stress_injections.append((worst_day, total_events, 'random'))
                                    injected_count += total_events
                                    debug_msg.append(f"**{strat_name}**: {total_events}x **${worst_day:,.0f}** (worst day)")
                                
                                debug_msg.insert(0, f"**Historical Worst Days**: {total_events} events per strategy, randomly distributed")
                                debug_msg.insert(1, "---")
                        else:
                            # THEORETICAL (Black Swan): All selected strategies hit SIMULTANEOUSLY
                            # Events distributed evenly - one per year max
                            n_events = int(np.ceil(n_events_per_year * n_years))
                            
                            combined_wc = combined_theoretical_wc
                            
                            if combined_wc < 0 and n_events > 0:
                                stress_injections.append((combined_wc, n_events, 'distributed'))
                                injected_count = n_events
                                debug_msg.append(f"**COMBINED Black Swan**: {n_events}x **${combined_wc:,.0f}** per sim")
                                debug_msg.append("---")
                                debug_msg.append(f"**Included strategies** ({len(stress_selected_strategies)} selected):")
                                for detail in strategy_wc_details:
                                    debug_msg.append(f"  - {detail}")
                            elif n_events > 0 and len(stress_selected_strategies) == 0:
                                debug_msg.append("⚠️ No strategies selected for stress test")
                            elif n_events > 0 and combined_wc >= 0:
                                debug_msg.append("⚠️ Selected strategies have no downside risk (combined loss = $0)")

                if len(final_trades_pool) == 0:
                    mc_loading.empty()
                    st.error("No valid data found for simulation.")
                    return

                n_steps = max(int((sim_months / 12) * auto_trades_per_year), 10)
                
                # Calculate number of years for event distribution
                n_years = max(1, sim_months / 12)
                
                # Prepare stress injection parameters based on mode
                stress_inj_list = []
                injection_mode = 'distributed'  # default
                total_injections = 0
                
                if len(stress_injections) > 0:
                    # Check the mode from first entry
                    injection_mode = stress_injections[0][2] if len(stress_injections[0]) > 2 else 'distributed'
                    
                    if injection_mode == 'random':
                        # HISTORICAL: Multiple separate values, each injected at random times
                        for entry in stress_injections:
                            val, count = entry[0], entry[1]
                            stress_inj_list.extend([val] * count)
                            total_injections += count
                    else:
                        # THEORETICAL: Single combined value, distributed across years
                        val, count = stress_injections[0][0], stress_injections[0][1]
                        stress_inj_list = [val]
                        total_injections = count
                
                stress_inj_array = np.array(stress_inj_list) if stress_inj_list else None

                # OPTIMIZED: Vectorized Monte Carlo with stress injections
                mc_result = calc.run_monte_carlo_optimized(
                    np.array(final_trades_pool), int(n_sims), n_steps, start_cap,
                    stress_injections=stress_inj_array, 
                    n_stress_per_sim=total_injections,
                    n_years=n_years,
                    injection_mode=injection_mode
                )
                
                # Handle both return formats
                if isinstance(mc_result, tuple):
                    mc_paths, end_vals, dds = mc_result
                else:
                    mc_paths = mc_result
                    end_vals = mc_paths[:, -1]
                    dds = calc.calculate_max_drawdown_batch(mc_paths)
                
                profit = np.mean(end_vals) - start_cap
                cagr = ((np.mean(end_vals) / start_cap) ** (12 / sim_months)) - 1

                dd_mean = np.mean(dds)
                mar = cagr / dd_mean if dd_mean > 0 else 0

                p95, p50, p05 = np.percentile(end_vals, [95, 50, 5])
                d05, d50, d95 = np.percentile(dds, [5, 50, 95])
                
                # Calculate CAGR for each percentile
                cagr_p95 = ((p95 / start_cap) ** (12 / sim_months)) - 1
                cagr_p50 = ((p50 / start_cap) ** (12 / sim_months)) - 1
                cagr_p05 = ((p05 / start_cap) ** (12 / sim_months)) - 1
                
                # Calculate MART = CAGR / (MaxDD% as ratio)
                mart = cagr / dd_mean if dd_mean > 0 else 0
                
                # Calculate Probability of Profit
                profitable_sims = np.sum(end_vals > start_cap)
                prob_profit = profitable_sims / len(end_vals)

                # Store results in session state
                st.session_state.mc_results = {
                    'mc_paths': mc_paths,
                    'end_vals': end_vals,
                    'profit': profit,
                    'cagr': cagr,
                    'dds': dds,
                    'dd_mean': dd_mean,
                    'mar': mar,
                    'mart': mart,
                    'p95': p95, 'p50': p50, 'p05': p05,
                    'cagr_p95': cagr_p95, 'cagr_p50': cagr_p50, 'cagr_p05': cagr_p05,
                    'd05': d05, 'd50': d50, 'd95': d95,
                    'start_cap': start_cap,
                    'sim_months': sim_months,
                    'n_sims': int(n_sims),
                    'n_steps': n_steps,
                    'prob_profit': prob_profit,
                    'injected_count': injected_count,
                    'n_stress_per_sim': total_injections,
                    'injection_mode': injection_mode,
                    'debug_msg': debug_msg
                }
                
                # Hide loading overlay
                mc_loading.empty()

            except Exception as e:
                mc_loading.empty()
                st.error(f"Simulation error: {str(e)}")
                st.session_state.sim_run = False
                return

        # Display results from session state
        if st.session_state.mc_results is not None:
            r = st.session_state.mc_results
            
            n_stress = r.get('n_stress_per_sim', 0)
            n_steps = r.get('n_steps', 0)
            sim_months = r.get('sim_months', 12)
            n_years = max(1, sim_months / 12)
            injection_mode = r.get('injection_mode', 'distributed')
            
            if n_stress > 0:
                if injection_mode == 'random':
                    # HISTORICAL MODE - not a black swan
                    with st.expander(f"✅ Historical Worst Days Stress Test Active", expanded=True):
                        st.markdown(f"""
                        <div style='background-color: #DBEAFE; padding: 12px; border-radius: 8px; font-size: 13px;'>
                        <b>Every simulation</b> ({r['n_sims']:,} total) includes historical worst-day events.<br>
                        Each strategy's worst day is injected <b>separately</b> at <b>random times</b> throughout the simulation.<br>
                        Events do NOT happen simultaneously - they are distributed randomly.
                        </div>
                        """, unsafe_allow_html=True)
                        for msg in r['debug_msg']:
                            if msg.startswith("---"):
                                st.markdown("---")
                            elif msg.startswith("**Historical"):
                                st.markdown(f"📊 {msg}")
                            elif msg.startswith("⚠️"):
                                st.warning(msg)
                            else:
                                st.markdown(f"  • {msg}")
                else:
                    # THEORETICAL MODE - black swan
                    with st.expander(f"✅ Black Swan Stress Test: {n_stress} event(s) per simulation", expanded=True):
                        st.markdown(f"""
                        <div style='background-color: #FEE2E2; padding: 12px; border-radius: 8px; font-size: 13px;'>
                        <b>Every simulation</b> ({r['n_sims']:,} total) includes exactly <b>{n_stress} black swan event(s)</b>.<br>
                        Events are <b>distributed evenly</b> across {n_years:.0f} year(s) - max 1 event per year.<br>
                        Each event hits <b>all selected strategies simultaneously</b> (like a real market crash).
                        </div>
                        """, unsafe_allow_html=True)
                        for msg in r['debug_msg']:
                            if msg.startswith("---"):
                                st.markdown("---")
                            elif msg.startswith("**Included") or msg.startswith("**COMBINED"):
                                st.markdown(f"🎯 {msg}")
                            elif msg.startswith("  -"):
                                st.markdown(msg)
                            elif msg.startswith("⚠️"):
                                st.warning(msg)
                            else:
                                st.markdown(msg)

            st.subheader("Key Metrics")
            k1, k2, k3, k4, k5 = st.columns(5)
            with k1:
                render_hero_metric("Avg. Net Profit", f"${r['profit']:,.0f}", "Mean Result", "hero-teal" if r['profit'] > 0 else "hero-coral",
                                  tooltip="Average ending portfolio value minus initial capital across all simulations")
            with k2:
                render_hero_metric("CAGR", f"{r['cagr']*100:.1f}%", "Ann. Growth", "hero-teal" if r['cagr'] > 0 else "hero-coral",
                                  tooltip="Compound Annual Growth Rate based on average ending value")
            with k3:
                render_hero_metric("Expected DD", f"{r['dd_mean']*100:.1f}%", "Avg. Drawdown", "hero-coral",
                                  tooltip="Average maximum drawdown across all simulations - the expected worst-case decline")
            with k4:
                mar_val = r.get('mar', r['cagr'] / r['dd_mean'] if r['dd_mean'] > 0 else 0)
                render_hero_metric("MAR Ratio", f"{mar_val:.2f}", "CAGR/DD", "hero-teal" if mar_val > 1 else "hero-coral",
                                  tooltip="CAGR divided by Expected Drawdown. Above 0.5 is acceptable, above 1.0 is good")
            with k5:
                prob_profit = r.get('prob_profit', 1.0)
                n_sims = r.get('n_sims', 1000)
                render_hero_metric("Prob. of Profit", f"{prob_profit*100:.1f}%", f"Out of {n_sims:,} sims", 
                                  "hero-teal" if prob_profit > 0.9 else ("hero-coral" if prob_profit < 0.7 else "hero-neutral"),
                                  tooltip="Percentage of simulations that ended with profit (ending value > starting capital)")

            st.write("")
            st.subheader("Return Scenarios (CAGR)")
            r1, r2, r3 = st.columns(3)
            with r1:
                cagr_best = r.get('cagr_p95', ((r['p95']/r['start_cap']) ** (12 / r.get('sim_months', 36))) - 1)
                render_hero_metric("Best Case (95%)", f"{cagr_best*100:.1f}%", f"${r['p95']:,.0f}", "hero-neutral",
                                  tooltip="95th percentile CAGR - only 5% of simulations performed better")
            with r2:
                cagr_likely = r.get('cagr_p50', ((r['p50']/r['start_cap']) ** (12 / r.get('sim_months', 36))) - 1)
                render_hero_metric("Most Likely (50%)", f"{cagr_likely*100:.1f}%", f"${r['p50']:,.0f}", "hero-neutral",
                                  tooltip="Median CAGR - 50% of simulations were better, 50% were worse")
            with r3:
                cagr_worst = r.get('cagr_p05', ((r['p05']/r['start_cap']) ** (12 / r.get('sim_months', 36))) - 1)
                render_hero_metric("Worst Case (5%)", f"{cagr_worst*100:.1f}%", f"${r['p05']:,.0f}", "hero-neutral",
                                  tooltip="5th percentile CAGR - only 5% of simulations performed worse")

            st.write("")
            st.subheader("Drawdown Scenarios")
            d1, d2, d3 = st.columns(3)
            with d1:
                render_hero_metric("Best Case DD", f"{r['d05']*100:.1f}%", "Top 5%", "hero-neutral",
                                  tooltip="5th percentile drawdown - only 5% of simulations had smaller drawdowns")
            with d2:
                render_hero_metric("Typical DD", f"{r['d50']*100:.1f}%", "Median", "hero-neutral",
                                  tooltip="Median drawdown - 50% of simulations had larger, 50% smaller drawdowns")
            with d3:
                render_hero_metric("Worst Case DD", f"{r['d95']*100:.1f}%", "Bottom 5%", "hero-neutral",
                                  tooltip="95th percentile drawdown - only 5% of simulations had larger drawdowns")

            st.write("")
            st.subheader("Portfolio Growth")
            show_paths = st.checkbox("Show individual paths", value=True)

            mc_paths = r['mc_paths']
            end_vals = r['end_vals']
            dds = r['dds']
            
            x = np.arange(mc_paths.shape[1])
            fig = go.Figure()

            if show_paths:
                n_display = min(50, mc_paths.shape[0])
                # Use fixed seed for consistent display
                np.random.seed(42)
                random_indices = np.random.choice(mc_paths.shape[0], n_display, replace=False)

                for idx in random_indices:
                    fig.add_trace(go.Scatter(
                        x=x, y=mc_paths[idx], mode='lines',
                        line=dict(color='rgba(200, 200, 200, 0.15)', width=1),
                        showlegend=False, hoverinfo='skip'
                    ))

                # Find best/worst within the stored paths (not all end_vals)
                stored_end_vals = mc_paths[:, -1]
                stored_dds = calc.calculate_max_drawdown_batch(mc_paths)
                
                best_idx = np.argmax(stored_end_vals)
                worst_idx = np.argmin(stored_end_vals)
                max_dd_idx = np.argmax(stored_dds)

                fig.add_trace(go.Scatter(x=x, y=mc_paths[best_idx], mode='lines',
                                         line=dict(color=COLOR_TEAL, width=2), name='Best Path'))
                fig.add_trace(go.Scatter(x=x, y=mc_paths[worst_idx], mode='lines',
                                         line=dict(color=COLOR_CORAL, width=2), name='Worst Path'))
                if max_dd_idx != worst_idx:
                    fig.add_trace(go.Scatter(x=x, y=mc_paths[max_dd_idx], mode='lines',
                                             line=dict(color=COLOR_PURPLE, width=2, dash='dot'), name='Max DD Path'))

            pp95, pp05 = np.percentile(mc_paths, [95, 5], axis=0)
            fig.add_trace(go.Scatter(
                x=np.concatenate([x, x[::-1]]),
                y=np.concatenate([pp95, pp05[::-1]]),
                fill='toself', fillcolor='rgba(0, 210, 190, 0.05)',
                line=dict(width=0), name='5-95% Conf.', showlegend=True
            ))

            pp50 = np.percentile(mc_paths, 50, axis=0)
            fig.add_trace(go.Scatter(x=x, y=pp50, mode='lines',
                                     line=dict(color=COLOR_BLUE, width=3), name='Median'))

            fig.add_shape(type="line", x0=0, y0=r['start_cap'], x1=len(x), y1=r['start_cap'],
                          line=dict(color="gray", width=1, dash="dash"))

            fig.update_layout(
                template="plotly_white", height=600,
                margin=dict(l=20, r=20, t=40, b=20),
                legend=dict(orientation="h", y=1.02, x=1, xanchor="right")
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Distribution Charts
            st.write("")
            dist_col1, dist_col2 = st.columns(2)
            
            with dist_col1:
                st.subheader("Return Distribution")
                # Calculate returns as percentage of starting capital
                returns_pct = ((end_vals - r['start_cap']) / r['start_cap']) * 100
                
                fig_return_dist = go.Figure()
                fig_return_dist.add_trace(go.Histogram(
                    x=returns_pct,
                    nbinsx=30,
                    marker_color=COLOR_BLUE,
                    opacity=0.8,
                    name="Returns"
                ))
                
                # Add percentile lines
                p5_ret = np.percentile(returns_pct, 5)
                p50_ret = np.percentile(returns_pct, 50)
                p95_ret = np.percentile(returns_pct, 95)
                
                fig_return_dist.add_vline(x=p5_ret, line_dash="dash", line_color="red", 
                                          annotation_text=f"P5: {p5_ret:.1f}%", annotation_position="top left")
                fig_return_dist.add_vline(x=p50_ret, line_dash="dash", line_color="blue",
                                          annotation_text=f"P50: {p50_ret:.1f}%", annotation_position="top")
                fig_return_dist.add_vline(x=p95_ret, line_dash="dash", line_color="green",
                                          annotation_text=f"P95: {p95_ret:.1f}%", annotation_position="top right")
                
                fig_return_dist.update_layout(
                    template="plotly_white",
                    height=350,
                    margin=dict(l=20, r=20, t=40, b=40),
                    xaxis_title="Cumulative Return (%)",
                    yaxis_title="Frequency",
                    showlegend=False
                )
                st.plotly_chart(fig_return_dist, use_container_width=True, key="mc_return_dist")
            
            with dist_col2:
                st.subheader("Drawdown Analysis")
                # Convert dds to percentage
                dds_pct = dds * 100
                
                fig_dd_dist = go.Figure()
                fig_dd_dist.add_trace(go.Histogram(
                    x=dds_pct,
                    nbinsx=30,
                    marker_color=COLOR_CORAL,
                    opacity=0.8,
                    name="Drawdowns"
                ))
                
                # Add percentile lines
                d5_pct = np.percentile(dds_pct, 5)
                d50_pct = np.percentile(dds_pct, 50)
                d95_pct = np.percentile(dds_pct, 95)
                
                fig_dd_dist.add_vline(x=d5_pct, line_dash="dash", line_color="red",
                                      annotation_text=f"P5: {d5_pct:.1f}%", annotation_position="top left")
                fig_dd_dist.add_vline(x=d50_pct, line_dash="dash", line_color="blue",
                                      annotation_text=f"P50: {d50_pct:.1f}%", annotation_position="top")
                fig_dd_dist.add_vline(x=d95_pct, line_dash="dash", line_color="green",
                                      annotation_text=f"P95: {d95_pct:.1f}%", annotation_position="top right")
                
                fig_dd_dist.update_layout(
                    template="plotly_white",
                    height=350,
                    margin=dict(l=20, r=20, t=40, b=40),
                    xaxis_title="Drawdown (%)",
                    yaxis_title="Frequency",
                    showlegend=False
                )
                st.plotly_chart(fig_dd_dist, use_container_width=True, key="mc_dd_dist")


def page_portfolio_builder(full_df):
    """
    Enhanced Portfolio Builder
    """
    st.markdown(
        """<h1 style='color: #4B5563; font-family: "Exo 2", sans-serif; font-weight: 800; 
        text-transform: uppercase; margin-bottom: 0;'>🏗️ PORTFOLIO BUILDER</h1>""",
        unsafe_allow_html=True
    )
    st.caption("INTERACTIVE CONTRACT ALLOCATION — 1 LOT = 1 CONTRACT/DAY")

    if full_df.empty:
        st.info("👆 Please upload CSV files to start building your portfolio.")
        return

    # === SECTION 1: CONFIGURATION ===
    st.markdown("### ⚙️ Configuration")
    
    with st.expander("📊 Account & Risk Settings", expanded=True):
        config_r1_c1, config_r1_c2, config_r1_c3 = st.columns(3)
        
        with config_r1_c1:
            account_size = st.number_input("Account Size ($)", value=100000, step=5000, min_value=1000, key="builder_account")
        with config_r1_c2:
            target_margin_pct = st.slider("Target Margin (%)", min_value=10, max_value=100, value=80, step=5)
        with config_r1_c3:
            target_margin = account_size * (target_margin_pct / 100)
            st.metric("Margin Budget", f"${target_margin:,.0f}")
    
    # Strategy Type Allocation
    with st.expander("🎯 Strategy Type Allocation", expanded=True):
        st.caption("Define target allocation percentages for each strategy category")
        
        type_c1, type_c2, type_c3, type_c4 = st.columns(4)
        with type_c1:
            workhorse_pct = st.slider("🐴 Workhorse %", min_value=0, max_value=100, value=60, step=5)
        with type_c2:
            airbag_pct = st.slider("🛡️ Airbag %", min_value=0, max_value=100, value=25, step=5)
        with type_c3:
            opportunist_pct = st.slider("🎯 Opportunist %", min_value=0, max_value=100, value=15, step=5)
        with type_c4:
            total_type_pct = workhorse_pct + airbag_pct + opportunist_pct
            if total_type_pct != 100:
                st.warning(f"⚠️ Total: {total_type_pct}%")
            else:
                st.success(f"✅ Total: {total_type_pct}%")
    
    # Evaluation Period
    st.markdown("### 📅 Evaluation Period")
    min_d = full_df['timestamp'].min().date()
    max_d = full_df['timestamp'].max().date()
    
    date_c1, date_c2 = st.columns(2)
    with date_c1:
        selected_dates = st.date_input("Select Date Range", [min_d, max_d], min_value=min_d, max_value=max_d, key="builder_dates")
    
    if len(selected_dates) != 2:
        st.warning("Please select a date range.")
        return
    
    # Filter data
    filtered_df = full_df[
        (full_df['timestamp'].dt.date >= selected_dates[0]) &
        (full_df['timestamp'].dt.date <= selected_dates[1])
    ].copy()
    
    if filtered_df.empty:
        st.warning("No data in selected date range.")
        return
    
    strategies = sorted(filtered_df['strategy'].unique().tolist())
    full_date_range = pd.date_range(start=selected_dates[0], end=selected_dates[1], freq='D')
    
    # Pre-calculate stats
    strategy_base_stats = {}
    strategy_daily_pnl = {}
    
    for strat in strategies:
        strat_data = filtered_df[filtered_df['strategy'] == strat].copy()
        if strat_data.empty: continue
        
        dna = get_cached_dna(strat, strat_data)
        category = calc.categorize_strategy(strat) # Use calc helper
        total_lots, contracts_per_day = calc.calculate_lots_from_trades(strat_data)
        
        contracts_per_day = max(0.5, round(contracts_per_day * 2) / 2)
        
        # Margin calculations
        margin_per_contract = strat_data['margin'].mean() if 'margin' in strat_data.columns else 0
        total_pnl = strat_data['pnl'].sum()
        
        # Kelly
        wins = strat_data[strat_data['pnl'] > 0]['pnl']
        losses = strat_data[strat_data['pnl'] <= 0]['pnl']
        win_rate = len(wins) / len(strat_data) if len(strat_data) > 0 else 0
        avg_win = wins.mean() if len(wins) > 0 else 0
        avg_loss = abs(losses.mean()) if len(losses) > 0 else 0
        kelly = 0
        if avg_loss > 0 and avg_win > 0:
            b = avg_win / avg_loss
            kelly = (win_rate * b - (1 - win_rate)) / b
            kelly = max(0, min(kelly, 1))

        daily_pnl = strat_data.set_index('timestamp').resample('D')['pnl'].sum()
        daily_pnl_aligned = daily_pnl.reindex(full_date_range, fill_value=0)
        strategy_daily_pnl[strat] = daily_pnl_aligned
        
        # Max DD
        cumsum = daily_pnl_aligned.cumsum()
        peak = cumsum.cummax()
        dd = (cumsum - peak).min()
        
        # Margin series
        margin_series = calc.generate_daily_margin_series_optimized(strat_data).reindex(full_date_range, fill_value=0)
        
        strategy_base_stats[strat] = {
            'category': category,
            'dna': dna,
            'contracts_per_day': contracts_per_day,
            'margin_per_contract': margin_per_contract,
            'total_pnl': total_pnl,
            'win_rate': win_rate,
            'kelly': kelly,
            'max_dd': abs(dd) if dd < 0 else 0,
            'daily_pnl_series': daily_pnl_aligned,
            'margin_series': margin_series
        }

    # Allocation Table
    st.markdown("### 📊 Strategy Allocation")
    
    if 'portfolio_allocation' not in st.session_state: st.session_state.portfolio_allocation = {s: 1.0 for s in strategies}
    if 'category_overrides' not in st.session_state: st.session_state.category_overrides = {}
    if 'kelly_pct' not in st.session_state: st.session_state.kelly_pct = 20

    allocation_data = []
    for strat in strategies:
        if strat not in strategy_base_stats: continue
        stats = strategy_base_stats[strat]
        cat = st.session_state.category_overrides.get(strat, stats['category'])
        mult = st.session_state.portfolio_allocation.get(strat, 1.0)
        
        allocation_data.append({
            'Category': cat,
            'Strategy': strat,
            'Hist': stats['contracts_per_day'],
            'P&L': stats['total_pnl'],
            'Multiplier': mult,
            'Kelly%': stats['kelly'] * 100
        })
    
    alloc_df = pd.DataFrame(allocation_data)
    
    alloc_col, action_col = st.columns([5, 1])
    with alloc_col:
        edited_alloc = st.data_editor(
            alloc_df,
            column_config={
                "Category": st.column_config.SelectboxColumn("Type", options=["Workhorse", "Airbag", "Opportunist"]),
                "Multiplier": st.column_config.NumberColumn("MULT", min_value=0.0, max_value=10.0, step=0.1)
            },
            use_container_width=True,
            key="allocation_editor_v16"
        )
        
        # Update state
        for _, row in edited_alloc.iterrows():
            st.session_state.portfolio_allocation[row['Strategy']] = float(row['Multiplier'])
            st.session_state.category_overrides[row['Strategy']] = row['Category']
            
    with action_col:
        if st.button("🧮 CALCULATE", use_container_width=True, type="primary"): st.session_state.calculate_kpis = True; st.rerun()
        if st.button("🔄 Reset", use_container_width=True): 
            st.session_state.portfolio_allocation = {s: 1.0 for s in strategies}
            st.rerun()
            
        kelly_input = st.number_input("Kelly %", 5, 100, st.session_state.kelly_pct, 5)
        st.session_state.kelly_pct = kelly_input
        
        if st.button("⚡ Kelly Opt", use_container_width=True):
            optimized = calc.kelly_optimize_allocation(
                strategy_base_stats, target_margin, kelly_input/100, 
                workhorse_pct/100, airbag_pct/100, opportunist_pct/100, 
                st.session_state.category_overrides
            )
            st.session_state.portfolio_allocation = optimized
            st.session_state.calculate_kpis = True
            st.rerun()

    if not st.session_state.get('calculate_kpis', False):
        st.info("👆 Adjust allocations and click CALCULATE.")
        return

    # Calculate Portfolio Metrics
    port_pnl = pd.Series(0.0, index=full_date_range)
    port_margin = pd.Series(0.0, index=full_date_range)
    
    total_pnl = 0
    for strat, mult in st.session_state.portfolio_allocation.items():
        if strat in strategy_base_stats and mult > 0:
            stats = strategy_base_stats[strat]
            port_pnl = port_pnl.add(stats['daily_pnl_series'] * mult, fill_value=0)
            port_margin = port_margin.add(stats['margin_series'] * mult, fill_value=0)
            total_pnl += stats['total_pnl'] * mult
            
    port_equity = account_size + port_pnl.cumsum()
    port_ret = port_equity.pct_change().fillna(0)
    
    # KPI Grid
    st.markdown("### 📈 Portfolio KPIs")
    
    # Calculate advanced metrics for the simulated portfolio
    spx = utils.fetch_spx_benchmark(pd.to_datetime(selected_dates[0]), pd.to_datetime(selected_dates[1]))
    spx_ret = spx.pct_change().fillna(0) if spx is not None else None
    
    m = calc.calculate_advanced_metrics(port_ret, None, spx_ret, account_size) # No trades DF for aggregate
    
    k1, k2, k3, k4, k5, k6 = st.columns(6)
    with k1: render_hero_metric("Total P/L", f"${total_pnl:,.0f}", color_class="hero-teal")
    with k2: render_hero_metric("CAGR", f"{m['CAGR']:.1%}", color_class="hero-teal")
    with k3: render_hero_metric("Max DD", f"{m['MaxDD']:.1%}", color_class="hero-coral")
    with k4: render_hero_metric("Max DD ($)", f"${abs(m['MaxDD_USD']):,.0f}", color_class="hero-coral")
    with k5: render_hero_metric("MAR", f"{m['MAR']:.2f}", color_class="hero-teal")
    with k6: render_hero_metric("Sharpe", f"{m['Sharpe']:.2f}", color_class="hero-neutral")

    # Monte Carlo Button
    if st.button("🎲 Stress Test with Monte Carlo →", use_container_width=True, type="primary"):
        st.session_state.mc_portfolio_daily_pnl = port_pnl
        st.session_state.mc_portfolio_account_size = account_size
        st.session_state.mc_from_builder = True
        st.session_state.navigate_to_page = "🎲 Monte Carlo Punisher"
        st.rerun()

    # Visualizations
    tab1, tab2 = st.tabs(["Equity", "Allocation"])
    with tab1:
        fig = px.line(x=port_equity.index, y=port_equity.values, title="Projected Equity")
        st.plotly_chart(fig, use_container_width=True)
    with tab2:
        alloc_pie = pd.DataFrame([
            {'Strategy': s, 'Allocation': m} 
            for s, m in st.session_state.portfolio_allocation.items() if m > 0
        ])
        if not alloc_pie.empty:
            fig_pie = px.pie(alloc_pie, values='Allocation', names='Strategy')
            st.plotly_chart(fig_pie, use_container_width=True)


def page_portfolio_analytics(full_df, live_df=None):
    st.markdown("<h1>PORTFOLIO ANALYTICS</h1>", unsafe_allow_html=True)
    
    data_source = "Backtest Data"
    if live_df is not None and not live_df.empty:
        data_source = st.radio("Source:", ["Backtest Data", "Live Data"])
    
    target_df = live_df if data_source == "Live Data" and live_df is not None else full_df
    if target_df.empty: return

    col_cap, col_date = st.columns(2)
    with col_cap: account_size = st.number_input("Account Size", 100000, 10000000, 100000)
    
    min_ts, max_ts = target_df['timestamp'].min(), target_df['timestamp'].max()
    with col_date:
        dates = st.date_input("Period", [min_ts.date(), max_ts.date()], min_value=min_ts.date(), max_value=max_ts.date())
    
    if len(dates) != 2: return
    filt = target_df[(target_df['timestamp'].dt.date >= dates[0]) & (target_df['timestamp'].dt.date <= dates[1])].copy()
    
    daily_pnl = filt.set_index('timestamp').resample('D')['pnl'].sum()
    full_idx = pd.date_range(dates[0], dates[1])
    daily_pnl = daily_pnl.reindex(full_idx, fill_value=0)
    
    equity = account_size + daily_pnl.cumsum()
    ret = equity.pct_change().fillna(0)
    
    spx = utils.fetch_spx_benchmark(pd.to_datetime(dates[0]), pd.to_datetime(dates[1]))
    spx_ret = spx.pct_change().fillna(0) if spx is not None else None
    
    m = calc.calculate_advanced_metrics(ret, filt, spx_ret, account_size)
    
    # KPI Grid
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    with c1: render_hero_metric("Total P/L", f"${filt['pnl'].sum():,.0f}", color_class="hero-teal")
    with c2: render_hero_metric("CAGR", f"{m['CAGR']:.1%}", color_class="hero-teal")
    with c3: render_hero_metric("Max DD", f"{m['MaxDD']:.1%}", color_class="hero-coral")
    with c4: render_hero_metric("Sharpe", f"{m['Sharpe']:.2f}")
    with c5: render_hero_metric("MAR", f"{m['MAR']:.2f}")
    with c6: render_hero_metric("Trades", f"{len(filt)}")
    
    st.divider()
    
    # Charts
    st.markdown("### Equity Curve")
    fig = px.area(x=equity.index, y=equity.values)
    st.plotly_chart(fig, use_container_width=True)
    
    # Monthly Matrix
    st.markdown("### Monthly Returns")
    filt['Year'] = filt['timestamp'].dt.year
    filt['Month'] = filt['timestamp'].dt.month
    pivot = filt.pivot_table(index='Year', columns='Month', values='pnl', aggfunc='sum').fillna(0)
    st.dataframe(pivot.style.applymap(color_monthly_performance).format("${:,.0f}"), use_container_width=True)

def page_meic_analysis(bt_df, live_df=None):
    st.markdown("<h1>🔬 MEIC DEEP DIVE</h1>", unsafe_allow_html=True)
    target = live_df if live_df is not None else bt_df
    
    if target.empty: return
    
    st.markdown("### Configuration")
    strats = st.multiselect("Select Strategies", target['strategy'].unique())
    if not strats: return
    
    df = target[target['strategy'].isin(strats)].copy()
    if 'timestamp_open' not in df.columns:
        st.error("No Entry Time data.")
        return
        
    df['EntryTime'] = df['timestamp_open'].dt.strftime('%H:%M')
    
    st.markdown("### Entry Time Analysis")
    stats = df.groupby('EntryTime')['pnl'].agg(['count', 'sum', 'mean'])
    stats.columns = ['Trades', 'Total P/L', 'Avg P/L']
    
    st.dataframe(stats.style.applymap(color_monthly_performance, subset=['Total P/L']), use_container_width=True)
    
    fig = px.bar(stats, y='Total P/L', color='Total P/L', color_continuous_scale='RdYlGn')
    st.plotly_chart(fig, use_container_width=True)

def page_meic_optimizer():
    st.markdown("<h1>🧪 MEIC OPTIMIZER</h1>", unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["Signal Generator", "Analyzer"])
    
    with tab1:
        st.markdown("### Generate Signals")
        d1 = st.date_input("Start")
        d2 = st.date_input("End")
        if st.button("Generate CSV"):
            df = utils.generate_oo_signals(d1, d2)
            csv = df.to_csv(index=False)
            st.download_button("Download", csv, "signals.csv", "text/csv")
            
    with tab2:
        st.markdown("### Analyze Results")
        files = st.file_uploader("Upload CSVs", accept_multiple_files=True)
        if files:
            res = []
            for f in files:
                meta = utils.parse_meic_filename(f.name)
                df = utils.load_file_with_caching(f)
                if df is not None:
                    mar = calc.analyze_meic_group(df, 100000)['MAR']
                    res.append({**meta, 'MAR': mar})
            st.dataframe(pd.DataFrame(res).sort_values('MAR', ascending=False))


def page_comparison(bt_df, live_df):
    st.markdown("<h1>⚖️ REALITY CHECK</h1>", unsafe_allow_html=True)
    if live_df is None or live_df.empty: return
    
    common = list(set(bt_df['strategy'].unique()) & set(live_df['strategy'].unique()))
    sel = st.selectbox("Strategy", common)
    
    b = bt_df[bt_df['strategy'] == sel]
    l = live_df[live_df['strategy'] == sel]
    
    # Cumulative comparison
    b_c = b.set_index('timestamp').sort_index()['pnl'].cumsum()
    l_c = l.set_index('timestamp').sort_index()['pnl'].cumsum()
    
    # Normalize
    b_c = b_c - b_c.iloc[0]
    l_c = l_c - l_c.iloc[0]
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=b_c.index, y=b_c, name="Backtest"))
    fig.add_trace(go.Scatter(x=l_c.index, y=l_c, name="Live"))
    st.plotly_chart(fig, use_container_width=True)

def page_ai_analyst(full_df):
    st.markdown("<h1>🤖 AI ANALYST</h1>", unsafe_allow_html=True)
    
    if not GEMINI_AVAILABLE:
        st.error("Gemini not installed.")
        return

    key = st.text_input("API Key", type="password")
    if key:
        genai.configure(api_key=key)
        model = genai.GenerativeModel("gemini-pro")
        
        if "messages" not in st.session_state: st.session_state.messages = []
        
        for m in st.session_state.messages:
            st.chat_message(m["role"]).write(m["content"])
            
        if p := st.chat_input():
            st.session_state.messages.append({"role": "user", "content": p})
            st.chat_message("user").write(p)
            
            summary = full_df.groupby('strategy')['pnl'].sum().to_string()
            try:
                resp = model.generate_content(f"Portfolio:\n{summary}\nUser: {p}")
                st.session_state.messages.append({"role": "assistant", "content": resp.text})
                st.chat_message("assistant").write(resp.text)
            except Exception as e:
                st.error(e)

def show_landing_page():
    st.title("⚡ CASHFLOW ENGINE")
    c1, c2 = st.columns(2)
    with c1:
        bt = st.file_uploader("Backtest Data", accept_multiple_files=True)
        live = st.file_uploader("Live Data", accept_multiple_files=True)
        if st.button("Launch", type="primary"):
            if bt:
                dfs = [utils.load_file_with_caching(f) for f in bt]
                st.session_state['full_df'] = pd.concat([d for d in dfs if d is not None], ignore_index=True)
                if live:
                    ldfs = [utils.load_file_with_caching(f) for f in live]
                    st.session_state['live_df'] = pd.concat([d for d in ldfs if d is not None], ignore_index=True)
                st.rerun()
    with c2:
        if utils.DB_AVAILABLE:
            saved = utils.get_analysis_list_enhanced()
            if saved:
                opts = {s['name']: s['id'] for s in saved}
                sel = st.selectbox("Load", list(opts.keys()))
                if st.button("Load"):
                    _load_with_feedback(opts[sel], sel)
