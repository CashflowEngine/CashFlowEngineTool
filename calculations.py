import streamlit as st
import pandas as pd
import numpy as np
from scipy import stats
import logging
import yfinance as yf
import io
import re

logger = logging.getLogger(__name__)

# --- DATA LOADING ---
@st.cache_data(show_spinner=False)
def load_and_clean(_file_content, file_name):
    try:
        if file_name.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(io.BytesIO(_file_content))
        else:
            df = pd.read_csv(io.BytesIO(_file_content))

        df.columns = df.columns.str.strip()
        
        col_map = {}
        for col in df.columns:
            c_low = col.lower()
            if c_low in ['profit/loss', 'p/l', 'net profit', 'pnl', 'profit']:
                col_map[col] = 'pnl'
            elif c_low in ['margin', 'margin req', 'margin req.', 'margin requirement']:
                col_map[col] = 'margin'
            elif 'no. of contracts' in c_low or c_low in ['contracts', 'quantity', 'qty', 'size']:
                col_map[col] = 'contracts'
            elif 'time closed' in c_low:
                col_map[col] = 'time'
            elif c_low in ['date closed', 'exit date', 'close date', 'date/time', 'date']:
                col_map[col] = 'date'
            elif 'time opened' in c_low:
                col_map[col] = 'time_open'
            elif c_low in ['date opened', 'entry date', 'open date']:
                col_map[col] = 'date_open'
            elif 'strategy' in c_low:
                col_map[col] = 'strategy'
            elif 'legs' in c_low:
                col_map[col] = 'legs'

        df.rename(columns=col_map, inplace=True)

        if 'Entry Time' in df.columns:
            df.rename(columns={'Entry Time': 'timestamp_open'}, inplace=True)
        if 'Close Time' in df.columns:
            df.rename(columns={'Close Time': 'timestamp_close'}, inplace=True)
        if 'Profit' in df.columns and 'pnl' not in df.columns:
            df.rename(columns={'Profit': 'pnl'}, inplace=True)

        if 'Strategy' in df.columns and 'strategy' not in df.columns:
            df['strategy'] = df['Strategy'].astype(str).str.replace('SPX: ', '', regex=False)
        elif 'Name' in df.columns and 'strategy' not in df.columns:
            df['strategy'] = df['Name']

        if 'pnl' not in df.columns:
            logger.warning(f"No PnL column found in {file_name}")
            return None

        for col in ['pnl', 'margin']:
            if col in df.columns and df[col].dtype == object:
                df[col] = pd.to_numeric(
                    df[col].astype(str).str.replace(r'[$,]', '', regex=True),
                    errors='coerce'
                )

        if 'margin' not in df.columns:
            df['margin'] = 0.0
        else:
            df['margin'] = df['margin'].abs().fillna(0)

        if 'timestamp_open' in df.columns:
            df['timestamp_open'] = pd.to_datetime(df['timestamp_open'], errors='coerce')

        if 'timestamp_close' in df.columns:
            df['timestamp_close'] = pd.to_datetime(df['timestamp_close'], errors='coerce')
            df['timestamp'] = df['timestamp_close'].fillna(df.get('timestamp_open', df['timestamp_close']))
        elif 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'], errors='coerce')
            if 'time' in df.columns:
                df['timestamp_close'] = pd.to_datetime(
                    df['date'].astype(str) + ' ' + df['time'].astype(str), errors='coerce'
                ).fillna(df['date'])
            else:
                df['timestamp_close'] = df['date']
            df['timestamp'] = df['timestamp_close']

            if 'date_open' in df.columns:
                df['date_open'] = pd.to_datetime(df['date_open'], errors='coerce')
                if 'time_open' in df.columns:
                    df['timestamp_open'] = pd.to_datetime(
                        df['date_open'].astype(str) + ' ' + df['time_open'].astype(str), errors='coerce'
                    ).fillna(df['date_open'])
                else:
                    df['timestamp_open'] = df['date_open']
            else:
                df['timestamp_open'] = df['timestamp_close']
        else:
            df['timestamp'] = pd.to_datetime(df.index)

        if not np.issubdtype(df['timestamp'].dtype, np.datetime64):
            df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')

        df = df.dropna(subset=['timestamp'])

        if 'strategy' not in df.columns:
            df['strategy'] = file_name.rsplit('.', 1)[0]

        cols = ['pnl', 'margin', 'contracts', 'timestamp', 'timestamp_open', 'timestamp_close', 'strategy']
        optional = ['legs', 'date', 'Open']
        cols.extend([c for c in optional if c in df.columns])
        
        return df[[c for c in cols if c in df.columns]]

    except Exception as e:
        logger.error(f"Error loading file {file_name}: {e}")
        return None

