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
    try:
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
        "SPX_CAGR": 0, "SPX_MaxDD": 0, "SPX_Vol": 0, "SPX_Sharpe": 0, "SPX_TotalRet": 0
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
            spx_cagr = (1 + spx_tot) ** (365 / len(benchmark_clean)) - 1 if len(benchmark_clean) > 0 and spx_tot > -1 else 0
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

# --- MONTE CARLO & OPTIMIZATION (Moved from calc.py) ---

def run_monte_carlo_optimized(trades, n_simulations, n_steps, start_capital, batch_size=1000, 
                               stress_injections=None, n_stress_per_sim=0, n_years=1, injection_mode='distributed'):
    """
    OPTIMIZED: Fully vectorized Monte Carlo simulation with batched processing.
    """
    def get_distributed_positions(n_steps, n_events, n_years):
        if n_events == 0: return []
        steps_per_year = n_steps / n_years
        positions = []
        for i in range(n_events):
            year_idx = i % int(n_years)
            year_start = int(year_idx * steps_per_year)
            year_end = int((year_idx + 1) * steps_per_year)
            if year_end > year_start:
                pos = np.random.randint(year_start, year_end)
                positions.append(pos)
        return positions
    
    def get_random_positions(n_steps, n_events):
        if n_events == 0: return []
        return np.random.choice(n_steps, size=min(n_events, n_steps), replace=False).tolist()
    
    def inject_stress_events(random_trades, sim_idx, stress_injections, n_stress_per_sim, n_steps, n_years, mode):
        if mode == 'random':
            positions = get_random_positions(n_steps, len(stress_injections))
            for i, pos in enumerate(positions):
                if i < len(stress_injections):
                    random_trades[sim_idx, pos] = stress_injections[i]
        else:
            positions = get_distributed_positions(n_steps, n_stress_per_sim, n_years)
            for pos in positions:
                random_trades[sim_idx, pos] = stress_injections[0]
    
    if n_simulations <= batch_size:
        random_trades = np.random.choice(trades, size=(n_simulations, n_steps), replace=True)
        if stress_injections is not None and n_stress_per_sim > 0 and len(stress_injections) > 0:
            for sim_idx in range(n_simulations):
                inject_stress_events(random_trades, sim_idx, stress_injections, n_stress_per_sim, n_steps, n_years, injection_mode)
        cumsum = np.cumsum(random_trades, axis=1)
        paths = np.zeros((n_simulations, n_steps + 1), dtype=np.float32)
        paths[:, 0] = start_capital
        paths[:, 1:] = start_capital + cumsum
        return paths
    
    n_batches = (n_simulations + batch_size - 1) // batch_size
    max_paths_to_store = min(500, n_simulations)
    stored_paths = np.zeros((max_paths_to_store, n_steps + 1), dtype=np.float32)
    all_end_vals = np.zeros(n_simulations, dtype=np.float32)
    all_max_dds = np.zeros(n_simulations, dtype=np.float32)
    paths_stored = 0
    
    for batch_idx in range(n_batches):
        batch_start = batch_idx * batch_size
        batch_end = min(batch_start + batch_size, n_simulations)
        current_batch_size = batch_end - batch_start
        
        random_trades = np.random.choice(trades, size=(current_batch_size, n_steps), replace=True)
        if stress_injections is not None and n_stress_per_sim > 0 and len(stress_injections) > 0:
            for sim_idx in range(current_batch_size):
                inject_stress_events(random_trades, sim_idx, stress_injections, n_stress_per_sim, n_steps, n_years, injection_mode)
        
        cumsum = np.cumsum(random_trades, axis=1)
        batch_paths = np.zeros((current_batch_size, n_steps + 1), dtype=np.float32)
        batch_paths[:, 0] = start_capital
        batch_paths[:, 1:] = start_capital + cumsum
        
        all_end_vals[batch_start:batch_end] = batch_paths[:, -1]
        
        running_max = np.maximum.accumulate(batch_paths, axis=1)
        with np.errstate(divide='ignore', invalid='ignore'):
            drawdowns = (running_max - batch_paths) / running_max
            drawdowns = np.nan_to_num(drawdowns, nan=0.0, posinf=0.0, neginf=0.0)
        all_max_dds[batch_start:batch_end] = np.max(drawdowns, axis=1)
        
        paths_to_add = min(current_batch_size, max_paths_to_store - paths_stored)
        if paths_to_add > 0:
            stored_paths[paths_stored:paths_stored + paths_to_add] = batch_paths[:paths_to_add]
            paths_stored += paths_to_add
            
    return stored_paths[:paths_stored], all_end_vals, all_max_dds

