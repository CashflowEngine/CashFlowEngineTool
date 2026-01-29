import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import ui_components as ui
import calculations as calc

def page_meic_analysis(bt_df, live_df=None):
    """MEIC Deep Dive page - Enhanced with Entry Time Filter, Monthly Performance, and Equity Curves."""
    ui.render_page_header("MEIC DEEP DIVE")
    st.caption("Analyze and optimize your Multiple Entry Iron Condor strategies by entry time, performance, and market patterns.")

    # === SECTION 1: CONFIGURATION (Card) ===
    with st.container(border=True):
        ui.section_header("Configuration")

        # MEIC Explanation Box
        st.markdown("""
        <div style='background-color: #F0F4FF; padding: 14px 18px; border-radius: 8px; margin-bottom: 16px; font-size: 13px;'>
            <strong>What is MEIC?</strong><br>
            <strong>Multiple Entry Iron Condor</strong> - a strategy where Iron Condors are opened at different
            times throughout the trading day to diversify timing risk. This analysis helps you identify which
            entry times historically produce the best performance, allowing you to focus on profitable time
            windows and filter out underperforming ones.
        </div>
        """, unsafe_allow_html=True)

        # Data Source Toggle - now inside Configuration
        data_source = "Backtest Data"
        if live_df is not None and not live_df.empty:
            config_source_col, _ = st.columns([1, 2])
            with config_source_col:
                data_source = st.radio("Data Source:", ["Backtest Data", "Live Data"], horizontal=True, key="meic_source")

        target_df = live_df if data_source == "Live Data" and live_df is not None else bt_df

        if target_df is None or target_df.empty:
            st.warning("No data available.")
            return

        # Date range and Account Size in first row
        min_ts, max_ts = target_df['timestamp'].min(), target_df['timestamp'].max()

        config_c1, config_c2 = st.columns([1, 1])
        with config_c1:
            sel_dates = st.date_input("Period", [min_ts.date(), max_ts.date()],
                                      min_value=min_ts.date(), max_value=max_ts.date(), key="meic_dates")

        with config_c2:
            account_size = st.number_input("Account Size ($)", value=100000, step=5000, min_value=1000, key="meic_account")

        if len(sel_dates) != 2:
            return

        # Filter by date first
        target_df = target_df[
            (target_df['timestamp'].dt.date >= sel_dates[0]) &
            (target_df['timestamp'].dt.date <= sel_dates[1])
        ].copy()

        # Strategy selector - FULL WIDTH below Period and Account Size
        all_strats = sorted(list(target_df['strategy'].unique()))
        default_meics = [s for s in all_strats if "MEIC" in s.upper()]

        st.write("")
        selected_meics = st.multiselect(
            "Select Strategies (full width):",
            options=all_strats,
            default=default_meics,
            key="meic_strats",
            help="Select the MEIC strategies you want to analyze"
        )

        if not selected_meics:
            st.error("Please select at least one strategy.")
            return

    # Filter by strategy
    meic_df = target_df[target_df['strategy'].isin(selected_meics)].copy()

    # Check for entry time data
    if 'timestamp_open' not in meic_df.columns:
        st.error("No 'Entry Time' data available. Make sure your data contains 'timestamp_open' column.")
        return

    # Create entry time string
    meic_df['EntryTimeStr'] = meic_df['timestamp_open'].dt.strftime('%H:%M')

    # === ENTRY TIME FILTER (Card) ===
    with st.container(border=True):
        ui.section_header("Entry Time Filter")

        # Get all available entry times
        all_entry_times = sorted(meic_df['EntryTimeStr'].unique().tolist())

        # Calculate stats for each entry time to help user decide
        time_quick_stats = meic_df.groupby('EntryTimeStr')['pnl'].agg(['count', 'sum', 'mean'])
        time_quick_stats.columns = ['trades', 'total_pnl', 'avg_pnl']

        # Get times with positive P/L as default suggestion
        positive_times = time_quick_stats[time_quick_stats['total_pnl'] > 0].index.tolist()

        # Handle pending quick action - directly modify session state BEFORE widget creation
        pending_action = st.session_state.pop('_meic_pending_filter_action', None)
        if pending_action == 'all':
            st.session_state['meic_entry_time_filter'] = all_entry_times
        elif pending_action == 'none':
            st.session_state['meic_entry_time_filter'] = []
        elif pending_action == 'profitable':
            st.session_state['meic_entry_time_filter'] = positive_times

        # Determine default for first load only
        if 'meic_entry_time_filter' not in st.session_state:
            default_times = all_entry_times
        else:
            # Filter to only valid options (in case strategies changed)
            current_val = st.session_state.get('meic_entry_time_filter', all_entry_times)
            default_times = [t for t in current_val if t in all_entry_times]

        filter_col1, filter_col2 = st.columns([3, 1])

        with filter_col1:
            # Entry time multi-select
            selected_entry_times = st.multiselect(
                "Select Entry Times to Analyze:",
                options=all_entry_times,
                default=default_times,
                key="meic_entry_time_filter",
                help="Filter trades by entry time. Only selected times will be included in analysis."
            )

        with filter_col2:
            st.markdown("**Quick Actions**")
            qa_col1, qa_col2 = st.columns(2)
            with qa_col1:
                if st.button("All", key="meic_select_all", use_container_width=True, help="Select all entry times"):
                    st.session_state['_meic_pending_filter_action'] = 'all'
                    st.rerun()
            with qa_col2:
                if st.button("None", key="meic_select_none", use_container_width=True, help="Clear all selections"):
                    st.session_state['_meic_pending_filter_action'] = 'none'
                    st.rerun()

            if st.button("Profitable Only", key="meic_select_profitable", use_container_width=True,
                         help="Select only entry times with positive total P/L"):
                st.session_state['_meic_pending_filter_action'] = 'profitable'
                st.rerun()

        if not selected_entry_times:
            st.warning("Please select at least one entry time.")
            return

        # Apply entry time filter
        meic_df_filtered = meic_df[meic_df['EntryTimeStr'].isin(selected_entry_times)].copy()

        # Show filter summary
        filter_summary_col1, filter_summary_col2, filter_summary_col3 = st.columns(3)
        with filter_summary_col1:
            st.metric("Selected Times", f"{len(selected_entry_times)} / {len(all_entry_times)}")
        with filter_summary_col2:
            st.metric("Filtered Trades", f"{len(meic_df_filtered):,}")
        with filter_summary_col3:
            filtered_pnl = meic_df_filtered['pnl'].sum()
            unfiltered_pnl = meic_df['pnl'].sum()
            pnl_retained = (filtered_pnl / unfiltered_pnl * 100) if unfiltered_pnl != 0 else 0
            st.metric("P/L Retained", f"{pnl_retained:.1f}%", delta=f"${filtered_pnl:,.0f}")

    # === SECTION 2: KPI SUMMARY (for filtered data) ===
    # Calculate metrics for filtered data
    full_date_range = pd.date_range(start=sel_dates[0], end=sel_dates[1], freq='D')
    daily_pnl = meic_df_filtered.set_index('timestamp').resample('D')['pnl'].sum().reindex(full_date_range, fill_value=0)

    port_equity = account_size + daily_pnl.cumsum()
    port_returns = port_equity.pct_change().fillna(0)

    # Basic metrics
    total_pnl = meic_df_filtered['pnl'].sum()
    num_trades = len(meic_df_filtered)
    win_trades = (meic_df_filtered['pnl'] > 0).sum()
    win_rate = win_trades / num_trades if num_trades > 0 else 0

    # Calculate CAGR and Max DD
    days = len(port_returns)
    if days > 1:
        total_ret = daily_pnl.sum() / account_size
        cagr = (1 + total_ret) ** (365 / days) - 1 if total_ret > -1 else 0

        peak = port_equity.cummax()
        dd = (port_equity - peak) / peak
        max_dd = dd.min()
        max_dd_usd = (port_equity - peak).min()

        mar = cagr / abs(max_dd) if max_dd != 0 else 0
    else:
        cagr, max_dd, max_dd_usd, mar = 0, 0, 0, 0

    # KPI Row
    kpi_c1, kpi_c2, kpi_c3, kpi_c4, kpi_c5 = st.columns(5)
    with kpi_c1:
        ui.render_hero_metric("Total P/L", f"${total_pnl:,.0f}", "", "hero-teal" if total_pnl > 0 else "hero-coral")
    with kpi_c2:
        ui.render_hero_metric("CAGR", f"{cagr:.1%}", "", "hero-teal" if cagr > 0 else "hero-coral")
    with kpi_c3:
        ui.render_hero_metric("Max DD", f"{max_dd:.1%}", f"${abs(max_dd_usd):,.0f}", "hero-coral")
    with kpi_c4:
        ui.render_hero_metric("MAR Ratio", f"{mar:.2f}", "", "hero-teal" if mar > 1 else "hero-coral")
    with kpi_c5:
        ui.render_hero_metric("Win Rate", f"{win_rate:.1%}", f"{num_trades} trades", "hero-neutral")

    st.write("")

    # === SECTION 3: ENTRY TIME PERFORMANCE TABLE ===
    # Calculate stats for filtered times only
    time_stats = meic_df_filtered.groupby('EntryTimeStr').agg({
        'pnl': ['count', 'sum', 'mean'],
        'strategy': lambda x: ", ".join(sorted(set(x)))
    })
    time_stats.columns = ['Trades', 'Total P/L', 'Avg P/L', 'Strategies']

    win_counts = meic_df_filtered.groupby('EntryTimeStr').apply(lambda x: (x['pnl'] > 0).sum())
    trade_counts = meic_df_filtered.groupby('EntryTimeStr').size()
    time_stats['Win Rate'] = win_counts / trade_counts

    # Calculate MAR for each entry time
    time_mars = {}
    for entry_time in meic_df_filtered['EntryTimeStr'].unique():
        et_df = meic_df_filtered[meic_df_filtered['EntryTimeStr'] == entry_time]
        et_daily_pnl = et_df.set_index('timestamp').resample('D')['pnl'].sum().reindex(full_date_range, fill_value=0)
        et_equity = account_size + et_daily_pnl.cumsum()
        et_peak = et_equity.cummax()
        et_dd = ((et_equity - et_peak) / et_peak).min()
        et_total_ret = et_daily_pnl.sum() / account_size
        et_cagr = (1 + et_total_ret) ** (365 / len(full_date_range)) - 1 if et_total_ret > -1 else 0
        time_mars[entry_time] = et_cagr / abs(et_dd) if et_dd != 0 else 0

    time_stats['MAR'] = pd.Series(time_mars)

    filtered_stats = time_stats[time_stats['Trades'] >= 10].sort_values('MAR', ascending=False)

    # Entry Time Performance Card
    with st.container(border=True):
        ui.section_header("Performance by Entry Time",
            description="Analysis based on filtered entry times. Times with < 10 trades are hidden.")

        if filtered_stats.empty:
            st.warning("No entry times found with >= 10 trades.")
        else:
            tbl_col, chart_col = st.columns([1, 1])

            with tbl_col:
                # Style the dataframe
                def color_mar(val):
                    try:
                        if val >= 2:
                            return 'background-color: rgba(0, 210, 190, 0.3)'
                        elif val >= 1:
                            return 'background-color: rgba(255, 193, 7, 0.3)'
                        else:
                            return 'background-color: rgba(255, 46, 77, 0.3)'
                    except:
                        return ''

                styled_stats = filtered_stats.style.format({
                    'Total P/L': '${:,.0f}',
                    'Avg P/L': '${:,.0f}',
                    'Win Rate': '{:.1%}',
                    'MAR': '{:.2f}'
                }).map(color_mar, subset=['MAR'])

                st.dataframe(styled_stats, use_container_width=True, height=450)

            with chart_col:
                chart_metric = st.radio("Chart Metric:", ["MAR", "Total P/L", "Avg P/L", "Win Rate"], horizontal=True, key="meic_chart_metric")

                # Create bar chart with color based on value
                if chart_metric == "MAR":
                    colors = [ui.COLOR_TEAL if v >= 2 else (ui.COLOR_CORAL if v < 1 else '#FFC107') for v in filtered_stats['MAR']]
                elif chart_metric == "Total P/L":
                    colors = [ui.COLOR_TEAL if v > 0 else ui.COLOR_CORAL for v in filtered_stats['Total P/L']]
                elif chart_metric == "Avg P/L":
                    colors = [ui.COLOR_TEAL if v > 0 else ui.COLOR_CORAL for v in filtered_stats['Avg P/L']]
                else:
                    colors = [ui.COLOR_TEAL if v >= 0.5 else ui.COLOR_CORAL for v in filtered_stats['Win Rate']]

                fig_bar = go.Figure(data=[go.Bar(
                    x=filtered_stats.index,
                    y=filtered_stats[chart_metric],
                    marker_color=colors
                )])
                fig_bar.update_layout(
                    title=f"{chart_metric} by Entry Time",
                    template="plotly_white",
                    height=400,
                    xaxis_title="Entry Time",
                    yaxis_title=chart_metric
                )
                st.plotly_chart(fig_bar, use_container_width=True)

    st.write("")

    # === SECTION 4: MONTHLY PERFORMANCE (Card) ===
    with st.container(border=True):
        ui.section_header("Monthly Performance")

        meic_df_filtered['Year'] = meic_df_filtered['timestamp'].dt.year
        meic_df_filtered['Month'] = meic_df_filtered['timestamp'].dt.month

        monthly_mode = st.radio("Display:", ["Dollar P/L", "Percent Return"], horizontal=True, key="meic_monthly_mode", label_visibility="collapsed")

        month_names = {1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr', 5: 'May', 6: 'Jun',
                       7: 'Jul', 8: 'Aug', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dec'}

        # Helper function for styling
        def _color_monthly(val):
            try:
                if isinstance(val, str):
                    clean_val = val.replace('$', '').replace(',', '').replace('%', '').strip()
                    num_val = float(clean_val)
                else:
                    num_val = float(val)

                if num_val > 0:
                    intensity = min(abs(num_val) / 5000, 1) if abs(num_val) > 100 else min(abs(num_val) / 10, 1)
                    return f'background-color: rgba(0, 210, 190, {0.1 + intensity * 0.4}); color: #065F46'
                elif num_val < 0:
                    intensity = min(abs(num_val) / 5000, 1) if abs(num_val) > 100 else min(abs(num_val) / 10, 1)
                    return f'background-color: rgba(255, 46, 77, {0.1 + intensity * 0.4}); color: #991B1B'
                else:
                    return 'background-color: white; color: #374151'
            except (ValueError, TypeError):
                return 'background-color: white; color: #374151'

        if "Dollar" in monthly_mode:
            pivot = meic_df_filtered.pivot_table(index='Year', columns='Month', values='pnl', aggfunc='sum').fillna(0)
            pivot['Total'] = pivot.sum(axis=1)
            pivot.loc['Average'] = pivot.mean()
            pivot.columns = [month_names.get(c, c) for c in pivot.columns]
            styled_pivot = pivot.style.map(_color_monthly).format("${:,.0f}")
        else:
            pivot = (meic_df_filtered.pivot_table(index='Year', columns='Month', values='pnl', aggfunc='sum').fillna(0) / account_size) * 100
            pivot['Total'] = pivot.sum(axis=1)
            pivot.loc['Average'] = pivot.mean()
            pivot.columns = [month_names.get(c, c) for c in pivot.columns]
            styled_pivot = pivot.style.map(_color_monthly).format("{:.1f}%")

        st.dataframe(styled_pivot, use_container_width=True)

    st.write("")

    # === SECTION 5: EQUITY CURVES BY STRATEGY (Card) ===
    with st.container(border=True):
        ui.section_header("Equity Curve by Strategy", description="Compare equity curves across selected strategies. Add individual strategies to see their performance overlay.")

        # Strategy selector for equity curves
        eq_strat_col1, eq_strat_col2 = st.columns([1, 5])
        with eq_strat_col1:
            if st.button("Select All", key="meic_eq_select_all", use_container_width=True):
                st.session_state.meic_equity_strategies = selected_meics
                st.rerun()

        default_eq_strats = st.session_state.get('meic_equity_strategies', None)
        if default_eq_strats is None:
            default_eq_strats = []
        else:
            default_eq_strats = [s for s in default_eq_strats if s in selected_meics]

        selected_eq_strategies = st.multiselect(
            "Add strategy lines to chart:",
            options=selected_meics,
            default=default_eq_strats,
            key="meic_equity_strats_select",
            placeholder="Select strategies to compare..."
        )
        st.session_state.meic_equity_strategies = selected_eq_strategies

        # Fetch SPX benchmark for the period
        spx = calc.fetch_spx_benchmark(pd.to_datetime(sel_dates[0]), pd.to_datetime(sel_dates[1]))

        # Create equity curve figure
        fig_eq = go.Figure()

        # Total portfolio equity (for filtered data)
        fig_eq.add_trace(go.Scatter(
            x=port_equity.index,
            y=port_equity,
            mode='lines',
            name='Combined Portfolio',
            line=dict(color=ui.COLOR_BLUE, width=3)
        ))

        # Add SPX benchmark if available
        if spx is not None and len(spx) > 0:
            # Normalize SPX to start at account_size
            spx_normalized = (spx / spx.iloc[0]) * account_size
            fig_eq.add_trace(go.Scatter(
                x=spx_normalized.index,
                y=spx_normalized,
                mode='lines',
                name='SPX Benchmark',
                line=dict(color='gray', width=2, dash='dot')
            ))

        # Add starting line
        fig_eq.add_hline(y=account_size, line_dash="dash", line_color="lightgray")

        # Color palette for strategies
        strategy_colors = px.colors.qualitative.Set2 + px.colors.qualitative.Pastel1 + px.colors.qualitative.Dark2

        # Add individual strategy equity curves
        for i, strat in enumerate(selected_eq_strategies):
            strat_data = meic_df_filtered[meic_df_filtered['strategy'] == strat]
            if not strat_data.empty:
                s_daily_pnl = strat_data.set_index('timestamp').resample('D')['pnl'].sum()
                s_daily_pnl = s_daily_pnl.reindex(full_date_range, fill_value=0)
                s_equity = account_size + s_daily_pnl.cumsum()
                color = strategy_colors[i % len(strategy_colors)]
                fig_eq.add_trace(go.Scatter(
                    x=s_equity.index,
                    y=s_equity,
                    mode='lines',
                    name=strat,
                    line=dict(color=color, width=2)
                ))

        # Calculate dynamic height based on legend items
        num_legend_items = 1 + len(selected_eq_strategies)
        legend_rows = (num_legend_items + 2) // 3
        extra_height = max(0, (legend_rows - 2) * 25)

        fig_eq.update_layout(
            template="plotly_white",
            height=500 + extra_height,
            legend=dict(
                orientation="h",
                yanchor="top",
                y=-0.12,
                xanchor="center",
                x=0.5,
                bgcolor="rgba(255,255,255,0.95)",
                bordercolor="rgba(0,0,0,0.1)",
                borderwidth=1,
                font=dict(size=9)
            ),
            margin=dict(l=20, r=20, t=40, b=20 + (legend_rows * 30)),
            hovermode='x unified',
            yaxis_title="Portfolio Value ($)"
        )

        st.plotly_chart(fig_eq, use_container_width=True)

    # === Strategy Performance Comparison (Card) ===
    if selected_eq_strategies:
        with st.container(border=True):
            ui.section_header("Strategy Performance Comparison", description="Side-by-side comparison of selected strategies' key metrics.")

            strat_perf = []
            for strat in selected_eq_strategies:
                strat_data = meic_df_filtered[meic_df_filtered['strategy'] == strat]
                if not strat_data.empty:
                    s_pnl = strat_data['pnl'].sum()
                    s_trades = len(strat_data)
                    s_win_rate = (strat_data['pnl'] > 0).mean()
                    s_avg_pnl = strat_data['pnl'].mean()
                    # Calculate required margin from the margin column
                    s_margin_series = calc.generate_daily_margin_series_optimized(strat_data)
                    s_max_margin = s_margin_series.max() if not s_margin_series.empty else 0
                    strat_perf.append({
                        'Strategy': strat,
                        'Total P/L': s_pnl,
                        'Trades': s_trades,
                        'Win Rate': s_win_rate,
                        'Avg Trade': s_avg_pnl,
                        'Required Margin': s_max_margin
                    })

            if strat_perf:
                perf_df = pd.DataFrame(strat_perf)
                st.dataframe(
                    perf_df.style.format({
                        'Total P/L': '${:,.0f}',
                        'Win Rate': '{:.1%}',
                        'Avg Trade': '${:,.0f}',
                        'Required Margin': '${:,.0f}'
                    }),
                    use_container_width=True,
                    hide_index=True
                )

    st.write("")

    # === SECTION 6: ENTRY TIME HEATMAP (Day × Time) (Card) ===
    with st.container(border=True):
        ui.section_header("Entry Time × Day of Week Heatmap", description="Analyze performance patterns by entry time and day of week. Green indicates profitable cells, red indicates losses.")

        meic_df_filtered['DayOfWeek'] = meic_df_filtered['timestamp_open'].dt.day_name()

        heatmap_metric = st.radio("Heatmap Metric:", ["Total P/L", "Avg P/L", "Win Rate", "Trade Count"], horizontal=True, key="meic_heatmap_metric")

        # Create pivot table
        if heatmap_metric == "Total P/L":
            heat_pivot = meic_df_filtered.pivot_table(index='EntryTimeStr', columns='DayOfWeek', values='pnl', aggfunc='sum').fillna(0)
            colorscale = 'RdYlGn'
        elif heatmap_metric == "Avg P/L":
            heat_pivot = meic_df_filtered.pivot_table(index='EntryTimeStr', columns='DayOfWeek', values='pnl', aggfunc='mean').fillna(0)
            colorscale = 'RdYlGn'
        elif heatmap_metric == "Win Rate":
            heat_pivot = meic_df_filtered.pivot_table(index='EntryTimeStr', columns='DayOfWeek', values='pnl', aggfunc=lambda x: (x > 0).mean()).fillna(0)
            colorscale = 'RdYlGn'
        else:
            heat_pivot = meic_df_filtered.pivot_table(index='EntryTimeStr', columns='DayOfWeek', values='pnl', aggfunc='count').fillna(0)
            colorscale = 'Blues'

        # Reorder days
        day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
        heat_pivot = heat_pivot.reindex(columns=[d for d in day_order if d in heat_pivot.columns])

        # Only show times with data
        heat_pivot = heat_pivot[heat_pivot.sum(axis=1) != 0]

        if not heat_pivot.empty:
            # Determine text format based on metric
            if heatmap_metric in ["Total P/L", "Avg P/L"]:
                text_template = "%{text:.0f}"
            elif heatmap_metric == "Win Rate":
                text_template = "%{text:.1%}"
            else:
                text_template = "%{text:.0f}"

            fig_heat = go.Figure(data=go.Heatmap(
                z=heat_pivot.values,
                x=heat_pivot.columns,
                y=heat_pivot.index,
                colorscale=colorscale,
                text=heat_pivot.values,
                texttemplate=text_template,
                textfont={"size": 14},
                hovertemplate="Time: %{y}<br>Day: %{x}<br>Value: %{z:.2f}<extra></extra>"
            ))

            fig_heat.update_layout(
                template="plotly_white",
                height=max(500, len(heat_pivot) * 28),
                xaxis_title="Day of Week",
                yaxis_title="Entry Time",
                margin=dict(l=80, r=20, t=40, b=60)
            )

            st.plotly_chart(fig_heat, use_container_width=True)
        else:
            st.warning("Not enough data to generate heatmap.")