def load_file_with_caching(uploaded_file):
    content = uploaded_file.read()
    uploaded_file.seek(0)
    return load_and_clean(content, uploaded_file.name)

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_spx_benchmark(start_date, end_date):
    """Fetch SPX benchmark data with timeout protection."""
    import concurrent.futures
    import threading

    def _fetch_data():
        """Inner function to fetch data - runs in thread."""
        s_date = start_date - pd.Timedelta(days=5)
        s_str = s_date.strftime('%Y-%m-%d')
        e_str = end_date.strftime('%Y-%m-%d')
        data = yf.download("^GSPC", start=s_str, end=e_str, progress=False, auto_adjust=True)
        if data.empty: return None
        if isinstance(data.columns, pd.MultiIndex):
            if 'Close' in data.columns.get_level_values(0):
                close_data = data['Close']
                if isinstance(close_data, pd.DataFrame):
                    close_data = close_data.iloc[:, 0]
                return close_data
            else:
                return data.iloc[:, 0]
        else:
            if 'Close' in data.columns: return data['Close']
            return data.iloc[:, 0]

    try:
        # Use ThreadPoolExecutor with timeout to prevent hanging
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(_fetch_data)
            try:
                # 10 second timeout for the API call
                result = future.result(timeout=10)
                return result
            except concurrent.futures.TimeoutError:
                logger.warning("SPX benchmark fetch timed out after 10 seconds")
                return None
    except Exception as e:
        logger.error(f"Failed to fetch SPX data: {e}")
        return None

# --- FINANCIAL MATH ---

def generate_daily_margin_series_optimized(df_strat):
    if df_strat.empty or 'margin' not in df_strat.columns:
        return pd.Series(dtype=float)
    
    if 'timestamp_open' not in df_strat.columns or 'timestamp_close' not in df_strat.columns:
        return pd.Series(dtype=float)

    df = df_strat.copy()
    df['margin'] = df['margin'].fillna(0)

    smart_trades = []
    
    for t_open, group in df.groupby('timestamp_open'):
        if pd.isna(t_open): continue
            
        put_m, call_m, unk_m = 0.0, 0.0, 0.0
        
        for _, row in group.iterrows():
            m = row['margin'] if not pd.isna(row['margin']) else 0
            legs = str(row.get('legs', '')).upper()
            
            if any(x in legs for x in [' P ', ' PUT ', ' P:']): put_m += m
            elif any(x in legs for x in [' C ', ' CALL ', ' C:']): call_m += m
            else: unk_m += m
        
        smart_margin = max(put_m, call_m) + unk_m
        
        if smart_margin > 0:
            t_close = group['timestamp_close'].max()
            if pd.isna(t_close): t_close = t_open
            smart_trades.append({
                'start': pd.Timestamp(t_open).normalize(),
                'end': pd.Timestamp(t_close).normalize(),
                'margin': smart_margin
            })

    if not smart_trades: return pd.Series(dtype=float)

    trades_df = pd.DataFrame(smart_trades)
    min_date = trades_df['start'].min()
    max_date = trades_df['end'].max()
    
    date_range = pd.date_range(start=min_date, end=max_date, freq='D')
    margin_changes = pd.Series(0.0, index=date_range)
    
    for _, trade in trades_df.iterrows():
        if trade['start'] in margin_changes.index:
            margin_changes.loc[trade['start']] += trade['margin']
        end_plus_one = trade['end'] + pd.Timedelta(days=1)
        if end_plus_one in margin_changes.index:
            margin_changes.loc[end_plus_one] -= trade['margin']

    return margin_changes.cumsum()

def calculate_streaks_optimized(pnl_values):
    if len(pnl_values) == 0: return 0, 0
    pnl = np.asarray(pnl_values)
    wins = pnl > 0
    losses = pnl <= 0
    def max_streak(arr):
        if len(arr) == 0 or not arr.any(): return 0
        padded = np.concatenate([[False], arr, [False]])
        changes = np.diff(padded.astype(int))
        starts = np.where(changes == 1)[0]
        ends = np.where(changes == -1)[0]
        if len(starts) == 0: return 0
        return int(np.max(ends - starts))
    return max_streak(wins), max_streak(losses)

