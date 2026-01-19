import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
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
    
    daily_pnl = filt.set_index('timestamp').resample('D')['pnl'].sum()
    full_idx = pd.date_range(dates[0], dates[1])
    daily_pnl = daily_pnl.reindex(full_idx, fill_value=0)
    
    equity = account_size + daily_pnl.cumsum()
    ret = equity.pct_change().fillna(0)
    
    spx = calc.fetch_spx_benchmark(pd.to_datetime(dates[0]), pd.to_datetime(dates[1]))
    spx_ret = spx.pct_change().fillna(0) if spx is not None else None
    
    m = calc.calculate_advanced_metrics(ret, filt, spx_ret, account_size)
    
    # KPI Grid
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    with c1: ui.render_hero_metric("Total P/L", f"${filt['pnl'].sum():,.0f}", color_class="hero-teal")
    with c2: ui.render_hero_metric("CAGR", f"{m['CAGR']:.1%}", color_class="hero-teal")
    with c3: ui.render_hero_metric("Max DD", f"{m['MaxDD']:.1%}", color_class="hero-coral")
    with c4: ui.render_hero_metric("Sharpe", f"{m['Sharpe']:.2f}")
    with c5: ui.render_hero_metric("MAR", f"{m['MAR']:.2f}")
    with c6: ui.render_hero_metric("Trades", f"{len(filt)}")
    
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
    st.dataframe(pivot.style.applymap(ui.color_monthly_performance).format("${:,.0f}"), use_container_width=True)
