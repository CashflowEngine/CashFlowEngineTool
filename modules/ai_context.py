"""
AI Context Builder for CashFlow Engine
Sammelt alle gecachten Daten und bereitet sie für die KI auf.
"""

import streamlit as st
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional

# ============================================================================
# KNOWLEDGE BASE - Unsere Definitionen und Berechnungsmethoden
# ============================================================================

CASHFLOW_ENGINE_KNOWLEDGE = """
## CASHFLOW ENGINE - BERECHNUNGSMETHODEN

Du bist der AI Portfolio Analyst für CashFlow Engine, eine Plattform für Options-Trader.
Du analysierst Backtests und hilfst Tradern, ihr Portfolio zu optimieren.

### METRIKEN-DEFINITIONEN

**MAR Ratio (Managed Account Ratio)**
- Formel: CAGR / Maximum Drawdown
- Zielwerte: > 2.0 (exzellent), 1.5-2.0 (gut), 1.0-1.5 (akzeptabel), < 1.0 (kritisch)
- Interpretation: Wie viel Return bekomme ich pro Einheit Risiko?

**CAGR (Compound Annual Growth Rate)**
- Formel: ((Endwert / Startwert) ^ (365 / Tage)) - 1
- Annualisierte Rendite, macht Zeiträume vergleichbar

**Maximum Drawdown**
- Formel: (Peak - Trough) / Peak
- Der größte prozentuale Rückgang vom Höchststand
- Kritisch wenn > 30%

**Sharpe Ratio**
- Formel: (Portfolio Return - Risk Free Rate) / Standardabweichung
- Risk Free Rate: 4% (US Treasury)
- Zielwert: > 1.5 (gut), > 2.0 (sehr gut)

**Sortino Ratio**
- Wie Sharpe, aber nur Downside-Volatilität berücksichtigt
- Besser für asymmetrische Returns (Options!)

**Profit Factor**
- Formel: Summe Gewinne / |Summe Verluste|
- Zielwert: > 1.5

**Win Rate**
- Formel: Gewinn-Trades / Gesamt-Trades
- Bei Options oft 70-85% (aber kleine Gewinne, große Verluste möglich!)

**Kelly Criterion**
- Optimale Positionsgröße: (Win% * AvgWin - Loss% * AvgLoss) / AvgWin
- Nutze 25-50% des Kelly für konservativeres Sizing

### STRATEGIE-KATEGORIEN

**WORKHORSE (60% Allocation)**
- Stabile, konsistente Performer
- MAR > 1.5, Win Rate > 70%
- Beispiele: Iron Condors, Credit Spreads auf Indizes

**AIRBAG (25% Allocation)**
- Hedging-Strategien, profitieren von Crashes
- Negative Korrelation zum Markt gewünscht
- Beispiele: Long Puts, Bear Call Spreads

**OPPORTUNIST (15% Allocation)**
- High-Risk/High-Reward
- Höhere Volatilität akzeptabel
- Beispiele: Earnings Plays, Momentum Strategies

### RISIKO-WARNUNGEN

**Korrelation zwischen Strategien**
- > 0.7: WARNUNG - Klumpenrisiko
- > 0.85: KRITISCH - Strategien bewegen sich fast identisch
- Empfehlung: Diversifiziere oder reduziere Allocation

**Margin-Nutzung**
- > 80%: WARNUNG - Wenig Puffer für Margin Calls
- > 95%: KRITISCH - Margin Call wahrscheinlich bei Marktbewegung

**Konzentration**
- Eine Strategie > 40% des Portfolios: WARNUNG
- Empfehlung: Max 25-30% pro Strategie

### MONTE CARLO INTERPRETATION

**Percentile-Bedeutung**
- P5 (5. Perzentil): Worst Case (nur 5% sind schlechter)
- P50 (Median): Erwartetes Ergebnis
- P95: Best Case (nur 5% sind besser)

**Profit-Wahrscheinlichkeit**
- > 90%: Sehr robust
- 70-90%: Akzeptabel
- < 70%: Risikobehaftet

### ANTWORTSTIL

- Antworte in der Sprache des Users (Deutsch oder Englisch)
- Sei konkret mit Zahlen und Referenzen
- Gib actionable Empfehlungen
- Warne proaktiv bei Risiken
- Verweise auf spezifische Strategien wenn relevant
"""