def calculate_advanced_metrics(daily_returns_series, trades_df=None, benchmark_series=None, account_size=100000):
    metrics = {
        "CAGR": 0, "Vol": 0, "Sharpe": 0, "Sortino": 0,
        "MaxDD": 0, "MaxDD_USD": 0, "MAR": 0, "MART": 0,
        "WinRate": 0, "PF": 0, "Alpha": 0, "Beta": 0, "Kelly": 0,
        "WinStreak": 0, "LossStreak": 0, "AvgRetMargin": 0, "Trades": 0,
        "SPX_CAGR": 0, "SPX_MaxDD": 0, "SPX_Vol": 0, "SPX_Sharpe": 0, 
        "SPX_TotalRet": 0, "SPX_TotalPnL_USD": 0
    }

    n_days = len(daily_returns_series)
    if n_days < 2: return metrics

    total_ret = (1 + daily_returns_series).prod() - 1
    cagr = (1 + total_ret) ** (365 / n_days) - 1 if total_ret > -1 else 0
    volatility = daily_returns_series.std() * np.sqrt(252)

    rf = 0.04
    excess_ret = daily_returns_series.mean() * 252 - rf
    sharpe = excess_ret / volatility if volatility > 0 else 0

    neg_ret = daily_returns_series[daily_returns_series < 0]
    downside_std = neg_ret.std() * np.sqrt(252) if len(neg_ret) > 0 else 0
    sortino = excess_ret / downside_std if downside_std > 0 else 0

    equity_curve = account_size * (1 + daily_returns_series).cumprod()
    peak_eq = equity_curve.cummax()
    
    dd_pct = (equity_curve - peak_eq) / peak_eq
    max_dd_pct = dd_pct.min()
    
    dd_usd = equity_curve - peak_eq
    max_dd_val = dd_usd.min()
    
    mar = cagr / abs(max_dd_pct) if max_dd_pct != 0 else 0
    
    dd_pct_initial = abs(max_dd_val) / account_size if account_size > 0 else 0
    mart = cagr / dd_pct_initial if dd_pct_initial != 0 else 0

    if trades_df is not None and not trades_df.empty:
        num_trades = len(trades_df)
        pnl = trades_df['pnl'].values
        wins = pnl[pnl > 0]
        losses = pnl[pnl <= 0]
        win_rate = len(wins) / num_trades if num_trades > 0 else 0
        pf = wins.sum() / abs(losses.sum()) if losses.sum() != 0 else 999
        avg_win = wins.mean() if len(wins) > 0 else 0
        avg_loss = abs(losses.mean()) if len(losses) > 0 else 0
        kelly = 0
        if avg_loss > 0 and avg_win > 0:
            b = avg_win / avg_loss
            if b > 0:
                p = win_rate
                q = 1 - p
                kelly = (p * b - q) / b

        avg_ret_margin = 0
        if 'margin' in trades_df.columns:
            valid_m = trades_df[trades_df['margin'] > 0]
            if not valid_m.empty:
                avg_ret_margin = (valid_m['pnl'] / valid_m['margin']).mean()

        max_w_streak, max_l_streak = calculate_streaks_optimized(pnl)

        metrics.update({
            "Trades": num_trades, "WinRate": win_rate, "PF": pf, "Kelly": kelly,
            "AvgRetMargin": avg_ret_margin, "WinStreak": max_w_streak, "LossStreak": max_l_streak
        })

    if benchmark_series is not None and not benchmark_series.empty:
        benchmark_clean = benchmark_series.dropna()
        if len(benchmark_clean) > 0:
            aligned = pd.concat([daily_returns_series, benchmark_clean], axis=1).dropna()
            if len(aligned) > 20:
                y = aligned.iloc[:, 0].values
                x = aligned.iloc[:, 1].values
                mask = np.isfinite(x) & np.isfinite(y)
                if mask.sum() > 20:
                    slope, intercept, _, _, _ = stats.linregress(x[mask], y[mask])
                    metrics["Beta"] = slope
                    metrics["Alpha"] = intercept * 252

            spx_tot = (1 + benchmark_clean).prod() - 1
            # Calculate SPX dollar PnL assuming same starting capital
            spx_pnl_usd = spx_tot * account_size
            
            # SPX CAGR
            spx_cagr = (1 + spx_tot) ** (365 / len(benchmark_clean)) - 1 if len(benchmark_clean) > 0 and spx_tot > -1 else 0
            
            # SPX Drawdown
            spx_cum = (1 + benchmark_clean).cumprod()
            spx_peak = spx_cum.cummax()
            spx_dd = (spx_cum - spx_peak) / spx_peak
            
            spx_vol = benchmark_clean.std() * np.sqrt(252) if len(benchmark_clean) > 0 else 0
            spx_excess = benchmark_clean.mean() * 252 - rf
            spx_sharpe = spx_excess / spx_vol if spx_vol > 0 else 0
            
            metrics["SPX_CAGR"] = spx_cagr
            metrics["SPX_MaxDD"] = spx_dd.min() if len(spx_dd) > 0 else 0
            metrics["SPX_Vol"] = spx_vol
            metrics["SPX_Sharpe"] = spx_sharpe
            metrics["SPX_TotalRet"] = spx_tot
            metrics["SPX_TotalPnL_USD"] = spx_pnl_usd

    metrics.update({
        "CAGR": cagr, "Vol": volatility, "Sharpe": sharpe, "Sortino": sortino,
        "MaxDD": max_dd_pct, "MaxDD_USD": max_dd_val, "MAR": mar, "MART": mart
    })

    return metrics

