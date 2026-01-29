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

def kelly_optimize_allocation(strategy_base_stats, target_margin, kelly_fraction,
                              workhorse_pct, airbag_pct, opportunist_pct,
                              category_overrides):
    """
    Optimize portfolio allocation using Kelly Criterion.

    This function calculates the optimal multiplier for each strategy based on:
    1. Individual strategy Kelly values
    2. Target margin budget
    3. Category allocation targets (workhorse/airbag/opportunist)

    Args:
        strategy_base_stats: Dict of strategy statistics
        target_margin: Total margin budget
        kelly_fraction: Fraction of Kelly to use (0-1, e.g., 0.2 for 20% Kelly)
        workhorse_pct: Target allocation for workhorse strategies
        airbag_pct: Target allocation for airbag strategies
        opportunist_pct: Target allocation for opportunist strategies
        category_overrides: Dict mapping strategy names to category overrides

    Returns:
        Dict mapping strategy names to optimal multipliers
    """
    result = {}

    # Group strategies by category
    categories = {'Workhorse': [], 'Airbag': [], 'Opportunist': []}

    for strat, stats in strategy_base_stats.items():
        cat = category_overrides.get(strat, stats.get('category', 'Workhorse'))
        if cat not in categories:
            cat = 'Workhorse'
        categories[cat].append((strat, stats))

    # Calculate Kelly-weighted allocations within each category
    for cat, cat_strategies in categories.items():
        if not cat_strategies:
            continue

        # Get category budget
        if cat == 'Workhorse':
            cat_budget = target_margin * workhorse_pct
        elif cat == 'Airbag':
            cat_budget = target_margin * airbag_pct
        else:
            cat_budget = target_margin * opportunist_pct

        # Calculate total weighted Kelly for category
        total_kelly_weight = 0
        for strat, stats in cat_strategies:
            kelly = stats.get('kelly', 0)
            kelly = max(0, min(kelly * kelly_fraction, 1))  # Apply fraction and cap at 1
            total_kelly_weight += kelly * stats.get('margin_per_contract', 0)

        # Allocate based on Kelly weights
        for strat, stats in cat_strategies:
            kelly = stats.get('kelly', 0)
            kelly = max(0, min(kelly * kelly_fraction, 1))
            margin_per = stats.get('margin_per_contract', 0)

            if total_kelly_weight > 0 and margin_per > 0:
                # Weight by Kelly value
                strat_budget = cat_budget * (kelly * margin_per / total_kelly_weight)
                multiplier = strat_budget / margin_per
                # Cap at reasonable values
                multiplier = max(0, min(multiplier, 10))
                # Round to 0.5 increments
                multiplier = round(multiplier * 2) / 2
            else:
                multiplier = 0

            result[strat] = multiplier

    return result


def mart_optimize_allocation(strategy_base_stats, target_margin, account_size,
                             category_overrides, full_date_range, filtered_df,
                             min_pnl=0, max_iterations=50):
    """
    Optimize portfolio allocation to maximize MART ratio.

    MART = CAGR / (Max Drawdown $ / Account Size)

    This function uses an iterative approach to find the allocation that
    maximizes the portfolio's MART ratio while respecting margin constraints.

    Args:
        strategy_base_stats: Dict of strategy statistics
        target_margin: Total margin budget
        account_size: Account size for calculations
        category_overrides: Dict mapping strategy names to category overrides
        full_date_range: Pandas date range for the evaluation period
        filtered_df: Filtered DataFrame with trade data
        min_pnl: Minimum required P/L
        max_iterations: Maximum iterations for optimization

    Returns:
        Dict mapping strategy names to optimal multipliers
    """
    # Start with equal allocation
    strategies = list(strategy_base_stats.keys())
    n_strats = len(strategies)

    if n_strats == 0:
        return {}

    # Initialize multipliers
    best_allocation = {s: 1.0 for s in strategies}
    best_mart = -999

    # Calculate initial allocation based on margin constraint
    total_margin_at_1x = sum(stats.get('margin_per_contract', 0) for stats in strategy_base_stats.values())

    if total_margin_at_1x > 0:
        base_multiplier = target_margin / total_margin_at_1x
        base_multiplier = max(0.1, min(base_multiplier, 5))  # Cap between 0.1 and 5
    else:
        base_multiplier = 1.0

    # Initialize with base multiplier
    current_allocation = {s: base_multiplier for s in strategies}

    # Simple iterative optimization
    for iteration in range(max_iterations):
        # Calculate portfolio metrics for current allocation
        port_pnl = pd.Series(0.0, index=full_date_range)

        for strat, mult in current_allocation.items():
            if strat in strategy_base_stats and mult > 0:
                stats = strategy_base_stats[strat]
                daily_pnl = stats.get('daily_pnl_series')
                if daily_pnl is not None:
                    port_pnl = port_pnl.add(daily_pnl * mult, fill_value=0)

        # Calculate MART
        total_pnl = port_pnl.sum()
        port_equity = account_size + port_pnl.cumsum()
        peak = port_equity.cummax()
        max_dd_usd = abs((port_equity - peak).min())

        if max_dd_usd > 0:
            days = len(port_pnl)
            if days > 0 and total_pnl > -account_size:
                cagr = (1 + total_pnl / account_size) ** (365 / days) - 1
                mart = cagr / (max_dd_usd / account_size) if max_dd_usd > 0 else 0
            else:
                mart = -999
        else:
            mart = 0

        # Check minimum P/L constraint
        if total_pnl < min_pnl:
            mart = -999

        # Update best if improved
        if mart > best_mart:
            best_mart = mart
            best_allocation = current_allocation.copy()

        # Generate next allocation by random perturbation
        if iteration < max_iterations - 1:
            new_allocation = {}
            for strat in strategies:
                # Random adjustment between -20% and +20%
                adjustment = 1.0 + (np.random.random() - 0.5) * 0.4
                new_mult = current_allocation[strat] * adjustment
                new_mult = max(0, min(new_mult, 10))  # Cap between 0 and 10
                new_mult = round(new_mult * 2) / 2  # Round to 0.5 increments
                new_allocation[strat] = new_mult

            # Check margin constraint
            total_new_margin = sum(
                strategy_base_stats[s].get('margin_per_contract', 0) * new_allocation[s]
                for s in strategies if s in strategy_base_stats
            )

            # Scale if over target margin
            if total_new_margin > target_margin * 1.1:  # Allow 10% overage
                scale = target_margin / total_new_margin
                new_allocation = {s: m * scale for s, m in new_allocation.items()}
                # Re-round after scaling
                new_allocation = {s: round(m * 2) / 2 for s, m in new_allocation.items()}

            current_allocation = new_allocation

    return best_allocation
