"""
Precomputation Module for CashFlow Engine.

This module handles background pre-computation of expensive calculations
to make page transitions instant. Results are stored in session state
and invalidated when data changes.

Usage:
    - Call precompute_all() after data upload
    - Check get_cached() before computing in each page
    - Call invalidate_cache() when data changes
"""

import streamlit as st
import pandas as pd
import numpy as np
import calculations as calc
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Cache version - increment when computation logic changes
CACHE_VERSION = "2.0"  # Updated to include kelly, margin_series, dna fields


def get_cache_key(name: str) -> str:
    """Generate a cache key with version."""
    return f"_cache_{CACHE_VERSION}_{name}"


def is_cache_valid(df: pd.DataFrame) -> bool:
    """Check if cache is still valid for the current data."""
    cache_hash = st.session_state.get('_cache_data_hash')
    if cache_hash is None:
        return False

    # Simple hash based on shape and first/last timestamps
    current_hash = _compute_data_hash(df)
    return cache_hash == current_hash


def _compute_data_hash(df: pd.DataFrame) -> str:
    """Compute a simple hash of the dataframe for cache invalidation."""
    if df is None or df.empty:
        return "empty"

    try:
        shape_str = f"{df.shape[0]}_{df.shape[1]}"
        pnl_sum = df['pnl'].sum() if 'pnl' in df.columns else 0
        ts_min = df['timestamp'].min() if 'timestamp' in df.columns else 0
        ts_max = df['timestamp'].max() if 'timestamp' in df.columns else 0
        return f"{shape_str}_{pnl_sum:.2f}_{ts_min}_{ts_max}"
    except:
        return f"hash_{datetime.now().timestamp()}"


def invalidate_cache():
    """Clear all cached computations."""
    keys_to_remove = [k for k in st.session_state.keys() if k.startswith('_cache_')]
    for key in keys_to_remove:
        del st.session_state[key]
    logger.info("Cache invalidated")


def get_cached(name: str, default=None):
    """Get a cached value if it exists."""
    key = get_cache_key(name)
    return st.session_state.get(key, default)


def set_cached(name: str, value):
    """Store a value in cache."""
    key = get_cache_key(name)
    st.session_state[key] = value


def precompute_all(df: pd.DataFrame, live_df: pd.DataFrame = None, account_size: int = 100000):
    """
    Pre-compute all expensive calculations after data upload.

    This function should be called after CSV upload to pre-calculate:
    - Strategy base statistics
    - SPX benchmark data
    - Daily P&L series per strategy
    - Correlation matrix
    - Basic portfolio metrics

    Results are stored in session state for instant access.
    """
    if df is None or df.empty:
        return False

    try:
        # Store data hash for cache validation
        st.session_state['_cache_data_hash'] = _compute_data_hash(df)
        st.session_state['_cache_timestamp'] = datetime.now()

        # 1. Pre-compute Strategy Base Stats (used by Portfolio Builder, Analytics)
        _precompute_strategy_stats(df, account_size)

        # 2. Pre-compute SPX Benchmark (used by multiple pages)
        _precompute_spx_benchmark(df)

        # 3. Pre-compute Correlation Matrix (used by Analytics, Builder)
        _precompute_correlation(df)

        # 4. Pre-compute basic metrics (used by Analytics)
        _precompute_basic_metrics(df, account_size)

        logger.info(f"Precomputation complete for {len(df)} trades")
        st.session_state['_precompute_done'] = True
        return True

    except Exception as e:
        logger.error(f"Precomputation failed: {e}")
        return False


def _precompute_strategy_stats(df: pd.DataFrame, account_size: int):
    """Pre-compute per-strategy statistics."""
    strategies = sorted(df['strategy'].unique())
    logger.info(f"Pre-computing stats for {len(strategies)} strategies...")

    # Get full date range
    min_ts = df['timestamp'].min()
    max_ts = df['timestamp'].max()
    full_idx = pd.date_range(start=min_ts.normalize(), end=max_ts.normalize(), freq='D')

    strategy_base_stats = {}

    for i, strat in enumerate(strategies):
        try:
            s_df = df[df['strategy'] == strat].copy()
            if s_df.empty:
                continue

            # Daily P&L series
            daily_pnl = s_df.set_index('timestamp').resample('D')['pnl'].sum().reindex(full_idx, fill_value=0)

            # Calculate stats
            total_pnl = s_df['pnl'].sum()

            # Equity and drawdown
            equity = account_size + daily_pnl.cumsum()
            peak = equity.cummax()
            dd = equity - peak
            max_dd = dd.min()

            # Contracts per day
            contracts_per_day = s_df['contracts'].sum() / max(1, len(full_idx)) if 'contracts' in s_df.columns else 1.0

            # Margin series (daily margin usage) - with fallback
            try:
                margin_series_raw = calc.generate_daily_margin_series_optimized(s_df)
                if margin_series_raw is not None and len(margin_series_raw) > 0:
                    margin_series = margin_series_raw.reindex(full_idx, fill_value=0)
                    margin_per_contract = margin_series.max()
                else:
                    # Fallback: use simple margin calculation
                    margin_per_contract = s_df['margin'].max() if 'margin' in s_df.columns else 5000
                    margin_series = pd.Series(0.0, index=full_idx)
            except Exception as e:
                logger.warning(f"Margin series failed for {strat}: {e}")
                margin_per_contract = s_df['margin'].max() if 'margin' in s_df.columns else 5000
                margin_series = pd.Series(0.0, index=full_idx)

            # Category detection
            category = calc.categorize_strategy(strat)

            # Win rate and Kelly criterion
            wins = s_df[s_df['pnl'] > 0]['pnl']
            losses = s_df[s_df['pnl'] <= 0]['pnl']
            win_rate = len(wins) / len(s_df) if len(s_df) > 0 else 0
            avg_win = wins.mean() if len(wins) > 0 else 0
            avg_loss = abs(losses.mean()) if len(losses) > 0 else 0

            kelly = 0
            if avg_loss > 0 and avg_win > 0:
                b = avg_win / avg_loss
                kelly = (win_rate * b - (1 - win_rate)) / b
                kelly = max(0, min(kelly, 1))

            # DNA (Greek exposure)
            dna = calc.get_cached_dna(strat, s_df)

            strategy_base_stats[strat] = {
                'total_pnl': total_pnl,
                'max_dd': abs(max_dd) if max_dd < 0 else 0,
                'contracts_per_day': max(0.5, round(contracts_per_day * 2) / 2),
                'margin_per_contract': margin_per_contract if margin_per_contract > 0 else 5000,
                'daily_pnl_series': daily_pnl,
                'margin_series': margin_series,
                'category': category,
                'dna': dna,
                'trade_count': len(s_df),
                'win_rate': win_rate,
                'kelly': kelly
            }

        except Exception as e:
            logger.error(f"Failed to compute stats for strategy {strat}: {e}")
            continue

    set_cached('strategy_base_stats', strategy_base_stats)
    set_cached('full_date_index', full_idx)
    set_cached('strategies', strategies)

    logger.info(f"Pre-computed stats for {len(strategy_base_stats)} strategies")