def calculate_lots_from_trades(strat_df):
    if strat_df.empty: return 0, 0
    qty_col = None
    for col in strat_df.columns:
        if col.lower() in ['quantity', 'qty', 'contracts', 'size']:
            qty_col = col
            break
    
    if 'timestamp_open' in strat_df.columns:
        if qty_col:
            lots_per_entry = strat_df.groupby('timestamp_open')[qty_col].sum()
        else:
            entries_per_open = strat_df.groupby('timestamp_open').size()
            lots_per_entry = pd.Series(1, index=entries_per_open.index)
        total_lots = len(lots_per_entry)
        trading_days = strat_df['timestamp_open'].dt.date.nunique()
        avg_lots_per_day = total_lots / trading_days if trading_days > 0 else 0
    else:
        if qty_col: total_lots = strat_df[qty_col].sum()
        else: total_lots = len(strat_df)
        trading_days = strat_df['timestamp'].dt.date.nunique()
        avg_lots_per_day = total_lots / trading_days if trading_days > 0 else 0
    
    return int(total_lots), avg_lots_per_day

def _infer_strategy_dna(strategy_name, strat_df=None):
    n = strategy_name.upper()
    dna = {"Type": "Custom", "Delta": "Neutral", "Vega": "Neutral", "Theta": "Neutral", "Gamma": "Neutral"}
    if "LONG PUT" in n or (" P " in n and "LONG" in n): return {"Type": "Long Put", "Delta": "Short", "Vega": "Long", "Theta": "Short", "Gamma": "Long"}
    if "SHORT PUT" in n or (" P " in n and "SHORT" in n): return {"Type": "Short Put", "Delta": "Long", "Vega": "Short", "Theta": "Long", "Gamma": "Short"}
    if "LONG CALL" in n: return {"Type": "Long Call", "Delta": "Long", "Vega": "Long", "Theta": "Short", "Gamma": "Long"}
    if strat_df is not None and not strat_df.empty and 'legs' in strat_df.columns and 'timestamp_open' in strat_df.columns:
        sample = strat_df.head(100)
        ic_count = 0
        for i, (_, group) in enumerate(sample.groupby('timestamp_open')):
            if i >= 20: break
            legs = " | ".join(group['legs'].dropna().astype(str).tolist()).upper()
            if (" C STO" in legs or " CALL STO" in legs) and (" P STO" in legs or " PUT STO" in legs): ic_count += 1
        if ic_count > 0: return {"Type": "Iron Condor", "Delta": "Neutral", "Vega": "Short", "Theta": "Long", "Gamma": "Short"}
    if "METF CALL" in n: return {"Type": "Bear Call Spread", "Delta": "Short", "Vega": "Short", "Theta": "Long", "Gamma": "Short"}
    if "METF PUT" in n: return {"Type": "Bull Put Spread", "Delta": "Long", "Vega": "Short", "Theta": "Long", "Gamma": "Short"}
    if "DC" in n or "DOUBLE CALENDAR" in n: return {"Type": "Double Calendar", "Delta": "Neutral", "Vega": "Long", "Theta": "Long", "Gamma": "Short"}
    if "RIC" in n or "REVERSE IRON" in n: return {"Type": "Reverse Iron Condor", "Delta": "Neutral", "Vega": "Long", "Theta": "Short", "Gamma": "Long"}
    if "BCS" in n: return {"Type": "Bull Call Spread", "Delta": "Long", "Vega": "Long", "Theta": "Short", "Gamma": "Long"}
    if "BPS" in n: return {"Type": "Bull Put Spread", "Delta": "Long", "Vega": "Short", "Theta": "Long", "Gamma": "Short"}
    if any(x in n for x in ["BUTTERFLY", "FLY", "BWB"]): return {"Type": "Butterfly", "Delta": "Neutral", "Vega": "Short", "Theta": "Long", "Gamma": "Short"}
    return dna

