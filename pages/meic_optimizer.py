import streamlit as st
import pandas as pd
import calculations as calc
import ui_components as ui

def page_meic_optimizer():
    """MEIC Optimizer page - Beta."""

    # Header with consistent font and Beta badge
    ui.inject_fonts()
    st.markdown(f"""
        <h1 style="font-family: 'Exo 2', sans-serif !important; font-weight: 800 !important;
                   font-size: 2.5rem !important; text-transform: uppercase !important;
                   color: {ui.COLOR_GREY} !important; letter-spacing: 1px !important;">
            MEIC OPTIMIZER
            <span style="display: inline-block; background-color: #FEF3C7; color: #D97706;
                        font-size: 12px; font-weight: 600; padding: 4px 10px; border-radius: 4px;
                        margin-left: 12px; vertical-align: middle; text-transform: uppercase;">
                Beta
            </span>
        </h1>
    """, unsafe_allow_html=True)

    # Beta notice
    st.warning("This tool is currently in development. Features may change and results should be verified independently.")

    tab1, tab2 = st.tabs(["Signal Generator", "Analyzer"])

    with tab1:
        with st.container(border=True):
            ui.section_header("Generate Option Omega Signals",
                description="Generate a signal CSV file for use with Option Omega's backtest engine. This allows you to force specific entry times for MEIC (Multiple Entry Iron Condor) strategies.")

            st.info("The generated CSV can be imported into Option Omega to run backtests with predetermined entry times, useful for testing MEIC strategies with specific time windows.")

            c1, c2, c3 = st.columns(3)
            with c1:
                d1 = st.date_input("Start Date", key="meic_start_date")
            with c2:
                d2 = st.date_input("End Date", key="meic_end_date")
            with c3:
                interval_minutes = st.selectbox(
                    "Signal Interval",
                    options=[5, 10, 15, 30, 60],
                    index=2,
                    format_func=lambda x: f"{x} minutes",
                    key="meic_interval",
                    help="Time interval between signals in the generated CSV"
                )

            if st.button("Generate CSV", type="primary"):
                try:
                    df = calc.generate_oo_signals(d1, d2)
                    csv = df.to_csv(index=False)
                    st.download_button("Download signals.csv", csv, "signals.csv", "text/csv")
                except Exception as e:
                    st.error(f"Error generating signals: {e}")

    with tab2:
        with st.container(border=True):
            ui.section_header("Analyze Backtest Results",
                description="Upload multiple MEIC backtest CSVs to compare performance across different parameter sets.")

            files = st.file_uploader("Upload Multiple MEIC CSVs", accept_multiple_files=True, key="meic_files")

            if files:
                res = []
                for f in files:
                    try:
                        meta = calc.parse_meic_filename(f.name)
                        df = calc.load_file_with_caching(f)
                        if df is not None:
                            stats = calc.analyze_meic_group(df, 100000)
                            res.append({**meta, 'MAR': stats['MAR'], 'CAGR': stats['CAGR'], 'MaxDD': stats['MaxDD']})
                    except Exception as e:
                        st.warning(f"Could not process {f.name}: {e}")

                if res:
                    df_res = pd.DataFrame(res).sort_values('MAR', ascending=False)
                    st.dataframe(
                        df_res.style.format({'MAR': '{:.2f}', 'CAGR': '{:.1%}', 'MaxDD': '{:.1%}'}),
                        use_container_width=True
                    )
                else:
                    st.info("No valid results to display.")
