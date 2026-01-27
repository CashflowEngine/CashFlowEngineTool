"""
Pre-Computation Engine for CashFlow Engine
Berechnet wichtige Metriken im Hintergrund nach Daten-Upload.
"""

import streamlit as st
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional
import calculations as calc


def precompute_on_upload(df: pd.DataFrame, account_size: float = 100000) -> Dict[str, Any]:
    """
    Führt alle wichtigen Berechnungen nach Daten-Upload durch.
    Speichert Ergebnisse in st.session_state für schnellen Zugriff.

    Args:
        df: Der DataFrame mit allen Trades
        account_size: Kontogröße für Berechnungen

    Returns:
        Dict mit allen berechneten Metriken
    """
    if df is None or df.empty:
        return {'status': 'no_data'}

    results = {
        'status': 'computing',
        'computed_at': pd.Timestamp.now().isoformat()
    }

    # --- 1. BASIC STATS ---
    results['basic_stats'] = _compute_basic_stats(df, account_size)

    # --- 2. STRATEGY PERFORMANCE ---
    results['strategy_stats'] = _compute_strategy_stats(df, account_size)

    # --- 3. DAILY P&L SERIES ---
    results['daily_pnl'] = _compute_daily_pnl(df)

    # --- 4. CORRELATION MATRIX ---
    results['correlation_matrix'] = _compute_correlation_matrix(df)

    # --- 5. SPX BENCHMARK (async if needed) ---
    results['benchmark'] = _fetch_benchmark(df)

    results['status'] = 'ready'

    # Store in session state
    st.session_state['precomputed_metrics'] = results
    st.session_state['strategy_base_stats'] = results['strategy_stats']
    st.session_state['daily_pnl_series'] = results['daily_pnl']
    st.session_state['correlation_matrix'] = results['correlation_matrix'].get('matrix')
    st.session_state['spx_benchmark'] = results['benchmark']

    return results


def _compute_basic_stats(df: pd.DataFrame, account_size: float) -> Dict:
    """Berechnet Basis-Statistiken."""
    strategies = df['strategy'].unique() if 'strategy' in df.columns else []
    total_pnl = df['pnl'].sum() if 'pnl' in df.columns else 0
    total_trades = len(df)

    # Zeitraum
    if 'timestamp' in df.columns:
        start_date = df['timestamp'].min()
        end_date = df['timestamp'].max()
        days = (end_date - start_date).days
        years = max(days / 365.25, 0.1)
    else:
        days = 365
        years = 1

    # CAGR
    end_capital = account_size + total_pnl
    cagr = (end_capital / account_size) ** (1 / years) - 1 if total_pnl > -account_size else -1

    # Daily returns for Sharpe
    daily_pnl = df.groupby(df['timestamp'].dt.date)['pnl'].sum() if 'timestamp' in df.columns else pd.Series([0])
    daily_returns = daily_pnl / account_size

    sharpe = 0
    if len(daily_returns) > 1 and daily_returns.std() > 0:
        sharpe = (daily_returns.mean() * 252) / (daily_returns.std() * np.sqrt(252))

    # Drawdown
    cumulative = daily_pnl.cumsum() + account_size
    running_max = cumulative.cummax()
    drawdown = (running_max - cumulative) / running_max
    max_dd = drawdown.max() if len(drawdown) > 0 else 0

    # MAR
    mar = cagr / max_dd if max_dd > 0 else 0

    return {
        'strategies_count': len(strategies),
        'strategies_list': list(strategies),
        'total_trades': total_trades,
        'total_pnl': total_pnl,
        'days': days,
        'years': years,
        'cagr': cagr,
        'sharpe': sharpe,
        'max_drawdown': max_dd,
        'mar': mar,
        'account_size': account_size,
        'best_day': daily_pnl.max() if len(daily_pnl) > 0 else 0,
        'worst_day': daily_pnl.min() if len(daily_pnl) > 0 else 0,
        'avg_daily_pnl': daily_pnl.mean() if len(daily_pnl) > 0 else 0,
    }


