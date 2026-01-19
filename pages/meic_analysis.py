import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import ui_components as ui

def page_meic_analysis(bt_df, live_df=None):
    st.markdown("<h1>🔬 MEIC DEEP DIVE</h1>", unsafe_allow_html=True)
    target = live_df if live_df is not None else bt_df
    
    if target.empty: return
    
    # === CONFIGURATION (Card) ===
    with st.container(border=True):
        ui.section_header("Configuration")
        strats = st.multiselect("Select Strategies", target['strategy'].unique())
    
    if not strats: return
    
    df = target[target['strategy'].isin(strats)].copy()
    if 'timestamp_open' not in df.columns:
        st.error("No Entry Time data found in dataset.")
        return
        
    df['EntryTime'] = df['timestamp_open'].dt.strftime('%H:%M')
    
    stats = df.groupby('EntryTime')['pnl'].agg(['count', 'sum', 'mean'])
    stats.columns = ['Trades', 'Total P/L', 'Avg P/L']
    
    # === ANALYSIS RESULTS (Card) ===
    with st.container(border=True):
        ui.section_header("Performance by Entry Time")
        
        col1, col2 = st.columns(2)
        with col1:
            st.dataframe(stats.style.applymap(ui.color_monthly_performance, subset=['Total P/L']).format({'Total P/L': '${:,.0f}', 'Avg P/L': '${:,.0f}'}), use_container_width=True)
        
        with col2:
            fig = px.bar(stats, y='Total P/L', color='Total P/L', color_continuous_scale='RdYlGn', title="Total P/L per Time Slot")
            fig.update_layout(template="plotly_white")
            st.plotly_chart(fig, use_container_width=True)
