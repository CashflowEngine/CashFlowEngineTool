import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import calculations as calc
import ui_components as ui

def page_portfolio_builder(full_df):
    """
    Enhanced Portfolio Builder
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
    strategy_daily_pnl = {}
    
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
        strategy_daily_pnl[strat] = daily_pnl_aligned
        
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
                "Multiplier": st.column_config.NumberColumn("MULT", min_value=0.0, max_value=10.0, step=0.1)
            },
            use_container_width=True,
            key="allocation_editor_v16"
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

    if not st.session_state.get('calculate_kpis', False):
        st.info("👆 Adjust allocations and click CALCULATE.")
        return

    # Calculate Portfolio Metrics
    port_pnl = pd.Series(0.0, index=full_date_range)
    port_margin = pd.Series(0.0, index=full_date_range)
    
    total_pnl = 0
    for strat, mult in st.session_state.portfolio_allocation.items():
        if strat in strategy_base_stats and mult > 0:
            stats = strategy_base_stats[strat]
            port_pnl = port_pnl.add(stats['daily_pnl_series'] * mult, fill_value=0)
            port_margin = port_margin.add(stats['margin_series'] * mult, fill_value=0)
            total_pnl += stats['total_pnl'] * mult
            
    port_equity = account_size + port_pnl.cumsum()
    port_ret = port_equity.pct_change().fillna(0)
    
    # KPI Grid
    st.markdown("### 📈 Portfolio KPIs")
    
    # Calculate advanced metrics for the simulated portfolio
    spx = calc.fetch_spx_benchmark(pd.to_datetime(selected_dates[0]), pd.to_datetime(selected_dates[1]))
    spx_ret = spx.pct_change().fillna(0) if spx is not None else None
    
    m = calc.calculate_advanced_metrics(port_ret, None, spx_ret, account_size) # No trades DF for aggregate
    
    k1, k2, k3, k4, k5, k6 = st.columns(6)
    with k1: ui.render_hero_metric("Total P/L", f"${total_pnl:,.0f}", color_class="hero-teal")
    with k2: ui.render_hero_metric("CAGR", f"{m['CAGR']:.1%}", color_class="hero-teal")
    with k3: ui.render_hero_metric("Max DD", f"{m['MaxDD']:.1%}", color_class="hero-coral")
    with k4: ui.render_hero_metric("Max DD ($)", f"${abs(m['MaxDD_USD']):,.0f}", color_class="hero-coral")
    with k5: ui.render_hero_metric("MAR", f"{m['MAR']:.2f}", color_class="hero-teal")
    with k6: ui.render_hero_metric("Sharpe", f"{m['Sharpe']:.2f}", color_class="hero-neutral")

    # Monte Carlo Button
    if st.button("🎲 Stress Test with Monte Carlo →", use_container_width=True, type="primary"):
        st.session_state.mc_portfolio_daily_pnl = port_pnl
        st.session_state.mc_portfolio_account_size = account_size
        st.session_state.mc_from_builder = True
        st.session_state.navigate_to_page = "🎲 Monte Carlo Punisher"
        st.rerun()

    # Visualizations
    tab1, tab2 = st.tabs(["Equity", "Allocation"])
    with tab1:
        fig = px.line(x=port_equity.index, y=port_equity.values, title="Projected Equity")
        st.plotly_chart(fig, use_container_width=True)
    with tab2:
        alloc_pie = pd.DataFrame([
            {'Strategy': s, 'Allocation': m} 
            for s, m in st.session_state.portfolio_allocation.items() if m > 0
        ])
        if not alloc_pie.empty:
            fig_pie = px.pie(alloc_pie, values='Allocation', names='Strategy')
            st.plotly_chart(fig_pie, use_container_width=True)