def get_cached_dna(strategy_name, strat_df=None):
    if 'dna_cache' not in st.session_state: st.session_state.dna_cache = {}
    if strategy_name in st.session_state.dna_cache: return st.session_state.dna_cache[strategy_name]
    dna = _infer_strategy_dna(strategy_name, strat_df)
    st.session_state.dna_cache[strategy_name] = dna
    return dna

def categorize_strategy(strategy_name, strat_df=None):
    n = strategy_name.upper()
    workhorse_patterns = ['IC', 'IRON CONDOR', 'MEIC', 'PUT SPREAD', 'CALL SPREAD', 'BPS', 'BCS', 'CREDIT', 'BUTTERFLY', 'FLY', 'BWB', 'SHORT PUT', 'SHORT CALL', 'NAKED', 'COVERED']
    airbag_patterns = ['CALENDAR', 'DC', 'DOUBLE CALENDAR', 'LONG PUT', 'STRANGLE', 'STRADDLE', 'PROTECTIVE', 'COLLAR', 'HEDGE', 'VIX', 'UVXY']
    opportunist_patterns = ['LONG CALL', 'DEBIT', 'BULL CALL', 'BEAR PUT', 'DIRECTIONAL', 'MOMENTUM', 'BREAKOUT', 'TREND']
    for pattern in workhorse_patterns:
        if pattern in n: return 'Workhorse'
    for pattern in airbag_patterns:
        if pattern in n: return 'Airbag'
    for pattern in opportunist_patterns:
        if pattern in n: return 'Opportunist'
    if 'METF' in n or 'SPREAD' in n: return 'Workhorse'
    return 'Workhorse'

# --- NEW HELPERS (Fixing AttributeError) ---
def parse_meic_filename(filename):
    """Parses params from filename: MEIC_W{width}_SL{sl}_P{premium}.csv"""
    width_match = re.search(r'W(\d+)', filename, re.IGNORECASE)
    sl_match = re.search(r'SL(\d+)', filename, re.IGNORECASE)
    prem_match = re.search(r'P(\d+\.?\d*)', filename, re.IGNORECASE)
    return {
        'Width': int(width_match.group(1)) if width_match else None,
        'SL': int(sl_match.group(1)) if sl_match else None,
        'Premium': float(prem_match.group(1)) if prem_match else None,
        'Filename': filename
    }

def generate_oo_signals(start_date, end_date, start_time="09:35", end_time="15:55", interval_min=5):
    """Generates OO signal CSV."""
    dates = pd.date_range(start=start_date, end=end_date, freq='B') 
    signal_rows = []
    t_start = pd.to_datetime(start_time).time()
    t_end = pd.to_datetime(end_time).time()
    
    for d in dates:
        if d.month == 12 and d.day == 25: continue
        if d.month == 1 and d.day == 1: continue
        if d.month == 7 and d.day == 4: continue
        current_ts = pd.Timestamp.combine(d.date(), t_start)
        end_ts = pd.Timestamp.combine(d.date(), t_end)
        while current_ts <= end_ts:
            signal_rows.append(current_ts)
            current_ts += pd.Timedelta(minutes=interval_min)
            
    df_signals = pd.DataFrame(signal_rows, columns=['OPEN_DATETIME'])
    df_signals['OPEN_DATETIME'] = df_signals['OPEN_DATETIME'].dt.strftime('%Y-%m-%d %H:%M')
    return df_signals