def calculate_max_drawdown_batch(paths, precomputed_dds=None):
    if precomputed_dds is not None: return precomputed_dds
    running_max = np.maximum.accumulate(paths, axis=1)
    with np.errstate(divide='ignore', invalid='ignore'):
        drawdowns = (running_max - paths) / running_max
        drawdowns = np.nan_to_num(drawdowns, nan=0.0, posinf=0.0, neginf=0.0)
    return np.max(drawdowns, axis=1)

def get_top_drawdowns_optimized(equity_curve, initial_capital):
    if equity_curve.empty: return pd.DataFrame()
    equity = equity_curve.values
    dates = equity_curve.index
    peak = np.maximum.accumulate(equity)
    dd_from_peak = equity - peak
    in_dd = dd_from_peak < 0
    dd_diff = np.diff(np.concatenate([[False], in_dd, [False]]).astype(int))
    starts_idx = np.where(dd_diff == 1)[0]
    ends_idx = np.where(dd_diff == -1)[0]
    
    drawdowns = []
    for i in range(len(starts_idx)):
        if i >= len(ends_idx): break
        start_idx = max(0, starts_idx[i] - 1)
        end_idx = min(ends_idx[i], len(equity) - 1)
        period_equity = equity[start_idx:end_idx + 1]
        period_peak = peak[start_idx:end_idx + 1]
        valley_idx_local = np.argmin(period_equity)
        valley_idx = start_idx + valley_idx_local
        dd_usd = period_peak[0] - period_equity[valley_idx_local]
        dd_pct_peak = (dd_usd / period_peak[0]) * 100 if period_peak[0] > 0 else 0
        dd_pct_initial = (dd_usd / initial_capital) * 100
        is_recovered = end_idx < len(equity) - 1 or not in_dd[-1] if len(in_dd) > 0 else True
        drawdowns.append({
            "Start Date": dates[start_idx].date() if hasattr(dates[start_idx], 'date') else dates[start_idx],
            "Bottom Date": dates[valley_idx].date() if hasattr(dates[valley_idx], 'date') else dates[valley_idx],
            "Recovery Date": dates[end_idx].date() if is_recovered and hasattr(dates[end_idx], 'date') else "Not yet",
            "Depth ($)": dd_usd,
            "Drop from Peak (%)": dd_pct_peak,
            "Drop of Init. Cap (%)": dd_pct_initial,
            "Duration (Days)": (dates[end_idx] - dates[start_idx]).days if hasattr(dates[end_idx] - dates[start_idx], 'days') else 0
        })
    df_dd = pd.DataFrame(drawdowns)
    if not df_dd.empty: df_dd = df_dd.sort_values(by="Depth ($)", ascending=False).head(10)
    return df_dd

def kelly_optimize_allocation(strategy_stats, target_margin, kelly_pct,
                              workhorse_target, airbag_target, opportunist_target,
                              category_overrides=None, max_multiplier=3.0):
    if category_overrides is None: category_overrides = {}
    available_capital = target_margin * kelly_pct
    category_budgets = {'Workhorse': available_capital * workhorse_target,
                        'Airbag': available_capital * airbag_target,
                        'Opportunist': available_capital * opportunist_target}
    category_strategies = {'Workhorse': [], 'Airbag': [], 'Opportunist': []}
    category_kelly_totals = {'Workhorse': 0, 'Airbag': 0, 'Opportunist': 0}
    
    for strat, stats in strategy_stats.items():
        category = category_overrides.get(strat, stats.get('category', 'Workhorse'))
        kelly = max(0, stats.get('kelly', 0))
        hist_lots = stats.get('contracts_per_day', 1)
        margin_historical = stats.get('margin_per_contract', 0) * hist_lots
        if margin_historical <= 0: continue
        if category in category_strategies:
            category_strategies[category].append({
                'strategy': strat, 'kelly': kelly, 'margin_historical': margin_historical,
                'hist_lots': hist_lots, 'margin_per_contract': stats.get('margin_per_contract', 0)
            })
            category_kelly_totals[category] += kelly
            
    allocation = {}
    for category, strategies in category_strategies.items():
        budget = category_budgets.get(category, 0)
        kelly_total = category_kelly_totals.get(category, 0)
        for s in strategies:
            if kelly_total > 0 and s['kelly'] > 0:
                weight = s['kelly'] / kelly_total
                allocated_margin = budget * weight
                multiplier = allocated_margin / s['margin_historical'] if s['margin_historical'] > 0 else 0
                hist_lots = s['hist_lots']
                if hist_lots <= 1: multiplier = round(multiplier)
                else:
                    step = 1.0 / hist_lots
                    multiplier = round(multiplier / step) * step
                multiplier = min(multiplier, max_multiplier)
                multiplier = max(0, multiplier)
            else: multiplier = 0
            allocation[s['strategy']] = round(multiplier, 4)
    return allocation

