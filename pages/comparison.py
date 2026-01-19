import streamlit as st
import plotly.graph_objects as go
import ui_components as ui

def page_comparison(bt_df, live_df):
    st.markdown("<h1>⚖️ REALITY CHECK</h1>", unsafe_allow_html=True)
    if live_df is None or live_df.empty: return
    
    common = list(set(bt_df['strategy'].unique()) & set(live_df['strategy'].unique()))
    sel = st.selectbox("Strategy", common)
    
    b = bt_df[bt_df['strategy'] == sel]
    l = live_df[live_df['strategy'] == sel]
    
    # Cumulative comparison
    b_c = b.set_index('timestamp').sort_index()['pnl'].cumsum()
    l_c = l.set_index('timestamp').sort_index()['pnl'].cumsum()
    
    # Normalize
    b_c = b_c - b_c.iloc[0]
    l_c = l_c - l_c.iloc[0]
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=b_c.index, y=b_c, name="Backtest"))
    fig.add_trace(go.Scatter(x=l_c.index, y=l_c, name="Live"))
    st.plotly_chart(fig, use_container_width=True)
