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
    
    # Calculate margin stats for display
    margin_series = calc.generate_daily_margin_series_optimized(filt).reindex(full_idx, fill_value=0)
    peak_margin = margin_series.max()
    avg_margin = margin_series[margin_series > 0].mean() if not margin_series.empty and (margin_series > 0).any() else 0
    max_margin_pct = (peak_margin / account_size) * 100 if account_size > 0 else 0
    avg_margin_pct = (avg_margin / account_size) * 100 if account_size > 0 else 0
    
    spx_pnl_equivalent = account_size * m['SPX_TotalRet'] if m['SPX_TotalRet'] != 0 else 0
    
    # === KPI GRID ===
    st.markdown("### 📊 Key Performance Indicators")
    
    # ROW 1: Primary metrics with colors AND SPX comparisons
    r1c1, r1c2, r1c3, r1c4, r1c5, r1c6 = st.columns(6)
    with r1c1:
        spx_txt = f"SPX: ${spx_pnl_equivalent:,.0f}" if spx_pnl_equivalent != 0 else ""
        ui.render_hero_metric("Total P/L", f"${filt['pnl'].sum():,.0f}", spx_txt, "hero-teal")
    with r1c2:
        spx_txt = f"SPX: {m['SPX_CAGR']:.1%}" if m['SPX_CAGR'] != 0 else ""
        ui.render_hero_metric("CAGR", f"{m['CAGR']:.1%}", spx_txt, "hero-teal")
    with r1c3:
        spx_txt = f"SPX: {m['SPX_MaxDD']:.1%}" if m['SPX_MaxDD'] != 0 else ""
        ui.render_hero_metric("Max DD (%)", f"{m['MaxDD']:.1%}", spx_txt, "hero-coral")
    with r1c4:
        spx_dd_usd = account_size * abs(m['SPX_MaxDD']) if m['SPX_MaxDD'] != 0 else 0
        spx_txt = f"SPX: ${spx_dd_usd:,.0f}" if spx_dd_usd != 0 else ""
        ui.render_hero_metric("Max DD ($)", f"${abs(m['MaxDD_USD']):,.0f}", spx_txt, "hero-coral")
    with r1c5:
        spx_mar = m['SPX_CAGR'] / abs(m['SPX_MaxDD']) if m['SPX_MaxDD'] != 0 else 0
        spx_txt = f"SPX: {spx_mar:.2f}" if spx_mar != 0 else ""
        ui.render_hero_metric("MAR Ratio", f"{m['MAR']:.2f}", spx_txt, "hero-teal")
    with r1c6:
        ui.render_hero_metric("MART Ratio", f"{m['MART']:.2f}", "", "hero-teal")

    st.write("")

    # ROW 2: Secondary metrics (neutral)
    r2c1, r2c2, r2c3, r2c4, r2c5, r2c6 = st.columns(6)
    with r2c1: ui.render_hero_metric("Total Trades", f"{m['Trades']}", "", "hero-neutral")
    with r2c2: ui.render_hero_metric("Win Rate", f"{m['WinRate']:.1%}", "", "hero-neutral")
    with r2c3: ui.render_hero_metric("Profit Factor", f"{m['PF']:.2f}", "", "hero-neutral")
    with r2c4: 
        spx_txt = f"SPX: {m['SPX_Sharpe']:.2f}" if m['SPX_Sharpe'] != 0 else ""
        ui.render_hero_metric("Sharpe", f"{m['Sharpe']:.2f}", spx_txt, "hero-neutral")
    with r2c5: ui.render_hero_metric("Sortino", f"{m['Sortino']:.2f}", "", "hero-neutral")
    with r2c6: 
        spx_txt = f"SPX: {m['SPX_Vol']:.1%}" if m['SPX_Vol'] != 0 else ""
        ui.render_hero_metric("Volatility", f"{m['Vol']:.1%}", spx_txt, "hero-neutral")

    st.write("")

    # ROW 3: More metrics
    r3c1, r3c2, r3c3, r3c4, r3c5, r3c6 = st.columns(6)
    with r3c1: ui.render_hero_metric("Alpha (vs SPX)", f"{m['Alpha']:.1%}", "", "hero-neutral")
    with r3c2: ui.render_hero_metric("Beta (vs SPX)", f"{m['Beta']:.2f}", "", "hero-neutral")
    with r3c3: ui.render_hero_metric("Avg Ret/Marg", f"{m['AvgRetMargin']:.1%}", "", "hero-neutral")
    with r3c4: ui.render_hero_metric("Kelly", f"{m['Kelly']:.1%}", "", "hero-neutral")
    with r3c5: ui.render_hero_metric("Peak Margin", f"${peak_margin:,.0f}", f"{max_margin_pct:.0f}%", "hero-neutral")
    with r3c6: ui.render_hero_metric("Avg Margin", f"${avg_margin:,.0f}", f"{avg_margin_pct:.0f}%", "hero-neutral")

    st.write("")

    # ROW 4: Streak metrics
    r4c1, r4c2, r4c3, r4c4, r4c5 = st.columns(5)
    with r4c1: ui.render_hero_metric("Win Streak", f"{m['WinStreak']}", "", "hero-neutral")
    with r4c2: ui.render_hero_metric("Loss Streak", f"{m['LossStreak']}", "", "hero-neutral")
    with r4c3: 
        avg_win = filt[filt['pnl'] > 0]['pnl'].mean() if len(filt[filt['pnl'] > 0]) > 0 else 0
        ui.render_hero_metric("Avg Win", f"${avg_win:,.0f}", "", "hero-neutral")
    with r4c4: 
        avg_loss = filt[filt['pnl'] <= 0]['pnl'].mean() if len(filt[filt['pnl'] <= 0]) > 0 else 0
        ui.render_hero_metric("Avg Loss", f"${avg_loss:,.0f}", "", "hero-neutral")
    with r4c5:
        best = filt['pnl'].max() if not filt.empty else 0
        worst = filt['pnl'].min() if not filt.empty else 0
        ui.render_hero_metric("Best/Worst", f"${best:,.0f} / ${worst:,.0f}", "", "hero-neutral")
    
    st.divider()
    
    # === EQUITY & MARGIN ===
    st.markdown("### 📈 Equity & Margin")
    
    tab_eq, tab_marg = st.tabs(["Equity Curve", "Margin Usage"])
    
    with tab_eq:
        fig_eq = px.area(x=equity.index, y=equity.values, title="Equity Curve")
        fig_eq.add_hline(y=account_size, line_dash="dash", line_color="gray")
        st.plotly_chart(fig_eq, use_container_width=True)
        
    with tab_marg:
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
