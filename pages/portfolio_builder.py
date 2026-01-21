import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import calculations as calc
import ui_components as ui
import time

def page_portfolio_builder(full_df):
    """
    Enhanced Portfolio Builder with full functionality.
    """
    # Loading overlay
    placeholder = st.empty()

    # Header with Exo 2 font (no emoji)
    st.markdown(f"""
        <h1 style="font-family: 'Exo 2', sans-serif !important; font-weight: 800 !important;
                   text-transform: uppercase; color: {ui.COLOR_GREY} !important; letter-spacing: 1px;">
            PORTFOLIO BUILDER
        </h1>
    """, unsafe_allow_html=True)
    st.caption("INTERACTIVE CONTRACT ALLOCATION - 1 LOT = 1 CONTRACT/DAY")

    if full_df.empty:
        st.info("Please upload CSV files to start building your portfolio.")
        return

    # === CONFIGURATION (Card) ===
    with st.container(border=True):
        ui.section_header("Configuration",
            description="Set your account parameters and evaluation period for portfolio optimization.")

        # Account & Risk Settings
        config_r1_c1, config_r1_c2, config_r1_c3 = st.columns(3)
        with config_r1_c1:
            account_size = st.number_input("Account Size ($)", value=100000, step=5000, min_value=1000, key="builder_account")
        with config_r1_c2:
            target_margin_pct = st.slider("Target Margin (%)", min_value=10, max_value=100, value=80, step=5)
        with config_r1_c3:
            target_margin = account_size * (target_margin_pct / 100)
            st.metric("Margin Budget", f"${target_margin:,.0f}")

        st.write("")

        # Hidden type allocation (used internally)
        workhorse_pct = 60
        airbag_pct = 25
        opportunist_pct = 15

        # Evaluation Period
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

        margin_per_contract = strat_data['margin'].mean() if 'margin' in strat_data.columns else 0
        total_pnl = strat_data['pnl'].sum()

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

        cumsum = daily_pnl_aligned.cumsum()
        peak = cumsum.cummax()
        dd = (cumsum - peak).min()

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

    # Allocation Table (Card)
    with st.container(border=True):
        ui.section_header("Strategy Allocation")

        # Optimizer explanation
        st.markdown("""
        <div style='background-color: #F0F4FF; padding: 16px; border-radius: 8px; margin-bottom: 20px; font-family: Poppins, sans-serif;'>
            <div style='font-weight: 600; color: #302BFF; margin-bottom: 8px;'>How to use this section:</div>
            <div style='font-size: 13px; color: #4B5563; line-height: 1.6;'>
                <strong>Multiplier Column:</strong> Adjust the multiplier (highlighted in yellow) to scale each strategy's position size.
                A multiplier of 1.0 = historical average contracts/day, 2.0 = double, 0.5 = half.<br><br>
                <strong>Kelly Optimizer:</strong> Uses the Kelly Criterion to maximize long-term growth based on each strategy's
                win rate and average win/loss ratio. The Kelly % input controls how aggressive the optimization is (lower = more conservative).<br><br>
                <strong>MART Optimizer:</strong> Optimizes for the best MART ratio (CAGR / Max Drawdown $ / Account Size),
                balancing returns against dollar drawdown risk. Set Min P/L to require a minimum expected return.
            </div>
        </div>
        """, unsafe_allow_html=True)

        if 'portfolio_allocation' not in st.session_state: st.session_state.portfolio_allocation = {s: 1.0 for s in strategies}
        if 'category_overrides' not in st.session_state: st.session_state.category_overrides = {}
        if 'kelly_pct' not in st.session_state: st.session_state.kelly_pct = 20
        if 'mart_min_pnl' not in st.session_state: st.session_state.mart_min_pnl = 0

        allocation_data = []
        for strat in strategies:
            if strat not in strategy_base_stats: continue
            stats = strategy_base_stats[strat]
            cat = st.session_state.category_overrides.get(strat, stats['category'])
            mult = st.session_state.portfolio_allocation.get(strat, 1.0)

            # Truncate strategy name for display
            strat_display = strat[:20] + ".." if len(strat) > 20 else strat

            allocation_data.append({
                'Category': cat,
                'Strategy': strat_display,
                'StrategyFull': strat,
                'Hist': stats['contracts_per_day'],
                'P&L': stats['total_pnl'],
                'Margin/Lot': stats['margin_per_contract'],
                'Margin After': stats['margin_per_contract'] * stats['contracts_per_day'] * mult,
                'Multiplier': mult
            })

        alloc_df = pd.DataFrame(allocation_data)

        # Data editor with styled Multiplier column
        edited_alloc = st.data_editor(
            alloc_df[['Category', 'Strategy', 'Hist', 'P&L', 'Margin/Lot', 'Margin After', 'Multiplier']],
            column_config={
                "Category": st.column_config.SelectboxColumn("Type", options=["Workhorse", "Airbag", "Opportunist"], width="small"),
                "Strategy": st.column_config.TextColumn(width="medium"),
                "Hist": st.column_config.NumberColumn("Hist C/D", format="%.1f", width="small"),
                "P&L": st.column_config.NumberColumn(format="$%.0f", width="small"),
                "Margin/Lot": st.column_config.NumberColumn("Marg/Lot", format="$%.0f", width="small"),
                "Margin After": st.column_config.NumberColumn("Total Marg", format="$%.0f", width="small"),
                "Multiplier": st.column_config.NumberColumn(
                    "MULT ✏️",
                    min_value=0.0,
                    max_value=10.0,
                    step=0.1,
                    help="Edit this column to adjust allocation"
                )
            },
            use_container_width=True,
            key="allocation_editor_v19",
            hide_index=True
        )

        # Update state using full strategy name
        for idx, row in edited_alloc.iterrows():
            full_strat = alloc_df.iloc[idx]['StrategyFull']
            st.session_state.portfolio_allocation[full_strat] = float(row['Multiplier'])
            st.session_state.category_overrides[full_strat] = row['Category']

        # Action buttons row
        btn_col1, btn_col2, btn_col3, btn_col4, btn_col5 = st.columns(5)
        with btn_col1:
            if st.button("CALCULATE", use_container_width=True, type="primary"):
                st.session_state.calculate_kpis = True
                st.rerun()
        with btn_col2:
            kelly_input = st.number_input("Kelly %", 5, 100, st.session_state.kelly_pct, 5, key="kelly_input", label_visibility="collapsed")
            st.session_state.kelly_pct = kelly_input
        with btn_col3:
            if st.button("Kelly Opt", use_container_width=True, type="secondary"):
                with placeholder:
                    ui.show_loading_overlay("Optimizing", "Running Kelly optimization...")
                optimized = calc.kelly_optimize_allocation(
                    strategy_base_stats, target_margin, kelly_input/100,
                    workhorse_pct/100, airbag_pct/100, opportunist_pct/100,
                    st.session_state.category_overrides
                )
                st.session_state.portfolio_allocation = optimized
                st.session_state.calculate_kpis = True
                placeholder.empty()
                st.rerun()
        with btn_col4:
            mart_min_pnl = st.number_input("Min P/L", value=st.session_state.mart_min_pnl, step=1000, key="mart_min_pnl_input", label_visibility="collapsed")
            st.session_state.mart_min_pnl = mart_min_pnl
        with btn_col5:
            if st.button("MART Opt", use_container_width=True, type="secondary"):
                with placeholder:
                    ui.show_loading_overlay("Optimizing", "Running MART optimization...")
                optimized = calc.mart_optimize_allocation(
                    strategy_base_stats, target_margin, account_size,
                    st.session_state.category_overrides, full_date_range, filtered_df,
                    min_pnl=mart_min_pnl
                )
                st.session_state.portfolio_allocation = optimized
                st.session_state.calculate_kpis = True
                placeholder.empty()
                st.rerun()

        # Reset links centered below
        st.markdown("<div style='text-align: center; margin-top: 8px;'>", unsafe_allow_html=True)
        reset_col1, reset_col2, reset_col3 = st.columns([2, 1, 2])
        with reset_col2:
            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("Reset", key="reset_btn", type="tertiary"):
                    st.session_state.portfolio_allocation = {s: 1.0 for s in strategies}
                    st.session_state.calculate_kpis = False
                    st.rerun()
            with col_b:
                if st.button("Set to 0", key="zero_btn", type="tertiary"):
                    st.session_state.portfolio_allocation = {s: 0.0 for s in strategies}
                    st.session_state.calculate_kpis = False
                    st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    if not st.session_state.get('calculate_kpis', False):
        st.info("Adjust allocations and click CALCULATE to see projected performance.")
        return

    # Show loading while calculating
    with placeholder:
        ui.show_loading_overlay("Calculating", "Computing portfolio metrics...")
    time.sleep(0.05)

    # === CALCULATE METRICS ===
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
                s_margin = stats['margin_per_contract'] * stats['contracts_per_day'] * mult
                category_margin[cat] += s_margin
                category_pnl[cat] += s_pnl

    port_equity = account_size + port_pnl.cumsum()
    port_ret = port_equity.pct_change().fillna(0)

    spx = calc.fetch_spx_benchmark(pd.to_datetime(selected_dates[0]), pd.to_datetime(selected_dates[1]))
    spx_ret = spx.pct_change().fillna(0) if spx is not None else None

    m = calc.calculate_advanced_metrics(port_ret, None, spx_ret, account_size)

    # Additional Metrics
    portfolio_peak_margin = port_margin.max() if len(port_margin) > 0 else 0
    mean_margin = port_margin[port_margin > 0].mean() if len(port_margin) > 0 and (port_margin > 0).any() else 0

    alpha_val, beta_val = 0, 0
    if spx_ret is not None and len(spx_ret) > 20 and len(port_ret) > 20:
        aligned = pd.concat([port_ret, spx_ret], axis=1).dropna()
        aligned = aligned[~aligned.isin([np.nan, np.inf, -np.inf]).any(axis=1)]
        if len(aligned) > 20:
            from scipy import stats
            y, x = aligned.iloc[:, 0], aligned.iloc[:, 1]
            slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
            beta_val = slope
            alpha_val = intercept * 252

    avg_correlation = 0
    if len(active_strategy_returns) > 1:
        corr_df = pd.DataFrame({s['name']: s['returns'] for s in active_strategy_returns})
        corr_matrix = corr_df.corr()
        corr_values = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(bool)).stack()
        avg_correlation = corr_values.mean() if not corr_values.empty else 0

    actual_max_daily_loss = port_pnl.min() if not port_pnl.empty else 0
    worst_10 = port_pnl.nsmallest(10).mean() if len(port_pnl) >= 10 else actual_max_daily_loss
    dd_vs_account = abs(m['MaxDD_USD']) / account_size if account_size > 0 else 0
    mar_on_margin = m['CAGR'] / (abs(m['MaxDD_USD']) / mean_margin) if mean_margin > 0 and m['MaxDD_USD'] != 0 else 0
    pos_days = port_pnl[port_pnl > 0].sum()
    neg_days = abs(port_pnl[port_pnl < 0].sum())
    profit_factor = pos_days / neg_days if neg_days != 0 else 0

    # Hide loading
    placeholder.empty()

    # === KPI GRID (Card) - Same colors as Portfolio Analytics ===
    with st.container(border=True):
        ui.section_header("Projected Performance")

        # Row 1: Primary metrics (Teal/Coral)
        k1, k2, k3, k4, k5, k6 = st.columns(6)
        with k1: ui.render_hero_metric("Total P/L", f"${total_pnl:,.0f}", "", "hero-teal" if total_pnl > 0 else "hero-coral")
        with k2: ui.render_hero_metric("CAGR", f"{m['CAGR']:.1%}", "", "hero-teal" if m['CAGR'] > 0 else "hero-coral")
        with k3: ui.render_hero_metric("Max DD (%)", f"{m['MaxDD']:.1%}", "", "hero-coral")
        with k4: ui.render_hero_metric("Max DD ($)", f"${abs(m['MaxDD_USD']):,.0f}", "", "hero-coral")
        with k5: ui.render_hero_metric("MAR Ratio", f"{m['MAR']:.2f}", "", "hero-teal" if m['MAR'] > 1 else "hero-neutral")
        with k6: ui.render_hero_metric("MART Ratio", f"{m['MART']:.2f}", "", "hero-teal")

        st.write("")

        # Row 2
        r2k1, r2k2, r2k3, r2k4, r2k5, r2k6 = st.columns(6)
        with r2k1: ui.render_hero_metric("Peak Margin", f"${portfolio_peak_margin:,.0f}", f"{(portfolio_peak_margin/account_size)*100:.0f}% Util", "hero-neutral")
        with r2k2: ui.render_hero_metric("Mean Margin", f"${mean_margin:,.0f}", f"{(mean_margin/account_size)*100:.0f}% Util", "hero-neutral")
        with r2k3:
            active_cnt = len([k for k,v in st.session_state.portfolio_allocation.items() if v > 0])
            ui.render_hero_metric("Active Strats", f"{active_cnt}", "", "hero-neutral")
        with r2k4: ui.render_hero_metric("Sharpe", f"{m['Sharpe']:.2f}", "", "hero-neutral")
        with r2k5: ui.render_hero_metric("Sortino", f"{m['Sortino']:.2f}", "", "hero-neutral")
        with r2k6: ui.render_hero_metric("DD vs Account", f"{dd_vs_account:.1%}", f"${abs(m['MaxDD_USD']):,.0f}", "hero-neutral")

        st.write("")

        # Row 3
        r3k1, r3k2, r3k3, r3k4, r3k5, r3k6 = st.columns(6)
        with r3k1: ui.render_hero_metric("Alpha", f"{alpha_val:.1%}", "", "hero-neutral")
        with r3k2: ui.render_hero_metric("Beta", f"{beta_val:.2f}", "", "hero-neutral")
        with r3k3: ui.render_hero_metric("MAR on Margin", f"{mar_on_margin:.2f}", "", "hero-neutral")
        with r3k4: ui.render_hero_metric("Max Daily Loss", f"${actual_max_daily_loss:,.0f}", f"Avg10: ${worst_10:,.0f}", "hero-neutral")
        with r3k5: ui.render_hero_metric("Avg Correlation", f"{avg_correlation:.2f}", "", "hero-neutral")
        with r3k6: ui.render_hero_metric("Profit Factor", f"{profit_factor:.2f}", "", "hero-neutral")

    # Monte Carlo Button
    st.write("")
    if st.button("Stress Test with Monte Carlo", use_container_width=True, type="primary"):
        st.session_state.mc_portfolio_daily_pnl = port_pnl
        st.session_state.mc_portfolio_account_size = account_size
        st.session_state.mc_from_builder = True
        st.session_state.mc_new_from_builder = True
        st.session_state.navigate_to_page = "Monte Carlo"
        st.rerun()

    # === VISUALIZATION TABS ===
    viz_tab1, viz_tab2, viz_tab3, viz_tab4, viz_tab5 = st.tabs([
        "Equity & DD", "Allocation", "Margin", "Correlation", "Greek Exposure"
    ])

    with viz_tab1:
        with st.container(border=True):
            ui.section_header("Equity Growth",
                description="Cumulative equity growth over the evaluation period.")
            fig_eq = px.line(x=port_equity.index, y=port_equity.values)
            fig_eq.update_layout(xaxis_title=None, yaxis_title="Equity ($)", template="plotly_white", height=400)
            fig_eq.add_hline(y=account_size, line_dash="dash", line_color="gray", annotation_text="Starting Capital")
            st.plotly_chart(fig_eq, use_container_width=True)

        with st.container(border=True):
            # Drawdown with toggle between $ and %
            dd_mode = st.radio("Drawdown Display:", ["Dollar ($)", "Percent (%)"], horizontal=True, key="dd_mode")

            if dd_mode == "Dollar ($)":
                ui.section_header("Drawdown ($)",
                    description="Dollar drawdown from peak equity over time.")
                dd_series = port_equity - port_equity.cummax()
                fig_dd = px.area(x=dd_series.index, y=dd_series.values)
                fig_dd.update_layout(xaxis_title=None, yaxis_title="Drawdown ($)", template="plotly_white", height=350)
            else:
                ui.section_header("Drawdown (%)",
                    description="Percentage drawdown from peak equity over time.")
                dd_series_pct = (port_equity - port_equity.cummax()) / port_equity.cummax() * 100
                fig_dd = px.area(x=dd_series_pct.index, y=dd_series_pct.values)
                fig_dd.update_layout(xaxis_title=None, yaxis_title="Drawdown (%)", template="plotly_white", height=350)

            fig_dd.update_traces(line_color=ui.COLOR_CORAL, fillcolor='rgba(255, 46, 77, 0.3)')
            st.plotly_chart(fig_dd, use_container_width=True)

    with viz_tab2:
        with st.container(border=True):
            ui.section_header("Portfolio Allocation",
                description="Margin distribution by category and strategy.")

            # Category allocation on top
            fig_cat = go.Figure(data=[go.Pie(
                labels=['Workhorse', 'Airbag', 'Opportunist'],
                values=[category_margin['Workhorse'], category_margin['Airbag'], category_margin['Opportunist']],
                hole=0.4
            )])
            fig_cat.update_layout(title="Margin Allocation by Category", height=350)
            st.plotly_chart(fig_cat, use_container_width=True)

            # Strategy allocation below
            alloc_data = [{'Strategy': s[:20], 'Margin': strategy_base_stats[s]['margin_per_contract'] * strategy_base_stats[s]['contracts_per_day'] * m_val}
                          for s, m_val in st.session_state.portfolio_allocation.items() if m_val > 0 and s in strategy_base_stats]
            if alloc_data:
                df_pie = pd.DataFrame(alloc_data)
                fig_strat = px.pie(df_pie, values='Margin', names='Strategy', title="Margin by Strategy")
                fig_strat.update_layout(height=400)
                st.plotly_chart(fig_strat, use_container_width=True)

    with viz_tab3:
        with st.container(border=True):
            ui.section_header("Margin Utilization",
                description="Daily margin usage with target and maximum thresholds.")

            fig_margin = go.Figure()
            fig_margin.add_trace(go.Scatter(x=port_margin.index, y=port_margin.values, fill='tozeroy', name='Margin', line=dict(color=ui.COLOR_BLUE)))
            fig_margin.add_hline(y=target_margin, line_dash="dash", line_color="orange", annotation_text="Target Margin")
            fig_margin.add_hline(y=account_size, line_dash="dash", line_color="red", annotation_text="Max (Account)")
            fig_margin.add_hline(y=portfolio_peak_margin, line_dash="dot", line_color="purple", annotation_text=f"Peak: ${portfolio_peak_margin:,.0f}")
            fig_margin.add_hline(y=mean_margin, line_dash="dot", line_color="green", annotation_text=f"Avg: ${mean_margin:,.0f}")
            fig_margin.update_layout(xaxis_title=None, yaxis_title="Margin ($)", template="plotly_white", height=450)
            st.plotly_chart(fig_margin, use_container_width=True)

    with viz_tab4:
        with st.container(border=True):
            ui.section_header("Strategy Correlation",
                description=f"Correlation matrix of daily P/L between strategies. Average correlation: {avg_correlation:.2f}")

            if len(active_strategy_returns) > 1:
                corr_df = pd.DataFrame({s['name'][:12]: s['returns'] for s in active_strategy_returns})
                corr_matrix = corr_df.corr()
                fig_corr = px.imshow(corr_matrix, text_auto=".2f", color_continuous_scale="RdBu_r", zmin=-1, zmax=1, aspect="auto")
                fig_corr.update_layout(height=500, margin=dict(l=10, r=10, t=30, b=10))
                st.plotly_chart(fig_corr, use_container_width=True)
            else:
                st.info("Need at least 2 active strategies to show correlation.")

    with viz_tab5:
        with st.container(border=True):
            ui.section_header("Greek Exposure",
                description="Distribution of Greek exposures across active strategies.")

            greek_stats = {'Delta': {'Long': 0, 'Short': 0, 'Neutral': 0},
                           'Vega': {'Long': 0, 'Short': 0, 'Neutral': 0},
                           'Theta': {'Long': 0, 'Short': 0, 'Neutral': 0}}

            greek_table_data = []

            for strat, mult in st.session_state.portfolio_allocation.items():
                if strat in strategy_base_stats and mult > 0:
                    dna = strategy_base_stats[strat]['dna']
                    weight = 1
                    greek_stats['Delta'][dna['Delta']] += weight
                    greek_stats['Vega'][dna['Vega']] += weight
                    greek_stats['Theta'][dna['Theta']] += weight

                    greek_table_data.append({
                        'Strategy': strat[:25],
                        'Delta': dna['Delta'],
                        'Vega': dna['Vega'],
                        'Theta': dna['Theta'],
                        'Margin': f"${strategy_base_stats[strat]['margin_per_contract'] * strategy_base_stats[strat]['contracts_per_day'] * mult:,.0f}",
                        'P/L': f"${strategy_base_stats[strat]['total_pnl'] * mult:,.0f}"
                    })

            g1, g2, g3 = st.columns(3)
            with g1:
                fig_d = px.pie(values=list(greek_stats['Delta'].values()), names=list(greek_stats['Delta'].keys()), title="Delta", hole=0.5)
                fig_d.update_layout(height=300)
                st.plotly_chart(fig_d, use_container_width=True)
            with g2:
                fig_v = px.pie(values=list(greek_stats['Vega'].values()), names=list(greek_stats['Vega'].keys()), title="Vega", hole=0.5)
                fig_v.update_layout(height=300)
                st.plotly_chart(fig_v, use_container_width=True)
            with g3:
                fig_t = px.pie(values=list(greek_stats['Theta'].values()), names=list(greek_stats['Theta'].keys()), title="Theta", hole=0.5)
                fig_t.update_layout(height=300)
                st.plotly_chart(fig_t, use_container_width=True)

            # Greek Exposure Table
            st.write("")
            st.markdown("**Strategy Greek Exposures**")
            if greek_table_data:
                greek_df = pd.DataFrame(greek_table_data)
                st.dataframe(greek_df, use_container_width=True, hide_index=True)
