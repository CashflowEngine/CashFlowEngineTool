import streamlit as st
import pandas as pd
import calculations as calc
import ui_components as ui

def page_meic_optimizer():
    st.markdown("<h1>🧪 MEIC OPTIMIZER</h1>", unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["Signal Generator", "Analyzer"])
    
    with tab1:
        with st.container(border=True):
            ui.section_header("Generate Option Omega Signals")
            st.caption("Create a CSV to force entry times in Option Omega backtests.")
            
            c1, c2 = st.columns(2)
            with c1: d1 = st.date_input("Start Date")
            with c2: d2 = st.date_input("End Date")
            
            if st.button("Generate CSV", type="primary"):
                df = calc.generate_oo_signals(d1, d2)
                csv = df.to_csv(index=False)
                st.download_button("⬇️ Download signals.csv", csv, "signals.csv", "text/csv")
            
    with tab2:
        with st.container(border=True):
            ui.section_header("Analyze Backtest Results")
            files = st.file_uploader("Upload Multiple MEIC CSVs", accept_multiple_files=True)
            
            if files:
                res = []
                for f in files:
                    meta = calc.parse_meic_filename(f.name)
                    df = calc.load_file_with_caching(f)
                    if df is not None:
                        # Simple MAR calc assumption
                        stats = calc.analyze_meic_group(df, 100000)
                        res.append({**meta, 'MAR': stats['MAR'], 'CAGR': stats['CAGR'], 'MaxDD': stats['MaxDD']})
                
                if res:
                    df_res = pd.DataFrame(res).sort_values('MAR', ascending=False)
                    st.dataframe(df_res.style.format({'MAR': '{:.2f}', 'CAGR': '{:.1%}', 'MaxDD': '{:.1%}'}), use_container_width=True)
