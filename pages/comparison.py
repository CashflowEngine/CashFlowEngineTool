import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
import ui_components as ui

def page_comparison(bt_df, live_df):
    """Reality Check: Backtest vs Live comparison page."""

    # Header with Exo 2 font
    st.markdown(f"""
        <h1 style="font-family: 'Exo 2', sans-serif !important; font-weight: 800 !important;
                   text-transform: uppercase; color: {ui.COLOR_GREY} !important; letter-spacing: 1px;">
            REALITY CHECK
        </h1>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style='color: #6B7280; font-size: 14px; line-height: 1.5; margin-bottom: 20px; font-family: Poppins, sans-serif;'>
        Compare your actual live trading execution against theoretical backtest results.
        Identify slippage, deviation, and performance gaps to refine your execution.
    </div>
    """, unsafe_allow_html=True)

    # Check for live data
    if live_df is None or live_df.empty:
        ui.render_data_required_overlay()
        st.warning("No Live Data loaded. Please import live trading data to use this comparison tool.")
        return

    # === STRATEGY MATCHING (Card) ===
    with st.container(border=True):
        ui.section_header("Strategy Matching",
            description="Match your backtest strategies with corresponding live trading strategies. Strategies may have different names between backtest and live data.")

        # Find common and unique strategies
        bt_strategies = set(bt_df['strategy'].unique()) if bt_df is not None and not bt_df.empty else set()
        live_strategies = set(live_df['strategy'].unique())

        common = list(bt_strategies & live_strategies)
        bt_only = list(bt_strategies - live_strategies)
        live_only = list(live_strategies - bt_strategies)

        # Initialize matching state
        if 'strategy_matching' not in st.session_state:
            st.session_state.strategy_matching = {s: s for s in common}

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Auto-Matched Strategies**")
            if common:
                for s in common[:10]:  # Show max 10
                    st.markdown(f"- {s}")
                if len(common) > 10:
                    st.caption(f"...and {len(common) - 10} more")
            else:
                st.info("No exact matches found.")

        with col2:
            st.markdown("**Manual Matching Required**")
            if live_only:
                for live_strat in live_only[:5]:  # Show max 5 for matching
                    if bt_only:
                        match = st.selectbox(
                            f"Match for '{live_strat[:30]}':",
                            options=["-- No Match --"] + list(bt_only),
                            key=f"match_{live_strat}"
                        )
                        if match != "-- No Match --":
                            st.session_state.strategy_matching[live_strat] = match

    # === CONFIGURATION (Card) ===
    with st.container(border=True):
        ui.section_header("Configuration")

        # Get all matchable strategies
        all_matched = list(st.session_state.strategy_matching.keys()) + common
        if not all_matched:
            st.warning("No strategies available for comparison.")
            return

        sel = st.selectbox("Select Strategy to Compare", sorted(set(all_matched)))

    if not sel:
        return

    # Get matching backtest strategy
    bt_strat = st.session_state.strategy_matching.get(sel, sel)

    b_full = bt_df[bt_df['strategy'] == bt_strat] if bt_strat in bt_df['strategy'].values else pd.DataFrame()
    l = live_df[live_df['strategy'] == sel]

    if b_full.empty:
        st.warning(f"No backtest data found for strategy: {bt_strat}")
        return

    if l.empty:
        st.warning(f"No live data found for strategy: {sel}")
        return

    # === TIME PERIOD MATCHING ===
    # Get live data date range
    live_start = l['timestamp'].min().date()
    live_end = l['timestamp'].max().date()
    bt_start = b_full['timestamp'].min().date()
    bt_end = b_full['timestamp'].max().date()

    # Filter backtest to match live period
    match_period = st.checkbox(
        f"Match time periods (Live: {live_start} to {live_end})",
        value=True,
        help="Filter backtest data to the same time period as live data for fair comparison."
    )

    if match_period:
        b = b_full[(b_full['timestamp'].dt.date >= live_start) & (b_full['timestamp'].dt.date <= live_end)]
        if b.empty:
            st.warning(f"No backtest data in live period ({live_start} to {live_end}). Showing full backtest.")
            b = b_full
        else:
            st.caption(f"Comparing: Live {live_start} to {live_end} | Backtest filtered to same period")
    else:
        b = b_full
        st.caption(f"Comparing: Live {live_start} to {live_end} | Backtest {bt_start} to {bt_end} (full period)")

    # === STATISTICAL COMPARISON (Card) ===
    with st.container(border=True):
        ui.section_header("Statistical Comparison",
            description="Side-by-side comparison of key metrics between backtest and live performance.")

        # Calculate metrics for both
        def calc_metrics(df):
            pnl = df['pnl']
            total = pnl.sum()
            trades = len(pnl)
            win_rate = (pnl > 0).mean() * 100
            avg_win = pnl[pnl > 0].mean() if len(pnl[pnl > 0]) > 0 else 0
            avg_loss = abs(pnl[pnl <= 0].mean()) if len(pnl[pnl <= 0]) > 0 else 0
            pf = pnl[pnl > 0].sum() / abs(pnl[pnl < 0].sum()) if pnl[pnl < 0].sum() != 0 else 0
            return {
                'Total P/L': total,
                'Trades': trades,
                'Win Rate': win_rate,
                'Avg Win': avg_win,
                'Avg Loss': avg_loss,
                'Profit Factor': pf
            }

        bt_metrics = calc_metrics(b)
        live_metrics = calc_metrics(l)

        # Display comparison table
        comparison_data = []
        for metric in bt_metrics.keys():
            bt_val = bt_metrics[metric]
            live_val = live_metrics[metric]

            if metric == 'Trades':
                diff = live_val - bt_val
                diff_str = f"{diff:+.0f}"
            elif metric in ['Win Rate']:
                diff = live_val - bt_val
                diff_str = f"{diff:+.1f}%"
            elif metric == 'Profit Factor':
                diff = live_val - bt_val
                diff_str = f"{diff:+.2f}"
            else:
                diff = live_val - bt_val
                diff_pct = (diff / abs(bt_val) * 100) if bt_val != 0 else 0
                diff_str = f"${diff:+,.0f} ({diff_pct:+.1f}%)"

            comparison_data.append({
                'Metric': metric,
                'Backtest': bt_val,
                'Live': live_val,
                'Difference': diff_str
            })

        comp_df = pd.DataFrame(comparison_data)

        # Format the dataframe
        st.dataframe(
            comp_df,
            column_config={
                "Backtest": st.column_config.NumberColumn(format="$%.0f" if comparison_data[0]['Metric'] == 'Total P/L' else None),
                "Live": st.column_config.NumberColumn(format="$%.0f" if comparison_data[0]['Metric'] == 'Total P/L' else None),
            },
            use_container_width=True,
            hide_index=True
        )

        # Key insight
        pnl_diff = live_metrics['Total P/L'] - bt_metrics['Total P/L']
        if pnl_diff >= 0:
            st.success(f"Live performance is ${pnl_diff:,.0f} better than backtest.")
        else:
            st.error(f"Live performance is ${abs(pnl_diff):,.0f} worse than backtest (slippage/deviation).")

    # === COMPARISON CHART (Card) ===
    with st.container(border=True):
        ui.section_header(f"Performance Comparison: {sel}",
            description="Cumulative P/L comparison showing backtest vs live execution over time.")

        c1, c2 = st.columns(2)
        with c1:
            ui.render_hero_metric("Backtest P/L", f"${b['pnl'].sum():,.0f}", "", "hero-neutral")
        with c2:
            color = "hero-teal" if l['pnl'].sum() >= b['pnl'].sum() else "hero-coral"
            ui.render_hero_metric("Live P/L", f"${l['pnl'].sum():,.0f}", "", color)

        # Cumulative comparison
        b_c = b.set_index('timestamp').sort_index()['pnl'].cumsum()
        l_c = l.set_index('timestamp').sort_index()['pnl'].cumsum()

        # Normalize start to 0
        b_c = b_c - b_c.iloc[0] if len(b_c) > 0 else b_c
        l_c = l_c - l_c.iloc[0] if len(l_c) > 0 else l_c

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=b_c.index, y=b_c, name="Backtest", line=dict(dash='dot', color='gray', width=2)))
        fig.add_trace(go.Scatter(x=l_c.index, y=l_c, name="Live", line=dict(color=ui.COLOR_BLUE, width=3)))
        fig.update_layout(
            template="plotly_white",
            height=500,
            xaxis_title=None,
            yaxis_title="Cumulative P/L ($)",
            legend=dict(orientation="h", y=-0.1)
        )
        st.plotly_chart(fig, use_container_width=True)

    # === TRADE DISTRIBUTION (Card) ===
    with st.container(border=True):
        ui.section_header("Trade Distribution Comparison",
            description="Distribution of individual trade P/L for backtest vs live.")

        col1, col2 = st.columns(2)

        with col1:
            fig_bt = go.Figure()
            fig_bt.add_trace(go.Histogram(x=b['pnl'], marker_color='gray', opacity=0.7, name='Backtest'))
            fig_bt.update_layout(title="Backtest Trade Distribution", template="plotly_white", height=300)
            st.plotly_chart(fig_bt, use_container_width=True)

        with col2:
            fig_live = go.Figure()
            fig_live.add_trace(go.Histogram(x=l['pnl'], marker_color=ui.COLOR_BLUE, opacity=0.7, name='Live'))
            fig_live.update_layout(title="Live Trade Distribution", template="plotly_white", height=300)
            st.plotly_chart(fig_live, use_container_width=True)

    # === ALL STRATEGIES OVERVIEW ===
    if len(common) > 1:
        with st.container(border=True):
            ui.section_header("All Matched Strategies Overview",
                description="Quick comparison across all matched strategies.")

            overview_data = []
            for strat in common[:20]:  # Limit to 20
                bt_pnl = bt_df[bt_df['strategy'] == strat]['pnl'].sum()
                live_pnl = live_df[live_df['strategy'] == strat]['pnl'].sum()
                diff = live_pnl - bt_pnl
                diff_pct = (diff / abs(bt_pnl) * 100) if bt_pnl != 0 else 0

                overview_data.append({
                    'Strategy': strat[:25],
                    'Backtest P/L': bt_pnl,
                    'Live P/L': live_pnl,
                    'Difference': diff,
                    'Diff %': diff_pct
                })

            ov_df = pd.DataFrame(overview_data).sort_values('Difference', ascending=False)

            st.dataframe(
                ov_df,
                column_config={
                    "Backtest P/L": st.column_config.NumberColumn(format="$%.0f"),
                    "Live P/L": st.column_config.NumberColumn(format="$%.0f"),
                    "Difference": st.column_config.NumberColumn(format="$%.0f"),
                    "Diff %": st.column_config.NumberColumn(format="%.1f%%")
                },
                use_container_width=True,
                hide_index=True
            )
