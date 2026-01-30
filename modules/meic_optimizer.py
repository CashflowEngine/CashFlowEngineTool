import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import ui_components as ui
import calc
import logging

logger = logging.getLogger(__name__)

def generate_oo_signals(start_date, end_date, start_time="09:32", interval_min=5):
    """Generate Option Omega entry signals for backtesting.

    Args:
        start_date: First date to generate signals for
        end_date: Last date to generate signals for
        start_time: Start time for signals (format: "HH:MM"), default "09:32"
        interval_min: Interval between signals in minutes
    """
    dates = pd.date_range(start=start_date, end=end_date, freq='B')  # Business days

    signals = []
    for d in dates:
        # Generate signals from start_time to 15:59 in specified intervals
        day_start = pd.Timestamp(f"{d.date()} {start_time}:00")
        end_time = pd.Timestamp(f"{d.date()} 15:59:00")

        current = day_start
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

    # Try to extract Premium (P2-5 means 2.5, P3 means 3, etc.)
    # Format uses hyphen instead of dot for decimal: P2-5 = $2.50, P3 = $3.00
    p_match = re.search(r'P(\d+)(?:-(\d+))?', filename, re.IGNORECASE)
    if p_match:
        whole_part = p_match.group(1)
        decimal_part = p_match.group(2)
        if decimal_part:
            result['Premium'] = float(f"{whole_part}.{decimal_part}")
        else:
            result['Premium'] = float(whole_part)

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


def load_file_with_caching(uploaded_file, chunksize=50000):
    """Load and parse CSV file with support for Option Omega export format.
    Uses chunked reading for large files to avoid memory issues."""
    try:
        # Get file size for progress indication
        file_size = uploaded_file.size if hasattr(uploaded_file, 'size') else 0

        # For large files (>50MB), use chunked reading
        if file_size > 50 * 1024 * 1024:  # 50MB
            chunks = []
            for chunk in pd.read_csv(uploaded_file, chunksize=chunksize, low_memory=False):
                chunks.append(chunk)
            df = pd.concat(chunks, ignore_index=True)
        else:
            df = pd.read_csv(uploaded_file, low_memory=False)

        # Handle Option Omega format: Date Closed + Time Closed -> timestamp
        if 'Date Closed' in df.columns and 'Time Closed' in df.columns:
            df['timestamp'] = pd.to_datetime(df['Date Closed'].astype(str) + ' ' + df['Time Closed'].astype(str), errors='coerce')
        elif 'Date Opened' in df.columns and 'Time Opened' in df.columns:
            # Fallback to open date if close date not available
            df['timestamp'] = pd.to_datetime(df['Date Opened'].astype(str) + ' ' + df['Time Opened'].astype(str), errors='coerce')
        else:
            # Try standard timestamp columns
            ts_cols = ['timestamp', 'Timestamp', 'date', 'Date', 'timestamp_close', 'close_time']
            for col in ts_cols:
                if col in df.columns:
                    df['timestamp'] = pd.to_datetime(df[col], errors='coerce')
                    break

        # Handle Option Omega format: Date Opened + Time Opened -> timestamp_open
        if 'Date Opened' in df.columns and 'Time Opened' in df.columns:
            df['timestamp_open'] = pd.to_datetime(df['Date Opened'].astype(str) + ' ' + df['Time Opened'].astype(str), errors='coerce')
        else:
            # Try standard entry time columns
            entry_cols = ['timestamp_open', 'open_time', 'entry_time', 'EntryTime']
            for col in entry_cols:
                if col in df.columns:
                    df['timestamp_open'] = pd.to_datetime(df[col], errors='coerce')
                    break

        # Try to find PnL column - handle Option Omega P/L format
        pnl_cols = ['P/L', 'pnl', 'PnL', 'profit', 'Profit', 'net_pnl']
        for col in pnl_cols:
            if col in df.columns:
                # Clean P/L values (remove $ and , if present)
                pnl_str = df[col].astype(str).str.replace('$', '', regex=False).str.replace(',', '', regex=False)
                df['pnl'] = pd.to_numeric(pnl_str, errors='coerce')
                break

        return df

    except Exception as e:
        logger.error(f"Error loading file: {e}")
        return None


