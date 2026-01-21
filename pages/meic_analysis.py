import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import ui_components as ui

def page_meic_analysis(bt_df, live_df=None):
    """MEIC Deep Dive analysis page."""

    # Header with consistent font
    ui.render_page_header(
        "MEIC DEEP DIVE",
        "Specialized analysis for Multiple Entry Iron Condors. Visualize performance based on entry times, market conditions, and specific trade parameters."
    )

    # === CONFIGURATION (Card) ===
    with st.container(border=True):
        ui.section_header("Configuration",
            description="Select data source, strategies, and time period for analysis.")

        # Data source selection
        col_source, col_period = st.columns(2)

        with col_source:
            data_options = ["Backtest Data"]
            if live_df is not None and not live_df.empty:
                data_options.append("Live Data")

            data_source = st.radio("Data Source:", data_options, horizontal=True, key="meic_data_source")

        target = live_df if data_source == "Live Data" and live_df is not None else bt_df

        if target is None or target.empty:
            st.warning("No data available for analysis.")
            return

        with col_period:
            # Time period selection
            min_date = target['timestamp'].min().date()
            max_date = target['timestamp'].max().date()
            date_range = st.date_input(
                "Time Period",
                [min_date, max_date],
                min_value=min_date,
                max_value=max_date,
                key="meic_date_range"
            )

        if len(date_range) != 2:
            return

        # Filter by date
        mask = (target['timestamp'].dt.date >= date_range[0]) & (target['timestamp'].dt.date <= date_range[1])
        target = target[mask].copy()

        # Strategy selection
        strats = st.multiselect(
            "Select Strategies",
            sorted(target['strategy'].unique()),
            default=list(target['strategy'].unique())[:5],  # Default to first 5
            key="meic_strats"
        )

    if not strats:
        st.info("Please select at least one strategy to analyze.")
        return

    df = target[target['strategy'].isin(strats)].copy()

    if 'timestamp_open' not in df.columns:
        st.warning("No Entry Time data found in dataset. This analysis requires 'timestamp_open' column.")

        # Show basic analysis without entry time
        with st.container(border=True):
            ui.section_header("Basic Performance Analysis",
                description="Entry time analysis not available. Showing general performance metrics.")

            basic_stats = df.groupby('strategy')['pnl'].agg(['count', 'sum', 'mean']).reset_index()
            basic_stats.columns = ['Strategy', 'Trades', 'Total P/L', 'Avg P/L']

            col1, col2 = st.columns(2)
            with col1:
                st.dataframe(
                    basic_stats.style.applymap(ui.color_monthly_performance, subset=['Total P/L', 'Avg P/L'])
                    .format({'Total P/L': '${:,.0f}', 'Avg P/L': '${:,.0f}'}),
                    use_container_width=True
                )
            with col2:
                fig = px.bar(basic_stats, x='Strategy', y='Total P/L', color='Total P/L',
                            color_continuous_scale='RdYlGn', title="Total P/L by Strategy")
                fig.update_layout(template="plotly_white")
                st.plotly_chart(fig, use_container_width=True)
        return

    # Entry time analysis
    df['EntryTime'] = df['timestamp_open'].dt.strftime('%H:%M')

    stats = df.groupby('EntryTime')['pnl'].agg(['count', 'sum', 'mean'])
    stats.columns = ['Trades', 'Total P/L', 'Avg P/L']

    # === ANALYSIS RESULTS (Card) ===
    with st.container(border=True):
        ui.section_header("Performance by Entry Time",
            description="Analysis of P/L based on trade entry times. Identify optimal entry windows.")

        col1, col2 = st.columns(2)
        with col1:
            st.dataframe(
                stats.style.applymap(ui.color_monthly_performance, subset=['Total P/L'])
                .format({'Total P/L': '${:,.0f}', 'Avg P/L': '${:,.0f}'}),
                use_container_width=True
            )

        with col2:
            fig = px.bar(stats, y='Total P/L', color='Total P/L',
                        color_continuous_scale='RdYlGn', title="Total P/L per Time Slot")
            fig.update_layout(template="plotly_white", height=400)
            st.plotly_chart(fig, use_container_width=True)

    # === ADDITIONAL ANALYSIS ===
    with st.container(border=True):
        ui.section_header("Strategy Comparison by Entry Time",
            description="Heatmap showing performance for each strategy at different entry times.")

        # Create pivot table for heatmap
        pivot = df.pivot_table(index='strategy', columns='EntryTime', values='pnl', aggfunc='sum').fillna(0)

        if not pivot.empty:
            fig_heat = px.imshow(
                pivot,
                color_continuous_scale='RdYlGn',
                aspect='auto',
                title="P/L Heatmap: Strategy vs Entry Time"
            )
            fig_heat.update_layout(height=max(300, len(strats) * 40))
            st.plotly_chart(fig_heat, use_container_width=True)

    # === PREMIUM ANALYSIS (if data available) ===
    if 'premium' in df.columns or 'target_premium' in df.columns:
        with st.container(border=True):
            ui.section_header("Premium Analysis",
                description="Compare target premiums vs actual premiums received.")

            if 'target_premium' in df.columns and 'premium' in df.columns:
                df['Premium Diff'] = df['premium'] - df['target_premium']
                premium_stats = df.groupby('strategy').agg({
                    'target_premium': 'mean',
                    'premium': 'mean',
                    'Premium Diff': 'mean'
                }).reset_index()
                premium_stats.columns = ['Strategy', 'Avg Target', 'Avg Actual', 'Avg Diff']

                st.dataframe(
                    premium_stats.style.format({
                        'Avg Target': '${:.2f}',
                        'Avg Actual': '${:.2f}',
                        'Avg Diff': '${:.2f}'
                    }),
                    use_container_width=True
                )
            elif 'premium' in df.columns:
                premium_by_time = df.groupby('EntryTime')['premium'].mean()
                fig_prem = px.bar(x=premium_by_time.index, y=premium_by_time.values,
                                 title="Average Premium by Entry Time")
                fig_prem.update_layout(template="plotly_white", xaxis_title="Entry Time", yaxis_title="Avg Premium ($)")
                st.plotly_chart(fig_prem, use_container_width=True)