def _compute_strategy_stats(df: pd.DataFrame, account_size: float) -> Dict[str, Dict]:
    """Berechnet Performance pro Strategie."""
    if 'strategy' not in df.columns:
        return {}

    results = {}

    for strategy in df['strategy'].unique():
        strat_df = df[df['strategy'] == strategy].copy()
        pnl = strat_df['pnl']

        if len(pnl) == 0:
            continue

        # Basic stats
        total_pnl = pnl.sum()
        trades = len(pnl)

        # Win/Loss
        wins = pnl[pnl > 0]
        losses = pnl[pnl <= 0]

        win_rate = len(wins) / trades if trades > 0 else 0
        avg_win = wins.mean() if len(wins) > 0 else 0
        avg_loss = abs(losses.mean()) if len(losses) > 0 else 0
        profit_factor = wins.sum() / abs(losses.sum()) if losses.sum() != 0 else float('inf')

        # Max Drawdown
        cumulative = pnl.cumsum()
        running_max = cumulative.cummax()
        drawdown = running_max - cumulative
        max_dd_abs = drawdown.max()
        max_dd_pct = max_dd_abs / (running_max.max() + account_size) if running_max.max() > 0 else 0

        # CAGR
        if 'timestamp' in strat_df.columns:
            days = (strat_df['timestamp'].max() - strat_df['timestamp'].min()).days
            years = max(days / 365.25, 0.1)
        else:
            years = 1

        cagr = ((account_size + total_pnl) / account_size) ** (1 / years) - 1 if total_pnl > -account_size else -1

        # MAR
        mar = cagr / max_dd_pct if max_dd_pct > 0 else 0

        # Margin
        avg_margin = strat_df['margin'].mean() if 'margin' in strat_df.columns else 0

        # Kelly Criterion
        kelly = 0
        if avg_loss > 0 and avg_win > 0:
            b = avg_win / avg_loss
            kelly = (win_rate * b - (1 - win_rate)) / b
            kelly = max(0, min(kelly, 1))

        # Category (DNA)
        try:
            dna = calc.get_cached_dna(strategy, strat_df)
            category = calc.categorize_strategy(strategy)
        except Exception:
            dna = {}
            category = 'Unknown'

        results[strategy] = {
            'total_pnl': total_pnl,
            'trades': trades,
            'win_rate': win_rate,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': profit_factor,
            'max_drawdown': max_dd_pct,
            'max_drawdown_abs': max_dd_abs,
            'cagr': cagr,
            'mar': mar,
            'avg_margin': avg_margin,
            'kelly': kelly,
            'category': category,
            'dna': dna,
        }

    return results


def _compute_daily_pnl(df: pd.DataFrame) -> Dict[str, pd.Series]:
    """Berechnet tägliche P&L pro Strategie."""
    if 'timestamp' not in df.columns or 'strategy' not in df.columns:
        return {}

    results = {}

    # Gesamt
    daily_total = df.groupby(df['timestamp'].dt.date)['pnl'].sum()
    results['_TOTAL'] = daily_total

    # Pro Strategie
    for strategy in df['strategy'].unique():
        strat_df = df[df['strategy'] == strategy]
        daily = strat_df.groupby(strat_df['timestamp'].dt.date)['pnl'].sum()
        results[strategy] = daily

    return results


def _compute_correlation_matrix(df: pd.DataFrame) -> Dict:
    """Berechnet Korrelationsmatrix zwischen Strategien."""
    if 'timestamp' not in df.columns or 'strategy' not in df.columns:
        return {'matrix': None, 'high_correlations': []}

    # Pivot: Tägliche Returns pro Strategie
    try:
        pivot = df.pivot_table(
            index=df['timestamp'].dt.date,
            columns='strategy',
            values='pnl',
            aggfunc='sum'
        ).fillna(0)

        if len(pivot.columns) < 2:
            return {'matrix': None, 'high_correlations': []}

        corr_matrix = pivot.corr()

        # Finde hohe Korrelationen
        high_correlations = []
        for i, col1 in enumerate(corr_matrix.columns):
            for j, col2 in enumerate(corr_matrix.columns):
                if i < j:
                    val = corr_matrix.loc[col1, col2]
                    if abs(val) > 0.7:
                        risk = 'KRITISCH' if abs(val) > 0.85 else 'WARNUNG'
                        high_correlations.append({
                            'strategy1': col1,
                            'strategy2': col2,
                            'correlation': val,
                            'risk_level': risk
                        })

        return {
            'matrix': corr_matrix,
            'high_correlations': sorted(high_correlations, key=lambda x: abs(x['correlation']), reverse=True)
        }

    except Exception as e:
        return {'matrix': None, 'high_correlations': [], 'error': str(e)}


