import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import calculations as calc
import ui_components as ui

def page_portfolio_analytics(full_df, live_df=None):
    # Header
    st.markdown("<h1>Backtest Portfolio Asset Allocation</h1>", unsafe_allow_html=True)
    
    st.markdown("""
    <div style='color: #4B5563; font-size: 15px; line-height: 1.6; margin-bottom: 20px;'>
        <strong>Portfolio Backtesting Overview</strong><br>
        Analyze and reconstruct the performance of your options strategies. 
        Review detailed risk metrics, drawdowns, and compare against the S&P 500 benchmark.
    </div>
    """, unsafe_allow_html=True)

    # === CONFIGURATION ===
    with st.container(border=True):
        ui.section_header("Configuration")
        
        data_source = "Backtest Data"
        if live_df is not None and not live_df.empty:
            data_source = st.radio("Source:", ["Backtest Data", "Live Data"], horizontal=True)
        
        target_df = live_df if data_source == "Live Data" and live_df is not None else full_df
        if target_df.empty: return

        col_cap, col_date = st.columns(2)
        with col_cap: account_size = st.number_input("Account Size ($)", 100000, 10000000, 100000)
        
        min_ts, max_ts = target_df['timestamp'].min(), target_df['timestamp'].max()
        with col_date:
            dates = st.date_input("Period", [min_ts.date(), max_ts.date()], min_value=min_ts.date(), max_value=max_ts.date())
        
        if len(dates) != 2: return
        
        filt = target_df[(target_df['timestamp'].dt.date >= dates[0]) & (target_df['timestamp'].dt.date <= dates[1])].copy()
    
    # === CALCULATIONS ===
    full_idx = pd.date_range(dates[0], dates[1])
    daily_pnl = filt.set_index('timestamp').resample('D')['pnl'].sum().reindex(full_idx, fill_value=0)
    equity = account_size + daily_pnl.cumsum()
    ret = equity.pct_change().fillna(0)
    
    spx = calc.fetch_spx_benchmark(pd.to_datetime(dates[0]), pd.to_datetime(dates[1]))
    spx_ret = spx.pct_change().fillna(0) if spx is not None else None
    
    # Calculate ALL advanced metrics
    m = calc.calculate_advanced_metrics(ret, filt, spx_ret, account_size)
    
    # Margin Stats
    margin_series = calc.generate_daily_margin_series_optimized(filt).reindex(full_idx, fill_value=0)
    peak_margin = margin_series.max()
    avg_margin = margin_series[margin_series > 0].mean() if not margin_series.empty and (margin_series > 0).any() else 0
    max_margin_pct = (peak_margin / account_size) * 100 if account_size > 0 else 0
    
    # === HIGHLIGHTS (Restored Comprehensive Grid) ===
    with st.container(border=True):
        ui.section_header("Highlights & Key Performance Indicators")
        
        # ROW 1: Primary Return/Risk
        c1, c2, c3, c4, c5, c6 = st.columns(6)
        with c1: ui.render_hero_metric("Total P/L", f"${filt['pnl'].sum():,.0f}", "", "hero-teal")
        with c2: ui.render_hero_metric("CAGR", f"{m['CAGR']:.1%}", f"SPX: {m['SPX_CAGR']:.1%}", "hero-teal")
        with c3: ui.render_hero_metric("Max DD", f"{m['MaxDD']:.1%}", f"${abs(m['MaxDD_USD']):,.0f}", "hero-coral")
        with c4: ui.render_hero_metric("MAR Ratio", f"{m['MAR']:.2f}", "CAGR/MaxDD", "hero-teal" if m['MAR'] > 1 else "hero-neutral")
        with c5: ui.render_hero_metric("Sharpe", f"{m['Sharpe']:.2f}", f"SPX: {m['SPX_Sharpe']:.2f}", "hero-neutral")
        with c6: ui.render_hero_metric("Sortino", f"{m['Sortino']:.2f}", "Downside Risk", "hero-neutral")
        
        st.write("")
        
        # ROW 2: Trade Statistics
        r2c1, r2c2, r2c3, r2c4, r2c5, r2c6 = st.columns(6)
        with r2c1: ui.render_hero_metric("Total Trades", f"{m['Trades']}", "", "hero-neutral")
        with r2c2: ui.render_hero_metric("Win Rate", f"{m['WinRate']:.1%}", "", "hero-neutral")
        with r2c3: ui.render_hero_metric("Profit Factor", f"{m['PF']:.2f}", "", "hero-neutral")
        with r2c4: ui.render_hero_metric("Kelly", f"{m['Kelly']:.1%}", "Optimal Stake", "hero-neutral")
        with r2c5: ui.render_hero_metric("Avg Win", f"${filt[filt['pnl']>0]['pnl'].mean():,.0f}", "", "hero-neutral")
        with r2c6: ui.render_hero_metric("Avg Loss", f"${filt[filt['pnl']<=0]['pnl'].mean():,.0f}", "", "hero-neutral")

        st.write("")

        # ROW 3: Advanced & Risk
        r3c1, r3c2, r3c3, r3c4, r3c5, r3c6 = st.columns(6)
        with r3c1: ui.render_hero_metric("Alpha", f"{m['Alpha']:.1%}", "vs SPX", "hero-neutral")
        with r3c2: ui.render_hero_metric("Beta", f"{m['Beta']:.2f}", "vs SPX", "hero-neutral")
        with r3c3: ui.render_hero_metric("Volatility", f"{m['Vol']:.1%}", f"SPX: {m['SPX_Vol']:.1%}", "hero-neutral")
        with r3c4: ui.render_hero_metric("MART", f"{m['MART']:.2f}", "Risk Adjusted", "hero-neutral")
        with r3c5: ui.render_hero_metric("Peak Margin", f"${peak_margin:,.0f}", f"{max_margin_pct:.0f}% Util", "hero-neutral")
        with r3c6: ui.render_hero_metric("Ret / Margin", f"{m['AvgRetMargin']:.1%}", "Efficiency", "hero-neutral")

        st.write("")
        
        # ROW 4: Streaks
        r4c1, r4c2, r4c3, r4c4 = st.columns(4)
        with r4c1: ui.render_hero_metric("Win Streak", f"{m['WinStreak']}", "Consecutive", "hero-neutral")
        with r4c2: ui.render_hero_metric("Loss Streak", f"{m['LossStreak']}", "Consecutive", "hero-neutral")
        with r4c3: ui.render_hero_metric("Best Trade", f"${filt['pnl'].max():,.0f}", "", "hero-neutral")
        with r4c4: ui.render_hero_metric("Worst Trade", f"${filt['pnl'].min():,.0f}", "", "hero-neutral")

    # === CHARTS ===
    with st.container(border=True):
        ui.section_header("Portfolio Growth")
        
        chart_data = pd.DataFrame(index=equity.index)
        chart_data['Sample Portfolio'] = equity
        
        if spx_ret is not None and len(spx_ret) > 0:
            spx_equity = (1 + spx_ret).cumprod() * account_size
            spx_equity = spx_equity.reindex(equity.index, method='ffill').fillna(account_size)
            chart_data['SPDR S&P 500 ETF'] = spx_equity
        
        fig_growth = px.line(chart_data, x=chart_data.index, y=chart_data.columns, 
                             color_discrete_map={'Sample Portfolio': '#302BFF', 'SPDR S&P 500 ETF': '#34D399'})
        
        fig_growth.update_layout(
            template="plotly_white",
            xaxis_title=None,
            yaxis_title="Portfolio Balance ($)",
            legend=dict(orientation="h", y=-0.2, x=0.5, xanchor="center", title=None),
            hovermode="x unified",
            height=450
        )
        st.plotly_chart(fig_growth, use_container_width=True)
        
        c1, c2 = st.columns(2)
        with c1: st.checkbox("Logarithmic scale")
        with c2: st.checkbox("Inflation adjusted")

    # === STRATEGY BREAKDOWN ===
    with st.container(border=True):
        ui.section_header("Strategy Allocation & Performance")
        
        c_table, c_chart = st.columns([3, 2])
        
        strat_stats = []
        for strat, group in filt.groupby('strategy'):
            s_pnl = group['pnl'].sum()
            s_trades = len(group)
            s_wr = (group['pnl'] > 0).mean()
            strat_stats.append({'Strategy': strat, 'P/L': s_pnl, 'Trades': s_trades, 'Win Rate': s_wr})
        
        if strat_stats:
            df_stats = pd.DataFrame(strat_stats).sort_values('P/L', ascending=False)
            
            with c_table:
                st.dataframe(
                    df_stats,
                    column_config={
                        "P/L": st.column_config.NumberColumn(format="$%d"),
                        "Win Rate": st.column_config.NumberColumn(format="%.1f%%")
                    },
                    use_container_width=True,
                    hide_index=True
                )
            
            with c_chart:
                fig_pie = px.pie(df_stats, values='Trades', names='Strategy', title="Allocation by Trade Count",
                                 color_discrete_sequence=px.colors.qualitative.Prism)
                st.plotly_chart(fig_pie, use_container_width=True)

    # === MONTHLY RETURNS ===
    with st.container(border=True):
        ui.section_header("Monthly Returns Table")
        filt['Year'] = filt['timestamp'].dt.year
        filt['Month'] = filt['timestamp'].dt.month
        pivot = filt.pivot_table(index='Year', columns='Month', values='pnl', aggfunc='sum').fillna(0)
        st.dataframe(pivot.style.applymap(ui.color_monthly_performance).format("${:,.0f}"), use_container_width=True)
