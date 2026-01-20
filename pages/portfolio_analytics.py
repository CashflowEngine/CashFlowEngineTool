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
        # Header
        st.markdown("<h1>PORTFOLIO ANALYTICS</h1>", unsafe_allow_html=True)
        
        st.markdown("""
        <div style='color: #4B5563; font-size: 14px; line-height: 1.5; margin-bottom: 20px;'>
            <strong>Comprehensive Portfolio Analysis (Backtest & Live)</strong><br>
            Analyze and reconstruct the performance of your options strategies using both backtest data and actual live execution logs.
        </div>
        """, unsafe_allow_html=True)

        # === CONFIGURATION (FILTER AT TOP) ===
        with st.container(border=True):
            ui.section_header("Configuration")
            
            # Data Source Selection
            data_source = "Backtest Data"
            if live_df is not None and not live_df.empty:
                data_source = st.radio("Source:", ["Backtest Data", "Live Data"], horizontal=True)
            
            target_df = live_df if data_source == "Live Data" and live_df is not None else full_df
            if target_df.empty: 
                placeholder.empty()
                st.warning("No data available.")
                return

            col_cap, col_date = st.columns(2)
            with col_cap: account_size = st.number_input("Account Size ($)", 100000, 10000000, 100000)
            
            min_ts, max_ts = target_df['timestamp'].min(), target_df['timestamp'].max()
            with col_date:
                dates = st.date_input("Period", [min_ts.date(), max_ts.date()], min_value=min_ts.date(), max_value=max_ts.date())
            
            if len(dates) != 2: 
                placeholder.empty()
                return
            
            # Strategy Filter - MOVED TO TOP
            all_strategies = sorted(target_df['strategy'].unique())
            selected_strats = st.multiselect("Filter Strategies", all_strategies, default=all_strategies)
            
            # Apply Filter
            mask = (target_df['timestamp'].dt.date >= dates[0]) & (target_df['timestamp'].dt.date <= dates[1])
            if selected_strats:
                mask = mask & (target_df['strategy'].isin(selected_strats))
            else:
                st.warning("Please select at least one strategy.")
                placeholder.empty()
                return
                
            filt = target_df[mask].copy()

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
        if spx is not None:
            # STRICT FILTERING: Match the exact selected dates to prevent buffer distortion
            spx.index = pd.to_datetime(spx.index)
            # Filter to selected dates
            spx_filtered = spx[(spx.index.date >= dates[0]) & (spx.index.date <= dates[1])]
            
            # Calculate returns on the filtered series
            if not spx_filtered.empty:
                spx_ret = spx_filtered.pct_change().fillna(0)
                spx_equity_source = spx_filtered
            else:
                spx_ret = None
                spx_equity_source = None
        else:
            spx_ret = None
            spx_equity_source = None
        
        m = calc.calculate_advanced_metrics(ret, filt, spx_ret, account_size)
        
        # Calculate Peak/Mean Margin for KPI display
        margin_series = calc.generate_daily_margin_series_optimized(filt)
        peak_margin = margin_series.max() if not margin_series.empty else 0
        avg_margin = margin_series.mean() if not margin_series.empty else 0
        
        # === KPI HIGHLIGHTS (Replicated 3x6 Grid from Screenshot) ===
        # Row 1: The Cyan Headers
        r1c1, r1c2, r1c3, r1c4, r1c5, r1c6 = st.columns(6)
        with r1c1: ui.render_hero_metric("Total P/L", f"${filt['pnl'].sum():,.0f}", f"SPX: ${m['SPX_TotalPnL_USD']:,.0f}", "hero-cyan")
        with r1c2: ui.render_hero_metric("CAGR", f"{m['CAGR']:.1%}", f"SPX: {m['SPX_CAGR']:.1%}", "hero-cyan")
        with r1c3: ui.render_hero_metric("Max DD (%)", f"{m['MaxDD']:.1%}", f"SPX: {m['SPX_MaxDD']:.1%}", "hero-red")
        with r1c4: ui.render_hero_metric("Max DD ($)", f"${abs(m['MaxDD_USD']):,.0f}", "", "hero-red")
        with r1c5: ui.render_hero_metric("MAR Ratio", f"{m['MAR']:.2f}", f"SPX: {abs(m['SPX_CAGR'] / m['SPX_MaxDD']) if m['SPX_MaxDD'] != 0 else 0:.2f}", "hero-cyan")
        with r1c6: ui.render_hero_metric("MART Ratio", f"{m['MART']:.2f}", "", "hero-cyan")
        
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
        
        # Row 3: Advanced & Streak
        r3c1, r3c2, r3c3, r3c4, r3c5, r3c6 = st.columns(6)
        with r3c1: ui.render_hero_metric("Alpha (vs SPX)", f"{m['Alpha']:.1%}", "Excess return", "hero-neutral")
        with r3c2: ui.render_hero_metric("Beta (vs SPX)", f"{m['Beta']:.2f}", "Market sensitivity", "hero-neutral")
        with r3c3: ui.render_hero_metric("Avg Ret/Marg", f"{m['AvgRetMargin']:.1%}", "", "hero-neutral")
        with r3c4: ui.render_hero_metric("Kelly", f"{m['Kelly']:.1%}", "", "hero-neutral")
        with r3c5: ui.render_hero_metric("Peak Margin", f"${peak_margin:,.0f}", f"{peak_margin/account_size:.0%} of Account", "hero-neutral")
        with r3c6: ui.render_hero_metric("Avg Margin", f"${avg_margin:,.0f}", f"{avg_margin/account_size:.0%} of Account", "hero-neutral")
        
        st.write("")
        
        # Row 4: Streaks (Optional but good for layout balancing)
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

        # === CHARTS SECTION (Full Width Stacked) ===
        st.write("")
        
        # --- EQUITY ---
        with st.container(border=True):
            ui.section_header("Equity Curve")
            
            eq_data = pd.DataFrame(index=full_idx)
            # Breakdown by Strategy (safe unique naming)
            for i, s in enumerate(selected_strats):
                s_df = filt[filt['strategy'] == s]
                if not s_df.empty:
                    s_pnl = s_df.set_index('timestamp').resample('D')['pnl'].sum().reindex(full_idx, fill_value=0)
                    eq_data[s] = s_pnl.cumsum()
            
            eq_data['Total Portfolio'] = eq_data.sum(axis=1)
            
            fig_eq = px.line(eq_data, x=eq_data.index, y=eq_data.columns, 
                             color_discrete_sequence=px.colors.qualitative.Prism)
            
            # ADD SPX BENCHMARK (FIXED NORMALIZATION)
            if spx_ret is not None and spx_equity_source is not None:
                # Calculate SPX Cumulative Return relative to the start of the period
                spx_cumulative_return = (1 + spx_ret).cumprod() - 1
                
                # Align SPX curve to Portfolio PnL scale (Dollars)
                # Formula: Invested Capital * Cumulative Return
                spx_pnl_curve = account_size * spx_cumulative_return
                
                fig_eq.add_trace(go.Scatter(x=spx_ret.index, y=spx_pnl_curve, name="SPX Benchmark (Rel)", line=dict(color='gray', dash='dot')))

            fig_eq.update_layout(template="plotly_white", xaxis_title=None, yaxis_title="Cumulative P/L ($)", height=500, legend=dict(orientation="h", y=-0.2))
            st.plotly_chart(fig_eq, use_container_width=True)

        # --- MARGIN ---
        with st.container(border=True):
            ui.section_header("Margin Usage")
            
            margin_data = pd.DataFrame(index=full_idx)
            for s in selected_strats:
                s_df = filt[filt['strategy'] == s]
                if not s_df.empty:
                    margin_data[s] = calc.generate_daily_margin_series_optimized(s_df).reindex(full_idx, fill_value=0)
                
            fig_mar = px.area(margin_data, x=margin_data.index, y=margin_data.columns, 
                              color_discrete_sequence=px.colors.qualitative.Prism)
            fig_mar.update_layout(template="plotly_white", xaxis_title=None, yaxis_title="Margin ($)", height=400, legend=dict(orientation="h", y=-0.2))
            st.plotly_chart(fig_mar, use_container_width=True)

        # --- CORRELATION ---
        with st.container(border=True):
            ui.section_header("Strategy Correlation")
            
            pnl_matrix = pd.DataFrame(index=full_idx)
            for s in selected_strats:
                s_df = filt[filt['strategy'] == s]
                if not s_df.empty:
                    pnl_matrix[s] = s_df.set_index('timestamp').resample('D')['pnl'].sum().reindex(full_idx, fill_value=0)
            
            if len(selected_strats) > 1 and not pnl_matrix.empty:
                new_cols = []
                seen = {}
                for c in pnl_matrix.columns:
                    trunc = c[:15] + ".." if len(c) > 15 else c
                    if trunc in seen:
                        seen[trunc] += 1
                        trunc = f"{trunc}_{seen[trunc]}"
                    else:
                        seen[trunc] = 0
                    new_cols.append(trunc)
                pnl_matrix.columns = new_cols
                
                corr = pnl_matrix.corr()
                fig_corr = px.imshow(corr, text_auto=".2f", color_continuous_scale="RdBu", zmin=-1, zmax=1, aspect="auto")
                fig_corr.update_layout(height=600)
                st.plotly_chart(fig_corr, use_container_width=True)
            else:
                st.info("Select multiple strategies to view correlation.")

        # === MONTHLY RETURNS TABLE ===
        with st.container(border=True):
            ui.section_header("Monthly Returns")
            
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
            ui.section_header("Strategy Performance")
            
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
                    "CAGR": s_cagr,  # Keep as float here
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
                
                # Multiply CAGR by 100 for proper display with %.1f%% format
                perf_df['CAGR'] = perf_df['CAGR'] * 100
            
            st.dataframe(
                perf_df,
                column_config={
                    "P/L": st.column_config.NumberColumn(format="$%.0f"),
                    "CAGR": st.column_config.NumberColumn(format="%.1f%%"), # Now using 100-based scale
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
            ui.section_header("Performance by Weekday")
            
            # Prepare data
            filt['weekday'] = filt['timestamp'].dt.day_name()
            # Sort order
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
