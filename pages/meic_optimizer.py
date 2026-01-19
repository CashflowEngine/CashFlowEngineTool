import streamlit as st
import pandas as pd
import calculations as calc

def page_meic_optimizer():
    st.markdown("<h1>🧪 MEIC OPTIMIZER</h1>", unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["Signal Generator", "Analyzer"])
    
    with tab1:
        st.markdown("### Generate Signals")
        d1 = st.date_input("Start")
        d2 = st.date_input("End")
        if st.button("Generate CSV"):
            df = calc.generate_oo_signals(d1, d2)
            csv = df.to_csv(index=False)
            st.download_button("Download", csv, "signals.csv", "text/csv")
            
    with tab2:
        st.markdown("### Analyze Results")
        files = st.file_uploader("Upload CSVs", accept_multiple_files=True)
        if files:
            res = []
            for f in files:
                meta = calc.parse_meic_filename(f.name)
                df = calc.load_file_with_caching(f)
                if df is not None:
                    mar = calc.analyze_meic_group(df, 100000)['MAR']
                    res.append({**meta, 'MAR': mar})
            st.dataframe(pd.DataFrame(res).sort_values('MAR', ascending=False))
