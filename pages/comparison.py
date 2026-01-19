import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import ui_components as ui

def page_comparison(bt_df, live_df):
    st.markdown("<h1>⚖️ REALITY CHECK</h1>", unsafe_allow_html=True)
    if live_df is None or live_df.empty: 
        st.warning("No Live Data loaded.")
        return
    
    # === CONFIGURATION (Card) ===
    with st.container(border=True):
        ui.section_header("Configuration")
        common = list(set(bt_df['strategy'].unique()) & set(live_df['strategy'].unique()))
        sel = st.selectbox("Select Strategy to Compare", common)
    
    if not sel: return

    b = bt_df[bt_df['strategy'] == sel]
    l = live_df[live_df['strategy'] == sel]
    
    # Cumulative comparison
    b_c = b.set_index('timestamp').sort_index()['pnl'].cumsum()
    l_c = l.set_index('timestamp').sort_index()['pnl'].cumsum()
    
    # Normalize start
    b_c = b_c - b_c.iloc[0]
    l_c = l_c - l_c.iloc[0]
    
    # === COMPARISON CHART (Card) ===
    with st.container(border=True):
        ui.section_header(f"Performance Comparison: {sel}")
        
        c1, c2 = st.columns(2)
        with c1: st.metric("Backtest P/L", f"${b['pnl'].sum():,.0f}")
        with c2: st.metric("Live P/L", f"${l['pnl'].sum():,.0f}")
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=b_c.index, y=b_c, name="Backtest", line=dict(dash='dot', color='gray')))
        fig.add_trace(go.Scatter(x=l_c.index, y=l_c, name="Live", line=dict(color=ui.COLOR_BLUE, width=3)))
        fig.update_layout(template="plotly_white", height=500, xaxis_title=None, yaxis_title="Cumulative P/L")
        st.plotly_chart(fig, use_container_width=True)
