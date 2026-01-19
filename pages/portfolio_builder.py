import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import calculations as calc
import ui_components as ui

def page_portfolio_builder(full_df):
    """
    Enhanced Portfolio Builder with full functionality:
    - Interactive Contract Allocation
    - 5 Visualization Tabs (Equity, Allocation, Margin, Correlation, Greeks)
    - Advanced Optimization (Kelly, MART)
    """
    st.markdown(
        """<h1 style='color: #4B5563; font-family: "Exo 2", sans-serif; font-weight: 800; 
        text-transform: uppercase; margin-bottom: 0;'>🏗️ PORTFOLIO BUILDER</h1>""",
        unsafe_allow_html=True
    )
    st.caption("INTERACTIVE CONTRACT ALLOCATION — 1 LOT = 1 CONTRACT/DAY")

    if full_df.empty:
        st.info("👆 Please upload CSV files to start building your portfolio.")
        return

    # === SECTION 1: CONFIGURATION ===
    st.markdown("### ⚙️ Configuration")
    
    with st.expander("📊 Account & Risk Settings", expanded=True):
        config_r1_c1, config_r1_c2, config_r1_c3 = st.columns(3)
        
        with config_r1_c1:
            account_size = st.number_input("Account Size ($)", value=100000, step=5000, min_value=1000, key="builder_account")
        with config_r1_c2:
            target_margin_pct = st.slider("Target Margin (%)", min_value=10, max_value=100, value=80, step=5)
        with config_r1_c3:
            target_margin = account_size * (target_margin_pct / 100)
            st.metric("Margin Budget", f"${target_margin:,.0f}")
    
    # Strategy Type Allocation
    with st.expander("🎯 Strategy Type Allocation", expanded=True):
        st.caption("Define target allocation percentages for each strategy category")
        
        type_c1, type_c2, type_c3, type_c4 = st.columns(4)
        with type_c1:
            workhorse_pct = st.slider("🐴 Workhorse %", min_value=0, max_value=100, value=60, step=5)
        with type_c2:
            airbag_pct = st.slider("🛡️ Airbag %", min_value=0, max_value=100, value=25, step=5)
        with type_c3:
            opportunist_pct = st.slider("🎯 Opportunist %", min_value=0, max_value=100, value=15, step=5)
        with type_c4:
            total_type_pct = workhorse_pct + airbag_pct + opportunist_pct
            if total_type_pct != 100:
                st.warning(f"⚠️ Total: {total_type_pct}%")
            else:
                st.success(f"✅ Total: {total_type_pct}%")
    
    # Evaluation Period
    st.markdown("### 📅 Evaluation Period")
    min_d = full_df['timestamp'].min().date()
    max_d = full_df['timestamp'].max().date()
    
    date_c1, date_c2 = st.columns(2)
    with date_c1:
        selected_dates = st.date_input("Select Date Range", [min_d, max_d], min_value=min_d, max_value=max_d, key="builder_dates")
    
    if len(selected_dates) != 2:
        st.warning("Please select a date range.")
        return
    
    # Filter data
    filtered_df = full_df[
        (full_df['timestamp'].dt.date >= selected_dates[0]) &
        (full_df['timestamp'].dt.date <= selected_dates[1])
    ].copy()
    
    if filtered_df.empty:
        st.warning("No data in selected date range.")
        return
    
    strategies = sorted(filtered_df['strategy'].unique().tolist())
    full_date_range = pd.date_range(start=selected_dates[0], end=selected_dates[1], freq='D')
    
    # Pre-calculate stats
    strategy_base_stats = {}
    
    for strat in strategies:
        strat_data = filtered_df[filtered_df['strategy'] == strat].copy()
        if strat_data.empty: continue
        
        dna = calc.get_cached_dna(strat, strat_data)
        category = calc.categorize_strategy(strat) 
        total_lots, contracts_per_day = calc.calculate_lots_from_trades(strat_data)
        
        contracts_per_day = max(0.5, round(contracts_per_day * 2) / 2)
        
        # Margin calculations
        margin_per_contract = strat_data['margin'].mean() if 'margin' in strat_data.columns else 0
        total_pnl = strat_data['pnl'].sum()
        
        # Kelly
        wins = strat_data[strat_data['pnl'] > 0]['pnl']
        losses = strat_data[strat_data['pnl'] <= 0]['pnl']
        win_rate = len(wins) / len(strat_data) if len(strat_data) > 0 else 0
        avg_win = wins.mean() if len(wins) > 0 else 0
        avg_loss = abs(losses.mean()) if len(losses) > 0 else 0
        kelly = 0
        if avg_loss > 0 and avg_win > 0:
            b = avg_win / avg_loss
            kelly = (win_rate * b - (1 - win_rate)) / b
            kelly = max(0, min(kelly, 1))

        daily_pnl = strat_data.set_index('timestamp').resample('D')['pnl'].sum()
        daily_pnl_aligned = daily_pnl.reindex(full_date_range, fill_value=0)
        
        # Max DD
        cumsum = daily_pnl_aligned.cumsum()
        peak = cumsum.cummax()
        dd = (cumsum - peak).min()
        
        # Margin series
        margin_series = calc.generate_daily_margin_series_optimized(strat_data).reindex(full_date_range, fill_value=0)
        
        strategy_base_stats[strat] = {
            'category': category,
            'dna': dna,
            'contracts_per_day': contracts_per_day,
            'margin_per_contract': margin_per_contract,
            'total_pnl': total_pnl,
            'win_rate': win_rate,
            'kelly': kelly,
            'max_dd': abs(dd) if dd < 0 else 0,
            'daily_pnl_series': daily_pnl_aligned,
            'margin_series': margin_series
        }

    # Allocation Table
    st.markdown("### 📊 Strategy Allocation")
    
    if 'portfolio_allocation' not in st.session_state: st.session_state.portfolio_allocation = {s: 1.0 for s in strategies}
    if 'category_overrides' not in st.session_state: st.session_state.category_overrides = {}
    if 'kelly_pct' not in st.session_state: st.session_state.kelly_pct = 20

    allocation_data = []
    for strat in strategies:
        if strat not in strategy_base_stats: continue
        stats = strategy_base_stats[strat]
        cat = st.session_state.category_overrides.get(strat, stats['category'])
        mult = st.session_state.portfolio_allocation.get(strat, 1.0)
        
        allocation_data.append({
            'Category': cat,
            'Strategy': strat,
            'Hist': stats['contracts_per_day'],
            'P&L': stats['total_pnl'],
            'Margin/Lot': stats['margin_per_contract'],
            'Margin After': stats['margin_per_contract'] * stats['contracts_per_day'] * mult,
            'Multiplier': mult,
            'Kelly%': stats['kelly'] * 100
        })
    
    alloc_df = pd.DataFrame(allocation_data)
    
    alloc_col, action_col = st.columns([5, 1])
    with alloc_col:
        edited_alloc = st.data_editor(
            alloc_df,
            column_config={
                "Category": st.column_config.SelectboxColumn("Type", options=["Workhorse", "Airbag", "Opportunist"]),
                "Multiplier": st.column_config.NumberColumn("MULT", min_value=0.0, max_value=10.0, step=0.1),
                "P&L": st.column_config.NumberColumn(format="$%.0f"),
                "Margin/Lot": st.column_config.NumberColumn(format="$%.0f"),
                "Margin After": st.column_config.NumberColumn(format="$%.0f"),
                "Kelly%": st.column_config.NumberColumn(format="%.1f%%")
            },
            use_container_width=True,
            key="allocation_editor_v17",
            hide_index=True
        )
        
        # Update state
        for _, row in edited_alloc.iterrows():
            st.session_state.portfolio_allocation[row['Strategy']] = float(row['Multiplier'])
            st.session_state.category_overrides[row['Strategy']] = row['Category']
            
    with action_col:
        if st.button("🧮 CALCULATE", use_container_width=True, type="primary"): st.session_state.calculate_kpis = True; st.rerun()
        if st.button("🔄 Reset", use_container_width=True): 
            st.session_state.portfolio_allocation = {s: 1.0 for s in strategies}
            st.rerun()
            
        kelly_input = st.number_input("Kelly %", 5, 100, st.session_state.kelly_pct, 5)
        st.session_state.kelly_pct = kelly_input
        
        if st.button("⚡ Kelly Opt", use_container_width=True):
            optimized = calc.kelly_optimize_allocation(
                strategy_base_stats, target_margin, kelly_input/100, 
                workhorse_pct/100, airbag_pct/100, opportunist_pct/100, 
                st.session_state.category_overrides
            )
            st.session_state.portfolio_allocation = optimized
            st.session_state.calculate_kpis = True
            st.rerun()
            
        if st.button("🎯 MART Opt", use_container_width=True):
            optimized = calc.mart_optimize_allocation(
                strategy_base_stats, target_margin, account_size,
                st.session_state.category_overrides, full_date_range, filtered_df
            )
            st.session_state.portfolio_allocation = optimized
            st.session_state.calculate_kpis = True
            st.rerun()

    if not st.session_state.get('calculate_kpis', False):
        st.info("👆 Adjust allocations and click CALCULATE.")
        return

    # === CALCULATE PORTFOLIO METRICS ===
    port_pnl = pd.Series(0.0, index=full_date_range)
    port_margin = pd.Series(0.0, index=full_date_range)
    
    total_pnl = 0
    active_strategy_returns = []
    category_margin = {'Workhorse': 0, 'Airbag': 0, 'Opportunist': 0}
    category_pnl = {'Workhorse': 0, 'Airbag': 0, 'Opportunist': 0}
    
    for strat, mult in st.session_state.portfolio_allocation.items():
        if strat in strategy_base_stats and mult > 0:
            stats = strategy_base_stats[strat]
            scaled_pnl = stats['daily_pnl_series'] * mult
            port_pnl = port_pnl.add(scaled_pnl, fill_value=0)
            port_margin = port_margin.add(stats['margin_series'] * mult, fill_value=0)
            
            s_pnl = stats['total_pnl'] * mult
            total_pnl += s_pnl
            
            if scaled_pnl.std() > 0:
                active_strategy_returns.append({'name': strat, 'returns': scaled_pnl})
                
            cat = st.session_state.category_overrides.get(strat, stats['category'])
            if cat in category_margin:
                # Margin calculation approximation for pie chart
                s_margin = stats['margin_per_contract'] * stats['contracts_per_day'] * mult
                category_margin[cat] += s_margin
                category_pnl[cat] += s_pnl
            
    port_equity = account_size + port_pnl.cumsum()
    port_ret = port_equity.pct_change().fillna(0)
    
    # KPI Grid
    st.markdown("### 📈 Portfolio KPIs")
    
    spx = calc.fetch_spx_benchmark(pd.to_datetime(selected_dates[0]), pd.to_datetime(selected_dates[1]))
    spx_ret = spx.pct_change().fillna(0) if spx is not None else None
    
    m = calc.calculate_advanced_metrics(port_ret, None, spx_ret, account_size)
    
    # Portfolio-level margin metrics
    portfolio_peak_margin = port_margin.max() if len(port_margin) > 0 else 0
    
    k1, k2, k3, k4, k5, k6 = st.columns(6)
    with k1: ui.render_hero_metric("Total P/L", f"${total_pnl:,.0f}", color_class="hero-teal" if total_pnl > 0 else "hero-coral")
    with k2: ui.render_hero_metric("CAGR", f"{m['CAGR']:.1%}", color_class="hero-teal" if m['CAGR'] > 0 else "hero-coral")
    with k3: ui.render_hero_metric("Max DD", f"{m['MaxDD']:.1%}", f"${abs(m['MaxDD_USD']):,.0f}", "hero-coral")
    with k4: ui.render_hero_metric("Peak Margin", f"${portfolio_peak_margin:,.0f}", f"{(portfolio_peak_margin/account_size)*100:.0f}% Util", "hero-neutral")
    with k5: ui.render_hero_metric("MAR", f"{m['MAR']:.2f}", color_class="hero-teal")
    with k6: ui.render_hero_metric("Sharpe", f"{m['Sharpe']:.2f}", color_class="hero-neutral")

    # Monte Carlo Button
    if st.button("🎲 Stress Test with Monte Carlo →", use_container_width=True, type="primary"):
        st.session_state.mc_portfolio_daily_pnl = port_pnl
        st.session_state.mc_portfolio_account_size = account_size
        st.session_state.mc_from_builder = True
        st.session_state.mc_new_from_builder = True
        st.session_state.navigate_to_page = "🎲 Monte Carlo Punisher"
        st.rerun()

    # === VISUALIZATION TABS ===
    viz_tab1, viz_tab2, viz_tab3, viz_tab4, viz_tab5 = st.tabs([
        "📈 Equity & DD", "📊 Allocation", "💰 Margin", "🔗 Correlation", "🧬 Greek Exposure"
    ])
    
    with viz_tab1:
        fig_eq = px.line(x=port_equity.index, y=port_equity.values, title="Projected Equity Curve")
        fig_eq.add_hline(y=account_size, line_dash="dash", line_color="gray")
        st.plotly_chart(fig_eq, use_container_width=True)
        
        # Drawdown chart
        dd_series = port_equity - port_equity.cummax()
        fig_dd = px.area(x=dd_series.index, y=dd_series.values, title="Drawdown ($)")
        fig_dd.update_traces(line_color=ui.COLOR_CORAL)
        st.plotly_chart(fig_dd, use_container_width=True)
        
    with viz_tab2:
        c_pie1, c_pie2 = st.columns(2)
        with c_pie1:
            fig_cat = go.Figure(data=[go.Pie(
                labels=['Workhorse', 'Airbag', 'Opportunist'],
                values=[category_margin['Workhorse'], category_margin['Airbag'], category_margin['Opportunist']],
                hole=0.4
            )])
            fig_cat.update_layout(title="Margin Allocation by Category")
            st.plotly_chart(fig_cat, use_container_width=True)
        with c_pie2:
            alloc_data = [{'Strategy': s, 'Margin': strategy_base_stats[s]['margin_per_contract'] * strategy_base_stats[s]['contracts_per_day'] * m} 
                          for s, m in st.session_state.portfolio_allocation.items() if m > 0]
            if alloc_data:
                df_pie = pd.DataFrame(alloc_data)
                fig_strat = px.pie(df_pie, values='Margin', names='Strategy', title="Margin by Strategy")
                st.plotly_chart(fig_strat, use_container_width=True)
                
    with viz_tab3:
        st.markdown("##### Daily Margin Usage")
        fig_margin = px.area(x=port_margin.index, y=port_margin.values, title="Margin Utilization")
        fig_margin.add_hline(y=target_margin, line_dash="dash", line_color="orange", annotation_text="Target")
        fig_margin.add_hline(y=account_size, line_dash="dash", line_color="red", annotation_text="Max Account")
        st.plotly_chart(fig_margin, use_container_width=True)
        
    with viz_tab4:
        st.markdown("##### Strategy Correlation Matrix")
        if len(active_strategy_returns) > 1:
            corr_df = pd.DataFrame({s['name']: s['returns'] for s in active_strategy_returns})
            corr_matrix = corr_df.corr()
            fig_corr = px.imshow(corr_matrix, text_auto=".2f", color_continuous_scale="RdBu_r", zmin=-1, zmax=1)
            st.plotly_chart(fig_corr, use_container_width=True)
        else:
            st.info("Need at least 2 active strategies to show correlation.")
            
    with viz_tab5:
        st.markdown("##### Greek Exposure")
        greek_stats = {'Delta': {'Long': 0, 'Short': 0, 'Neutral': 0},
                       'Vega': {'Long': 0, 'Short': 0, 'Neutral': 0},
                       'Theta': {'Long': 0, 'Short': 0, 'Neutral': 0}}
        
        for strat, mult in st.session_state.portfolio_allocation.items():
            if strat in strategy_base_stats and mult > 0:
                dna = strategy_base_stats[strat]['dna']
                weight = 1  # Simplified weight count
                greek_stats['Delta'][dna['Delta']] += weight
                greek_stats['Vega'][dna['Vega']] += weight
                greek_stats['Theta'][dna['Theta']] += weight
        
        g1, g2, g3 = st.columns(3)
        with g1:
            fig_d = px.pie(values=list(greek_stats['Delta'].values()), names=list(greek_stats['Delta'].keys()), title="Delta Exposure", hole=0.5)
            st.plotly_chart(fig_d, use_container_width=True)
        with g2:
            fig_v = px.pie(values=list(greek_stats['Vega'].values()), names=list(greek_stats['Vega'].keys()), title="Vega Exposure", hole=0.5)
            st.plotly_chart(fig_v, use_container_width=True)
        with g3:
            fig_t = px.pie(values=list(greek_stats['Theta'].values()), names=list(greek_stats['Theta'].keys()), title="Theta Exposure", hole=0.5)
            st.plotly_chart(fig_t, use_container_width=True)
