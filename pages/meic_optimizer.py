import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import ui_components as ui
import calc
import logging

logger = logging.getLogger(__name__)

def generate_oo_signals(start_date, end_date, interval_min=5):
    """Generate Option Omega entry signals for backtesting."""
    dates = pd.date_range(start=start_date, end=end_date, freq='B')  # Business days

    signals = []
    for d in dates:
        # Generate signals from 9:35 to 15:55 in 5-minute increments
        start_time = pd.Timestamp(f"{d.date()} 09:35:00")
        end_time = pd.Timestamp(f"{d.date()} 15:55:00")

        current = start_time
        while current <= end_time:
            signals.append({
                'Date': d.date(),
                'Time': current.strftime('%H:%M:%S'),
                'Signal': 'OPEN'
            })
            current += pd.Timedelta(minutes=interval_min)

    return pd.DataFrame(signals)


def parse_meic_filename(filename):
    """Parse MEIC backtest filename to extract parameters."""
    import re

    result = {
        'Filename': filename,
        'Width': None,
        'SL': None,
        'Premium': None
    }

    # Try to extract Width (W50, W100, etc.)
    w_match = re.search(r'W(\d+)', filename, re.IGNORECASE)
    if w_match:
        result['Width'] = int(w_match.group(1))

    # Try to extract Stop Loss (SL100, SL200, etc.)
    sl_match = re.search(r'SL(\d+)', filename, re.IGNORECASE)
    if sl_match:
        result['SL'] = int(sl_match.group(1))

    # Try to extract Premium (P2.5, P3, etc.)
    p_match = re.search(r'P(\d+\.?\d*)', filename, re.IGNORECASE)
    if p_match:
        result['Premium'] = float(p_match.group(1))

    return result


def analyze_meic_group(df, account_size):
    """Calculate stats for a group of trades."""
    if df.empty:
        return {'MAR': 0, 'CAGR': 0, 'MaxDD': 0, 'Trades': 0, 'WinRate': 0, 'P/L': 0}

    # Sort by timestamp
    df = df.sort_values('timestamp')

    # Daily P&L
    daily_pnl = df.groupby(df['timestamp'].dt.date)['pnl'].sum()

    if len(daily_pnl) < 2:
        return {
            'MAR': 0,
            'CAGR': 0,
            'MaxDD': 0,
            'Trades': len(df),
            'WinRate': (df['pnl'] > 0).mean(),
            'P/L': df['pnl'].sum()
        }

    # Calculate equity curve
    equity = account_size + daily_pnl.cumsum()

    # Max Drawdown
    peak = equity.cummax()
    dd = (equity - peak) / peak
    max_dd = abs(dd.min())

    # CAGR
    days = (df['timestamp'].max() - df['timestamp'].min()).days
    days = max(days, 1)
    total_return = daily_pnl.sum() / account_size
    cagr = (1 + total_return) ** (365 / days) - 1 if total_return > -1 else -1

    # MAR Ratio
    mar = cagr / max_dd if max_dd > 0 else 0

    return {
        'MAR': mar,
        'CAGR': cagr,
        'MaxDD': max_dd,
        'Trades': len(df),
        'WinRate': (df['pnl'] > 0).mean(),
        'P/L': df['pnl'].sum()
    }


def load_file_with_caching(uploaded_file):
    """Load and parse CSV file."""
    try:
        df = pd.read_csv(uploaded_file)

        # Try to find timestamp column
        ts_cols = ['timestamp', 'Timestamp', 'date', 'Date', 'timestamp_close', 'close_time']
        for col in ts_cols:
            if col in df.columns:
                df['timestamp'] = pd.to_datetime(df[col], errors='coerce')
                break

        # Try to find entry time column
        entry_cols = ['timestamp_open', 'open_time', 'entry_time', 'EntryTime']
        for col in entry_cols:
            if col in df.columns:
                df['timestamp_open'] = pd.to_datetime(df[col], errors='coerce')
                break

        # Try to find PnL column
        pnl_cols = ['pnl', 'P/L', 'PnL', 'profit', 'Profit', 'net_pnl']
        for col in pnl_cols:
            if col in df.columns:
                df['pnl'] = pd.to_numeric(df[col], errors='coerce')
                break

        return df

    except Exception as e:
        logger.error(f"Error loading file: {e}")
        return None