class AIContextBuilder:
    """Baut den kompletten Kontext für AI-Anfragen aus allen gecachten Daten."""

    @staticmethod
    def get_data_availability() -> Dict[str, bool]:
        """Prüft welche Daten verfügbar sind."""
        return {
            'full_df': 'full_df' in st.session_state and st.session_state.get('full_df') is not None and not st.session_state['full_df'].empty,
            'live_df': 'live_df' in st.session_state and st.session_state.get('live_df') is not None and not st.session_state['live_df'].empty,
            'strategy_base_stats': 'strategy_base_stats' in st.session_state,
            'daily_pnl_series': 'daily_pnl_series' in st.session_state,
            'correlation_matrix': 'correlation_matrix' in st.session_state,
            'spx_benchmark': 'spx_benchmark' in st.session_state,
            'mc_results': 'mc_results' in st.session_state and st.session_state.get('mc_results') is not None,
            'portfolio_allocation': 'portfolio_allocation' in st.session_state,
            'dna_cache': 'dna_cache' in st.session_state and len(st.session_state.get('dna_cache', {})) > 0,
        }

    @staticmethod
    def get_availability_summary() -> str:
        """Gibt eine lesbare Zusammenfassung der verfügbaren Daten."""
        avail = AIContextBuilder.get_data_availability()

        lines = ["## DATENVERFÜGBARKEIT\n"]

        status_map = {
            'full_df': ('Backtest-Daten', 'Basis für alle Analysen'),
            'live_df': ('Live-Trading-Daten', 'Für Backtest vs Live Vergleich'),
            'strategy_base_stats': ('Strategie-Statistiken', 'Performance pro Strategie'),
            'daily_pnl_series': ('Tägliche P&L', 'Für Drawdown und Volatilität'),
            'correlation_matrix': ('Korrelationsmatrix', 'Risiko-Cluster erkennen'),
            'spx_benchmark': ('SPX Benchmark', 'Alpha/Beta Berechnung'),
            'mc_results': ('Monte Carlo Ergebnisse', 'Zukunftsszenarien'),
            'portfolio_allocation': ('Portfolio-Allocation', 'Aktuelle Gewichtung'),
        }

        for key, (name, desc) in status_map.items():
            status = "✅" if avail.get(key) else "❌"
            lines.append(f"{status} **{name}**: {desc}")

        return "\n".join(lines)

    @staticmethod
    def build_portfolio_overview(df: pd.DataFrame) -> str:
        """Baut Überblick aus den Rohdaten."""
        if df is None or df.empty:
            return "Keine Daten verfügbar."

        strategies = df['strategy'].unique() if 'strategy' in df.columns else []
        total_pnl = df['pnl'].sum() if 'pnl' in df.columns else 0
        total_trades = len(df)

        # Zeitraum
        if 'timestamp' in df.columns:
            start_date = df['timestamp'].min().strftime('%Y-%m-%d')
            end_date = df['timestamp'].max().strftime('%Y-%m-%d')
            days = (df['timestamp'].max() - df['timestamp'].min()).days
        else:
            start_date = end_date = "N/A"
            days = 0

        return f"""
## PORTFOLIO ÜBERSICHT

- **Strategien**: {len(strategies)} ({', '.join(strategies[:5])}{'...' if len(strategies) > 5 else ''})
- **Trades gesamt**: {total_trades:,}
- **Zeitraum**: {start_date} bis {end_date} ({days} Tage)
- **Total P&L**: ${total_pnl:,.0f}
"""

    @staticmethod
    def build_strategy_performance(df: pd.DataFrame) -> str:
        """Baut Performance-Tabelle pro Strategie."""
        if df is None or df.empty or 'strategy' not in df.columns:
            return ""

        lines = ["\n## STRATEGIE PERFORMANCE\n"]

        for strategy in sorted(df['strategy'].unique()):
            strat_df = df[df['strategy'] == strategy]
            pnl = strat_df['pnl']

            total_pnl = pnl.sum()
            trades = len(pnl)
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
            max_dd_pct = max_dd_abs / (running_max.max() + 100000) if running_max.max() > 0 else 0

            # MAR (vereinfacht)
            days = (strat_df['timestamp'].max() - strat_df['timestamp'].min()).days if 'timestamp' in strat_df.columns else 365
            years = max(days / 365.25, 0.1)
            cagr = ((100000 + total_pnl) / 100000) ** (1/years) - 1 if total_pnl > -100000 else -1
            mar = cagr / max_dd_pct if max_dd_pct > 0 else 0

            # Margin
            avg_margin = strat_df['margin'].mean() if 'margin' in strat_df.columns else 0

            lines.append(f"""
### {strategy}
- **P&L**: ${total_pnl:,.0f} | **Trades**: {trades}
- **Win Rate**: {win_rate*100:.0f}% | **Profit Factor**: {profit_factor:.2f}
- **Avg Win**: ${avg_win:,.0f} | **Avg Loss**: ${avg_loss:,.0f}
- **Max Drawdown**: {max_dd_pct*100:.1f}% | **MAR**: {mar:.2f}
- **Avg Margin**: ${avg_margin:,.0f}
""")

        return "\n".join(lines)

    @staticmethod
    def build_correlation_context() -> str:
        """Baut Korrelations-Kontext aus gecachten Daten."""
        if 'correlation_matrix' not in st.session_state:
            return ""

        corr = st.session_state['correlation_matrix']

        if isinstance(corr, pd.DataFrame):
            # Finde hohe Korrelationen
            high_corr = []
            for i, col1 in enumerate(corr.columns):
                for j, col2 in enumerate(corr.columns):
                    if i < j:
                        val = corr.loc[col1, col2]
                        if abs(val) > 0.7:
                            risk = "KRITISCH" if abs(val) > 0.85 else "WARNUNG"
                            high_corr.append(f"- {col1} ↔ {col2}: {val:.2f} ({risk})")

            if high_corr:
                return f"""
## KORRELATIONS-ANALYSE

**Hohe Korrelationen gefunden:**
{chr(10).join(high_corr)}

⚠️ Hohe Korrelation bedeutet Klumpenrisiko - bei Marktbewegung verlieren mehrere Strategien gleichzeitig!
"""
        return ""

    @staticmethod
    def build_monte_carlo_context() -> str:
        """Baut Monte Carlo Kontext aus gecachten Ergebnissen."""
        mc = st.session_state.get('mc_results')
        if not mc:
            return "\n## MONTE CARLO\n❌ Noch nicht ausgeführt. Gehe zu 'Monte Carlo Punisher' für Simulation."

        return f"""
## MONTE CARLO SIMULATION

**Konfiguration**: {mc.get('n_sims', 'N/A')} Simulationen, {mc.get('sim_months', 'N/A')} Monate

**Return-Szenarien**:
- Worst Case (P5): ${mc.get('p05', 0):,.0f}
- Expected (P50): ${mc.get('p50', 0):,.0f}
- Best Case (P95): ${mc.get('p95', 0):,.0f}

**Drawdown-Szenarien**:
- Best Case DD: {mc.get('d05', 0)*100:.1f}%
- Typical DD: {mc.get('d50', 0)*100:.1f}%
- Worst Case DD: {mc.get('d95', 0)*100:.1f}%

**Key Metrics**:
- CAGR (erwartet): {mc.get('cagr', 0)*100:.1f}%
- MAR Ratio: {mc.get('mar', 0):.2f}
- Profit-Wahrscheinlichkeit: {mc.get('prob_profit', 0)*100:.0f}%
"""

    @staticmethod
    def build_full_context(current_page: Optional[str] = None) -> str:
        """
        Baut den kompletten Kontext für eine AI-Anfrage.
        Nutzt vorberechnete Daten wenn verfügbar.

        Args:
            current_page: Die aktuelle Seite (für kontextspezifische Hilfe)

        Returns:
            Vollständiger Kontext-String für den AI-Prompt
        """
        # Check if precomputed data is available
        from modules.precompute import is_precomputed, get_precomputed_context_for_ai

        if is_precomputed():
            # Use precomputed data for faster context building
            context_parts = [
                get_precomputed_context_for_ai(),
                AIContextBuilder.build_monte_carlo_context(),
            ]
        else:
            # Fallback: compute on the fly
            df = st.session_state.get('full_df', pd.DataFrame())
            context_parts = [
                AIContextBuilder.get_availability_summary(),
                AIContextBuilder.build_portfolio_overview(df),
                AIContextBuilder.build_strategy_performance(df),
                AIContextBuilder.build_correlation_context(),
                AIContextBuilder.build_monte_carlo_context(),
            ]

        # Seiten-spezifischer Kontext
        if current_page:
            context_parts.append(f"\n## AKTUELLER KONTEXT\nUser ist auf der Seite: **{current_page}**")

        return "\n".join(context_parts)

    @staticmethod
    def get_quick_stats() -> Dict[str, Any]:
        """Schnelle Stats für Sidebar-Anzeige."""
        df = st.session_state.get('full_df', pd.DataFrame())

        if df is None or df.empty:
            return {'status': 'no_data'}

        return {
            'status': 'ready',
            'strategies': len(df['strategy'].unique()) if 'strategy' in df.columns else 0,
            'trades': len(df),
            'total_pnl': df['pnl'].sum() if 'pnl' in df.columns else 0,
            'mc_available': st.session_state.get('mc_results') is not None,
        }