def analyze_meic_group(df, account_size):
    if df.empty: return {'MAR': 0, 'CAGR': 0, 'MaxDD': 0}
    df = df.sort_values('timestamp')
    daily_pnl = df.set_index('timestamp').resample('D')['pnl'].sum()
    equity = account_size + daily_pnl.cumsum()
    peak = equity.cummax()
    max_dd = ((equity - peak) / peak).min()
    days = (df['timestamp'].max() - df['timestamp'].min()).days or 1
    cagr = (1 + daily_pnl.sum() / account_size) ** (365 / days) - 1
    mar = cagr / abs(max_dd) if max_dd != 0 else 0
    return {'MAR': mar, 'CAGR': cagr, 'MaxDD': max_dd}


# --- PORTFOLIO OPTIMIZATION FUNCTIONS ---

def kelly_optimize_allocation(strategy_stats, target_margin, kelly_pct,
                              workhorse_target=None, airbag_target=None, opportunist_target=None,
                              category_overrides=None, max_multiplier=3.0):
    """
    Kelly Criterion optimization - distributes margin based on each strategy's Kelly %.

    NO CATEGORIES - all strategies compete equally for the margin budget.

    Logic:
    1. Available capital = target_margin × kelly_pct
    2. Each strategy gets: (its_kelly / sum_of_all_kelly) × available_capital
    3. Convert allocated margin to multiplier

    Args:
        strategy_stats: Dict with strategy data (kelly, margin_per_contract, contracts_per_day)
        target_margin: Total margin budget in dollars
        kelly_pct: Fraction of target_margin to allocate (0.0 to 1.0)
        max_multiplier: Cap on multiplier value (default 3.0)

    Returns:
        Dict of {strategy_name: multiplier}
    """
    # Available capital = target_margin * kelly_pct
    available_capital = target_margin * kelly_pct

    # Build list of strategies with their data
    strategy_list = []
    total_kelly = 0.0

    for strat_name, stats in strategy_stats.items():
        kelly = stats.get('kelly', 0)
        if kelly <= 0:
            kelly = 0.01  # Give tiny allocation to strategies with 0 or negative Kelly

        # margin_per_contract is actually max daily margin for this strategy
        margin_at_1x = stats.get('margin_per_contract', 0)

        if margin_at_1x <= 0:
            continue

        strategy_list.append({
            'name': strat_name,
            'kelly': kelly,
            'margin_at_1x': margin_at_1x
        })
        total_kelly += kelly

    # Calculate allocation for each strategy
    allocation = {}

    for s in strategy_list:
        if total_kelly > 0:
            # Weight = this strategy's Kelly / total Kelly
            weight = s['kelly'] / total_kelly

            # Allocated margin for this strategy
            allocated_margin = available_capital * weight

            # Multiplier = allocated_margin / margin_at_1x
            multiplier = allocated_margin / s['margin_at_1x']

            # Round to 1 decimal place
            multiplier = round(multiplier, 1)

            # Cap at max_multiplier, floor at 0
            multiplier = max(0, min(multiplier, max_multiplier))
        else:
            multiplier = 0

        allocation[s['name']] = multiplier

    return allocation