def page_meic_optimizer():
    """MEIC Optimizer (4D) page."""
    ui.render_page_header("🧪 MEIC OPTIMIZER (4D)")
    st.caption("ENTRY TIMES • PREMIUM • WIDTH • STOP LOSS")

    tab_gen, tab_ana = st.tabs(["1️⃣ Signal Generator (für Option Omega)", "2️⃣ 4D Analyzer (Ergebnisse)"])

    # --- TAB 1: GENERATOR ---
    with tab_gen:
        st.markdown("### Erstelle Entry-Signale für Option Omega")
        st.info("Lade diese Datei bei Option Omega unter **'Custom Signals'** hoch (Open Only), um Backtests zu jeder möglichen Uhrzeit zu erzwingen.")

        c1, c2 = st.columns(2)
        with c1:
            # Standard: SPX Dailies Start bis Heute
            gen_start = st.date_input("Start Datum", value=pd.to_datetime("2022-05-16"), key="opt_gen_start")
            gen_end = st.date_input("End Datum", value=pd.Timestamp.now(), key="opt_gen_end")
        with c2:
            gen_interval = st.number_input("Intervall (Minuten)", value=5, min_value=1, max_value=60, key="opt_gen_interval")

        if st.button("CSV Generieren", type="primary", key="opt_gen_btn"):
            df_signals = generate_oo_signals(gen_start, gen_end, interval_min=gen_interval)

            # Convert to CSV string
            csv = df_signals.to_csv(index=False)

            st.success(f"Generiert: {len(df_signals):,} Entry Signale ({gen_interval}min Intervall)")
            st.download_button(
                label="⬇️ Download signals_open_only.csv",
                data=csv,
                file_name="signals_open_only.csv",
                mime="text/csv"
            )

    # --- TAB 2: ANALYZER ---
    with tab_ana:
        st.markdown("### Dimensionale Analyse")
        st.markdown("""
        **Workflow:**
        1. Führe Backtests in Option Omega durch (nutze die Signal-CSV von Tab 1).
        2. Benenne die Ergebnis-Dateien strikt nach dem Schema: `MEIC_W{Width}_SL{StopLoss}_P{Premium}.csv`
           *(Beispiel: MEIC_W50_SL100_P2.5.csv)*
        3. Lade alle Ergebnisse hier hoch.
        """)

        uploaded_files = st.file_uploader("Upload OO Backtest CSVs (Mehrfachauswahl)", accept_multiple_files=True, type=['csv'], key="opt_files")

        account_size = st.number_input("Account Size ($)", value=100000, step=10000, key="opt_acc_size")

        if uploaded_files:
            all_trades = []
            file_stats = []

            # Progress Bar initialisieren
            progress_text = "Verarbeite Dateien..."
            my_bar = st.progress(0, text=progress_text)

            for i, uploaded_file in enumerate(uploaded_files):
                # 1. Parse Metadaten aus Dateinamen
                meta = parse_meic_filename(uploaded_file.name)

                # 2. Lade Content
                try:
                    df = load_file_with_caching(uploaded_file)

                    if df is None or df.empty:
                        continue

                    # 3. Entry Time extrahieren (Format HH:MM)
                    if 'timestamp_open' in df.columns:
                        df['EntryTime'] = df['timestamp_open'].dt.strftime('%H:%M')
                    else:
                        continue  # Skip if no time info

                    # 4. Dimensionen anfügen (wenn im Dateinamen gefunden, sonst 0)
                    df['Width'] = meta['Width'] if meta['Width'] else 0
                    df['SL'] = meta['SL'] if meta['SL'] else 0
                    df['Premium'] = meta['Premium'] if meta['Premium'] else 0.0
                    df['SourceFile'] = meta['Filename']

                    all_trades.append(df)
                    file_stats.append(meta)

                except Exception as e:
                    logger.error(f"Error parsing {uploaded_file.name}: {e}")

                # Update Progress
                my_bar.progress((i + 1) / len(uploaded_files), text=f"Lade {uploaded_file.name}")

            my_bar.empty()

            if not all_trades:
                st.error("Keine validen Trades gefunden. Bitte prüfe die CSV-Dateien.")
                return

            master_df = pd.concat(all_trades, ignore_index=True)
            st.success(f"Daten geladen: {len(master_df):,} Trades aus {len(uploaded_files)} Dateien.")

            # --- ANALYSE LOGIK ---
            st.divider()

            # Datumsgrenze für "Letzte 6 Monate"
            max_date = master_df['timestamp'].max()
            date_6m = max_date - pd.DateOffset(months=6)

            st.markdown(f"#### 🏆 Strategie-Ranking")
            st.caption(f"Vergleich: Full History vs. Letzte 6 Monate (ab {date_6m.date()})")

            with st.spinner("Berechne 4D-Metriken (Width x SL x Premium x EntryTime)..."):
                combinations = []

                # Gruppieren nach ALLEN Dimensionen
                groups = master_df.groupby(['Width', 'SL', 'Premium', 'EntryTime'])

                for name, group in groups:
                    width, sl, prem, entry_time = name

                    # Filter: Nur Einträge mit sinnvollen Parametern berücksichtigen
                    if width == 0 and sl == 0 and prem == 0:
                        continue

                    # Split in 6M und Total
                    df_6m = group[group['timestamp'] >= date_6m]

                    # Wenn in den letzten 6M keine Trades, überspringen
                    if df_6m.empty:
                        continue

                    # Stats berechnen
                    stats_total = analyze_meic_group(group, account_size)
                    stats_6m = analyze_meic_group(df_6m, account_size)

                    combinations.append({
                        'Width': width,
                        'SL': sl,
                        'Premium': prem,
                        'EntryTime': entry_time,
                        'MAR (6M)': stats_6m['MAR'],
                        'MAR (Total)': stats_total['MAR'],
                        'CAGR (6M)': stats_6m['CAGR'],
                        'MaxDD (6M)': stats_6m['MaxDD'],
                        'Trades (6M)': stats_6m['Trades'],
                        'WinRate (6M)': stats_6m['WinRate'],
                        'P/L (6M)': stats_6m['P/L']
                    })

                results_df = pd.DataFrame(combinations)

            if results_df.empty:
                st.warning("Keine Kombinationen gefunden. Bitte Dateinamen prüfen (z.B. MEIC_W50...).")
                return

            # --- INTERACTIVE FILTERING ---
            col_f1, col_f2 = st.columns([1, 3])

            with col_f1:
                st.markdown("##### Filter")
                min_mar_6m = st.slider("Min MAR (6M)", 0.0, 5.0, 1.5, 0.1, key="opt_min_mar_6m")
                min_mar_total = st.slider("Min MAR (Total)", 0.0, 3.0, 0.5, 0.1, key="opt_min_mar_total")
                min_trades = st.slider("Min Trades (6M)", 0, 100, 20, 5, key="opt_min_trades")

            # Filter anwenden
            filtered_res = results_df[
                (results_df['MAR (6M)'] >= min_mar_6m) &
                (results_df['MAR (Total)'] >= min_mar_total) &
                (results_df['Trades (6M)'] >= min_trades)
            ].sort_values('MAR (6M)', ascending=False)

            with col_f2:
                st.markdown(f"##### Ergebnisse ({len(filtered_res)} Kombos gefunden)")

                # Farb-Formatierung für MAR
                def color_mar(val):
                    if val >= 3:
                        return 'background-color: #065F46; color: white'  # Excellent
                    if val >= 2:
                        return 'background-color: #10B981; color: white'  # Good
                    if val >= 1:
                        return 'background-color: #FBBF24; color: black'  # Okay
                    return 'background-color: #EF4444; color: white'  # Bad

                st.dataframe(
                    filtered_res.style.format({
                        'MAR (6M)': '{:.2f}',
                        'MAR (Total)': '{:.2f}',
                        'CAGR (6M)': '{:.1%}',
                        'MaxDD (6M)': '{:.1%}',
                        'WinRate (6M)': '{:.1%}',
                        'P/L (6M)': '${:,.0f}',
                        'Premium': '${:.2f}'
                    }).map(color_mar, subset=['MAR (6M)', 'MAR (Total)']),
                    use_container_width=True,
                    height=500
                )

            # --- DEEP DIVE VISUALISIERUNG ---
            st.divider()
            st.markdown("### 🔬 Deep Dive: Parameter Impact")

            viz_c1, viz_c2 = st.columns(2)

            with viz_c1:
                st.markdown("**Beste Entry Times (Top 50 Kombos)**")
                if not filtered_res.empty:
                    top_times = filtered_res.head(50)['EntryTime'].value_counts().sort_index()
                    fig_times = px.bar(x=top_times.index, y=top_times.values,
                                       labels={'x': 'Entry Time', 'y': 'Häufigkeit in Top 50'},
                                       template="plotly_white")
                    fig_times.update_traces(marker_color=ui.COLOR_TEAL)
                    st.plotly_chart(fig_times, use_container_width=True)

            with viz_c2:
                st.markdown("**Robustheit: 6M vs Total**")
                if not filtered_res.empty:
                    fig_scat = px.scatter(
                        filtered_res,
                        x="MAR (Total)",
                        y="MAR (6M)",
                        color="Width",
                        size="Premium",
                        hover_data=["EntryTime", "SL"],
                        template="plotly_white",
                        title="Konsistenz-Check (Größe = Premium, Farbe = Width)"
                    )
                    # Grüne Zone einzeichnen
                    fig_scat.add_shape(type="rect",
                                       x0=1.0, y0=2.0, x1=5.0, y1=10.0,
                                       line=dict(color="Green", width=1, dash="dot"),
                                       fillcolor="rgba(0,255,0,0.1)")
                    st.plotly_chart(fig_scat, use_container_width=True)

            # --- DOWNLOAD BEST ---
            st.markdown("### 📥 Export")
            if not filtered_res.empty:
                csv_export = filtered_res.to_csv(index=False)
                st.download_button("Download Top Ergebnisse (.csv)", csv_export, "meic_optimized_results.csv", "text/csv", key="opt_download")
