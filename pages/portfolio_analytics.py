import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import calculations as calc
import ui_components as ui
import time

def page_portfolio_analytics(full_df, live_df=None):
    # --- 1. OVERLAY & LOADING ---
    placeholder = st.empty()
    with placeholder:
        ui.show_loading_overlay("Calculating Analytics", "Crunching numbers for Portfolio Analysis...")
    time.sleep(0.05)

    try:
        # Header with Exo 2 font
        st.markdown(f"""
            <h1 style="font-family: 'Exo 2', sans-serif !important; font-weight: 800 !important;
                       text-transform: uppercase; color: {ui.COLOR_GREY} !important; letter-spacing: 1px;">
                PORTFOLIO ANALYTICS
            </h1>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div style='color: #6B7280; font-size: 14px; line-height: 1.5; margin-bottom: 20px; font-family: Poppins, sans-serif;'>
            Comprehensive analysis of your portfolio performance. Analyze backtest and live trade data,
            key performance indicators, monthly return matrices, and equity growth curves.
        </div>
        """, unsafe_allow_html=True)

        # === CONFIGURATION (FILTER AT TOP) ===
        with st.container(border=True):
            ui.section_header("Configuration")

            # Data Source Selection
            data_source = "Backtest Data"
            if live_df is not None and not live_df.empty:
                data_source = st.radio("Data Source:", ["Backtest Data", "Live Data"], horizontal=True)

            target_df = live_df if data_source == "Live Data" and live_df is not None else full_df
            if target_df.empty:
                placeholder.empty()
                st.warning("No data available.")
                return

            col_cap, col_date = st.columns(2)
            with col_cap:
                account_size = st.number_input("Account Size ($)", 100000, 10000000, 100000)

            min_ts, max_ts = target_df['timestamp'].min(), target_df['timestamp'].max()
            with col_date:
                dates = st.date_input("Period", [min_ts.date(), max_ts.date()], min_value=min_ts.date(), max_value=max_ts.date())

            if len(dates) != 2:
                placeholder.empty()
                return

            # Strategy Filter - IMPROVED: Collapsible with Select All
            all_strategies = sorted(target_df['strategy'].unique())

            # Initialize session state for selected strategies
            if 'pa_selected_strats' not in st.session_state:
                st.session_state.pa_selected_strats = all_strategies.copy()

            # Filter header with Select All link
            filter_col1, filter_col2 = st.columns([3, 1])
            with filter_col1:
                st.markdown("**Filter Strategies**")
            with filter_col2:
                if st.button("Select All", key="select_all_strats", type="tertiary"):
                    st.session_state.pa_selected_strats = all_strategies.copy()
                    st.rerun()

            # Collapsible strategy selection
            with st.expander(f"Selected: {len(st.session_state.pa_selected_strats)} of {len(all_strategies)} strategies", expanded=False):
                selected_strats = st.multiselect(
                    "Strategies",
                    all_strategies,
                    default=st.session_state.pa_selected_strats,
                    label_visibility="collapsed",
                    key="pa_strat_multiselect"
                )
                st.session_state.pa_selected_strats = selected_strats

            selected_strats = st.session_state.pa_selected_strats

            # Recalculate button
            st.write("")
            if st.button("RECALCULATE", type="primary", use_container_width=True):
                st.session_state.pa_recalculate = True
                st.rerun()

            # Check if we should recalculate or use cached results
            if not st.session_state.get('pa_recalculate', True):
                placeholder.empty()
                st.info("Adjust filters above and click RECALCULATE to update analytics.")
                return

            # Apply Filter
            mask = (target_df['timestamp'].dt.date >= dates[0]) & (target_df['timestamp'].dt.date <= dates[1])
            if selected_strats:
                mask = mask & (target_df['strategy'].isin(selected_strats))
            else:
                st.warning("Please select at least one strategy.")
                placeholder.empty()
                return

            filt = target_df[mask].copy()

            # Reset recalculate flag after running
            st.session_state.pa_recalculate = False

        # === CALCULATIONS ===
        if filt.empty:
            st.warning("No data matches filters.")
            placeholder.empty()
            return

        daily_pnl = filt.set_index('timestamp').resample('D')['pnl'].sum()
        full_idx = pd.date_range(dates[0], dates[1])
        daily_pnl = daily_pnl.reindex(full_idx, fill_value=0)

        equity = account_size + daily_pnl.cumsum()
        ret = equity.pct_change().fillna(0)

        # Benchmarking
        spx = calc.fetch_spx_benchmark(pd.to_datetime(dates[0]), pd.to_datetime(dates[1]))
        spx_ret = None

        if spx is not None:
            spx.index = pd.to_datetime(spx.index)
            spx_filtered = spx[(spx.index.date >= dates[0]) & (spx.index.date <= dates[1])]
            if not spx_filtered.empty:
                spx_ret = spx_filtered.pct_change().fillna(0)

        m = calc.calculate_advanced_metrics(ret, filt, spx_ret, account_size)

        # Calculate Peak/Mean Margin for KPI display
        margin_series = calc.generate_daily_margin_series_optimized(filt)
        peak_margin = margin_series.max() if not margin_series.empty else 0
        avg_margin = margin_series.mean() if not margin_series.empty else 0

        # === KPI HIGHLIGHTS (3x6 Grid) ===
        # Row 1: Primary metrics (Teal/Coral)
        r1c1, r1c2, r1c3, r1c4, r1c5, r1c6 = st.columns(6)
        with r1c1: ui.render_hero_metric("Total P/L", f"${filt['pnl'].sum():,.0f}", f"SPX: ${m['SPX_TotalPnL_USD']:,.0f}", "hero-teal")
        with r1c2: ui.render_hero_metric("CAGR", f"{m['CAGR']:.1%}", f"SPX: {m['SPX_CAGR']:.1%}", "hero-teal")
        with r1c3: ui.render_hero_metric("Max DD (%)", f"{m['MaxDD']:.1%}", f"SPX: {m['SPX_MaxDD']:.1%}", "hero-coral")
        with r1c4: ui.render_hero_metric("Max DD ($)", f"${abs(m['MaxDD_USD']):,.0f}", "", "hero-coral")
        with r1c5: ui.render_hero_metric("MAR Ratio", f"{m['MAR']:.2f}", f"SPX: {abs(m['SPX_CAGR'] / m['SPX_MaxDD']) if m['SPX_MaxDD'] != 0 else 0:.2f}", "hero-teal")
        with r1c6: ui.render_hero_metric("MART Ratio", f"{m['MART']:.2f}", "", "hero-teal")

        st.write("")

        # Row 2: Standard metrics
        r2c1, r2c2, r2c3, r2c4, r2c5, r2c6 = st.columns(6)
        with r2c1: ui.render_hero_metric("Total Trades", f"{m['Trades']}", "", "hero-neutral")
        with r2c2: ui.render_hero_metric("Win Rate", f"{m['WinRate']:.1%}", "", "hero-neutral")
        with r2c3: ui.render_hero_metric("Profit Factor", f"{m['PF']:.2f}", "", "hero-neutral")
        with r2c4: ui.render_hero_metric("Sharpe", f"{m['Sharpe']:.2f}", f"SPX: {m['SPX_Sharpe']:.2f}", "hero-neutral")
        with r2c5: ui.render_hero_metric("Sortino", f"{m['Sortino']:.2f}", "", "hero-neutral")
        with r2c6: ui.render_hero_metric("Volatility", f"{m['Vol']:.1%}", f"SPX: {m['SPX_Vol']:.1%}", "hero-neutral")

        st.write("")

        # Row 3: Advanced & Margin
        r3c1, r3c2, r3c3, r3c4, r3c5, r3c6 = st.columns(6)
        with r3c1: ui.render_hero_metric("Alpha (vs SPX)", f"{m['Alpha']:.1%}", "Excess return", "hero-neutral")
        with r3c2: ui.render_hero_metric("Beta (vs SPX)", f"{m['Beta']:.2f}", "Market sensitivity", "hero-neutral")
        with r3c3: ui.render_hero_metric("Avg Ret/Marg", f"{m['AvgRetMargin']:.1%}", "", "hero-neutral")
        with r3c4: ui.render_hero_metric("Kelly", f"{m['Kelly']:.1%}", "", "hero-neutral")
        with r3c5: ui.render_hero_metric("Peak Margin", f"${peak_margin:,.0f}", f"{peak_margin/account_size:.0%} of Account", "hero-neutral")
        with r3c6: ui.render_hero_metric("Avg Margin", f"${avg_margin:,.0f}", f"{avg_margin/account_size:.0%} of Account", "hero-neutral")

        st.write("")

        # Row 4: Streaks
        r4c1, r4c2, r4c3, r4c4, r4c5 = st.columns([1, 1, 1, 1, 1])
        with r4c1: ui.render_hero_metric("Win Streak", f"{m['WinStreak']}", "Best run", "hero-neutral")
        with r4c2: ui.render_hero_metric("Loss Streak", f"{m['LossStreak']}", "Worst run", "hero-neutral")
        with r4c3:
            pnl_series = filt['pnl']
            avg_w = pnl_series[pnl_series > 0].mean() if len(pnl_series[pnl_series > 0]) > 0 else 0
            avg_l = pnl_series[pnl_series <= 0].mean() if len(pnl_series[pnl_series <= 0]) > 0 else 0
            ui.render_hero_metric("Avg Win", f"${avg_w:,.0f}", "", "hero-neutral")
        with r4c4: ui.render_hero_metric("Avg Loss", f"${avg_l:,.0f}", "", "hero-neutral")
        with r4c5:
            best_trade = pnl_series.max() if not pnl_series.empty else 0
            worst_trade = pnl_series.min() if not pnl_series.empty else 0
            ui.render_hero_metric("Best/Worst", f"${best_trade:,.0f} / ${worst_trade:,.0f}", "", "hero-neutral")

        # === CHARTS SECTION ===
        st.write("")

        # --- EQUITY CURVE ---
        with st.container(border=True):
            ui.section_header("Equity Curve",
                description="Cumulative P/L over time for each strategy and the total portfolio. The gray dotted line shows the S&P 500 benchmark for comparison.")

            eq_data = pd.DataFrame(index=full_idx)
            for i, s in enumerate(selected_strats):
                s_df = filt[filt['strategy'] == s]
                if not s_df.empty:
                    s_pnl = s_df.set_index('timestamp').resample('D')['pnl'].sum().reindex(full_idx, fill_value=0)
                    eq_data[s] = s_pnl.cumsum()

            eq_data['Total Portfolio'] = eq_data.sum(axis=1)

            fig_eq = px.line(eq_data, x=eq_data.index, y=eq_data.columns,
                             color_discrete_sequence=px.colors.qualitative.Prism)

            if spx_ret is not None and not spx_ret.empty:
                spx_cumulative_return = (1 + spx_ret).cumprod() - 1
                spx_pnl_curve = account_size * spx_cumulative_return
                spx_pnl_curve = spx_pnl_curve.reindex(eq_data.index, method='ffill')
                fig_eq.add_trace(go.Scatter(x=spx_pnl_curve.index, y=spx_pnl_curve, name="SPX Benchmark", line=dict(color='gray', dash='dot')))

            fig_eq.update_layout(template="plotly_white", xaxis_title=None, yaxis_title="Cumulative P/L ($)", height=500, legend=dict(orientation="h", y=-0.2))
            st.plotly_chart(fig_eq, use_container_width=True)

        # --- MARGIN USAGE ---
        with st.container(border=True):
            margin_note = " (Backtest data only - margin not available in live data)" if data_source == "Live Data" else ""
            ui.section_header("Margin Usage",
                description=f"Daily margin utilization stacked by strategy. This shows how much buying power is being used over time.{margin_note}")

            if data_source == "Live Data":
                st.info("Margin data is only available for backtest data. Switch to Backtest Data to view margin usage.")
            else:
                margin_data = pd.DataFrame(index=full_idx)
                for s in selected_strats:
                    s_df = filt[filt['strategy'] == s]
                    if not s_df.empty:
                        margin_data[s] = calc.generate_daily_margin_series_optimized(s_df).reindex(full_idx, fill_value=0)

                # Calculate total margin and stats
                total_margin = margin_data.sum(axis=1)
                margin_max = total_margin.max()
                margin_avg = total_margin.mean()

                fig_mar = px.area(margin_data, x=margin_data.index, y=margin_data.columns,
                                  color_discrete_sequence=px.colors.qualitative.Prism)
                # Add max and avg margin lines
                fig_mar.add_hline(y=margin_max, line_dash="dash", line_color="red", annotation_text=f"Peak: ${margin_max:,.0f}")
                fig_mar.add_hline(y=margin_avg, line_dash="dot", line_color="green", annotation_text=f"Avg: ${margin_avg:,.0f}")
                fig_mar.update_layout(template="plotly_white", xaxis_title=None, yaxis_title="Margin ($)", height=400, legend=dict(orientation="h", y=-0.2))
                st.plotly_chart(fig_mar, use_container_width=True)

        # --- CORRELATION ---
        with st.container(border=True):
            ui.section_header("Strategy Correlation",
                description="Correlation matrix showing how strategy returns move together. Low or negative correlation indicates diversification benefit.")

            pnl_matrix = pd.DataFrame(index=full_idx)
            for s in selected_strats:
                s_df = filt[filt['strategy'] == s]
                if not s_df.empty:
                    pnl_matrix[s] = s_df.set_index('timestamp').resample('D')['pnl'].sum().reindex(full_idx, fill_value=0)

            if len(selected_strats) > 1 and not pnl_matrix.empty:
                # Truncate column names for better display
                new_cols = []
                seen = {}
                for c in pnl_matrix.columns:
                    trunc = c[:12] + ".." if len(c) > 12 else c
                    if trunc in seen:
                        seen[trunc] += 1
                        trunc = f"{trunc}_{seen[trunc]}"
                    else:
                        seen[trunc] = 0
                    new_cols.append(trunc)
                pnl_matrix.columns = new_cols

                corr = pnl_matrix.corr()
                # RdBu_r: Red=positive correlation (bad for diversification), Blue=negative correlation (good)
                fig_corr = px.imshow(corr, text_auto=".2f", color_continuous_scale="RdBu_r", zmin=-1, zmax=1, aspect="auto")
                fig_corr.update_layout(height=500, margin=dict(l=10, r=10, t=30, b=10))
                st.plotly_chart(fig_corr, use_container_width=True)
                st.caption("Red = positive correlation (less diversification), Blue = negative correlation (better diversification)")
            else:
                st.info("Select multiple strategies to view correlation.")

        # === MONTHLY RETURNS TABLE ===
        with st.container(border=True):
            ui.section_header("Monthly Returns",
                description="Month-by-month P/L breakdown showing seasonal patterns and yearly totals.")

            filt['Year'] = filt['timestamp'].dt.year
            filt['Month'] = filt['timestamp'].dt.month

            pivot = filt.pivot_table(index='Year', columns='Month', values='pnl', aggfunc='sum').fillna(0)

            import calendar
            pivot.columns = [calendar.month_abbr[c] for c in pivot.columns]
            pivot['TOTAL'] = pivot.sum(axis=1)
            sum_row = pivot.sum()
            pivot.loc['TOTAL'] = sum_row

            st.dataframe(pivot.style.applymap(ui.color_monthly_performance).format("${:,.0f}"), use_container_width=True)

        # === STRATEGY PERFORMANCE TABLE ===
        with st.container(border=True):
            ui.section_header("Strategy Performance",
                description="Individual strategy metrics including P/L, CAGR, drawdown, and margin usage.")

            strat_metrics = []

            for s in selected_strats:
                s_df = filt[filt['strategy'] == s].copy()
                if s_df.empty: continue

                s_pnl = s_df['pnl'].sum()
                lots, lots_per_day = calc.calculate_lots_from_trades(s_df)

                days = (s_df['timestamp'].max() - s_df['timestamp'].min()).days
                days = max(days, 1)
                s_ret = s_pnl / account_size
                s_cagr = (1 + s_ret) ** (365/days) - 1

                s_daily = s_df.set_index('timestamp').resample('D')['pnl'].sum().reindex(full_idx, fill_value=0)
                s_cum = s_daily.cumsum()
                s_peak = s_cum.cummax()
                s_dd_usd = (s_cum - s_peak).min()
                s_max_dd_pct = s_dd_usd / account_size

                s_mar = s_cagr / abs(s_max_dd_pct) if s_max_dd_pct != 0 else 0
                s_mart = s_cagr / (abs(s_dd_usd) / account_size) if s_dd_usd != 0 else 0

                s_margin_series = calc.generate_daily_margin_series_optimized(s_df)
                s_peak_margin = s_margin_series.max() if not s_margin_series.empty else 0

                strat_metrics.append({
                    "Strategy": s,
                    "Contracts/Day": lots_per_day,
                    "P/L": s_pnl,
                    "CAGR": s_cagr,
                    "Max DD ($)": s_dd_usd,
                    "MAR": s_mar,
                    "MART": s_mart,
                    "Peak Margin": s_peak_margin
                })

            perf_df = pd.DataFrame(strat_metrics)

            if not perf_df.empty:
                total_row = {
                    "Strategy": "TOTAL",
                    "Contracts/Day": perf_df["Contracts/Day"].sum(),
                    "P/L": perf_df["P/L"].sum(),
                    "CAGR": m['CAGR'],
                    "Max DD ($)": m['MaxDD_USD'],
                    "MAR": m['MAR'],
                    "MART": m['MART'],
                    "Peak Margin": perf_df["Peak Margin"].max()
                }
                perf_df = pd.concat([perf_df, pd.DataFrame([total_row])], ignore_index=True)
                perf_df['CAGR'] = perf_df['CAGR'] * 100

            st.dataframe(
                perf_df,
                column_config={
                    "P/L": st.column_config.NumberColumn(format="$%.0f"),
                    "CAGR": st.column_config.NumberColumn(format="%.1f%%"),
                    "Max DD ($)": st.column_config.NumberColumn(format="$%.0f"),
                    "MAR": st.column_config.NumberColumn(format="%.2f"),
                    "MART": st.column_config.NumberColumn(format="%.2f"),
                    "Peak Margin": st.column_config.NumberColumn(format="$%.0f"),
                    "Contracts/Day": st.column_config.NumberColumn(format="%.1f")
                },
                use_container_width=True,
                hide_index=True
            )

        # === PERFORMANCE BY WEEKDAY ===
        with st.container(border=True):
            ui.section_header("Performance by Weekday",
                description="P/L distribution across trading days to identify any day-of-week patterns.")

            filt['weekday'] = filt['timestamp'].dt.day_name()
            days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
            filt['weekday'] = pd.Categorical(filt['weekday'], categories=days_order, ordered=True)

            weekday_stats = filt.groupby('weekday', observed=True)['pnl'].agg(['count', 'sum', 'mean']).reset_index()
            weekday_stats.columns = ['Weekday', 'Trades', 'Total P/L', 'Avg P/L']

            col_wd1, col_wd2 = st.columns(2)

            with col_wd1:
                st.dataframe(
                    weekday_stats.style.applymap(ui.color_monthly_performance, subset=['Total P/L', 'Avg P/L']).format({'Total P/L': '${:,.0f}', 'Avg P/L': '${:,.0f}'}),
                    use_container_width=True,
                    hide_index=True
                )

            with col_wd2:
                fig_wd = px.bar(weekday_stats, x='Weekday', y='Total P/L', color='Total P/L', color_continuous_scale='RdYlGn')
                fig_wd.update_layout(template="plotly_white", xaxis_title=None, showlegend=False)
                st.plotly_chart(fig_wd, use_container_width=True)

        # Hide loading overlay after successful render
        placeholder.empty()

    except Exception as e:
        placeholder.empty()
        st.error(f"An error occurred during analysis: {e}")
        import traceback
        st.code(traceback.format_exc())