def _fetch_benchmark(df: pd.DataFrame) -> Optional[pd.Series]:
    """Holt SPX Benchmark Daten."""
    if 'timestamp' not in df.columns:
        return None

    try:
        start_date = df['timestamp'].min().strftime('%Y-%m-%d')
        end_date = df['timestamp'].max().strftime('%Y-%m-%d')

        # Nutze die existierende Cache-Funktion
        benchmark = calc.fetch_spx_benchmark(start_date, end_date)
        return benchmark

    except Exception:
        return None


def get_cached_or_compute(key: str, compute_fn, *args, **kwargs):
    """
    Holt Daten aus Cache oder berechnet sie.

    Args:
        key: Session state key
        compute_fn: Funktion zum Berechnen
        *args, **kwargs: Argumente für die Funktion

    Returns:
        Gecachte oder neu berechnete Daten
    """
    if key not in st.session_state or st.session_state[key] is None:
        st.session_state[key] = compute_fn(*args, **kwargs)
    return st.session_state[key]


def invalidate_cache():
    """Invalidiert den Cache wenn sich Daten ändern."""
    keys_to_clear = [
        'precomputed_metrics',
        'strategy_base_stats',
        'daily_pnl_series',
        'correlation_matrix',
        'spx_benchmark',
        'mc_results',
        'portfolio_allocation',
        'dna_cache',
    ]

    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]


def is_precomputed() -> bool:
    """Prüft ob Vorberechnungen durchgeführt wurden."""
    return (
        'precomputed_metrics' in st.session_state and
        st.session_state['precomputed_metrics'].get('status') == 'ready'
    )


def get_precomputed_context_for_ai() -> str:
    """
    Gibt alle vorberechneten Daten als formatierten String für die AI zurück.
    """
    if not is_precomputed():
        return "Keine vorberechneten Daten verfügbar."

    m = st.session_state['precomputed_metrics']
    basic = m.get('basic_stats', {})
    strategies = m.get('strategy_stats', {})
    corr = m.get('correlation_matrix', {})

    context = f"""
## VORBERECHNETE PORTFOLIO-DATEN

### Übersicht
- Strategien: {basic.get('strategies_count', 0)}
- Trades: {basic.get('total_trades', 0):,}
- Zeitraum: {basic.get('days', 0)} Tage ({basic.get('years', 0):.1f} Jahre)
- Kontogröße: ${basic.get('account_size', 100000):,.0f}

### Performance
- Total P&L: ${basic.get('total_pnl', 0):,.0f}
- CAGR: {basic.get('cagr', 0)*100:.1f}%
- Sharpe Ratio: {basic.get('sharpe', 0):.2f}
- Max Drawdown: {basic.get('max_drawdown', 0)*100:.1f}%
- MAR Ratio: {basic.get('mar', 0):.2f}

### Tägliche Statistiken
- Bester Tag: ${basic.get('best_day', 0):,.0f}
- Schlechtester Tag: ${basic.get('worst_day', 0):,.0f}
- Durchschnitt: ${basic.get('avg_daily_pnl', 0):,.0f}

### Strategie-Performance
"""

    for name, stats in strategies.items():
        context += f"""
**{name}** ({stats.get('category', 'Unknown')})
- P&L: ${stats.get('total_pnl', 0):,.0f} | Trades: {stats.get('trades', 0)}
- Win Rate: {stats.get('win_rate', 0)*100:.0f}% | PF: {stats.get('profit_factor', 0):.2f}
- MAR: {stats.get('mar', 0):.2f} | Max DD: {stats.get('max_drawdown', 0)*100:.1f}%
"""

    # Korrelations-Warnungen
    high_corr = corr.get('high_correlations', [])
    if high_corr:
        context += "\n### Korrelations-Warnungen\n"
        for c in high_corr[:5]:  # Top 5
            context += f"- {c['strategy1']} ↔ {c['strategy2']}: {c['correlation']:.2f} ({c['risk_level']})\n"

    return context
