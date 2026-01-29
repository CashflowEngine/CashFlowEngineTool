import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
import ui_components as ui

def page_comparison(bt_df_arg=None, live_df_arg=None):
    """Live vs Backtest comparison page - COMPLETE."""
    ui.render_page_header("REALITY CHECK")

    # Use arguments if provided, otherwise fall back to session state
    if bt_df_arg is not None:
        bt_df = bt_df_arg.copy()
    elif 'full_df' in st.session_state:
        bt_df = st.session_state['full_df'].copy()
    else:
        st.warning("Please upload Backtest data.")
        return

    if live_df_arg is not None:
        live_df = live_df_arg.copy() if not live_df_arg.empty else pd.DataFrame()
    elif 'live_df' in st.session_state:
        live_df = st.session_state['live_df'].copy()
    else:
        live_df = pd.DataFrame()

    if live_df is None or live_df.empty:
        st.warning("Live data is empty. Please upload live trading data to compare.")
        return

    # Ensure timestamps are datetime
    if not np.issubdtype(live_df['timestamp'].dtype, np.datetime64):
        live_df['timestamp'] = pd.to_datetime(live_df['timestamp'], errors='coerce')
    if bt_df is not None and not bt_df.empty and not np.issubdtype(bt_df['timestamp'].dtype, np.datetime64):
        bt_df['timestamp'] = pd.to_datetime(bt_df['timestamp'], errors='coerce')

    # Get date range from live data
    live_min_ts = live_df['timestamp'].min()
    live_max_ts = live_df['timestamp'].max()

    # Get date range from backtest data
    bt_min_ts = bt_df['timestamp'].min() if bt_df is not None and not bt_df.empty else None
    bt_max_ts = bt_df['timestamp'].max() if bt_df is not None and not bt_df.empty else None

    # Get strategies for comparison
    live_strategies = sorted(live_df['strategy'].unique())
    bt_strategies = sorted(bt_df['strategy'].unique()) if bt_df is not None and not bt_df.empty else []

    # === SECTION 0: STRATEGY MAPPING OVERVIEW (Card) ===
    with st.container(border=True):
        ui.section_header("Strategy Mapping Overview",
            description="Review and map all strategies between your live trading and backtest data.")

        # Build automatic mapping
        auto_mapping = {}
        unmapped_live = []
        unmapped_bt = list(bt_strategies)

        for live_s in live_strategies:
            matched = None
            for bt_s in bt_strategies:
                # Try various matching strategies
                if bt_s == live_s:
                    matched = bt_s
                    break
                if bt_s in live_s or live_s in bt_s:
                    matched = bt_s
                    break
                # Try matching by core name (without prefixes/suffixes)
                live_core = live_s.replace('_', ' ').replace('-', ' ').upper()
                bt_core = bt_s.replace('_', ' ').replace('-', ' ').upper()
                if live_core in bt_core or bt_core in live_core:
                    matched = bt_s
                    break

            if matched:
                auto_mapping[live_s] = matched
                if matched in unmapped_bt:
                    unmapped_bt.remove(matched)
            else:
                unmapped_live.append(live_s)

        # Display mapping table
        mapping_data = []
        for live_s in live_strategies:
            bt_match = auto_mapping.get(live_s, "Not Matched")
            status = "Matched" if live_s in auto_mapping else "Unmapped"
            mapping_data.append({
                'Live Strategy': live_s,
                'Backtest Strategy': bt_match,
                'Status': status
            })

        mapping_df = pd.DataFrame(mapping_data)

        # Style the status column
        def color_status(val):
            if val == "Matched":
                return 'background-color: rgba(0, 210, 190, 0.2); color: #065F46'
            else:
                return 'background-color: rgba(255, 46, 77, 0.2); color: #991B1B'

        st.dataframe(
            mapping_df.style.map(color_status, subset=['Status']),
            use_container_width=True,
            hide_index=True,
            height=min(300, 35 + len(mapping_df) * 35)
        )

        # Show warnings for unmapped strategies
        if unmapped_live:
            st.warning(f"**Unmapped Live Strategies:** {', '.join(unmapped_live)}")
            st.markdown("""
            <div style='background-color: #FEF3C7; padding: 12px 16px; border-radius: 8px; margin-top: 8px; font-size: 12px;'>
                <strong>Suggestions for unmapped strategies:</strong><br>
                • Verify strategy names match between live and backtest data<br>
                • Check for typos or different naming conventions<br>
                • Some live strategies may not have backtest equivalents (new strategies)
            </div>
            """, unsafe_allow_html=True)

        if unmapped_bt:
            st.info(f"**Backtest strategies without live matches:** {', '.join(unmapped_bt)}")

    # === SECTION 0.5: DATA MISMATCH ANALYSIS (Card) ===
    with st.container(border=True):
        ui.section_header("Data Coverage Analysis",
            description="Compare date ranges and identify gaps between live and backtest data.")

        col_live, col_bt = st.columns(2)

        with col_live:
            st.markdown("**Live Data**")
            st.markdown(f"""
            - Date Range: **{live_min_ts.strftime('%Y-%m-%d') if pd.notna(live_min_ts) else 'N/A'}** to **{live_max_ts.strftime('%Y-%m-%d') if pd.notna(live_max_ts) else 'N/A'}**
            - Trading Days: **{live_df['timestamp'].dt.date.nunique()}**
            - Strategies: **{len(live_strategies)}**
            - Total Trades: **{len(live_df):,}**
            """)

        with col_bt:
            st.markdown("**Backtest Data**")
            st.markdown(f"""
            - Date Range: **{bt_min_ts.strftime('%Y-%m-%d') if pd.notna(bt_min_ts) else 'N/A'}** to **{bt_max_ts.strftime('%Y-%m-%d') if pd.notna(bt_max_ts) else 'N/A'}**
            - Trading Days: **{bt_df['timestamp'].dt.date.nunique() if bt_df is not None and not bt_df.empty else 0}**
            - Strategies: **{len(bt_strategies)}**
            - Total Trades: **{len(bt_df) if bt_df is not None else 0:,}**
            """)

        # Check for date mismatches
        issues = []
        suggestions = []

        if pd.notna(bt_min_ts) and pd.notna(live_min_ts):
            if bt_max_ts < live_min_ts:
                issues.append("Backtest data ends before live data starts - no overlap period.")
                suggestions.append("Update your backtest to include dates from your live trading period.")
            elif bt_min_ts > live_min_ts:
                issues.append(f"Backtest starts later ({bt_min_ts.strftime('%Y-%m-%d')}) than live data ({live_min_ts.strftime('%Y-%m-%d')}).")
                suggestions.append("Some live trades may not have backtest comparison data.")

        if pd.notna(bt_max_ts) and pd.notna(live_max_ts) and bt_max_ts < live_max_ts:
            issues.append(f"Backtest ends ({bt_max_ts.strftime('%Y-%m-%d')}) before live data ends ({live_max_ts.strftime('%Y-%m-%d')}).")
            suggestions.append("Update your backtest to cover the full live trading period.")

        if len(bt_strategies) < len(live_strategies):
            issues.append(f"Fewer backtest strategies ({len(bt_strategies)}) than live strategies ({len(live_strategies)}).")
            suggestions.append("Some live strategies may not have backtest equivalents.")

        if issues:
            st.markdown("**Data Coverage Issues:**")
            for i, issue in enumerate(issues):
                st.markdown(f"""
                <div style='background-color: #FEE2E2; padding: 10px 14px; border-radius: 6px; margin: 4px 0; font-size: 12px;'>
                    <strong style='color: #991B1B;'>Issue:</strong> {issue}<br>
                    <strong style='color: #065F46;'>Suggestion:</strong> {suggestions[i] if i < len(suggestions) else 'Review data sources.'}
                </div>
                """, unsafe_allow_html=True)
        else:
            st.success("Data coverage looks good! Both datasets have overlapping date ranges.")

    # === SECTION 1: CONFIGURATION (Card) ===
    with st.container(border=True):
        ui.section_header("Analysis Configuration", description="Set the evaluation period and select strategies to compare.")

        # Context about the data source
        st.markdown(f"""
        <div style='background-color: #F0F4FF; padding: 14px 18px; border-radius: 8px; margin-bottom: 16px; font-size: 13px;'>
            <strong>Data Period:</strong> This analysis uses your <strong>Live trading data</strong> as the baseline period.<br>
            Live data range: <strong>{live_min_ts.strftime('%Y-%m-%d') if pd.notna(live_min_ts) else 'N/A'}</strong> to
            <strong>{live_max_ts.strftime('%Y-%m-%d') if pd.notna(live_max_ts) else 'N/A'}</strong>
            ({(live_max_ts - live_min_ts).days if pd.notna(live_min_ts) and pd.notna(live_max_ts) else 0} days) •
            {len(live_strategies)} strategies • {len(live_df)} total trades
        </div>
        """, unsafe_allow_html=True)

        # Date range
        config_c1, config_c2, config_c3 = st.columns([1, 1, 2])

        with config_c1:
            data_start = live_min_ts.date() if pd.notna(live_min_ts) else pd.Timestamp.now().date()
            data_end = live_max_ts.date() if pd.notna(live_max_ts) else pd.Timestamp.now().date()

            comp_presets = {
                "Full Period": (data_start, data_end),
                "Last Month": (max((pd.Timestamp(data_end) - pd.DateOffset(months=1)).date(), data_start), data_end),
                "Last Quarter": (max((pd.Timestamp(data_end) - pd.DateOffset(months=3)).date(), data_start), data_end),
                "Last 6 Months": (max((pd.Timestamp(data_end) - pd.DateOffset(months=6)).date(), data_start), data_end),
                "Year to Date": (max(pd.Timestamp(data_end.year, 1, 1).date(), data_start), data_end),
                "Custom": None
            }

            comp_preset = st.selectbox("Quick Select:", list(comp_presets.keys()), key="comp_date_preset")

        with config_c2:
            if comp_preset != "Custom" and comp_presets[comp_preset] is not None:
                preset_start, preset_end = comp_presets[comp_preset]
                default_comp_dates = [preset_start, preset_end]
            else:
                default_comp_dates = [data_start, data_end]

            selected_comp_dates = st.date_input("Analysis Period", default_comp_dates,
                                                min_value=data_start, max_value=data_end, key="comp_dates_input")

        # Filter data by selected dates
        if len(selected_comp_dates) == 2:
            live_df = live_df[
                (live_df['timestamp'].dt.date >= selected_comp_dates[0]) &
                (live_df['timestamp'].dt.date <= selected_comp_dates[1])
            ].copy()
            if bt_df is not None and not bt_df.empty:
                bt_df = bt_df[
                    (bt_df['timestamp'].dt.date >= selected_comp_dates[0]) &
                    (bt_df['timestamp'].dt.date <= selected_comp_dates[1])
                ].copy()

        # Update strategy lists after date filtering
        bt_strategies_filtered = sorted(bt_df['strategy'].unique()) if bt_df is not None and not bt_df.empty else []
        live_strategies_filtered = sorted(live_df['strategy'].unique())

        with config_c3:
            st.markdown("**Strategy Selection**")
            # Single dropdown for strategy selection
            selected_strategy = st.selectbox(
                "Select Live Strategy to Analyze:",
                options=live_strategies_filtered,
                key="comp_live_strategy"
            )

            # Find best matching backtest strategy using the auto-mapping or manual selection
            default_bt_ix = 0
            if selected_strategy in auto_mapping:
                bt_match = auto_mapping[selected_strategy]
                if bt_match in bt_strategies_filtered:
                    default_bt_ix = bt_strategies_filtered.index(bt_match)
            else:
                for k, bt_s in enumerate(bt_strategies_filtered):
                    if bt_s in selected_strategy or selected_strategy in bt_s:
                        default_bt_ix = k
                        break

            mapped_bt_strategy = st.selectbox(
                "Map to Backtest Strategy:",
                options=bt_strategies_filtered,
                index=default_bt_ix,
                key="comp_bt_strategy"
            )

    # Create mapping for selected strategy
    mapping = {selected_strategy: mapped_bt_strategy}

    # === SECTION 2: PORTFOLIO OVERVIEW (Card) ===
    with st.container(border=True):
        ui.section_header("Portfolio Overview", description="Comparison of live trading vs backtest performance for the selected strategy.")

        # Get mapped data
        s_live = live_df[live_df['strategy'] == selected_strategy].copy().sort_values('timestamp')
        s_bt = bt_df[bt_df['strategy'] == mapped_bt_strategy].copy() if bt_df is not None and not bt_df.empty else pd.DataFrame()

        if s_live.empty:
            st.warning("No live trades for selected strategy.")
            return

        s_start = s_live['timestamp'].min()
        if not s_bt.empty and pd.notna(s_start):
            s_bt = s_bt[s_bt['timestamp'] >= s_start].sort_values('timestamp')

        if s_bt.empty:
            st.warning("Backtest has no data from the live start date.")
            return

        # Calculate metrics
        pl_live = s_live['pnl'].sum()
        pl_bt = s_bt['pnl'].sum()
        diff = pl_live - pl_bt
        real_rate = (pl_live / pl_bt * 100) if pl_bt != 0 else 0

        # Trade counts
        live_trades = len(s_live)
        bt_trades = len(s_bt)

        # Win rates
        live_wins = (s_live['pnl'] > 0).sum()
        bt_wins = (s_bt['pnl'] > 0).sum()
        live_wr = live_wins / live_trades if live_trades > 0 else 0
        bt_wr = bt_wins / bt_trades if bt_trades > 0 else 0

        # Calculate additional statistics
        live_avg_win = s_live[s_live['pnl'] > 0]['pnl'].mean() if live_wins > 0 else 0
        live_avg_loss = s_live[s_live['pnl'] <= 0]['pnl'].mean() if (live_trades - live_wins) > 0 else 0
        bt_avg_win = s_bt[s_bt['pnl'] > 0]['pnl'].mean() if bt_wins > 0 else 0
        bt_avg_loss = s_bt[s_bt['pnl'] <= 0]['pnl'].mean() if (bt_trades - bt_wins) > 0 else 0

        # KPI Row 1
        m1, m2, m3, m4, m5, m6 = st.columns(6)
        with m1:
            ui.render_hero_metric("Live P/L", f"${pl_live:,.0f}", f"{live_trades} trades", "hero-teal" if pl_live > 0 else "hero-coral")
        with m2:
            ui.render_hero_metric("Backtest P/L", f"${pl_bt:,.0f}", f"{bt_trades} trades", "hero-neutral")
        with m3:
            ui.render_hero_metric("Net Slippage", f"${diff:,.0f}", "Live - Backtest", "hero-teal" if diff >= 0 else "hero-coral")
        with m4:
            ui.render_hero_metric("Realization Rate", f"{real_rate:.1f}%", "% of backtest captured", "hero-teal" if real_rate >= 80 else "hero-coral")
        with m5:
            wr_diff = (live_wr - bt_wr) * 100
            ui.render_hero_metric("Win Rate Diff", f"{wr_diff:+.1f}%", f"Live: {live_wr:.1%} vs BT: {bt_wr:.1%}", "hero-neutral")
        with m6:
            trade_diff = live_trades - bt_trades
            ui.render_hero_metric("Trade Count Diff", f"{trade_diff:+d}", f"L: {live_trades} vs B: {bt_trades}", "hero-neutral")

        st.write("")

        # KPI Row 2: Additional statistics
        s1, s2, s3, s4, s5, s6 = st.columns(6)
        with s1:
            ui.render_hero_metric("Live Avg Win", f"${live_avg_win:,.0f}", f"BT: ${bt_avg_win:,.0f}", "hero-neutral")
        with s2:
            ui.render_hero_metric("Live Avg Loss", f"${live_avg_loss:,.0f}", f"BT: ${bt_avg_loss:,.0f}", "hero-neutral")
        with s3:
            live_pf = abs(s_live[s_live['pnl'] > 0]['pnl'].sum() / s_live[s_live['pnl'] < 0]['pnl'].sum()) if s_live[s_live['pnl'] < 0]['pnl'].sum() != 0 else 0
            bt_pf = abs(s_bt[s_bt['pnl'] > 0]['pnl'].sum() / s_bt[s_bt['pnl'] < 0]['pnl'].sum()) if s_bt[s_bt['pnl'] < 0]['pnl'].sum() != 0 else 0
            ui.render_hero_metric("Profit Factor", f"{live_pf:.2f}", f"BT: {bt_pf:.2f}", "hero-neutral")
        with s4:
            live_best = s_live['pnl'].max() if not s_live.empty else 0
            bt_best = s_bt['pnl'].max() if not s_bt.empty else 0
            ui.render_hero_metric("Best Trade", f"${live_best:,.0f}", f"BT: ${bt_best:,.0f}", "hero-neutral")
        with s5:
            live_worst = s_live['pnl'].min() if not s_live.empty else 0
            bt_worst = s_bt['pnl'].min() if not s_bt.empty else 0
            ui.render_hero_metric("Worst Trade", f"${live_worst:,.0f}", f"BT: ${bt_worst:,.0f}", "hero-neutral")
        with s6:
            live_std = s_live['pnl'].std() if len(s_live) > 1 else 0
            bt_std = s_bt['pnl'].std() if len(s_bt) > 1 else 0
            ui.render_hero_metric("P/L Std Dev", f"${live_std:,.0f}", f"BT: ${bt_std:,.0f}", "hero-neutral")

        # Equity curves
        st.write("")
        cum_l = s_live.set_index('timestamp').resample('D')['pnl'].sum().fillna(0).cumsum()
        cum_b = s_bt.set_index('timestamp').resample('D')['pnl'].sum().fillna(0).cumsum()

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=cum_b.index, y=cum_b, name=f"Backtest: {mapped_bt_strategy}",
                                 line=dict(color='gray', dash='dot', width=2)))
        fig.add_trace(go.Scatter(x=cum_l.index, y=cum_l, name=f"Live: {selected_strategy}",
                                 line=dict(color=ui.COLOR_BLUE, width=3)))
        fig.update_layout(
            template="plotly_white",
            height=450,
            xaxis_title=None,
            yaxis_title="Cumulative P/L ($)",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig, use_container_width=True)

    # === SECTION 3: TRADE-BY-TRADE ANALYSIS (Card) ===
    with st.container(border=True):
        ui.section_header("Trade-by-Trade Deviation Analysis",
            description="Individual trade comparison showing the largest deviations between live and backtest results.")

        # Try to match trades by date
        s_live['trade_date'] = s_live['timestamp'].dt.date
        s_bt['trade_date'] = s_bt['timestamp'].dt.date

        # Daily P/L comparison
        live_daily = s_live.groupby('trade_date')['pnl'].sum().reset_index()
        live_daily.columns = ['Date', 'Live P/L']

        bt_daily = s_bt.groupby('trade_date')['pnl'].sum().reset_index()
        bt_daily.columns = ['Date', 'Backtest P/L']

        # Merge on date
        comparison_df = pd.merge(live_daily, bt_daily, on='Date', how='outer').fillna(0)
        comparison_df['Deviation'] = comparison_df['Live P/L'] - comparison_df['Backtest P/L']
        comparison_df['Deviation %'] = np.where(
            comparison_df['Backtest P/L'] != 0,
            (comparison_df['Deviation'] / abs(comparison_df['Backtest P/L'])) * 100,
            0
        )
        comparison_df = comparison_df.sort_values('Deviation')

        # Statistics
        stat_c1, stat_c2, stat_c3, stat_c4 = st.columns(4)
        with stat_c1:
            worst_dev = comparison_df['Deviation'].min()
            st.metric("Worst Deviation", f"${worst_dev:,.0f}")
        with stat_c2:
            best_dev = comparison_df['Deviation'].max()
            st.metric("Best Deviation", f"${best_dev:,.0f}")
        with stat_c3:
            avg_dev = comparison_df['Deviation'].mean()
            st.metric("Avg Daily Deviation", f"${avg_dev:,.0f}")
        with stat_c4:
            negative_days = (comparison_df['Deviation'] < 0).sum()
            total_days = len(comparison_df)
            st.metric("Underperform Days", f"{negative_days} / {total_days}", f"{negative_days/total_days*100:.0f}%")

        st.write("")

        # Show table with worst deviations
        st.markdown("**Days with Largest Negative Deviations (Underperformance)**")
        worst_10 = comparison_df.nsmallest(10, 'Deviation').copy()
        worst_10['Date'] = pd.to_datetime(worst_10['Date']).dt.strftime('%Y-%m-%d')

        def color_deviation(val):
            if val < 0:
                return f'background-color: rgba(255, 46, 77, {min(abs(val)/1000, 0.5)}); color: #991B1B'
            elif val > 0:
                return f'background-color: rgba(0, 210, 190, {min(abs(val)/1000, 0.5)}); color: #065F46'
            return ''

        st.dataframe(
            worst_10.style.format({
                'Live P/L': '${:,.0f}',
                'Backtest P/L': '${:,.0f}',
                'Deviation': '${:,.0f}',
                'Deviation %': '{:.1f}%'
            }).map(color_deviation, subset=['Deviation']),
            use_container_width=True,
            hide_index=True
        )

        st.write("")
        st.markdown("**Days with Largest Positive Deviations (Outperformance)**")
        best_10 = comparison_df.nlargest(10, 'Deviation').copy()
        best_10['Date'] = pd.to_datetime(best_10['Date']).dt.strftime('%Y-%m-%d')

        st.dataframe(
            best_10.style.format({
                'Live P/L': '${:,.0f}',
                'Backtest P/L': '${:,.0f}',
                'Deviation': '${:,.0f}',
                'Deviation %': '{:.1f}%'
            }).map(color_deviation, subset=['Deviation']),
            use_container_width=True,
            hide_index=True
        )

        # Deviation distribution chart
        st.write("")
        st.markdown("**Deviation Distribution Over Time**")

        # Sort by date for chart
        comparison_sorted = comparison_df.sort_values('Date')

        fig_dev = go.Figure()
        fig_dev.add_trace(go.Bar(
            x=comparison_sorted['Date'],
            y=comparison_sorted['Deviation'],
            marker_color=[ui.COLOR_TEAL if d >= 0 else ui.COLOR_CORAL for d in comparison_sorted['Deviation']],
            name='Daily Deviation'
        ))
        fig_dev.add_hline(y=0, line_dash="solid", line_color="gray")
        fig_dev.add_hline(y=avg_dev, line_dash="dash", line_color="blue", annotation_text=f"Avg: ${avg_dev:,.0f}")
        fig_dev.update_layout(
            template="plotly_white",
            height=400,
            xaxis_title="Date",
            yaxis_title="Deviation ($)",
            showlegend=False
        )
        st.plotly_chart(fig_dev, use_container_width=True)

    # === SECTION 4: ALL STRATEGIES COMPARISON (Card) ===
    with st.container(border=True):
        ui.section_header("All Strategies Quick Comparison",
            description="Overview of all available strategy mappings and their performance.")

        # Build comparison table for all strategies
        all_comparisons = []

        for live_s in live_strategies_filtered:
            # Use auto-mapping if available, otherwise try to find best match
            matched_bt = auto_mapping.get(live_s)
            if not matched_bt:
                for bt_s in bt_strategies_filtered:
                    if bt_s in live_s or live_s in bt_s:
                        matched_bt = bt_s
                        break

            if matched_bt:
                s_live_temp = live_df[live_df['strategy'] == live_s]
                s_bt_temp = bt_df[bt_df['strategy'] == matched_bt]

                if not s_live_temp.empty:
                    s_start = s_live_temp['timestamp'].min()
                    s_bt_temp = s_bt_temp[s_bt_temp['timestamp'] >= s_start] if not s_bt_temp.empty else s_bt_temp

                    live_pnl = s_live_temp['pnl'].sum()
                    bt_pnl = s_bt_temp['pnl'].sum() if not s_bt_temp.empty else 0
                    deviation = live_pnl - bt_pnl
                    realization = (live_pnl / bt_pnl * 100) if bt_pnl != 0 else 0

                    all_comparisons.append({
                        'Live Strategy': live_s,
                        'Backtest Strategy': matched_bt,
                        'Live P/L': live_pnl,
                        'Backtest P/L': bt_pnl,
                        'Deviation': deviation,
                        'Realization %': realization
                    })

        if all_comparisons:
            comp_df = pd.DataFrame(all_comparisons)
            st.dataframe(
                comp_df.style.format({
                    'Live P/L': '${:,.0f}',
                    'Backtest P/L': '${:,.0f}',
                    'Deviation': '${:,.0f}',
                    'Realization %': '{:.1f}%'
                }).map(color_deviation, subset=['Deviation']),
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No matching strategies found. Please manually map strategies above.")