def _precompute_spx_benchmark(df: pd.DataFrame):
    """Pre-fetch SPX benchmark data."""
    try:
        min_ts = df['timestamp'].min()
        max_ts = df['timestamp'].max()

        spx = calc.fetch_spx_benchmark(min_ts, max_ts)
        if spx is not None and len(spx) > 0:
            set_cached('spx_benchmark', spx)

            # Also calculate SPX returns
            spx_ret = spx.pct_change().fillna(0)
            set_cached('spx_returns', spx_ret)

            logger.info(f"Pre-fetched SPX benchmark: {len(spx)} days")
    except Exception as e:
        logger.warning(f"Could not pre-fetch SPX: {e}")


def _precompute_correlation(df: pd.DataFrame):
    """Pre-compute strategy correlation matrix."""
    strategies = sorted(df['strategy'].unique())

    if len(strategies) < 2:
        return

    min_ts = df['timestamp'].min()
    max_ts = df['timestamp'].max()
    full_idx = pd.date_range(start=min_ts.normalize(), end=max_ts.normalize(), freq='D')

    # Build P&L matrix
    pnl_matrix = pd.DataFrame(index=full_idx)
    for strat in strategies:
        s_df = df[df['strategy'] == strat]
        if not s_df.empty:
            pnl_matrix[strat] = s_df.set_index('timestamp').resample('D')['pnl'].sum().reindex(full_idx, fill_value=0)

    if len(pnl_matrix.columns) > 1:
        corr_matrix = pnl_matrix.corr()
        set_cached('correlation_matrix', corr_matrix)

        # Calculate average correlation (upper triangle, excluding diagonal)
        corr_values = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(bool)).stack()
        avg_corr = corr_values.mean() if not corr_values.empty else 0
        set_cached('avg_correlation', avg_corr)

        logger.info(f"Pre-computed correlation matrix: avg={avg_corr:.2f}")


def _precompute_basic_metrics(df: pd.DataFrame, account_size: int):
    """Pre-compute basic portfolio metrics."""
    min_ts = df['timestamp'].min()
    max_ts = df['timestamp'].max()
    full_idx = pd.date_range(start=min_ts.normalize(), end=max_ts.normalize(), freq='D')

    # Daily portfolio P&L
    daily_pnl = df.set_index('timestamp').resample('D')['pnl'].sum().reindex(full_idx, fill_value=0)

    # Portfolio equity
    port_equity = account_size + daily_pnl.cumsum()

    # Portfolio returns
    port_returns = port_equity.pct_change().fillna(0)

    # Basic metrics
    total_pnl = daily_pnl.sum()

    # Max drawdown
    peak = port_equity.cummax()
    dd = (port_equity - peak) / peak
    max_dd = dd.min()
    max_dd_usd = (port_equity - peak).min()

    # CAGR
    days = len(full_idx)
    total_return = total_pnl / account_size
    cagr = (1 + total_return) ** (365 / max(days, 1)) - 1 if total_return > -1 else 0

    # MAR
    mar = cagr / abs(max_dd) if max_dd != 0 else 0

    set_cached('daily_pnl', daily_pnl)
    set_cached('port_equity', port_equity)
    set_cached('port_returns', port_returns)
    set_cached('basic_metrics', {
        'total_pnl': total_pnl,
        'cagr': cagr,
        'max_dd': max_dd,
        'max_dd_usd': max_dd_usd,
        'mar': mar,
        'days': days,
        'trade_count': len(df)
    })

    logger.info(f"Pre-computed basic metrics: CAGR={cagr:.1%}, MAR={mar:.2f}")


def get_precompute_status() -> dict:
    """Get status of precomputation."""
    return {
        'done': st.session_state.get('_precompute_done', False),
        'timestamp': st.session_state.get('_cache_timestamp'),
        'strategies_count': len(get_cached('strategies', [])),
        'has_spx': get_cached('spx_benchmark') is not None,
        'has_correlation': get_cached('correlation_matrix') is not None
    }
