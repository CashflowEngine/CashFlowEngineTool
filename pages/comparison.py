import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import ui_components as ui

def page_comparison(bt_df_arg=None, live_df_arg=None):
    """Live vs Backtest comparison page - COMPLETE."""
    ui.render_page_header("⚖️ REALITY CHECK")

    # Use arguments if provided, otherwise fall back to session state
    if bt_df_arg is not None:
        bt_df = bt_df_arg.copy()
    elif 'full_df' in st.session_state:
        bt_df = st.session_state['full_df'].copy()
    else:
        st.warning("⚠️ Please upload Backtest data.")
        return

    if live_df_arg is not None:
        live_df = live_df_arg.copy() if not live_df_arg.empty else pd.DataFrame()
    elif 'live_df' in st.session_state:
        live_df = st.session_state['live_df'].copy()
    else:
        live_df = pd.DataFrame()

    if live_df is None or live_df.empty:
        st.warning("⚠️ Live data is empty.")
        return

    # Ensure timestamps are datetime
    if not np.issubdtype(live_df['timestamp'].dtype, np.datetime64):
        live_df['timestamp'] = pd.to_datetime(live_df['timestamp'], errors='coerce')
    if bt_df is not None and not bt_df.empty and not np.issubdtype(bt_df['timestamp'].dtype, np.datetime64):
        bt_df['timestamp'] = pd.to_datetime(bt_df['timestamp'], errors='coerce')

    # Get date range from live data
    live_min_ts = live_df['timestamp'].min()
    live_max_ts = live_df['timestamp'].max()

    # Evaluation period selector
    st.markdown("### 📅 Evaluation Period")
    col_preset, col_dates = st.columns(2)

    with col_preset:
        data_start = live_min_ts.date() if pd.notna(live_min_ts) else pd.Timestamp.now().date()
        data_end = live_max_ts.date() if pd.notna(live_max_ts) else pd.Timestamp.now().date()

        # Use data_end as reference point for presets, not today
        comp_presets = {
            "Full Period": (data_start, data_end),
            "Last Month": (max((pd.Timestamp(data_end) - pd.DateOffset(months=1)).date(), data_start), data_end),
            "Last Quarter": (max((pd.Timestamp(data_end) - pd.DateOffset(months=3)).date(), data_start), data_end),
            "Last 6 Months": (max((pd.Timestamp(data_end) - pd.DateOffset(months=6)).date(), data_start), data_end),
            "Year to Date": (max(pd.Timestamp(data_end.year, 1, 1).date(), data_start), data_end),
            "Custom": None
        }

        comp_preset = st.selectbox("Quick Select:", list(comp_presets.keys()), key="comp_date_preset")

    with col_dates:
        if comp_preset != "Custom" and comp_presets[comp_preset] is not None:
            preset_start, preset_end = comp_presets[comp_preset]
            default_comp_dates = [preset_start, preset_end]
        else:
            default_comp_dates = [data_start, data_end]

        selected_comp_dates = st.date_input("Analysis Period", default_comp_dates,
                                            min_value=data_start, max_value=data_end, key="comp_dates_input")

    st.divider()

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

    bt_strategies = sorted(bt_df['strategy'].unique()) if bt_df is not None and not bt_df.empty else []
    live_strategies = sorted(live_df['strategy'].unique())

    st.markdown("### 1. Strategy Mapping")
    with st.expander("🔗 Configuration", expanded=True):
        c1, c2 = st.columns(2)
        mapping = {}

        for i, live_s in enumerate(live_strategies):
            default_ix = 0
            for k, bt_s in enumerate(bt_strategies):
                if bt_s in live_s or live_s in bt_s:
                    default_ix = k + 1
                    break

            col = c1 if i % 2 == 0 else c2
            with col:
                options = ["-- Ignore --"] + list(bt_strategies)
                selection = st.selectbox(f"Live: **{live_s}**", options=options, index=default_ix, key=f"map_{i}")
                if selection != "-- Ignore --":
                    mapping[live_s] = selection

    if not mapping:
        st.warning("Please map at least one strategy.")
        return

    st.divider()
    st.markdown("### 2. Detailed Breakdown")

    tabs = st.tabs(["📊 TOTAL PORTFOLIO"] + [f"🔎 {live} vs {bt}" for live, bt in mapping.items()])

    with tabs[0]:
        mapped_live = live_df[live_df['strategy'].isin(mapping.keys())].copy()
        mapped_bt_list = []
        global_start_date = mapped_live['timestamp'].min()

        for live_s, bt_s in mapping.items():
            temp = bt_df[bt_df['strategy'] == bt_s].copy()
            temp['strategy'] = live_s
            mapped_bt_list.append(temp)

        mapped_bt = pd.concat(mapped_bt_list, ignore_index=True) if mapped_bt_list else pd.DataFrame()
        if not mapped_bt.empty and pd.notna(global_start_date):
            mapped_bt = mapped_bt[mapped_bt['timestamp'] >= global_start_date]

        daily_live = mapped_live.set_index('timestamp').resample('D')['pnl'].sum().fillna(0).cumsum()
        daily_bt = mapped_bt.set_index('timestamp').resample('D')['pnl'].sum().fillna(0).cumsum() if not mapped_bt.empty else pd.Series([0])

        tot_live = daily_live.iloc[-1] if not daily_live.empty else 0
        tot_bt = daily_bt.iloc[-1] if not daily_bt.empty and len(daily_bt) > 0 else 0
        diff = tot_live - tot_bt
        real_rate = (tot_live / tot_bt * 100) if tot_bt != 0 else 0

        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.metric("Live Net Profit", f"${tot_live:,.0f}")
        with m2:
            st.metric("Backtest Net Profit", f"${tot_bt:,.0f}")
        with m3:
            st.metric("Net Slippage", f"${diff:,.0f}", delta_color="normal" if diff >= 0 else "inverse")
        with m4:
            st.metric("Realization Rate", f"{real_rate:.1f}%")

        fig = go.Figure()
        if not daily_bt.empty:
            fig.add_trace(go.Scatter(x=daily_bt.index, y=daily_bt, name="Backtest (Ideal)",
                                     line=dict(color='gray', dash='dot')))
        fig.add_trace(go.Scatter(x=daily_live.index, y=daily_live, name="Live (Real)",
                                 line=dict(color=ui.COLOR_BLUE, width=3)))
        fig.update_layout(template="plotly_white", height=500)
        st.plotly_chart(fig, use_container_width=True)

    for i, (live_s, bt_s) in enumerate(mapping.items()):
        with tabs[i + 1]:
            s_live = live_df[live_df['strategy'] == live_s].copy().sort_values('timestamp')
            if s_live.empty:
                st.write("No live trades.")
                continue

            s_start = s_live['timestamp'].min()
            s_bt = bt_df[bt_df['strategy'] == bt_s].copy() if bt_df is not None and not bt_df.empty else pd.DataFrame()
            if not s_bt.empty and pd.notna(s_start):
                s_bt = s_bt[s_bt['timestamp'] >= s_start].sort_values('timestamp')

            if s_bt.empty:
                st.warning("Backtest has no data from start date.")
                continue

            pl_live = s_live['pnl'].sum()
            pl_bt = s_bt['pnl'].sum()
            s_diff = pl_live - pl_bt
            s_real = (pl_live / pl_bt * 100) if pl_bt != 0 else 0

            st.metric("P/L Difference", f"${s_diff:,.0f}", f"{s_real:.1f}% Realization")

            cum_l = s_live.set_index('timestamp').resample('D')['pnl'].sum().cumsum()
            cum_b = s_bt.set_index('timestamp').resample('D')['pnl'].sum().cumsum()

            fig_s = go.Figure()
            fig_s.add_trace(go.Scatter(x=cum_b.index, y=cum_b, name=f"Backtest: {bt_s}",
                                       line=dict(color='gray', dash='dot')))
            fig_s.add_trace(go.Scatter(x=cum_l.index, y=cum_l, name=f"Live: {live_s}",
                                       line=dict(color=ui.COLOR_TEAL, width=3)))
            fig_s.update_layout(template="plotly_white", height=450)
            st.plotly_chart(fig_s, use_container_width=True, key=f"chart_{i}")
