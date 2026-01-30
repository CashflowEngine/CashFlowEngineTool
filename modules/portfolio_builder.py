import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import calculations as calc
import ui_components as ui
import precompute
import time

def page_portfolio_builder(full_df):
    """
    Enhanced Portfolio Builder with full functionality.
    """
    # Loading overlay
    placeholder = st.empty()

    # Header with consistent font
    ui.render_page_header(
        "PORTFOLIO BUILDER",
        "Interactive contract allocation tool. 1 LOT = 1 CONTRACT/DAY"
    )

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
            target_margin_pct = st.slider("Target Margin (%)", min_value=10, max_value=100, value=50, step=5)
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

    # Check if we can use pre-computed stats (when using full date range)
    cached_stats = precompute.get_cached('strategy_base_stats')
    use_cache = (
        cached_stats is not None and
        selected_dates[0] == min_d and
        selected_dates[1] == max_d and
        precompute.is_cache_valid(full_df)
    )

    if use_cache:
        # Use pre-computed stats (instant!)
        strategy_base_stats = cached_stats
    else:
        # Compute stats for custom date range
        strategy_base_stats = {}

        for strat in strategies:
            strat_data = filtered_df[filtered_df['strategy'] == strat].copy()
            if strat_data.empty: continue

            dna = calc.get_cached_dna(strat, strat_data)
            category = calc.categorize_strategy(strat)
            total_lots, contracts_per_day = calc.calculate_lots_from_trades(strat_data)

            contracts_per_day = max(0.5, round(contracts_per_day * 2) / 2)

            # Calculate max daily margin (sum of all open positions on any given day)
            margin_series = calc.generate_daily_margin_series_optimized(strat_data)
            margin_per_contract = margin_series.max() if len(margin_series) > 0 else 0
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

        # Basic initialization - detailed initialization happens after function definitions below
        if 'portfolio_allocation' not in st.session_state:
            st.session_state.portfolio_allocation = {s: 1.0 for s in strategies}
        if 'category_overrides' not in st.session_state:
            st.session_state.category_overrides = {}
        if 'option_strategy_overrides' not in st.session_state:
            st.session_state.option_strategy_overrides = {}
        if 'kelly_pct' not in st.session_state: st.session_state.kelly_pct = 20
        if 'mart_min_pnl' not in st.session_state: st.session_state.mart_min_pnl = 0
        if 'allocation_editor_version' not in st.session_state: st.session_state.allocation_editor_version = 0

        # Option strategy types for dropdown
        OPTION_STRATEGIES = ["Iron Condor", "Reverse Iron Condor", "Double Calendar", "Bull Put Spread", "Bear Call Spread",
                            "Bull Call Spread", "Bear Put Spread", "Long Put", "Long Call",
                            "Butterfly", "Straddle", "Strangle", "Covered Call", "Cash Secured Put", "Other"]

        def detect_option_strategy_from_legs(strat_name, strat_df):
            """Detect option strategy by analyzing the legs of trades.

            Priority 1: Analyze legs to determine strategy type.
            Priority 2: Fall back to strategy name pattern matching.
            """
            # First try to detect from legs
            if strat_df is not None and not strat_df.empty and 'legs' in strat_df.columns:
                sample = strat_df.head(50)  # Sample trades for analysis

                # Count leg patterns
                has_short_put = 0
                has_short_call = 0
                has_long_put = 0
                has_long_call = 0

                for _, row in sample.iterrows():
                    legs_str = str(row.get('legs', '')).upper()

                    # Detect short/long puts and calls
                    if ' P STO' in legs_str or ' PUT STO' in legs_str or 'SELL.*PUT' in legs_str:
                        has_short_put += 1
                    if ' C STO' in legs_str or ' CALL STO' in legs_str or 'SELL.*CALL' in legs_str:
                        has_short_call += 1
                    if ' P BTO' in legs_str or ' PUT BTO' in legs_str or 'BUY.*PUT' in legs_str:
                        has_long_put += 1
                    if ' C BTO' in legs_str or ' CALL BTO' in legs_str or 'BUY.*CALL' in legs_str:
                        has_long_call += 1

                # Determine strategy from leg composition
                total = len(sample)
                if total > 0:
                    # Iron Condor: Both short put and short call
                    if has_short_put > total * 0.4 and has_short_call > total * 0.4:
                        return "Iron Condor"
                    # Bull Put Spread: Short put + long put (at lower strike)
                    elif has_short_put > total * 0.4 and has_long_put > total * 0.4 and has_short_call < total * 0.1:
                        return "Bull Put Spread"
                    # Bear Call Spread: Short call + long call (at higher strike)
                    elif has_short_call > total * 0.4 and has_long_call > total * 0.4 and has_short_put < total * 0.1:
                        return "Bear Call Spread"
                    # Long Put only
                    elif has_long_put > total * 0.4 and has_short_put < total * 0.1 and has_short_call < total * 0.1 and has_long_call < total * 0.1:
                        return "Long Put"
                    # Long Call only
                    elif has_long_call > total * 0.4 and has_short_call < total * 0.1 and has_short_put < total * 0.1 and has_long_put < total * 0.1:
                        return "Long Call"

            # Fall back to strategy name pattern matching
            return detect_option_strategy_from_name(strat_name)

        def detect_option_strategy_from_name(strat_name):
            """Detect option strategy from strategy name patterns."""
            name_upper = strat_name.upper()

            # Reverse Iron Condor (check before Iron Condor)
            # Use word boundary check for RIC to avoid false positives
            import re
            if 'REVERSE IRON' in name_upper or re.search(r'\bRIC\b', name_upper):
                return "Reverse Iron Condor"

            # Long positions (check first as they're specific)
            if 'LONG PUT' in name_upper:
                return "Long Put"
            if 'LONG CALL' in name_upper:
                return "Long Call"

            # Spread patterns
            if 'BPS' in name_upper or 'BULL PUT' in name_upper:
                return "Bull Put Spread"
            if 'BCS' in name_upper or 'BULL CALL' in name_upper:
                return "Bull Call Spread"
            if 'BEAR CALL' in name_upper:
                return "Bear Call Spread"
            if 'BEAR PUT' in name_upper:
                return "Bear Put Spread"

            # METF patterns
            if 'METF' in name_upper:
                if 'CALL' in name_upper:
                    return "Bear Call Spread"  # METF-Call is typically a call spread (credit)
                if 'PUT' in name_upper:
                    return "Bull Put Spread"   # METF-Put is typically a put spread (credit)

            # Iron Condor
            if 'IRON CONDOR' in name_upper or 'IC' in name_upper or 'MEIC' in name_upper:
                return "Iron Condor"

            # Calendar spreads
            if 'DOUBLE CALENDAR' in name_upper or 'DC' in name_upper or 'CALENDAR' in name_upper:
                return "Double Calendar"

            # Credit spreads (generic)
            if 'PUT CREDIT' in name_upper or 'PCS' in name_upper:
                return "Bull Put Spread"
            if 'CALL CREDIT' in name_upper or 'CCS' in name_upper:
                return "Bear Call Spread"

            # Other patterns
            if 'BUTTERFLY' in name_upper or 'FLY' in name_upper or 'BWB' in name_upper:
                return "Butterfly"
            if 'STRADDLE' in name_upper:
                return "Straddle"
            if 'STRANGLE' in name_upper:
                return "Strangle"
            if 'COVERED CALL' in name_upper:
                return "Covered Call"
            if 'CSP' in name_upper or 'CASH SECURED' in name_upper:
                return "Cash Secured Put"

            return "Other"

        def get_default_category_for_strategy(strat_name, opt_strat):
            """Determine the default Type (Category) based on strategy characteristics.

            Rules:
            - Delta-neutral strategies: Workhorse
            - Delta-Long strategies: Opportunist
            - Delta-Short strategies: Airbag
            - Double Calendars and RICs: Airbag (ALWAYS)
            - METF strategies: Workhorse
            """
            import re
            name_upper = strat_name.upper()

            # FORCE Airbag for Double Calendar and RIC strategies
            # Check both option strategy type AND strategy name patterns
            if opt_strat in ["Double Calendar", "Reverse Iron Condor"]:
                return "Airbag"

            # Also check strategy name directly for DC/RIC patterns
            if 'DOUBLE CALENDAR' in name_upper or 'DC' in name_upper or 'CALENDAR' in name_upper:
                return "Airbag"
            if 'REVERSE IRON' in name_upper or re.search(r'\bRIC\b', name_upper):
                return "Airbag"

            # METF strategies are Workhorse
            if 'METF' in name_upper:
                return "Workhorse"

            # Delta-Long strategies are Opportunist
            if opt_strat in ["Long Call", "Bull Call Spread", "Bull Put Spread"]:
                return "Opportunist"

            # Delta-Short strategies are Airbag
            if opt_strat in ["Long Put", "Bear Call Spread", "Bear Put Spread"]:
                return "Airbag"

            # Delta-neutral strategies (Iron Condor, Butterfly, etc.) are Workhorse
            if opt_strat in ["Iron Condor", "Butterfly", "Straddle", "Strangle", "Covered Call", "Cash Secured Put"]:
                return "Workhorse"

            # Default to Workhorse
            return "Workhorse"

        # Pre-populate overrides for all strategies BEFORE building the DataFrame
        # This prevents value jumping when editing the data_editor
        for strat in strategies:
            if strat not in strategy_base_stats:
                continue

            # Ensure portfolio allocation exists
            if strat not in st.session_state.portfolio_allocation:
                st.session_state.portfolio_allocation[strat] = 1.0

            # Detect and set option strategy if not already set
            if strat not in st.session_state.option_strategy_overrides:
                strat_data_for_init = filtered_df[filtered_df['strategy'] == strat] if strat in filtered_df['strategy'].values else None
                detected_opt_strat = detect_option_strategy_from_legs(strat, strat_data_for_init)
                st.session_state.option_strategy_overrides[strat] = detected_opt_strat

            # Set category based on option strategy if not already set
            if strat not in st.session_state.category_overrides:
                opt_strat = st.session_state.option_strategy_overrides[strat]
                st.session_state.category_overrides[strat] = get_default_category_for_strategy(strat, opt_strat)

        allocation_data = []
        for strat in strategies:
            if strat not in strategy_base_stats: continue
            stats = strategy_base_stats[strat]

            # Get values from session_state (which were initialized above)
            # This ensures consistency and prevents value jumping
            opt_strat = st.session_state.option_strategy_overrides.get(strat, "Other")
            cat = st.session_state.category_overrides.get(strat, "Workhorse")
            mult = st.session_state.portfolio_allocation.get(strat, 1.0)

            allocation_data.append({
                'Strategy': strat,  # Full strategy name
                'StrategyFull': strat,
                'MaxDailyMargin': stats['margin_per_contract'],  # This is the max total daily margin, not per contract
                'P&L': stats['total_pnl'],
                'P&L*M': stats['total_pnl'] * mult,
                'DD': stats['max_dd'],
                'DD*M': stats['max_dd'] * mult,
                'Margin*M': stats['margin_per_contract'] * mult,
                'Multiplier': mult,
                'Category': cat,
                'OptStrategy': opt_strat
            })

        alloc_df = pd.DataFrame(allocation_data)

        # Calculate totals for display
        total_margin_daily = alloc_df['MaxDailyMargin'].sum()

        # Data editor with improved columns - Strategy Name first, Type and OptStrategy at end
        edited_alloc = st.data_editor(
            alloc_df[['Strategy', 'MaxDailyMargin', 'P&L', 'P&L*M', 'DD*M', 'Margin*M', 'Multiplier', 'Category', 'OptStrategy']],
            column_config={
                "Strategy": st.column_config.TextColumn(
                    "Strategy Name",
                    width="large",
                    help="Full strategy name from your CSV file"
                ),
                "MaxDailyMargin": st.column_config.NumberColumn(
                    "Max Margin",
                    format="$%.0f",
                    width="small",
                    help="Maximum total daily margin for this strategy (includes all open positions on any day)"
                ),
                "P&L": st.column_config.NumberColumn(
                    "P&L (1x)",
                    format="$%.0f",
                    width="small",
                    help="Total P&L at 1x multiplier"
                ),
                "P&L*M": st.column_config.NumberColumn(
                    "P&L*M",
                    format="$%.0f",
                    width="small",
                    help="P&L scaled by your multiplier"
                ),
                "DD*M": st.column_config.NumberColumn(
                    "DD*M",
                    format="$%.0f",
                    width="small",
                    help="Max drawdown scaled by multiplier"
                ),
                "Margin*M": st.column_config.NumberColumn(
                    "Margin*M",
                    format="$%.0f",
                    width="small",
                    help="Daily margin usage scaled by multiplier"
                ),
                "Multiplier": st.column_config.NumberColumn(
                    "MULT ✏️",
                    min_value=0.0,
                    max_value=10.0,
                    step=0.1,
                    help="Adjust position size: 1.0 = historical, 2.0 = double, 0.5 = half"
                ),
                "Category": st.column_config.SelectboxColumn(
                    "Type ✏️",
                    options=["Workhorse", "Airbag", "Opportunist"],
                    width="small",
                    help="Strategy type: Workhorse (core), Airbag (hedge), Opportunist (tactical)"
                ),
                "OptStrategy": st.column_config.SelectboxColumn(
                    "Option Strategy ✏️",
                    options=OPTION_STRATEGIES,
                    width="medium",
                    help="Option strategy type (auto-detected, editable)"
                )
            },
            use_container_width=True,
            key=f"allocation_editor_v{st.session_state.allocation_editor_version}",
            hide_index=True
        )

        # Show totals row
        st.markdown(f"""
            <div style="background-color: #F3F4F6; padding: 12px 20px; border-radius: 8px; margin-top: 10px;
                        display: flex; justify-content: space-between; font-family: Poppins, sans-serif; font-size: 13px;
                        flex-wrap: wrap; gap: 15px;">
                <span><strong>TOTAL ({len(alloc_df)} strategies)</strong></span>
                <span>Max Margin: <strong>${alloc_df['MaxDailyMargin'].sum():,.0f}</strong></span>
                <span>P&L (1x): <strong>${alloc_df['P&L'].sum():,.0f}</strong></span>
                <span>P&L*M: <strong>${alloc_df['P&L*M'].sum():,.0f}</strong></span>
                <span>Max DD*M: <strong>${-abs(alloc_df['DD*M'].max()):,.0f}</strong></span>
                <span>Margin*M: <strong>${alloc_df['Margin*M'].sum():,.0f}</strong></span>
            </div>
        """, unsafe_allow_html=True)

        # Update state using full strategy name
        for idx, row in edited_alloc.iterrows():
            full_strat = alloc_df.iloc[idx]['StrategyFull']
            st.session_state.portfolio_allocation[full_strat] = float(row['Multiplier'])
            st.session_state.category_overrides[full_strat] = row['Category']
            st.session_state.option_strategy_overrides[full_strat] = row['OptStrategy']

        # === BUTTON LAYOUT: Section headers, then Reset/Kelly%/MinPL, then action buttons ===
        st.markdown("")

        # Row 1: Section headers for all three columns
        calc_col, kelly_col, mart_col = st.columns([1, 1, 1])

        with calc_col:
            st.markdown("""
                <div style="font-size: 12px; color: #6B7280; font-weight: 600; margin-bottom: 5px; text-align: center;">
                    PORTFOLIO METRICS
                </div>
            """, unsafe_allow_html=True)

        with kelly_col:
            st.markdown("""
                <div style="font-size: 12px; color: #6B7280; font-weight: 600; margin-bottom: 5px; text-align: center;">
                    KELLY OPTIMIZER
                </div>
            """, unsafe_allow_html=True)

        with mart_col:
            st.markdown("""
                <div style="font-size: 12px; color: #6B7280; font-weight: 600; margin-bottom: 5px; text-align: center;">
                    MART OPTIMIZER
                </div>
            """, unsafe_allow_html=True)

        # Row 2: Reset/Set to 0 links under PORTFOLIO METRICS, Kelly% and Min P/L inputs
        input_col1, input_col2, input_col3 = st.columns([1, 1, 1])

        with input_col1:
            # Reset and Set to 0 links under PORTFOLIO METRICS
            reset_sub1, reset_sub2 = st.columns(2)
            with reset_sub1:
                if st.button("Reset", key="reset_btn", type="tertiary", use_container_width=True):
                    st.session_state.portfolio_allocation = {s: 1.0 for s in strategies}
                    st.session_state.calculate_kpis = False
                    st.session_state.allocation_editor_version += 1
                    st.rerun()
            with reset_sub2:
                if st.button("Set to 0", key="zero_btn", type="tertiary", use_container_width=True):
                    st.session_state.portfolio_allocation = {s: 0.0 for s in strategies}
                    st.session_state.calculate_kpis = False
                    st.session_state.allocation_editor_version += 1
                    st.rerun()

        with input_col2:
            kelly_input = st.number_input("Kelly %", 5, 100, st.session_state.kelly_pct, 5, key="kelly_input")
            st.session_state.kelly_pct = kelly_input

        with input_col3:
            mart_min_pnl = st.number_input("Min P/L ($)", value=st.session_state.mart_min_pnl, step=1000, key="mart_min_pnl_input")
            st.session_state.mart_min_pnl = mart_min_pnl

        # Row 3: Buttons row - all three on same level
        btn_col1, btn_col2, btn_col3 = st.columns([1, 1, 1])

        with btn_col1:
            if st.button("CALCULATE", use_container_width=True, type="primary"):
                st.session_state.calculate_kpis = True
                st.rerun()

        with btn_col2:
            if st.button("RUN KELLY", use_container_width=True, type="primary", key="run_kelly_btn"):
                try:
                    with placeholder:
                        ui.show_loading_overlay("Optimizing", "Running Kelly optimization...")
                    optimized = calc.kelly_optimize_allocation(
                        strategy_base_stats, target_margin, kelly_input/100,
                        workhorse_pct/100, airbag_pct/100, opportunist_pct/100,
                        st.session_state.category_overrides
                    )
                    st.session_state.portfolio_allocation = optimized
                    st.session_state.calculate_kpis = True
                    # Increment editor version to force data_editor to refresh with new values
                    st.session_state.allocation_editor_version += 1
                finally:
                    placeholder.empty()
                st.rerun()

        with btn_col3:
            if st.button("RUN MART", use_container_width=True, type="primary", key="run_mart_btn"):
                try:
                    with placeholder:
                        ui.show_loading_overlay("Optimizing", "Running MART optimization...")
                    optimized = calc.mart_optimize_allocation(
                        strategy_base_stats, target_margin, account_size,
                        st.session_state.category_overrides, full_date_range, filtered_df,
                        min_pnl=mart_min_pnl,
                        max_iterations=100  # Reasonable iteration count for optimization
                    )
                    st.session_state.portfolio_allocation = optimized
                    st.session_state.calculate_kpis = True
                    # Increment editor version to force data_editor to refresh with new values
                    st.session_state.allocation_editor_version += 1
                finally:
                    placeholder.empty()
                st.rerun()

    if not st.session_state.get('calculate_kpis', False):
        st.info("Adjust allocations and click CALCULATE to see projected performance.")
        return

    # Show loading while calculating (will be cleared after metrics are computed)
    with placeholder:
        ui.show_loading_overlay("Calculating", "Computing portfolio metrics...")

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
                s_margin = stats['margin_per_contract'] * mult
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
        # Note: main_nav_radio will be synced in app.py before widget renders
        st.rerun()

    # === VISUALIZATION TABS ===
    viz_tab1, viz_tab2, viz_tab3, viz_tab4, viz_tab5 = st.tabs([
        "Equity & DD", "Allocation", "Margin", "Correlation", "Greek Exposure"
    ])

    with viz_tab1:
        # Strategy selection for charts - pre-select all strategies
        active_strats = [s for s, mult in st.session_state.portfolio_allocation.items() if mult > 0 and s in strategy_base_stats]
        chart_strats = st.multiselect(
            "Select strategies to display:",
            options=["Total Portfolio", "SPX Benchmark"] + active_strats,
            default=["Total Portfolio"] + active_strats,  # Pre-select all
            key="eq_chart_strat_select_v2"
        )

        with st.container(border=True):
            ui.section_header("Equity Growth",
                description="Cumulative equity growth over the evaluation period.")

            fig_eq = go.Figure()

            # Add total portfolio line if selected
            if "Total Portfolio" in chart_strats:
                fig_eq.add_trace(go.Scatter(x=port_equity.index, y=port_equity.values, name="Total Portfolio", line=dict(width=3, color=ui.COLOR_BLUE)))

            # Add SPX benchmark if selected
            if "SPX Benchmark" in chart_strats and spx is not None:
                # Normalize SPX to start at account_size
                spx_normalized = (spx / spx.iloc[0]) * account_size if len(spx) > 0 else None
                if spx_normalized is not None:
                    fig_eq.add_trace(go.Scatter(x=spx_normalized.index, y=spx_normalized.values, name="SPX Benchmark", line=dict(width=2, dash='dash', color='gray')))

            # Add individual strategy lines if selected
            for strat in chart_strats:
                if strat not in ["Total Portfolio", "SPX Benchmark"] and strat in strategy_base_stats:
                    mult = st.session_state.portfolio_allocation.get(strat, 1.0)
                    strat_pnl = strategy_base_stats[strat]['daily_pnl_series'] * mult
                    strat_equity = account_size + strat_pnl.cumsum()
                    fig_eq.add_trace(go.Scatter(x=strat_equity.index, y=strat_equity.values, name=strat[:25]))

            fig_eq.update_layout(xaxis_title=None, yaxis_title="Equity ($)", template="plotly_white", height=400, legend=dict(orientation="h", y=-0.15))
            fig_eq.add_hline(y=account_size, line_dash="dash", line_color="gray", annotation_text="Starting Capital")
            st.plotly_chart(fig_eq, use_container_width=True)

        with st.container(border=True):
            # Drawdown with toggle between $ and %
            dd_mode = st.radio("Drawdown Display:", ["Dollar ($)", "Percent (%)"], horizontal=True, key="dd_mode")

            if dd_mode == "Dollar ($)":
                ui.section_header("Drawdown ($)",
                    description="Dollar drawdown from peak equity over time.")

                fig_dd = go.Figure()

                if "Total Portfolio" in chart_strats:
                    dd_series = port_equity - port_equity.cummax()
                    fig_dd.add_trace(go.Scatter(x=dd_series.index, y=dd_series.values, fill='tozeroy', name="Total Portfolio", line=dict(color=ui.COLOR_CORAL)))

                for strat in chart_strats:
                    if strat not in ["Total Portfolio", "SPX Benchmark"] and strat in strategy_base_stats:
                        mult = st.session_state.portfolio_allocation.get(strat, 1.0)
                        strat_pnl = strategy_base_stats[strat]['daily_pnl_series'] * mult
                        strat_equity = account_size + strat_pnl.cumsum()
                        strat_dd = strat_equity - strat_equity.cummax()
                        fig_dd.add_trace(go.Scatter(x=strat_dd.index, y=strat_dd.values, name=strat[:25]))

                fig_dd.update_layout(xaxis_title=None, yaxis_title="Drawdown ($)", template="plotly_white", height=350, legend=dict(orientation="h", y=-0.2))
            else:
                ui.section_header("Drawdown (%)",
                    description="Percentage drawdown from peak equity over time.")

                fig_dd = go.Figure()

                if "Total Portfolio" in chart_strats:
                    dd_series_pct = (port_equity - port_equity.cummax()) / port_equity.cummax() * 100
                    fig_dd.add_trace(go.Scatter(x=dd_series_pct.index, y=dd_series_pct.values, fill='tozeroy', name="Total Portfolio", line=dict(color=ui.COLOR_CORAL)))

                for strat in chart_strats:
                    if strat not in ["Total Portfolio", "SPX Benchmark"] and strat in strategy_base_stats:
                        mult = st.session_state.portfolio_allocation.get(strat, 1.0)
                        strat_pnl = strategy_base_stats[strat]['daily_pnl_series'] * mult
                        strat_equity = account_size + strat_pnl.cumsum()
                        strat_dd_pct = (strat_equity - strat_equity.cummax()) / strat_equity.cummax() * 100
                        fig_dd.add_trace(go.Scatter(x=strat_dd_pct.index, y=strat_dd_pct.values, name=strat[:25]))

                fig_dd.update_layout(xaxis_title=None, yaxis_title="Drawdown (%)", template="plotly_white", height=350, legend=dict(orientation="h", y=-0.2))

            st.plotly_chart(fig_dd, use_container_width=True)

    with viz_tab2:
        with st.container(border=True):
            ui.section_header("Portfolio Allocation",
                description="Margin distribution by category and strategy.")

            # Two larger pie charts side by side
            pie_col1, pie_col2 = st.columns(2)

            with pie_col1:
                # Category allocation
                fig_cat = go.Figure(data=[go.Pie(
                    labels=['Workhorse', 'Airbag', 'Opportunist'],
                    values=[category_margin['Workhorse'], category_margin['Airbag'], category_margin['Opportunist']],
                    hole=0.4,
                    textinfo='label+percent',
                    marker=dict(colors=[ui.COLOR_BLUE, ui.COLOR_TEAL, ui.COLOR_CORAL])
                )])
                fig_cat.update_layout(title="Margin by Category", height=450, showlegend=True, legend=dict(orientation="h", y=-0.1))
                st.plotly_chart(fig_cat, use_container_width=True)

            with pie_col2:
                # Strategy allocation
                alloc_data = [{'Strategy': s[:25], 'StrategyFull': s, 'Margin': strategy_base_stats[s]['margin_per_contract'] * strategy_base_stats[s]['contracts_per_day'] * m_val}
                              for s, m_val in st.session_state.portfolio_allocation.items() if m_val > 0 and s in strategy_base_stats]
                if alloc_data:
                    df_pie = pd.DataFrame(alloc_data)
                    fig_strat = px.pie(df_pie, values='Margin', names='Strategy', title="Margin by Strategy",
                                       hover_data=['StrategyFull'])
                    fig_strat.update_layout(height=450, showlegend=True, legend=dict(orientation="h", y=-0.1))
                    fig_strat.update_traces(textposition='inside', textinfo='percent')
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
                description="Correlation matrix of daily P/L between strategies.")

            # Highlight Average Correlation prominently
            corr_color = "hero-teal" if avg_correlation < 0.3 else ("hero-neutral" if avg_correlation < 0.6 else "hero-coral")
            corr_hint = "Low (diversified)" if avg_correlation < 0.3 else ("Moderate" if avg_correlation < 0.6 else "High (concentrated)")
            st.markdown(f"""
                <div style="background: linear-gradient(135deg, #302BFF 0%, #00BFBF 100%); padding: 20px 30px;
                            border-radius: 12px; margin-bottom: 20px; text-align: center;">
                    <div style="font-size: 14px; color: rgba(255,255,255,0.8); text-transform: uppercase; letter-spacing: 1px;">
                        Average Portfolio Correlation
                    </div>
                    <div style="font-size: 48px; font-weight: 700; color: white; font-family: 'Exo 2', sans-serif;">
                        {avg_correlation:.2f}
                    </div>
                    <div style="font-size: 13px; color: rgba(255,255,255,0.9);">
                        {corr_hint} • Lower is better for diversification
                    </div>
                </div>
            """, unsafe_allow_html=True)

            if len(active_strategy_returns) > 1:
                corr_df = pd.DataFrame({s['name'][:15]: s['returns'] for s in active_strategy_returns})
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
