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
    # We display the overlay using a placeholder, run calcs, then remove it
    placeholder = st.empty()
    with placeholder:
        ui.show_loading_overlay("Calculating Analytics", "Crunching numbers for Portfolio Analysis...")
    
    # Allow UI to render the overlay before blocking computation
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

        # === CONFIGURATION ===
        with st.container(border=True):
            ui.section_header("Configuration")
            
            data_source = "Backtest Data"
            if live_df is not None and not live_df.empty:
                data_source = st.radio("Source:", ["Backtest Data", "Live Data"], horizontal=True)
            
            target_df = live_df if data_source == "Live Data" and live_df is not None else full_df
            if target_df.empty: 
                placeholder.empty()
                return

            col_cap, col_date = st.columns(2)
            with col_cap: account_size = st.number_input("Account Size ($)", 100000, 10000000, 100000)
            
            min_ts, max_ts = target_df['timestamp'].min(), target_df['timestamp'].max()
            with col_date:
                dates = st.date_input("Period", [min_ts.date(), max_ts.date()], min_value=min_ts.date(), max_value=max_ts.date())
            
            if len(dates) != 2: 
                placeholder.empty()
                return
            
            # Global Filter
            mask = (target_df['timestamp'].dt.date >= dates[0]) & (target_df['timestamp'].dt.date <= dates[1])
            filt = target_df[mask].copy()

        # === CALCULATIONS ===
        daily_pnl = filt.set_index('timestamp').resample('D')['pnl'].sum()
        full_idx = pd.date_range(dates[0], dates[1])
        daily_pnl = daily_pnl.reindex(full_idx, fill_value=0)
        
        equity = account_size + daily_pnl.cumsum()
        ret = equity.pct_change().fillna(0)
        
        spx = calc.fetch_spx_benchmark(pd.to_datetime(dates[0]), pd.to_datetime(dates[1]))
        spx_ret = spx.pct_change().fillna(0) if spx is not None else None
        
        m = calc.calculate_advanced_metrics(ret, filt, spx_ret, account_size)
        
        # === KPI HIGHLIGHTS (All Returned) ===
        # Row 1: High Level
        with st.container(border=True):
            ui.section_header("Highlights")
            k1, k2, k3, k4, k5, k6 = st.columns(6)
            with k1: ui.render_hero_metric("Total P/L", f"${filt['pnl'].sum():,.0f}", "", "hero-teal" if filt['pnl'].sum() > 0 else "hero-coral")
            with k2: ui.render_hero_metric("CAGR", f"{m['CAGR']:.1%}", "", "hero-teal" if m['CAGR'] > 0 else "hero-coral")
            with k3: ui.render_hero_metric("Max DD (%)", f"{m['MaxDD']:.1%}", "", "hero-coral")
            with k4: ui.render_hero_metric("Max DD ($)", f"${abs(m['MaxDD_USD']):,.0f}", "", "hero-coral")
            with k5: ui.render_hero_metric("MAR Ratio", f"{m['MAR']:.2f}", "", "hero-teal" if m['MAR'] > 1 else "hero-neutral")
            with k6: ui.render_hero_metric("MART Ratio", f"{m['MART']:.2f}", "", "hero-teal" if m['MART'] > 5 else "hero-neutral")
        
        # Row 2: Stats
        with st.container(border=True):
            ui.section_header("Statistics")
            r2k1, r2k2, r2k3, r2k4, r2k5, r2k6 = st.columns(6)
            with r2k1: ui.render_hero_metric("Sharpe", f"{m['Sharpe']:.2f}", "", "hero-neutral")
            with r2k2: ui.render_hero_metric("Sortino", f"{m['Sortino']:.2f}", "", "hero-neutral")
            with r2k3: ui.render_hero_metric("Win Rate", f"{m['WinRate']:.1%}", f"{m['Trades']} Trades", "hero-neutral")
            with r2k4: ui.render_hero_metric("Profit Factor", f"{m['PF']:.2f}", "", "hero-neutral")
            with r2k5: ui.render_hero_metric("Alpha", f"{m['Alpha']:.1%}", "", "hero-neutral")
            with r2k6: ui.render_hero_metric("Beta", f"{m['Beta']:.2f}", "", "hero-neutral")

        # === CHARTS SECTION (Full Width Stacked) ===
        st.write("")
        all_strategies = sorted(filt['strategy'].unique())
        
        # Strategy Filter for Charts
        selected_strats = st.multiselect("Filter Charts by Strategy", all_strategies, default=all_strategies)
        
        if not selected_strats:
            st.warning("Please select at least one strategy.")
        else:
            # --- EQUITY ---
            with st.container(border=True):
                ui.section_header("Equity Curve")
                
                eq_data = pd.DataFrame(index=full_idx)
                for s in selected_strats:
                    s_df = filt[filt['strategy'] == s]
                    s_pnl = s_df.set_index('timestamp').resample('D')['pnl'].sum().reindex(full_idx, fill_value=0)
                    eq_data[s] = s_pnl.cumsum()
                
                eq_data['Total Portfolio'] = eq_data.sum(axis=1)
                
                fig_eq = px.line(eq_data, x=eq_data.index, y=eq_data.columns, 
                                 color_discrete_sequence=px.colors.qualitative.Prism)
                fig_eq.update_layout(template="plotly_white", xaxis_title=None, yaxis_title="Cumulative P/L ($)", height=500, legend=dict(orientation="h", y=-0.2))
                st.plotly_chart(fig_eq, use_container_width=True)

            # --- MARGIN ---
            with st.container(border=True):
                ui.section_header("Margin Usage")
                
                margin_data = pd.DataFrame(index=full_idx)
                for s in selected_strats:
                    s_df = filt[filt['strategy'] == s]
                    margin_data[s] = calc.generate_daily_margin_series_optimized(s_df).reindex(full_idx, fill_value=0)
                    
                fig_mar = px.area(margin_data, x=margin_data.index, y=margin_data.columns, 
                                  color_discrete_sequence=px.colors.qualitative.Prism)
                fig_mar.update_layout(template="plotly_white", xaxis_title=None, yaxis_title="Margin ($)", height=400, legend=dict(orientation="h", y=-0.2))
                st.plotly_chart(fig_mar, use_container_width=True)

            # --- CORRELATION (Bigger, Truncated) ---
            with st.container(border=True):
                ui.section_header("Strategy Correlation")
                
                pnl_matrix = pd.DataFrame(index=full_idx)
                for s in selected_strats:
                    s_df = filt[filt['strategy'] == s]
                    pnl_matrix[s] = s_df.set_index('timestamp').resample('D')['pnl'].sum().reindex(full_idx, fill_value=0)
                
                if len(selected_strats) > 1:
                    # Truncate column names for cleaner heatmap
                    pnl_matrix.columns = [c[:15] + ".." if len(c) > 15 else c for c in pnl_matrix.columns]
                    
                    corr = pnl_matrix.corr()
                    fig_corr = px.imshow(corr, text_auto=".2f", color_continuous_scale="RdBu", zmin=-1, zmax=1, aspect="auto")
                    fig_corr.update_layout(height=600) # Bigger
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
            
            for s in all_strategies:
                s_df = filt[filt['strategy'] == s].copy()
                
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
            
            st.dataframe(
                perf_df,
                column_config={
                    "P/L": st.column_config.NumberColumn(format="$%.0f"),
                    "CAGR": st.column_config.NumberColumn(format="%.1%"), # Fixed % format
                    "Max DD ($)": st.column_config.NumberColumn(format="$%.0f"),
                    "MAR": st.column_config.NumberColumn(format="%.2f"),
                    "MART": st.column_config.NumberColumn(format="%.2f"),
                    "Peak Margin": st.column_config.NumberColumn(format="$%.0f"),
                    "Contracts/Day": st.column_config.NumberColumn(format="%.1f")
                },
                use_container_width=True,
                hide_index=True
            )
        
        # Hide loading overlay after successful render
        placeholder.empty()

    except Exception as e:
        placeholder.empty()
        st.error(f"An error occurred during analysis: {e}")