def mart_optimize_allocation(strategy_stats, target_margin, account_size,
                             category_overrides=None, full_date_range=None,
                             filtered_df=None, min_pnl=0, max_iterations=50):
    """
    MART Ratio optimization - maximizes MART = CAGR / (MaxDD$ / Account).

    Uses greedy algorithm:
    1. Start with all multipliers at 0
    2. Each iteration: try adding 0.1 to each strategy's multiplier
    3. Pick the change that improves MART the most
    4. Stop when margin limit reached or no improvement

    Args:
        strategy_stats: Dict with strategy data
        target_margin: Margin constraint in dollars
        account_size: Account value for MART calculation
        full_date_range: Date range for portfolio calculations
        min_pnl: Optional minimum P&L target
        max_iterations: Maximum optimization steps

    Returns:
        Dict of {strategy_name: multiplier}
    """
    # Build strategy list
    strategy_list = []

    for strat_name, stats in strategy_stats.items():
        margin_at_1x = stats.get('margin_per_contract', 0)
        pnl_at_1x = stats.get('total_pnl', 0)
        daily_pnl = stats.get('daily_pnl_series', None)

        if margin_at_1x <= 0 or daily_pnl is None:
            continue

        strategy_list.append({
            'name': strat_name,
            'margin_at_1x': margin_at_1x,
            'pnl_at_1x': pnl_at_1x,
            'daily_pnl': daily_pnl
        })

    if not strategy_list or full_date_range is None:
        # Return 1.0 for all if we can't optimize
        return {strat_name: 1.0 for strat_name in strategy_stats.keys()}

    # Initialize all multipliers at 0
    allocation = {s['name']: 0.0 for s in strategy_list}

    def calc_portfolio_metrics(alloc):
        """Calculate MART, total margin, and total P&L for given allocation."""
        port_pnl = pd.Series(0.0, index=full_date_range)
        total_margin = 0.0
        total_pnl = 0.0

        for s in strategy_list:
            mult = alloc.get(s['name'], 0)
            if mult > 0:
                port_pnl = port_pnl.add(s['daily_pnl'] * mult, fill_value=0)
                total_margin += s['margin_at_1x'] * mult
                total_pnl += s['pnl_at_1x'] * mult

        if total_margin == 0:
            return 0.0, 0.0, 0.0

        # Calculate equity curve
        port_equity = account_size + port_pnl.cumsum()

        # Calculate CAGR
        days = len(port_pnl)
        if days < 2:
            return 0.0, total_margin, total_pnl

        total_ret = port_pnl.sum() / account_size
        if total_ret <= -1:
            cagr = -1.0
        else:
            cagr = (1 + total_ret) ** (365 / days) - 1

        # Calculate max drawdown in dollars
        peak = port_equity.cummax()
        drawdown = port_equity - peak
        max_dd_dollars = abs(drawdown.min())

        # MART = CAGR / (MaxDD$ / Account)
        dd_ratio = max_dd_dollars / account_size if account_size > 0 else 1.0
        mart = cagr / dd_ratio if dd_ratio > 0.001 else 0.0

        return mart, total_margin, total_pnl

    # Greedy optimization
    step_size = 0.1
    best_mart = 0.0

    for _ in range(max_iterations):
        best_improvement = 0.0
        best_change = None

        # Try incrementing each strategy
        for s in strategy_list:
            current_mult = allocation[s['name']]
            new_mult = round(current_mult + step_size, 1)

            # Cap at 3.0
            if new_mult > 3.0:
                continue

            # Test this change
            test_alloc = allocation.copy()
            test_alloc[s['name']] = new_mult

            mart, margin, pnl = calc_portfolio_metrics(test_alloc)

            # Check margin constraint (allow 5% overshoot)
            if margin > target_margin * 1.05:
                continue

            # Is this better?
            improvement = mart - best_mart
            if improvement > best_improvement:
                best_improvement = improvement
                best_change = (s['name'], new_mult, mart)

        # Apply best change if found
        if best_change and best_improvement > 0.001:
            allocation[best_change[0]] = best_change[1]
            best_mart = best_change[2]
        else:
            # No improvement found, stop
            break

    # Phase 2: If min_pnl target not met, add more positions
    if min_pnl > 0:
        _, _, current_pnl = calc_portfolio_metrics(allocation)

        if current_pnl < min_pnl:
            # Sort by P&L efficiency (P&L per margin dollar)
            sorted_strats = sorted(strategy_list,
                key=lambda s: s['pnl_at_1x'] / max(1, s['margin_at_1x']),
                reverse=True)

            for _ in range(max_iterations):
                _, current_margin, current_pnl = calc_portfolio_metrics(allocation)

                if current_pnl >= min_pnl or current_margin >= target_margin:
                    break

                # Try adding to best P&L strategy that fits
                added = False
                for s in sorted_strats:
                    current_mult = allocation[s['name']]
                    new_mult = round(current_mult + step_size, 1)

                    if new_mult > 3.0:
                        continue

                    test_alloc = allocation.copy()
                    test_alloc[s['name']] = new_mult
                    _, test_margin, _ = calc_portfolio_metrics(test_alloc)

                    if test_margin <= target_margin * 1.05:
                        allocation[s['name']] = new_mult
                        added = True
                        break

                if not added:
                    break

    return allocation
