import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import ui_components as ui
import calc

def page_monte_carlo(full_df):
    """Monte Carlo simulation page - OPTIMIZED with error handling."""
    if 'sim_run' not in st.session_state:
        st.session_state.sim_run = False
    if 'mc_results' not in st.session_state:
        st.session_state.mc_results = None

    ui.render_page_header("MONTE CARLO PUNISHER")
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

    # --- CONFIGURATION BOX ---
    with st.container(border=True):
        ui.section_header("CONFIGURATION", "Set simulation parameters and stress test options")

        c1, c2, c3 = st.columns(3)
        with c1:
            n_sims = st.number_input("Number of Simulations", value=1000, step=500, min_value=100, max_value=10000)
        with c2:
            sim_months = st.number_input("Simulation Period (Months)", value=36, step=6, min_value=1, max_value=120)
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
                        default=available_strategies,
                        key="stress_test_strategies",
                        help="Only selected strategies will be hit simultaneously. Deselect strategies that profit from crashes."
                    )
                else:
                    stress_strategies = []

                stress_val = st.slider("Frequency (times per year)", 0, 12, 0, 1, format="%d x/Year",
                                      help="How many combined crash events per year", key="theo_stress_slider")
                if stress_val > 0:
                    n_events = int(np.ceil(stress_val * (sim_months / 12.0)))
                    st.caption(f"⚠️ {n_events} event(s) distributed across {max(1, sim_months//12)} year(s)")

                # Store selected strategies in session state for use during simulation
                st.session_state.stress_test_selected_strategies = stress_strategies

        st.write("")

        if st.button("🎲 Run Simulation", type="primary", use_container_width=True):
            st.session_state.sim_run = True
            st.session_state.mc_results = None

    if st.session_state.sim_run:
        if st.session_state.mc_results is None:
            try:
                mc_loading = st.empty()
                ui.show_loading_overlay("Running Simulations", "Crunching thousands of possible futures...", mc_loading)

                stress_injections = []

                if from_builder and portfolio_daily_pnl is not None:
                    daily_pnl_values = portfolio_daily_pnl.dropna().values
                    daily_pnl_values = daily_pnl_values[daily_pnl_values != 0]

                    if len(daily_pnl_values) < 10:
                        mc_loading.empty()
                        st.error("Not enough non-zero days for simulation.")
                        return

                    final_trades_pool = list(daily_pnl_values)
                    days = len(portfolio_daily_pnl)
                    auto_trades_per_year = 252

                    debug_msg = []
                    injected_count = 0

                    if stress_val > 0:
                        worst_day = np.min(daily_pnl_values)
                        if worst_day < 0:
                            n = int(np.ceil(stress_val * (sim_months / 12.0)))
                            if n > 0:
                                stress_injections.append((worst_day, n))
                                injected_count += n
                                debug_msg.append(f"**Portfolio**: {n}x **${worst_day:,.0f}** per sim (Worst Day)")
                else:
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

                    stress_selected_strategies = st.session_state.get('stress_test_selected_strategies', [])

                    historical_worst_days = []
                    combined_theoretical_wc = 0
                    strategy_wc_details = []

                    for strat_name, group in active_df.groupby('strategy'):
                        strat_pnl = group['pnl'].dropna().values
                        if len(strat_pnl) == 0:
                            continue
                        final_trades_pool.extend(strat_pnl)

                        if stress_val > 0:
                            daily_pnl = group.groupby(group['timestamp'].dt.date)['pnl'].sum()
                            hist_worst_day = daily_pnl.min() if len(daily_pnl) > 0 else np.min(strat_pnl)

                            if hist_worst_day < 0:
                                historical_worst_days.append((strat_name, hist_worst_day))

                            if strat_name in stress_selected_strategies:
                                strat_theoretical_wc = 0
                                avg_daily_premium = 0

                                if 'margin' in group.columns and 'legs' in group.columns:
                                    daily_premium = group.groupby(group['timestamp'].dt.date)['pnl'].sum()
                                    avg_daily_premium = daily_premium.mean() if len(daily_premium) > 0 else 0

                                    daily_put_margins = []

                                    timestamp_col = 'timestamp_open' if 'timestamp_open' in group.columns else 'timestamp'
                                    for entry_date, day_group in group.groupby(group[timestamp_col].dt.date):
                                        day_put_margin = 0

                                        for _, row in day_group.iterrows():
                                            m = row['margin'] if not pd.isna(row['margin']) else 0
                                            legs = str(row.get('legs', '')).upper()

                                            is_put_side = any(x in legs for x in [' P ', ' PUT ', ' P:', '/P', '-P', 'PUT SPREAD', 'BULL PUT'])
                                            is_call_side = any(x in legs for x in [' C ', ' CALL ', ' C:', '/C', '-C', 'CALL SPREAD', 'BEAR CALL'])
                                            is_long_put = 'LONG PUT' in legs or 'BUY PUT' in legs

                                            if is_put_side and is_call_side:
                                                day_put_margin += m / 2
                                            elif is_put_side and not is_long_put:
                                                day_put_margin += m
                                            elif is_call_side or is_long_put:
                                                pass
                                            else:
                                                day_put_margin += m

                                        if day_put_margin > 0:
                                            daily_put_margins.append(day_put_margin)

                                    max_daily_put_margin = max(daily_put_margins) if daily_put_margins else 0

                                    if max_daily_put_margin > 0:
                                        strat_theoretical_wc = -(max_daily_put_margin - abs(avg_daily_premium))

                                if strat_theoretical_wc < 0:
                                    combined_theoretical_wc += strat_theoretical_wc
                                    strategy_wc_details.append(f"**{strat_name}**: ${abs(strat_theoretical_wc):,.0f}")
                                elif hist_worst_day < 0:
                                    combined_theoretical_wc += hist_worst_day
                                    strategy_wc_details.append(f"**{strat_name}**: ${abs(hist_worst_day):,.0f} (hist)")

                    if stress_val > 0:
                        n_events_per_year = stress_val
                        n_years = max(1, sim_months / 12)

                        if "Historical" in stress_mode:
                            total_events = int(np.ceil(n_events_per_year * n_years))

                            if len(historical_worst_days) > 0 and total_events > 0:
                                for strat_name, worst_day in historical_worst_days:
                                    stress_injections.append((worst_day, total_events, 'random'))
                                    injected_count += total_events
                                    debug_msg.append(f"**{strat_name}**: {total_events}x **${worst_day:,.0f}** (worst day)")

                                debug_msg.insert(0, f"**Historical Worst Days**: {total_events} events per strategy, randomly distributed")
                                debug_msg.insert(1, "---")
                        else:
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
                n_years = max(1, sim_months / 12)

                stress_inj_list = []
                injection_mode = 'distributed'
                total_injections = 0

                if len(stress_injections) > 0:
                    injection_mode = stress_injections[0][2] if len(stress_injections[0]) > 2 else 'distributed'

                    if injection_mode == 'random':
                        for entry in stress_injections:
                            val, count = entry[0], entry[1]
                            stress_inj_list.extend([val] * count)
                            total_injections += count
                    else:
                        val, count = stress_injections[0][0], stress_injections[0][1]
                        stress_inj_list = [val]
                        total_injections = count

                stress_inj_array = np.array(stress_inj_list) if stress_inj_list else None

                mc_result = calc.run_monte_carlo_optimized(
                    np.array(final_trades_pool), int(n_sims), n_steps, start_cap,
                    stress_injections=stress_inj_array,
                    n_stress_per_sim=total_injections,
                    n_years=n_years,
                    injection_mode=injection_mode
                )

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

                cagr_p95 = ((p95 / start_cap) ** (12 / sim_months)) - 1
                cagr_p50 = ((p50 / start_cap) ** (12 / sim_months)) - 1
                cagr_p05 = ((p05 / start_cap) ** (12 / sim_months)) - 1

                mart = cagr / dd_mean if dd_mean > 0 else 0

                profitable_sims = np.sum(end_vals > start_cap)
                prob_profit = profitable_sims / len(end_vals)

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

                mc_loading.empty()

            except Exception as e:
                mc_loading.empty()
                st.error(f"Simulation error: {str(e)}")
                st.session_state.sim_run = False
                return

        if st.session_state.mc_results is not None:
            r = st.session_state.mc_results

            n_stress = r.get('n_stress_per_sim', 0)
            n_steps = r.get('n_steps', 0)
            sim_months = r.get('sim_months', 12)
            n_years = max(1, sim_months / 12)
            injection_mode = r.get('injection_mode', 'distributed')

            if n_stress > 0:
                if injection_mode == 'random':
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

        # --- KEY METRICS BOX ---
        with st.container(border=True):
            ui.section_header("KEY METRICS", "Core performance indicators across all simulations")
            k1, k2, k3, k4, k5 = st.columns(5)
            with k1:
                ui.render_hero_metric("Avg. Net Profit", f"${r['profit']:,.0f}", "Mean Result", "hero-teal" if r['profit'] > 0 else "hero-coral",
                                  tooltip="Average ending portfolio value minus initial capital across all simulations")
            with k2:
                ui.render_hero_metric("CAGR", f"{r['cagr']*100:.1f}%", "Ann. Growth", "hero-teal" if r['cagr'] > 0 else "hero-coral",
                                  tooltip="Compound Annual Growth Rate based on average ending value")
            with k3:
                ui.render_hero_metric("Expected DD", f"{r['dd_mean']*100:.1f}%", "Avg. Drawdown", "hero-coral",
                                  tooltip="Average maximum drawdown across all simulations - the expected worst-case decline")
            with k4:
                mar_val = r.get('mar', r['cagr'] / r['dd_mean'] if r['dd_mean'] > 0 else 0)
                ui.render_hero_metric("MAR Ratio", f"{mar_val:.2f}", "CAGR/DD", "hero-teal" if mar_val > 1 else "hero-coral",
                                  tooltip="CAGR divided by Expected Drawdown. Above 0.5 is acceptable, above 1.0 is good")
            with k5:
                prob_profit = r.get('prob_profit', 1.0)
                n_sims = r.get('n_sims', 1000)
                ui.render_hero_metric("Prob. of Profit", f"{prob_profit*100:.1f}%", f"Out of {n_sims:,} sims",
                                  "hero-teal" if prob_profit > 0.9 else ("hero-coral" if prob_profit < 0.7 else "hero-neutral"),
                                  tooltip="Percentage of simulations that ended with profit (ending value > starting capital)")

        # --- RETURN & DRAWDOWN SCENARIOS BOX ---
        with st.container(border=True):
            ui.section_header("RETURN SCENARIOS (CAGR)", "Performance percentiles across simulations")
            r1, r2, r3 = st.columns(3)
            with r1:
                cagr_best = r.get('cagr_p95', ((r['p95']/r['start_cap']) ** (12 / r.get('sim_months', 36))) - 1)
                ui.render_hero_metric("Best Case (95%)", f"{cagr_best*100:.1f}%", f"${r['p95']:,.0f}", "hero-neutral",
                                  tooltip="95th percentile CAGR - only 5% of simulations performed better")
            with r2:
                cagr_likely = r.get('cagr_p50', ((r['p50']/r['start_cap']) ** (12 / r.get('sim_months', 36))) - 1)
                ui.render_hero_metric("Most Likely (50%)", f"{cagr_likely*100:.1f}%", f"${r['p50']:,.0f}", "hero-neutral",
                                  tooltip="Median CAGR - 50% of simulations were better, 50% were worse")
            with r3:
                cagr_worst = r.get('cagr_p05', ((r['p05']/r['start_cap']) ** (12 / r.get('sim_months', 36))) - 1)
                ui.render_hero_metric("Worst Case (5%)", f"{cagr_worst*100:.1f}%", f"${r['p05']:,.0f}", "hero-neutral",
                                  tooltip="5th percentile CAGR - only 5% of simulations performed worse")

            st.write("")
            ui.section_header("DRAWDOWN SCENARIOS", "Risk percentiles across simulations")
            d1, d2, d3 = st.columns(3)
            with d1:
                ui.render_hero_metric("Best Case DD", f"{r['d05']*100:.1f}%", "Top 5%", "hero-neutral",
                                  tooltip="5th percentile drawdown - only 5% of simulations had smaller drawdowns")
            with d2:
                ui.render_hero_metric("Typical DD", f"{r['d50']*100:.1f}%", "Median", "hero-neutral",
                                  tooltip="Median drawdown - 50% of simulations had larger, 50% smaller drawdowns")
            with d3:
                ui.render_hero_metric("Worst Case DD", f"{r['d95']*100:.1f}%", "Bottom 5%", "hero-neutral",
                                  tooltip="95th percentile drawdown - only 5% of simulations had larger drawdowns")

        # --- PORTFOLIO GROWTH BOX ---
        with st.container(border=True):
            ui.section_header("PORTFOLIO GROWTH", "Visualization of simulation paths")
            show_paths = st.checkbox("Show individual paths", value=True)

            mc_paths = r['mc_paths']
            end_vals = r['end_vals']
            dds = r['dds']

            x = np.arange(mc_paths.shape[1])
            fig = go.Figure()

            if show_paths:
                n_display = min(50, mc_paths.shape[0])
                np.random.seed(42)
                random_indices = np.random.choice(mc_paths.shape[0], n_display, replace=False)

                for idx in random_indices:
                    fig.add_trace(go.Scatter(
                        x=x, y=mc_paths[idx], mode='lines',
                        line=dict(color='rgba(200, 200, 200, 0.15)', width=1),
                        showlegend=False, hoverinfo='skip'
                    ))

                stored_end_vals = mc_paths[:, -1]
                stored_dds = calc.calculate_max_drawdown_batch(mc_paths)

                best_idx = np.argmax(stored_end_vals)
                worst_idx = np.argmin(stored_end_vals)
                max_dd_idx = np.argmax(stored_dds)

                fig.add_trace(go.Scatter(x=x, y=mc_paths[best_idx], mode='lines',
                                         line=dict(color=ui.COLOR_TEAL, width=2), name='Best Path'))
                fig.add_trace(go.Scatter(x=x, y=mc_paths[worst_idx], mode='lines',
                                         line=dict(color=ui.COLOR_CORAL, width=2), name='Worst Path'))
                if max_dd_idx != worst_idx:
                    fig.add_trace(go.Scatter(x=x, y=mc_paths[max_dd_idx], mode='lines',
                                             line=dict(color='#7B2BFF', width=2, dash='dot'), name='Max DD Path'))

            pp95, pp05 = np.percentile(mc_paths, [95, 5], axis=0)
            fig.add_trace(go.Scatter(
                x=np.concatenate([x, x[::-1]]),
                y=np.concatenate([pp95, pp05[::-1]]),
                fill='toself', fillcolor='rgba(0, 210, 190, 0.05)',
                line=dict(width=0), name='5-95% Conf.', showlegend=True
            ))

            pp50 = np.percentile(mc_paths, 50, axis=0)
            fig.add_trace(go.Scatter(x=x, y=pp50, mode='lines',
                                     line=dict(color=ui.COLOR_BLUE, width=3), name='Median'))

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
                returns_pct = ((end_vals - r['start_cap']) / r['start_cap']) * 100

                fig_return_dist = go.Figure()
                fig_return_dist.add_trace(go.Histogram(
                    x=returns_pct,
                    nbinsx=30,
                    marker_color=ui.COLOR_BLUE,
                    opacity=0.8,
                    name="Returns"
                ))

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
                dds_pct = dds * 100

                fig_dd_dist = go.Figure()
                fig_dd_dist.add_trace(go.Histogram(
                    x=dds_pct,
                    nbinsx=30,
                    marker_color=ui.COLOR_CORAL,
                    opacity=0.8,
                    name="Drawdowns"
                ))

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