def page_meic_optimizer():
    """MEIC Optimizer (4D) page."""
    ui.render_page_header("MEIC OPTIMIZER (4D)")
    st.caption("ENTRY TIMES • PREMIUM • WIDTH • STOP LOSS")

    # Page Explanation
    with st.expander("ℹ️ What is the MEIC Optimizer?", expanded=False):
        st.markdown("""
        **The MEIC Optimizer helps you find the optimal combination of trading parameters:**

        This tool analyzes your Option Omega backtest results across **4 dimensions**:
        1. **Entry Time** - What time of day produces the best results?
        2. **Premium** - What credit received levels work best?
        3. **Wing Width** - What strike width optimizes risk/reward?
        4. **Stop Loss** - What stop loss level balances protection and profitability?

        **How to use:**
        1. **Generate Signals** - Create a CSV file with every possible entry time
        2. **Run Backtests** - Use Option Omega with "Custom Signals (Open Only)" mode
        3. **Name Files Correctly** - Use format: `MEIC_W50_SL100_P2-5.csv` (W=Width, SL=StopLoss, P=Premium)
        4. **Upload & Analyze** - Upload all result files here to find optimal parameters

        **File Size Note:** For large backtests (many entry times), files can be 100MB+.
        The analyzer processes files in chunks to handle large datasets efficiently.
        If uploads fail, try uploading fewer files at once or reduce the date range in your backtest.
        """)

    tab_gen, tab_ana = st.tabs(["1. Signal Generator (for Option Omega)", "2. 4D Analyzer (Results)"])

    # --- TAB 1: GENERATOR ---
    with tab_gen:
        ui.section_header("Create Entry Signals for Option Omega")
        st.info("Upload this file to Option Omega under **'Custom Signals'** (Open Only) to force backtests at every possible entry time.")

        # 4-block layout: Start Date, End Date, Interval, Minutes, Start Time
        row1_c1, row1_c2 = st.columns(2)
        with row1_c1:
            gen_start = st.date_input("Start Date", value=pd.to_datetime("2022-05-16"), key="opt_gen_start")
        with row1_c2:
            gen_interval = st.number_input("Interval (Minutes)", value=5, min_value=1, max_value=60, key="opt_gen_interval")

        row2_c1, row2_c2 = st.columns(2)
        with row2_c1:
            gen_end = st.date_input("End Date", value=pd.Timestamp.now(), key="opt_gen_end")
        with row2_c2:
            # Start Time as manual text input (not dropdown)
            gen_start_time = st.text_input(
                "Start Time (HH:MM)",
                value="09:32",
                key="opt_gen_start_time",
                help="First signal time each day. Format: HH:MM (e.g., 09:32). Must be between 09:32 and 15:59."
            )

            # Validate the start time
            start_time_valid = True
            start_time_error = ""
            try:
                time_parts = gen_start_time.split(":")
                if len(time_parts) != 2:
                    start_time_valid = False
                    start_time_error = "Invalid format. Use HH:MM (e.g., 09:32)"
                else:
                    hour = int(time_parts[0])
                    minute = int(time_parts[1])
                    # Validate range: 09:32 to 15:59
                    if hour < 9 or hour > 15:
                        start_time_valid = False
                        start_time_error = "Hour must be between 9 and 15"
                    elif hour == 9 and minute < 32:
                        start_time_valid = False
                        start_time_error = "Earliest start time is 09:32"
                    elif hour == 15 and minute > 59:
                        start_time_valid = False
                        start_time_error = "Latest start time is 15:59"
                    elif minute < 0 or minute > 59:
                        start_time_valid = False
                        start_time_error = "Invalid minute value"
            except (ValueError, IndexError):
                start_time_valid = False
                start_time_error = "Invalid format. Use HH:MM (e.g., 09:32)"

            if not start_time_valid:
                st.error(start_time_error)

        st.markdown("")

        if st.button("Generate CSV", type="primary", key="opt_gen_btn", disabled=not start_time_valid):
            df_signals = generate_oo_signals(gen_start, gen_end, start_time=gen_start_time, interval_min=gen_interval)

            # Convert to CSV string
            csv = df_signals.to_csv(index=False)

            st.success(f"Generated: {len(df_signals):,} entry signals ({gen_interval}min interval, starting at {gen_start_time})")
            st.download_button(
                label="Download signals_open_only.csv",
                data=csv,
                file_name="signals_open_only.csv",
                mime="text/csv"
            )

    # --- TAB 2: ANALYZER ---
    with tab_ana:
        ui.section_header("Dimensional Analysis")
        st.markdown("""
        **Workflow:**
        1. Run backtests in Option Omega (use the signal CSV from Tab 1).
        2. Name the result files strictly following this schema: `MEIC_W{Width}_SL{StopLoss}_P{Premium}.csv`
           *(Example: MEIC_W50_SL100_P2-5.csv for $2.50 premium, MEIC_W50_SL100_P3.csv for $3.00)*
           **Note:** Use hyphen for decimals in Premium (P2-5 = $2.50, P2-75 = $2.75)
        3. Upload all results here.

        **Supported CSV formats:** Option Omega exports with columns like Date Opened, Time Opened, P/L, etc.
        """)

        # File upload with size warning
        st.markdown("""
        <div style='background-color: #FEF3C7; padding: 12px 16px; border-radius: 8px; margin-bottom: 12px; font-size: 12px;'>
            <strong>⚠️ Large File Upload Tips:</strong><br>
            • Files up to 200MB each are supported<br>
            • For very large files, consider splitting your backtest into smaller date ranges<br>
            • If upload fails, refresh the page and try uploading fewer files at once<br>
            • Processing time increases with file size - please be patient
        </div>
        """, unsafe_allow_html=True)

        uploaded_files = st.file_uploader("Upload Backtest CSVs (Multiple Selection)", accept_multiple_files=True, type=['csv'], key="opt_files")

        # Show file size info if files uploaded
        if uploaded_files:
            total_size = sum(f.size for f in uploaded_files if hasattr(f, 'size'))
            st.caption(f"📁 {len(uploaded_files)} file(s) selected • Total size: {total_size / (1024*1024):.1f} MB")

        account_size = st.number_input("Account Size ($)", value=100000, step=10000, key="opt_acc_size")

        if uploaded_files:
            all_trades = []
            file_stats = []

            # Initialize Progress Bar
            progress_text = "Processing files..."
            my_bar = st.progress(0, text=progress_text)

            for i, uploaded_file in enumerate(uploaded_files):
                # 1. Parse metadata from filename
                meta = parse_meic_filename(uploaded_file.name)

                # 2. Load content
                try:
                    df = load_file_with_caching(uploaded_file)

                    if df is None or df.empty:
                        st.warning(f"Could not parse {uploaded_file.name} - skipping.")
                        continue

                    # 3. Extract entry time (Format HH:MM)
                    if 'timestamp_open' in df.columns and df['timestamp_open'].notna().any():
                        df['EntryTime'] = df['timestamp_open'].dt.strftime('%H:%M')
                    else:
                        st.warning(f"No entry time data in {uploaded_file.name} - skipping.")
                        continue

                    # 4. Add dimensions (from filename if found, otherwise 0)
                    df['Width'] = meta['Width'] if meta['Width'] else 0
                    df['SL'] = meta['SL'] if meta['SL'] else 0
                    df['Premium'] = meta['Premium'] if meta['Premium'] else 0.0
                    df['SourceFile'] = meta['Filename']

                    all_trades.append(df)
                    file_stats.append(meta)

                except Exception as e:
                    logger.error(f"Error parsing {uploaded_file.name}: {e}")
                    st.warning(f"Error loading {uploaded_file.name}: {str(e)}")

                # Update Progress
                my_bar.progress((i + 1) / len(uploaded_files), text=f"Loading {uploaded_file.name}")

            my_bar.empty()

            if not all_trades:
                st.error("No valid trades found. Please check the CSV files. Ensure they have Date/Time columns and P/L data.")
                return

            master_df = pd.concat(all_trades, ignore_index=True)
            st.success(f"Data loaded: {len(master_df):,} trades from {len(uploaded_files)} files.")

            # --- ANALYSIS LOGIC ---
            st.divider()

            # Get data date range
            min_date = master_df['timestamp'].min()
            max_date = master_df['timestamp'].max()

            # Data range info
            st.markdown(f"""
            <div style='background-color: #F0F4FF; padding: 12px 16px; border-radius: 8px; margin-bottom: 16px; font-size: 13px;'>
                <strong>Available Data:</strong> {min_date.strftime('%Y-%m-%d')} to {max_date.strftime('%Y-%m-%d')}
                ({(max_date - min_date).days} days) • {len(master_df):,} total trades
            </div>
            """, unsafe_allow_html=True)

            # Variable date range selection
            ui.section_header("Analysis Period Selection")

            period_col1, period_col2 = st.columns(2)
            with period_col1:
                analysis_mode = st.selectbox(
                    "Analysis Mode",
                    options=["Last N Months", "Custom Date Range"],
                    key="opt_analysis_mode"
                )

            with period_col2:
                if analysis_mode == "Last N Months":
                    num_months = st.number_input(
                        "Number of Months",
                        min_value=1,
                        max_value=36,
                        value=6,
                        key="opt_num_months"
                    )
                    date_recent = max_date - pd.DateOffset(months=num_months)
                else:
                    recent_dates = st.date_input(
                        "Date Range",
                        value=(max_date - pd.DateOffset(months=6), max_date),
                        min_value=min_date.date(),
                        max_value=max_date.date(),
                        key="opt_custom_dates"
                    )
                    if len(recent_dates) == 2:
                        date_recent = pd.Timestamp(recent_dates[0])
                        max_date_for_period = pd.Timestamp(recent_dates[1])
                    else:
                        date_recent = max_date - pd.DateOffset(months=6)
                        max_date_for_period = max_date

            period_label = f"Last {num_months} Months" if analysis_mode == "Last N Months" else f"{recent_dates[0]} to {recent_dates[1]}" if len(recent_dates) == 2 else "Custom Period"

            ui.section_header("Strategy Ranking")
            st.caption(f"Comparison: Full History vs. {period_label} (from {date_recent.date()})")

            with st.spinner("Calculating 4D metrics (Width x SL x Premium x EntryTime)..."):
                combinations = []

                # Gruppieren nach ALLEN Dimensionen
                groups = master_df.groupby(['Width', 'SL', 'Premium', 'EntryTime'])

                for name, group in groups:
                    width, sl, prem, entry_time = name

                    # Filter: Only include entries with valid parameters
                    if width == 0 and sl == 0 and prem == 0:
                        continue

                    # Split into selected period and Total
                    df_recent = group[group['timestamp'] >= date_recent]

                    # Skip if no trades in recent period
                    if df_recent.empty:
                        continue

                    # Calculate stats
                    stats_total = analyze_meic_group(group, account_size)
                    stats_recent = analyze_meic_group(df_recent, account_size)

                    combinations.append({
                        'Width': width,
                        'SL': sl,
                        'Premium': prem,
                        'EntryTime': entry_time,
                        # Recent period metrics
                        'MAR (Recent)': stats_recent['MAR'],
                        'CAGR (Recent)': stats_recent['CAGR'],
                        'MaxDD (Recent)': stats_recent['MaxDD'],
                        'Trades (Recent)': stats_recent['Trades'],
                        'WinRate (Recent)': stats_recent['WinRate'],
                        'P/L (Recent)': stats_recent['P/L'],
                        # Full history metrics
                        'MAR (Total)': stats_total['MAR'],
                        'CAGR (Total)': stats_total['CAGR'],
                        'MaxDD (Total)': stats_total['MaxDD'],
                        'Trades (Total)': stats_total['Trades'],
                        'WinRate (Total)': stats_total['WinRate'],
                        'P/L (Total)': stats_total['P/L']
                    })

                results_df = pd.DataFrame(combinations)

            if results_df.empty:
                st.warning("No combinations found. Please check filenames (e.g., MEIC_W50...).")
                return

            # --- INTERACTIVE FILTERING (Above the table) ---
            st.markdown("### Filters")

            # Row 1: Performance filters
            filter_row1 = st.columns(5)
            with filter_row1[0]:
                min_mar_recent = st.slider("Min MAR (Recent)", 0.0, 5.0, 1.5, 0.1, key="opt_min_mar_recent")
            with filter_row1[1]:
                min_mar_total = st.slider("Min MAR (Total)", 0.0, 3.0, 0.5, 0.1, key="opt_min_mar_total")
            with filter_row1[2]:
                min_trades = st.slider("Min Trades (Recent)", 0, 100, 20, 5, key="opt_min_trades")
            with filter_row1[3]:
                # New: Max Drawdown filter for recent period
                max_dd_range = st.slider(
                    "Max DD (Recent) %",
                    min_value=0.0,
                    max_value=50.0,
                    value=(0.0, 30.0),
                    step=1.0,
                    key="opt_max_dd_filter"
                )
            with filter_row1[4]:
                # New: CAGR filter for recent period
                cagr_range = st.slider(
                    "CAGR (Recent) %",
                    min_value=-50.0,
                    max_value=200.0,
                    value=(0.0, 200.0),
                    step=5.0,
                    key="opt_cagr_filter"
                )

            # Row 2: Parameter filters
            filter_row2 = st.columns(4)

            # Width filter
            available_widths = sorted(results_df['Width'].unique())
            with filter_row2[0]:
                if len(available_widths) > 1:
                    selected_widths = st.multiselect(
                        "Width",
                        options=available_widths,
                        default=available_widths,
                        key="opt_filter_width"
                    )
                else:
                    selected_widths = available_widths
                    st.text(f"Width: {available_widths[0] if available_widths else 'N/A'}")

            # Premium filter
            available_premiums = sorted(results_df['Premium'].unique())
            with filter_row2[1]:
                if len(available_premiums) > 1:
                    selected_premiums = st.multiselect(
                        "Premium",
                        options=available_premiums,
                        default=available_premiums,
                        key="opt_filter_premium",
                        format_func=lambda x: f"${x:.2f}"
                    )
                else:
                    selected_premiums = available_premiums
                    st.text(f"Premium: ${available_premiums[0]:.2f}" if available_premiums else "Premium: N/A")

            # SL filter
            available_sls = sorted(results_df['SL'].unique())
            with filter_row2[2]:
                if len(available_sls) > 1:
                    selected_sls = st.multiselect(
                        "Stop Loss",
                        options=available_sls,
                        default=available_sls,
                        key="opt_filter_sl"
                    )
                else:
                    selected_sls = available_sls
                    st.text(f"SL: {available_sls[0] if available_sls else 'N/A'}")

            # Entry Time filter
            available_times = sorted(results_df['EntryTime'].unique())
            with filter_row2[3]:
                if len(available_times) > 1:
                    st.markdown("**Entry Time Range**")
                    time_col1, time_col2 = st.columns(2)
                    with time_col1:
                        time_start = st.selectbox("From", options=available_times, index=0, key="opt_time_start")
                    with time_col2:
                        time_end = st.selectbox("To", options=available_times, index=len(available_times)-1, key="opt_time_end")
                    selected_times = [t for t in available_times if t >= time_start and t <= time_end]
                else:
                    selected_times = available_times

            # Apply filters
            filtered_res = results_df[
                (results_df['MAR (Recent)'] >= min_mar_recent) &
                (results_df['MAR (Total)'] >= min_mar_total) &
                (results_df['Trades (Recent)'] >= min_trades) &
                (results_df['MaxDD (Recent)'] * 100 >= max_dd_range[0]) &
                (results_df['MaxDD (Recent)'] * 100 <= max_dd_range[1]) &
                (results_df['CAGR (Recent)'] * 100 >= cagr_range[0]) &
                (results_df['CAGR (Recent)'] * 100 <= cagr_range[1]) &
                (results_df['Width'].isin(selected_widths)) &
                (results_df['Premium'].isin(selected_premiums)) &
                (results_df['SL'].isin(selected_sls)) &
                (results_df['EntryTime'].isin(selected_times))
            ].sort_values('MAR (Recent)', ascending=False)

            st.divider()

            # Results table - FULL WIDTH
            st.markdown(f"### Results ({len(filtered_res)} combinations found)")

            # Color formatting for MAR
            def color_mar(val):
                if val >= 3:
                    return 'background-color: #065F46; color: white'  # Excellent
                if val >= 2:
                    return 'background-color: #10B981; color: white'  # Good
                if val >= 1:
                    return 'background-color: #FBBF24; color: black'  # Okay
                return 'background-color: #EF4444; color: white'  # Bad

            # Display table with both recent and historical metrics
            display_cols = ['Width', 'SL', 'Premium', 'EntryTime',
                           'MAR (Recent)', 'CAGR (Recent)', 'MaxDD (Recent)', 'Trades (Recent)', 'WinRate (Recent)', 'P/L (Recent)',
                           'MAR (Total)', 'CAGR (Total)', 'MaxDD (Total)', 'WinRate (Total)', 'P/L (Total)']

            st.dataframe(
                filtered_res[display_cols].style.format({
                    'MAR (Recent)': '{:.2f}',
                    'MAR (Total)': '{:.2f}',
                    'CAGR (Recent)': '{:.1%}',
                    'CAGR (Total)': '{:.1%}',
                    'MaxDD (Recent)': '{:.1%}',
                    'MaxDD (Total)': '{:.1%}',
                    'WinRate (Recent)': '{:.1%}',
                    'WinRate (Total)': '{:.1%}',
                    'P/L (Recent)': '${:,.0f}',
                    'P/L (Total)': '${:,.0f}',
                    'Premium': '${:.2f}'
                }).map(color_mar, subset=['MAR (Recent)', 'MAR (Total)']),
                use_container_width=True,
                height=500
            )

            # --- DEEP DIVE VISUALIZATION ---
            st.divider()
            ui.section_header("Deep Dive: Parameter Impact")

            viz_c1, viz_c2 = st.columns(2)

            with viz_c1:
                st.markdown("**Best Entry Times (Top 50 Combinations)**")
                if not filtered_res.empty:
                    # Sort entry times chronologically
                    top_times = filtered_res.head(50)['EntryTime'].value_counts()
                    top_times = top_times.reindex(sorted(top_times.index))
                    fig_times = px.bar(x=top_times.index, y=top_times.values,
                                       labels={'x': 'Entry Time', 'y': 'Frequency in Top 50'},
                                       template="plotly_white")
                    fig_times.update_traces(marker_color=ui.COLOR_TEAL)
                    st.plotly_chart(fig_times, use_container_width=True)

            with viz_c2:
                st.markdown("**Robustness: Recent vs Total**")
                if not filtered_res.empty:
                    fig_scat = px.scatter(
                        filtered_res,
                        x="MAR (Total)",
                        y="MAR (Recent)",
                        color="Width",
                        size="Premium",
                        hover_data=["EntryTime", "SL"],
                        template="plotly_white",
                        title="Consistency Check (Size = Premium, Color = Width)"
                    )
                    # Draw green zone
                    fig_scat.add_shape(type="rect",
                                       x0=1.0, y0=2.0, x1=5.0, y1=10.0,
                                       line=dict(color="Green", width=1, dash="dot"),
                                       fillcolor="rgba(0,255,0,0.1)")
                    st.plotly_chart(fig_scat, use_container_width=True)

            # --- HEATMAP: Entry Time × Strategy Parameter ---
            st.divider()
            ui.section_header("Entry Time × Strategy Heatmap")

            if not filtered_res.empty and len(filtered_res) > 5:
                heatmap_col1, heatmap_col2 = st.columns([1, 3])

                with heatmap_col1:
                    heatmap_x = st.selectbox("X-Axis (Strategy Param):", ["Width", "SL", "Premium"], key="heatmap_x_axis")
                    heatmap_metric = st.selectbox("Metric:", ["MAR (Recent)", "MAR (Total)", "P/L (Recent)", "WinRate (Recent)"], key="heatmap_metric")

                with heatmap_col2:
                    # Create pivot table for heatmap
                    try:
                        heat_pivot = filtered_res.pivot_table(
                            index='EntryTime',
                            columns=heatmap_x,
                            values=heatmap_metric,
                            aggfunc='mean'
                        ).fillna(0)

                        if not heat_pivot.empty:
                            # Sort entry times chronologically (9:32 to 16:00)
                            sorted_times = sorted(heat_pivot.index)
                            heat_pivot = heat_pivot.reindex(sorted_times)

                            # Color scale based on metric
                            if "MAR" in heatmap_metric:
                                colorscale = 'RdYlGn'
                            elif "P/L" in heatmap_metric:
                                colorscale = 'RdYlGn'
                            else:
                                colorscale = 'Blues'

                            fig_heat = go.Figure(data=go.Heatmap(
                                z=heat_pivot.values,
                                x=[str(c) for c in heat_pivot.columns],
                                y=heat_pivot.index,
                                colorscale=colorscale,
                                text=heat_pivot.values,
                                texttemplate="%{text:.2f}",
                                textfont={"size": 11},
                                hovertemplate=f"Entry Time: %{{y}}<br>{heatmap_x}: %{{x}}<br>{heatmap_metric}: %{{z:.2f}}<extra></extra>"
                            ))

                            fig_heat.update_layout(
                                template="plotly_white",
                                height=max(400, len(heat_pivot) * 25),
                                xaxis_title=heatmap_x,
                                yaxis_title="Entry Time",
                                margin=dict(l=80, r=20, t=40, b=60),
                                # Ensure y-axis is sorted chronologically
                                yaxis=dict(categoryorder='array', categoryarray=sorted_times)
                            )

                            st.plotly_chart(fig_heat, use_container_width=True)
                        else:
                            st.info("Not enough data for heatmap with current filters.")
                    except Exception as e:
                        st.warning(f"Could not generate heatmap: {e}")
            else:
                st.info("Need more filtered results to generate heatmap.")

            # --- DOWNLOAD RESULTS ---
            ui.section_header("Export")
            if not filtered_res.empty:
                csv_export = filtered_res.to_csv(index=False)
                st.download_button("Download Top Results (.csv)", csv_export, "meic_optimized_results.csv", "text/csv", key="opt_download")