def mart_optimize_allocation(strategy_stats, target_margin, account_size,
                             category_overrides=None, full_date_range=None,
                             filtered_df=None, min_total_pnl=0, max_iterations=100):
    if category_overrides is None: category_overrides = {}
    strategies = []
    for strat, stats in strategy_stats.items():
        hist_lots = stats['contracts_per_day']
        margin_per_mult = stats['margin_per_contract'] * hist_lots
        total_pnl_at_1x = stats.get('total_pnl', 0)
        if margin_per_mult <= 0 or hist_lots <= 0: continue
        daily_pnl = stats.get('daily_pnl_series', None)
        if daily_pnl is None: continue
        if hist_lots <= 1: step, allowed_values = 1.0, [0, 1]
        else: step, allowed_values = max(0.1, round(1 / hist_lots, 1)), None
        strategies.append({
            'name': strat, 'hist_lots': hist_lots, 'margin_per_mult': margin_per_mult,
            'total_pnl_at_1x': total_pnl_at_1x, 'daily_pnl': daily_pnl,
            'step': step, 'allowed_values': allowed_values, 'max_mult': 3.0
        })
    
    if not strategies or full_date_range is None: return {s['name']: 1.0 for s in strategies}
    allocation = {s['name']: 0.0 for s in strategies}
    
    def calculate_metrics(alloc):
        portfolio_pnl = pd.Series(0.0, index=full_date_range)
        total_margin, total_pnl = 0, 0
        for s in strategies:
            mult = alloc.get(s['name'], 0)
            if mult <= 0: continue
            portfolio_pnl = portfolio_pnl.add(s['daily_pnl'] * mult, fill_value=0)
            total_margin += s['margin_per_mult'] * mult
            total_pnl += s['total_pnl_at_1x'] * mult
        if total_margin == 0: return 0, 0, 0
        portfolio_equity = account_size + portfolio_pnl.cumsum()
        if len(portfolio_equity) < 2: return 0, total_margin, total_pnl
        days = len(portfolio_pnl)
        total_ret = portfolio_pnl.sum() / account_size
        cagr = (1 + total_ret) ** (365 / days) - 1 if days > 0 and total_ret > -1 else 0
        peak = portfolio_equity.cummax()
        max_dd_usd = abs((portfolio_equity - peak).min())
        dd_vs_account = max_dd_usd / account_size if account_size > 0 else 1
        mart = cagr / dd_vs_account if dd_vs_account > 0 else 0
        return mart, total_margin, total_pnl
    
    best_mart = 0
    for iteration in range(max_iterations):
        best_improvement = 0
        best_change = None
        for s in strategies:
            current_mult = allocation[s['name']]
            if s['allowed_values']:
                idx = s['allowed_values'].index(current_mult) if current_mult in s['allowed_values'] else 0
                if idx < len(s['allowed_values']) - 1: new_mult = s['allowed_values'][idx + 1]
                else: continue
            else:
                new_mult = round(current_mult + s['step'], 1)
                if new_mult > s['max_mult']: continue
            test_alloc = allocation.copy()
            test_alloc[s['name']] = new_mult
            mart, margin, pnl = calculate_metrics(test_alloc)
            if margin > target_margin * 1.05: continue
            improvement = mart - best_mart
            if improvement > best_improvement:
                best_improvement = improvement
                best_change = (s['name'], new_mult, mart)
        if best_change and best_improvement > 0.001:
            allocation[best_change[0]] = best_change[1]
            best_mart = best_change[2]
        else: break
    return allocation
