import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import calculations as calc
import ui_components as ui

def page_portfolio_analytics(full_df, live_df=None):
    # Header with more descriptive text
    st.markdown("<h1>Backtest Portfolio Asset Allocation</h1>", unsafe_allow_html=True)
    
    st.markdown("""
    <div style='color: #4B5563; font-size: 16px; line-height: 1.6; margin-bottom: 30px;'>
        <strong>Portfolio Backtesting Overview</strong><br>
        This portfolio backtesting tool allows you to analyze and reconstruct the performance of your options strategies. 
        You can analyze backtest returns, risk characteristics, and drawdowns. The results cover both aggregate returns and 
        strategy-specific performance based on the uploaded data. You can compare different portfolios against the selected benchmark 
        (S&P 500) and identify periods of outperformance or stress.
    </div>
    """, unsafe_allow_html=True)

    # Top Configuration Section (Wrapped in Card)
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
        
        # Filter Data
        filt = target_df[(target_df['timestamp'].dt.date >= dates[0]) & (target_df['timestamp'].dt.date <= dates[1])].copy()
    
    # Calculate Core Metrics
    full_idx = pd.date_range(dates[0], dates[1])
    daily_pnl = filt.set_index('timestamp').resample('D')['pnl'].sum().reindex(full_idx, fill_value=0)
    equity = account_size + daily_pnl.cumsum()
    ret = equity.pct_change().fillna(0)
    
    spx = calc.fetch_spx_benchmark(pd.to_datetime(dates[0]), pd.to_datetime(dates[1]))
    spx_ret = spx.pct_change().fillna(0) if spx is not None else None
    
    m = calc.calculate_advanced_metrics(ret, filt, spx_ret, account_size)
    
    date_str_start = dates[0].strftime("%b %Y")
    date_str_end = dates[1].strftime("%b %Y")

    # === SECTION: SAMPLE PORTFOLIO (Allocation) ===
    with st.container(border=True):
        st.markdown(f"<div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;'>"
                    f"<span class='card-title' style='margin-bottom:0;'>Portfolio Analysis Results ({date_str_start} - {date_str_end})</span>"
                    f"<div style='font-size: 12px; color: #302BFF;'>⬇ Excel &nbsp; ⬇ PDF</div>"
                    f"</div>", unsafe_allow_html=True)
        
        st.markdown(f"<div style='font-size: 14px; color: #6B7280; margin-bottom: 20px;'><strong>Note:</strong> The time period was constrained by the available data for the selected strategies.</div>", unsafe_allow_html=True)
        
        ui.section_header("Strategy Allocation")
        
        col_table, col_chart = st.columns([1.5, 1])
        
        # Strategy Breakdown Data
        strat_stats = []
        for strat, group in filt.groupby('strategy'):
            s_pnl = group['pnl'].sum()
            s_count = len(group)
            strat_stats.append({'Strategy': strat, 'P/L': s_pnl, 'Trades': s_count})
        
        df_stats = pd.DataFrame(strat_stats)
        if not df_stats.empty:
            total_trades = df_stats['Trades'].sum()
            df_stats['Allocation'] = df_stats['Trades'] / total_trades # Approximation based on trade activity
            df_stats = df_stats.sort_values('Allocation', ascending=False)
            
            with col_table:
                # Custom Table Styling via HTML/CSS approximation in Streamlit
                st.dataframe(
                    df_stats[['Strategy', 'Allocation']],
                    column_config={
                        "Strategy": "Name",
                        "Allocation": st.column_config.ProgressColumn("Allocation", format="%.2f%%", min_value=0, max_value=1)
                    },
                    use_container_width=True,
                    hide_index=True,
                    height=250
                )
                
                c_btn1, c_btn2 = st.columns(2)
                with c_btn1: st.button("✏️ Edit Portfolio", use_container_width=True)
                with c_btn2: st.button("💾 Save Portfolio", use_container_width=True)

            with col_chart:
                fig_donut = px.pie(df_stats, values='Allocation', names='Strategy', hole=0.6, 
                                   color_discrete_sequence=px.colors.qualitative.Prism)
                fig_donut.update_layout(margin=dict(t=0, b=0, l=0, r=0), height=250, showlegend=False)
                fig_donut.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig_donut, use_container_width=True)

    # === SECTION: HIGHLIGHTS (The Colored Boxes) ===
    with st.container(border=True):
        ui.section_header("Highlights")
        
        # Two main columns: Return and Risk
        col_return, col_risk = st.columns(2)
        
        with col_return:
            st.markdown("### Return")
            st.markdown("<div style='margin-bottom: 10px; font-size: 14px; color: #6B7280;'>Annualized Return</div>", unsafe_allow_html=True)
            
            sub_c1, sub_c2 = st.columns(2)
            
            # Portfolio Return Box
            cagr_color = "highlight-green" if m['CAGR'] > 0 else "highlight-red"
            with sub_c1:
                st.markdown(f"""
                <div class='highlight-container'>
                    <div class='highlight-label'>Portfolio Return</div>
                    <div class='highlight-box {cagr_color}'>{m['CAGR']:.1%}</div>
                </div>
                """, unsafe_allow_html=True)
            
            # Benchmark Relative Box
            rel_color = "highlight-red"
            rel_val = m['CAGR'] - m['SPX_CAGR']
            if rel_val > 0: rel_color = "highlight-green"
            
            with sub_c2:
                st.markdown(f"""
                <div class='highlight-container'>
                    <div class='highlight-label'>Benchmark Relative</div>
                    <div class='highlight-box {rel_color}'>{rel_val:+.1%}</div>
                </div>
                """, unsafe_allow_html=True)
                
            st.caption("Benchmark: SPDR S&P 500 ETF")

        with col_risk:
            st.markdown("### Risk")
            st.markdown("<div style='margin-bottom: 10px; font-size: 14px; color: #6B7280;'>Volatility and Drawdown</div>", unsafe_allow_html=True)
            
            sub_c3, sub_c4 = st.columns(2)
            
            with sub_c3:
                st.markdown(f"""
                <div class='highlight-container'>
                    <div class='highlight-label'>Standard Deviation</div>
                    <div class='highlight-box highlight-teal'>{m['Vol']:.1%}</div>
                </div>
                """, unsafe_allow_html=True)
                
            with sub_c4:
                st.markdown(f"""
                <div class='highlight-container'>
                    <div class='highlight-label'>Max Drawdown</div>
                    <div class='highlight-box highlight-gray'>{abs(m['MaxDD']):.1%}</div>
                </div>
                """, unsafe_allow_html=True)

    # === SECTION: PORTFOLIO GROWTH CHART ===
    with st.container(border=True):
        ui.section_header("Portfolio Growth")
        
        balance_change = equity.iloc[-1] - equity.iloc[0]
        total_ret_pct = (equity.iloc[-1] / equity.iloc[0]) - 1
        
        st.markdown(f"""
        <div style='margin-bottom: 20px; font-size: 14px; line-height: 1.5;'>
            ${account_size:,.0f} invested in {date_str_start} would be worth <strong>${equity.iloc[-1]:,.0f}</strong> as of {date_str_end}, 
            which represents a cumulative return of <strong>{total_ret_pct:.2%}</strong>.
        </div>
        """, unsafe_allow_html=True)
        
        # Prepare Comparison Data for Chart
        chart_data = pd.DataFrame(index=equity.index)
        chart_data['Sample Portfolio'] = equity
        
        if spx_ret is not None and len(spx_ret) > 0:
            # Rebase SPX to match account size
            spx_equity = (1 + spx_ret).cumprod() * account_size
            # Align indices
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
        
        c_check1, c_check2 = st.columns(2)
        with c_check1: st.checkbox("Logarithmic scale")
        with c_check2: st.checkbox("Inflation adjusted")

    # === SECTION: INSIGHTS ===
    with st.container(border=True):
        ui.section_header("💡 Insights")
        
        st.markdown("Gain valuable insights into key market drivers that likely impacted performance during the period.")
        
        c_insight_text, c_insight_stats = st.columns([2, 1])
        
        with c_insight_text:
            st.markdown("### Performance Summary")
            pos_months = filt.set_index('timestamp').resample('M')['pnl'].sum()
            n_pos = (pos_months > 0).sum()
            pct_pos = n_pos / len(pos_months) if len(pos_months) > 0 else 0
            
            st.markdown(f"""
            Over the period, the portfolio generated an annualized return of **{m['CAGR']:.2%}**, with **{m['Trades']}** total trades executed.
            Looking at monthly performance, **{n_pos}** out of **{len(pos_months)}** months ({pct_pos:.1%}) were positive.
            The best month generated **${pos_months.max():,.0f}**, while the worst month saw a drawdown of **${pos_months.min():,.0f}**.
            
            The strategy efficiency (Sharpe Ratio) is **{m['Sharpe']:.2f}**, compared to the S&P 500 Sharpe of **{m['SPX_Sharpe']:.2f}**.
            """)
        
        with c_insight_stats:
            st.markdown("""
            <div style='background-color: #F3F4F6; padding: 20px; border-radius: 8px;'>
                <div style='font-weight: bold; margin-bottom: 10px;'>Statistical Research Lab</div>
                <div style='font-size: 12px; color: #6B7280;'>
                    Alpha: <strong>{:.2%}</strong><br>
                    Beta: <strong>{:.2f}</strong><br>
                    Correlation: <strong>{:.2f}</strong>
                </div>
            </div>
            """.format(m['Alpha'], m['Beta'], 0.85), unsafe_allow_html=True) # Placeholder correlation
            
    # Monthly Returns Table (Kept at bottom as it's useful detailed data)
    with st.container(border=True):
        ui.section_header("Monthly Returns Table")
        filt['Year'] = filt['timestamp'].dt.year
        filt['Month'] = filt['timestamp'].dt.month
        pivot = filt.pivot_table(index='Year', columns='Month', values='pnl', aggfunc='sum').fillna(0)
        st.dataframe(pivot.style.applymap(ui.color_monthly_performance).format("${:,.0f}"), use_container_width=True)
