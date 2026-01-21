import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import calc  # Use calc module for run_monte_carlo_optimized
import ui_components as ui
import time

def page_monte_carlo(full_df):
    """Monte Carlo simulation page - OPTIMIZED."""
    # Loading overlay placeholder
    placeholder = st.empty()

    if 'sim_run' not in st.session_state:
        st.session_state.sim_run = False
    if 'mc_results' not in st.session_state:
        st.session_state.mc_results = None

    # Header with Exo 2 font
    st.markdown(f"""
        <h1 style="font-family: 'Exo 2', sans-serif !important; font-weight: 800 !important;
                   text-transform: uppercase; color: {ui.COLOR_GREY} !important; letter-spacing: 1px;">
            MONTE CARLO PUNISHER
        </h1>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style='color: #6B7280; font-size: 14px; line-height: 1.5; margin-bottom: 20px; font-family: Poppins, sans-serif;'>
        Stress test your portfolio against thousands of simulated scenarios. See how your strategies perform
        under various market conditions including black swan events.
    </div>
    """, unsafe_allow_html=True)

    # Check data source
    from_builder = st.session_state.get('mc_from_builder', False)
    portfolio_daily_pnl = st.session_state.get('mc_portfolio_daily_pnl', None)

    if from_builder and st.session_state.get('mc_new_from_builder', False):
        st.session_state.sim_run = False
        st.session_state.mc_results = None
        st.session_state.mc_new_from_builder = False

    if from_builder and portfolio_daily_pnl is not None:
        st.success("Using Assembled Portfolio from Portfolio Builder")
        if st.button("Use Raw Trade Data Instead", type="secondary"):
            st.session_state.mc_from_builder = False
            st.session_state.mc_portfolio_daily_pnl = None
            st.session_state.sim_run = False
            st.session_state.mc_results = None
            st.rerun()
        st.write("")

    # === CONFIGURATION (Card) ===
    with st.container(border=True):
        ui.section_header("Simulation Parameters",
            description="Configure the number of simulations, time period, and initial capital for the Monte Carlo analysis.")
        c1, c2, c3 = st.columns(3)
        with c1:
            n_sims = st.number_input("Number of Simulations", value=1000, step=500, min_value=100, max_value=10000,
                help="More simulations = more accurate results, but slower. 1000 is usually sufficient.")
        with c2:
            sim_months = st.number_input("Simulation Period (Months)", value=36, step=6, min_value=1, max_value=120,
                help="How far into the future to simulate. 36 months (3 years) is a good baseline.")
        with c3:
            if from_builder and portfolio_daily_pnl is not None:
                start_cap = st.number_input("Initial Capital ($)",
                                            value=st.session_state.get('mc_portfolio_account_size', 100000),
                                            step=1000, min_value=1000,
                                            help="Starting account balance for simulations.")
            else:
                start_cap = st.number_input("Initial Capital ($)", value=100000, step=1000, min_value=1000,
                    help="Starting account balance for simulations.")

    available_strategies = []
    if full_df is not None and not full_df.empty and 'strategy' in full_df.columns:
        available_strategies = sorted(full_df['strategy'].dropna().unique().tolist())

    # === STRESS TEST (Collapsible) ===
    with st.container(border=True):
        with st.expander("Stress Test Configuration (optional)", expanded=False):
            st.markdown("""
            <div style='color: #6B7280; font-size: 13px; line-height: 1.5; margin-bottom: 16px; font-family: Poppins, sans-serif;'>
                Inject worst-case scenarios to stress test your portfolio against market crashes.
            </div>
            """, unsafe_allow_html=True)

            stress_mode = st.radio(
                "Stress Test Mode:",
                ["Historical Max Loss (Real)", "Theoretical Max Risk (Black Swan)"],
                index=1,
                key="stress_mode_radio",
                help="Historical uses actual worst days from your data. Theoretical simulates a simultaneous crash."
            )

            if "Historical" in stress_mode:
                st.caption("Injects each strategy's actual worst day P&L from backtest data.")
                stress_val = st.slider("Frequency (times per year)", 0, 12, 0, 1, key="hist_stress_slider",
                    help="How many stress events to inject per simulated year. 0 = no stress test.")
                stress_strategies = available_strategies
            else:
                st.caption("Simulates a market crash hitting ALL selected strategies at once.")
                if len(available_strategies) > 0:
                    stress_strategies = st.multiselect(
                        "Strategies at risk during crash:",
                        options=available_strategies,
                        default=available_strategies,
                        key="stress_strategies_select"
                    )
                else:
                    stress_strategies = []

                stress_val = st.slider("Frequency (times per year)", 0, 12, 0, 1, key="theo_stress_slider",
                    help="How many crash events to inject per simulated year. 0 = no stress test.")

            st.session_state.stress_test_selected_strategies = stress_strategies

    st.write("")

    if st.button("Run Simulation", type="primary", use_container_width=True):
        st.session_state.sim_run = True
        st.session_state.mc_results = None

    if st.session_state.sim_run:
        if st.session_state.mc_results is None:
            # Show loading overlay
            with placeholder:
                ui.show_loading_overlay("Simulating", "Running thousands of Monte Carlo paths...")
            time.sleep(0.1)

            try:
                stress_injections = []
                final_trades_pool = []

                if from_builder and portfolio_daily_pnl is not None:
                    daily_pnl_values = portfolio_daily_pnl.dropna().values
                    daily_pnl_values = daily_pnl_values[daily_pnl_values != 0]
                    final_trades_pool = list(daily_pnl_values)
                    auto_trades_per_year = 252

                    if stress_val > 0:
                        worst_day = np.min(daily_pnl_values)
                        if worst_day < 0:
                            n = int(np.ceil(stress_val * (sim_months / 12.0)))
                            if n > 0: stress_injections.append((worst_day, n))
                else:
                    active_df = full_df.sort_values('timestamp')
                    days = (active_df['timestamp'].iloc[-1] - active_df['timestamp'].iloc[0]).days
                    days = max(days, 1)
                    auto_trades_per_year = len(active_df) / (days / 365.25)

                    stress_sel = st.session_state.get('stress_test_selected_strategies', [])
                    combined_theoretical_wc = 0

                    for strat_name, group in active_df.groupby('strategy'):
                        strat_pnl = group['pnl'].dropna().values
                        final_trades_pool.extend(strat_pnl)

                        if stress_val > 0:
                            daily_pnl = group.groupby(group['timestamp'].dt.date)['pnl'].sum()
                            hist_worst = daily_pnl.min() if len(daily_pnl) > 0 else np.min(strat_pnl)

                            if "Historical" in stress_mode and hist_worst < 0:
                                n = int(np.ceil(stress_val * (sim_months / 12.0)))
                                stress_injections.append((hist_worst, n, 'random'))
                            elif "Theoretical" in stress_mode and strat_name in stress_sel:
                                combined_theoretical_wc += hist_worst if hist_worst < 0 else 0

                    if "Theoretical" in stress_mode and stress_val > 0 and combined_theoretical_wc < 0:
                        n = int(np.ceil(stress_val * (sim_months / 12.0)))
                        stress_injections.append((combined_theoretical_wc, n, 'distributed'))

                n_steps = max(int((sim_months / 12) * auto_trades_per_year), 10)
                n_years = max(1, sim_months / 12)

                # Flatten stress injections
                stress_inj_list = []
                inj_mode = 'distributed'
                total_inj = 0
                if stress_injections:
                    inj_mode = stress_injections[0][2] if len(stress_injections[0]) > 2 else 'distributed'
                    for item in stress_injections:
                        val, count = item[0], item[1]
                        if inj_mode == 'random':
                            stress_inj_list.extend([val]*count)
                        else:
                            stress_inj_list = [val]
                        total_inj += count

                mc_result = calc.run_monte_carlo_optimized(
                    np.array(final_trades_pool), int(n_sims), n_steps, start_cap,
                    stress_injections=np.array(stress_inj_list) if stress_inj_list else None,
                    n_stress_per_sim=total_inj, n_years=n_years, injection_mode=inj_mode
                )

                if isinstance(mc_result, tuple):
                    mc_paths, end_vals, dds = mc_result
                else:
                    mc_paths = mc_result
                    end_vals = mc_paths[:, -1]
                    dds = calc.calculate_max_drawdown_batch(mc_paths)

                # Calculate stats
                profit = np.mean(end_vals) - start_cap
                cagr = ((np.mean(end_vals) / start_cap) ** (12 / sim_months)) - 1
                dd_mean = np.mean(dds)
                mar = cagr / dd_mean if dd_mean > 0 else 0

                p95, p50, p05 = np.percentile(end_vals, [95, 50, 5])
                d05, d50, d95 = np.percentile(dds, [5, 50, 95])
                prob_profit = np.sum(end_vals > start_cap) / len(end_vals)

                st.session_state.mc_results = {
                    'mc_paths': mc_paths, 'end_vals': end_vals, 'dds': dds,
                    'profit': profit, 'cagr': cagr, 'dd_mean': dd_mean, 'mar': mar,
                    'p95': p95, 'p50': p50, 'p05': p05,
                    'd05': d05, 'd50': d50, 'd95': d95,
                    'start_cap': start_cap, 'prob_profit': prob_profit,
                    'n_sims': n_sims
                }
                placeholder.empty()
            except Exception as e:
                placeholder.empty()
                st.error(f"Error running simulation: {e}")
                import traceback
                st.code(traceback.format_exc())
                return

        # Display Results
        r = st.session_state.mc_results

        # === RESULTS METRICS (Card) ===
        with st.container(border=True):
            ui.section_header("Simulation Results",
                description=f"Summary statistics from {r['n_sims']:,} Monte Carlo simulations.")

            # Row 1: Primary metrics
            k1, k2, k3, k4, k5, k6 = st.columns(6)
            with k1: ui.render_hero_metric("Avg Net Profit", f"${r['profit']:,.0f}", "", "hero-teal",
                tooltip="Average ending equity minus starting capital across all simulations")
            with k2: ui.render_hero_metric("CAGR", f"{r['cagr']:.1%}", "", "hero-teal",
                tooltip="Compound Annual Growth Rate")
            with k3: ui.render_hero_metric("Avg MaxDD", f"{r['dd_mean']:.1%}", "", "hero-coral",
                tooltip="Average maximum drawdown across all simulations")
            with k4: ui.render_hero_metric("MAR", f"{r['mar']:.2f}", "", "hero-teal" if r['mar'] > 1 else "hero-neutral",
                tooltip="MAR Ratio = CAGR / Max Drawdown. Higher is better.")
            with k5: ui.render_hero_metric("Prob. Profit", f"{r['prob_profit']:.1%}", "", "hero-neutral",
                tooltip="Percentage of simulations ending with profit")
            with k6:
                # Calculate Sharpe-like metric
                returns_std = np.std(r['end_vals'] - start_cap)
                sharpe_like = r['profit'] / returns_std if returns_std > 0 else 0
                ui.render_hero_metric("Return/Risk", f"{sharpe_like:.2f}", "", "hero-neutral",
                    tooltip="Average return divided by return standard deviation")

        # === SCENARIOS (Card) ===
        with st.container(border=True):
            ui.section_header("Scenarios",
                description="Percentile-based outcomes showing best, median, and worst case scenarios.")
            r1, r2, r3 = st.columns(3)
            with r1: ui.render_hero_metric("Best Case (95%)", f"${r['p95']:,.0f}", f"DD: {r['d05']:.1%}", "hero-neutral")
            with r2: ui.render_hero_metric("Median (50%)", f"${r['p50']:,.0f}", f"DD: {r['d50']:.1%}", "hero-neutral")
            with r3: ui.render_hero_metric("Worst Case (5%)", f"${r['p05']:,.0f}", f"DD: {r['d95']:.1%}", "hero-neutral")

        # === VISUALIZATION (Card) ===
        with st.container(border=True):
            ui.section_header("Portfolio Growth Paths",
                description="Sample of simulated equity paths with percentile bands showing the range of possible outcomes.")

            mc_paths = r['mc_paths']
            x = np.arange(mc_paths.shape[1])
            fig = go.Figure()

            # Show a subset of paths
            indices = np.random.choice(mc_paths.shape[0], min(50, mc_paths.shape[0]), replace=False)
            for idx in indices:
                fig.add_trace(go.Scatter(x=x, y=mc_paths[idx], mode='lines', line=dict(color='rgba(200,200,200,0.2)', width=1), showlegend=False))

            # Percentiles
            pp95, pp50, pp05 = np.percentile(mc_paths, [95, 50, 5], axis=0)
            fig.add_trace(go.Scatter(x=x, y=pp95, mode='lines', line=dict(color=ui.COLOR_TEAL, width=2), name="95th %"))
            fig.add_trace(go.Scatter(x=x, y=pp50, mode='lines', line=dict(color=ui.COLOR_BLUE, width=3), name="Median"))
            fig.add_trace(go.Scatter(x=x, y=pp05, mode='lines', line=dict(color=ui.COLOR_CORAL, width=2), name="5th %"))

            fig.update_layout(template="plotly_white", height=500, xaxis_title="Trade Steps", yaxis_title="Equity ($)")
            st.plotly_chart(fig, use_container_width=True)

        # === DISTRIBUTIONS (Card) ===
        with st.container(border=True):
            ui.section_header("Distributions",
                description="Distribution of ending equity values and maximum drawdowns across all simulations.")
            d1, d2 = st.columns(2)
            with d1:
                fig_ret = go.Figure()
                fig_ret.add_trace(go.Histogram(x=r['end_vals'], marker_color=ui.COLOR_BLUE, opacity=0.7))
                fig_ret.add_vline(x=r['start_cap'], line_dash="dash", line_color="gray", annotation_text="Starting Capital")
                fig_ret.update_layout(title="Ending Equity Distribution", template="plotly_white", height=350)
                st.plotly_chart(fig_ret, use_container_width=True)
            with d2:
                fig_dd = go.Figure()
                fig_dd.add_trace(go.Histogram(x=r['dds']*100, marker_color=ui.COLOR_CORAL, opacity=0.7))
                fig_dd.update_layout(title="Max Drawdown Distribution (%)", template="plotly_white", height=350)
                st.plotly_chart(fig_dd, use_container_width=True)
