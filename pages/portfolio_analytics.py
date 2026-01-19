import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import calculations as calc
import ui_components as ui

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
    
    full_idx = pd.date_range(dates[0], dates[1])
    daily_pnl = filt.set_index('timestamp').resample('D')['pnl'].sum().reindex(full_idx, fill_value=0)
    
    equity = account_size + daily_pnl.cumsum()
    ret = equity.pct_change().fillna(0)
    
    spx = calc.fetch_spx_benchmark(pd.to_datetime(dates[0]), pd.to_datetime(dates[1]))
    spx_ret = spx.pct_change().fillna(0) if spx is not None else None
    
    m = calc.calculate_advanced_metrics(ret, filt, spx_ret, account_size)
    
    # === KPI GRID ===
    st.markdown("### 📊 Key Performance Indicators")
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    with c1: ui.render_hero_metric("Total P/L", f"${filt['pnl'].sum():,.0f}", color_class="hero-teal")
    with c2: ui.render_hero_metric("CAGR", f"{m['CAGR']:.1%}", color_class="hero-teal")
    with c3: ui.render_hero_metric("Max DD", f"{m['MaxDD']:.1%}", color_class="hero-coral")
    with c4: ui.render_hero_metric("Sharpe", f"{m['Sharpe']:.2f}")
    with c5: ui.render_hero_metric("MAR", f"{m['MAR']:.2f}")
    with c6: ui.render_hero_metric("Trades", f"{len(filt)}")
    
    st.divider()
    
    # === EQUITY & MARGIN ===
    st.markdown("### 📈 Equity & Margin")
    
    tab_eq, tab_marg = st.tabs(["Equity Curve", "Margin Usage"])
    
    with tab_eq:
        fig_eq = px.area(x=equity.index, y=equity.values, title="Equity Curve")
        fig_eq.add_hline(y=account_size, line_dash="dash", line_color="gray")
        st.plotly_chart(fig_eq, use_container_width=True)
        
    with tab_marg:
        # Calculate daily margin
        margin_series = calc.generate_daily_margin_series_optimized(filt).reindex(full_idx, fill_value=0)
        peak_margin = margin_series.max()
        
        fig_marg = px.area(x=margin_series.index, y=margin_series.values, title=f"Margin Usage (Peak: ${peak_margin:,.0f})")
        fig_marg.update_traces(line_color=ui.COLOR_PURPLE)
        st.plotly_chart(fig_marg, use_container_width=True)

    st.divider()
    
    # === STRATEGY BREAKDOWN ===
    st.markdown("### 🧬 Strategy Breakdown")
    
    strat_stats = []
    for strat, group in filt.groupby('strategy'):
        s_pnl = group['pnl'].sum()
        s_trades = len(group)
        s_wr = (group['pnl'] > 0).mean()
        strat_stats.append({'Strategy': strat, 'P/L': s_pnl, 'Trades': s_trades, 'Win Rate': s_wr})
    
    if strat_stats:
        df_stats = pd.DataFrame(strat_stats).sort_values('P/L', ascending=False)
        st.dataframe(df_stats.style.format({'P/L': '${:,.0f}', 'Win Rate': '{:.1%}'}), use_container_width=True)

    st.divider()

    # === MONTHLY RETURNS ===
    st.markdown("### 📅 Monthly Performance")
    filt['Year'] = filt['timestamp'].dt.year
    filt['Month'] = filt['timestamp'].dt.month
    pivot = filt.pivot_table(index='Year', columns='Month', values='pnl', aggfunc='sum').fillna(0)
    st.dataframe(pivot.style.applymap(ui.color_monthly_performance).format("${:,.0f}"), use_container_width=True)
    
    st.divider()
    
    # === DAY OF WEEK ANALYSIS ===
    c_day, c_chart = st.columns(2)
    with c_day:
        st.markdown("### Day of Week Analysis")
        filt['Day'] = filt['timestamp'].dt.day_name()
        days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
        day_stats = filt.groupby('Day')['pnl'].agg(['sum', 'count', 'mean'])
        day_stats = day_stats.reindex(days_order).dropna()
        day_stats.columns = ['Total P/L', 'Trades', 'Avg P/L']
        st.dataframe(day_stats.style.format({'Total P/L': "${:,.0f}", 'Avg P/L': "${:,.0f}"}), use_container_width=True)

    with c_chart:
        fig_days = px.bar(day_stats, x=day_stats.index, y='Total P/L', title="PnL by Weekday", template="plotly_white")
        st.plotly_chart(fig_days, use_container_width=True)
