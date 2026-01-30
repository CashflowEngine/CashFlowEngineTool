"""
AI Context Builder for CashFlow Engine
Collects all cached data and prepares it for the AI.
"""

import streamlit as st
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional

# ============================================================================
# KNOWLEDGE BASE - Unsere Definitionen und Berechnungsmethoden
# ============================================================================

CASHFLOW_ENGINE_KNOWLEDGE = """
## CRITICAL INSTRUCTIONS

YOU MUST USE THE DEFINITIONS PROVIDED BELOW. Do NOT use your own general knowledge.
When asked about MAR Ratio, Sharpe, or any metric, use ONLY the definitions in this document.

---

## CORE METRICS - USE THESE DEFINITIONS

### MAR Ratio (Managed Account Ratio)
- **Definition**: MAR = CAGR / Maximum Drawdown %
- **Drawdown-Basis**: Relativ zum aktuellen Peak der Equity-Kurve
- **Example**: Account wächst auf $150k, fällt auf $120k → DD = 20% (von $150k Peak)
- **Targets**: > 2.0 (excellent), 1.5-2.0 (good), 1.0-1.5 (acceptable), < 1.0 (needs improvement)

### MART Ratio (MAR based on Initial Account)
- **Definition**: MART = CAGR / (Max Drawdown $ / Initial Account Size)
- **Drawdown-Basis**: Relativ zur INITIALEN Kontogröße (feste Basis)
- **Example**: Account startet bei $100k, Max DD = $30k → DD = 30% (von $100k Start)
- **Unterschied zu MAR**: MART ist konservativer, da es immer das Startkapital als Basis verwendet
- **Wann MART nutzen**: Für Portfolios die stark gewachsen sind, für faire Zeitraum-Vergleiche
- **In CashFlow Engine**: MART wird im Portfolio Builder für die Optimierung verwendet

### CAGR (Compound Annual Growth Rate)
- **Definition**: CAGR = ((End Value / Start Value) ^ (365 / Days)) - 1
- **Example**: $100,000 growing to $150,000 over 2 years = (1.50)^(1/2) - 1 = 22.5% CAGR
- **Interpretation**: Annualized return, makes different time periods comparable

### Maximum Drawdown
- **Definition**: Max DD = (Peak - Trough) / Peak
- **Example**: Account peaks at $120,000 then drops to $90,000 = (120k-90k)/120k = 25%
- **Warning levels**: < 20% (good), 20-30% (acceptable), > 30% (concerning)

### Profit Factor
- **Definition**: Profit Factor = Sum of All Wins / |Sum of All Losses|
- **Example**: $50,000 in wins, $30,000 in losses = 50k/30k = 1.67
- **Targets**: > 1.5 (sustainable), 1.0-1.5 (marginal), < 1.0 (losing money)

### Sharpe Ratio
- **Definition**: Sharpe = (Return - Risk Free Rate) / Standard Deviation
- **Risk Free Rate**: ~4-5% (current US Treasury)
- **Targets**: > 1.5 (good), > 2.0 (very good), > 3.0 (excellent)

### Sortino Ratio
- **Definition**: Like Sharpe, but only considers downside volatility
- **Why it's better for options**: Doesn't penalize upside volatility

### Kelly Criterion
- **Definition**: Kelly% = (Win% × Avg Win - Loss% × Avg Loss) / Avg Win
- **CRITICAL**: Always use 25-50% of full Kelly (Half-Kelly or Quarter-Kelly)
- **Example**: If Kelly says 20%, use only 5-10% position size

### Expected Value (EV)
- **Definition**: EV = (Win% × Avg Win) - (Loss% × Avg Loss)
- Must be positive for profitable strategy

---

## CASHFLOW ENGINE - AI PORTFOLIO ANALYST

You are the AI Portfolio Analyst for CashFlow Engine, a platform for options traders.
You analyze backtests and help traders optimize their portfolios.
You are an expert in options trading, Monte Carlo simulation, and portfolio optimization.

---

## STRATEGY CATEGORIES (User-Defined Portfolio Allocation)

IMPORTANT: The following are USER-DEFINED portfolio allocation categories in CashFlow Engine.
DO NOT use these terms to describe performance (like "top performers" or "best strategies").
These are role-based categories that users assign to their strategies, NOT performance labels.

### WORKHORSE (typically 60% Allocation)
- User-assigned category for daily, consistent income strategies
- Typically: Iron Condors, Credit Spreads on indices (SPX, RUT)
- These are the "bread and butter" trades the user runs regularly
- NOT a synonym for "best performing" - it means "core income strategy"

### AIRBAG (typically 25% Allocation)
- User-assigned category for hedging/protection strategies
- Typically: Long Puts, Bear Call Spreads, VIX calls
- Purpose: Protect portfolio during market crashes
- NOT a synonym for "safe" - it means "crash protection"

### OPPORTUNIST (typically 15% Allocation)
- User-assigned category for occasional high-conviction trades
- Typically: Earnings Plays, Momentum Strategies, Straddles
- These are trades taken when special opportunities arise
- NOT a synonym for "risky" - it means "opportunistic entry"

WHEN DESCRIBING STRATEGY PERFORMANCE, USE NEUTRAL TERMS:
- "Top performers by P&L" (not "Workhorses")
- "Best risk-adjusted strategies" (not "Workhorses")
- "Underperforming strategies" (not "Laggards" or similar)
- "Strategies needing attention"
Never invent category names - use the data-driven rankings only

---

## RISK WARNINGS

### Correlation Between Strategies
- > 0.7: WARNING - Cluster risk
- > 0.85: CRITICAL - Strategies move almost identically
- Recommendation: Diversify or reduce allocation
- Goal: Keep correlations < 0.5 for true diversification

### Margin Usage
- > 80%: WARNING - Little buffer for margin calls
- > 95%: CRITICAL - Margin call likely on market movement
- Recommendation: Keep margin usage < 50% for safety buffer

### Concentration
- One strategy > 40% of portfolio: WARNING
- Recommendation: Max 25-30% per strategy
- Exception: Index strategies can be slightly higher

### Tail Risk (Options Specific)
- Options selling has negative skew
- 1-2 standard deviation moves are fine
- 3+ sigma events can wipe out months of gains
- Always have defined risk or hedges in place

---

## MONTE CARLO SIMULATION

### What It Does
- Simulates thousands of possible future paths
- Uses historical returns and their distribution
- Accounts for randomness and sequence of returns
- Shows probability distributions, not predictions

### Percentile Meaning
- P5 (5th percentile): Worst Case (only 5% are worse)
- P25: Below average but realistic scenario
- P50 (Median): Expected outcome
- P75: Above average scenario
- P95: Best Case (only 5% are better)

### Profit Probability
- > 90%: Very robust strategy
- 70-90%: Acceptable
- < 70%: Risky - proceed with caution
- This shows % of simulations ending in profit

### Simulation Parameters
- Number of simulations: 1,000-10,000 typical
- Time horizon: 12-36 months typical
- Resampling method: Bootstrap from historical trades
- Assumes past distribution continues

### Interpreting Results
- Don't focus on single paths
- Look at the distribution (range of outcomes)
- P5 is more important than P50 for risk management
- Wide spread = high uncertainty = more caution needed

---

## OPTIONS TRADING TOOLS & PLATFORMS

### Optionomega
- Options backtesting platform
- Tests strategies against historical data
- Exports trade data compatible with CashFlow Engine
- Key features: Strategy builder, Greeks analysis

### Optionstrat
- Options visualization tool
- Shows P&L diagrams at various prices/dates
- Useful for planning complex spreads
- Real-time Greeks calculations

### OptionsApp
- Mobile-focused options tracking
- Position monitoring on the go
- Alerts for Greeks thresholds

### Trade Automation Toolbox (TAT)
- Automated options trading for TastyTrade
- Sets up recurring trades based on rules
- Manages positions automatically
- Export capabilities for analysis

### Tradestuart
- Options backtesting focused on income strategies
- Pre-built strategy templates
- Rolling and adjustment analysis

### Using These Tools with CashFlow Engine
- Export trade history from any platform
- Import CSV into CashFlow Engine
- Analyze combined portfolio performance
- Run Monte Carlo on aggregated data

---

## OPTIONS STRATEGY KNOWLEDGE

### Credit Spreads
- Sell premium, defined risk
- Bull Put Spread: Bullish, collect credit
- Bear Call Spread: Bearish, collect credit
- Max loss = width - credit received
- Best when IV is high

### Iron Condor
- Sell both sides (put spread + call spread)
- Neutral strategy, profits from time decay
- Works best in low volatility, range-bound markets
- Manage when tested (typically at 21 DTE or 50% profit)

### Strangles/Straddles
- Undefined risk strategies
- Higher premium collection
- Require active management
- Use on large accounts only

### Wheel Strategy
- Sell puts until assigned, then sell calls
- Systematic approach to stock accumulation
- Works best on stocks you want to own
- Combines premium collection with ownership

### Calendar/Diagonal Spreads
- Exploit time decay differential
- Long back month, short front month
- Requires volatility forecasting
- More complex management

---

## POSITION SIZING GUIDELINES

### Fixed Percentage
- Risk 1-2% of portfolio per trade
- Simplest approach
- Doesn't optimize for edge

### Kelly-Based Sizing
- Calculate Kelly percentage
- Use fractional Kelly (25-50%)
- Adjusts size based on strategy edge
- Requires accurate win rate/average win-loss data

### Volatility-Based
- Smaller positions when IV is high
- Larger when IV is low (cheaper)
- Adjusts for market conditions

### Optimal f
- Mathematical optimization of position size
- Maximizes geometric growth
- Similar to Kelly but more aggressive
- Use with extreme caution

---

## RESPONSE STYLE

- Respond in the user's language (German if German question, English if English question)
- Be specific with numbers and references
- Give actionable recommendations
- Proactively warn about risks
- Reference specific strategies when relevant
- Use the actual data from the portfolio context
- Don't make up numbers - use what's provided
- If data is missing, tell the user what analysis to run
"""


class AIContextBuilder:
    """Builds complete context for AI requests from all cached data."""

    @staticmethod
    def get_data_availability() -> Dict[str, bool]:
        """Check which data is available."""
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
        """Returns a readable summary of available data."""
        avail = AIContextBuilder.get_data_availability()

        lines = ["## DATA AVAILABILITY\n"]

        status_map = {
            'full_df': ('Backtest Data', 'Foundation for all analyses'),
            'live_df': ('Live Trading Data', 'For backtest vs live comparison'),
            'strategy_base_stats': ('Strategy Statistics', 'Performance per strategy'),
            'daily_pnl_series': ('Daily P&L', 'For drawdown and volatility'),
            'correlation_matrix': ('Correlation Matrix', 'Identify risk clusters'),
            'spx_benchmark': ('SPX Benchmark', 'Alpha/Beta calculation'),
            'mc_results': ('Monte Carlo Results', 'Future scenarios'),
            'portfolio_allocation': ('Portfolio Allocation', 'Current weights'),
        }

        for key, (name, desc) in status_map.items():
            status = "✅" if avail.get(key) else "❌"
            lines.append(f"{status} **{name}**: {desc}")

        return "\n".join(lines)

    @staticmethod
    def build_portfolio_overview(df: pd.DataFrame) -> str:
        """Build overview from raw data."""
        if df is None or df.empty:
            return "No data available."

        strategies = df['strategy'].unique() if 'strategy' in df.columns else []
        total_pnl = df['pnl'].sum() if 'pnl' in df.columns else 0
        total_trades = len(df)

        # Time period
        if 'timestamp' in df.columns:
            start_date = df['timestamp'].min().strftime('%Y-%m-%d')
            end_date = df['timestamp'].max().strftime('%Y-%m-%d')
            days = (df['timestamp'].max() - df['timestamp'].min()).days
        else:
            start_date = end_date = "N/A"
            days = 0

        # Portfolio-level metrics
        pnl = df['pnl'] if 'pnl' in df.columns else pd.Series([0])
        wins = pnl[pnl > 0]
        losses = pnl[pnl <= 0]
        portfolio_win_rate = len(wins) / len(pnl) if len(pnl) > 0 else 0
        portfolio_pf = wins.sum() / abs(losses.sum()) if losses.sum() != 0 else float('inf')

        # Drawdown
        cumulative = pnl.cumsum()
        running_max = cumulative.cummax()
        drawdown = running_max - cumulative
        max_dd = drawdown.max()
        max_dd_pct = max_dd / (running_max.max() + 100000) if running_max.max() > 0 else 0

        # CAGR and MAR
        years = max(days / 365.25, 0.1) if days > 0 else 1
        cagr = ((100000 + total_pnl) / 100000) ** (1/years) - 1 if total_pnl > -100000 else -1
        mar = cagr / max_dd_pct if max_dd_pct > 0 else 0

        return f"""
## PORTFOLIO OVERVIEW

- **Strategies**: {len(strategies)} ({', '.join(strategies[:5])}{'...' if len(strategies) > 5 else ''})
- **Total Trades**: {total_trades:,}
- **Period**: {start_date} to {end_date} ({days} days, {years:.1f} years)
- **Total P&L**: ${total_pnl:,.0f}

### Portfolio-Level Metrics
- **Win Rate**: {portfolio_win_rate*100:.1f}%
- **Profit Factor**: {portfolio_pf:.2f}
- **CAGR**: {cagr*100:.1f}%
- **Max Drawdown**: {max_dd_pct*100:.1f}%
- **MAR Ratio**: {mar:.2f}
"""

    @staticmethod
    def build_strategy_performance(df: pd.DataFrame) -> str:
        """Build performance table per strategy."""
        if df is None or df.empty or 'strategy' not in df.columns:
            return "No strategy data available."

        lines = ["\n## STRATEGY PERFORMANCE\n"]
        lines.append(f"**Number of strategies in portfolio: {len(df['strategy'].unique())}**\n")

        # Collect stats for ranking
        strategy_stats = []

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

            # MAR (simplified)
            days = (strat_df['timestamp'].max() - strat_df['timestamp'].min()).days if 'timestamp' in strat_df.columns else 365
            years = max(days / 365.25, 0.1)
            cagr = ((100000 + total_pnl) / 100000) ** (1/years) - 1 if total_pnl > -100000 else -1
            mar = cagr / max_dd_pct if max_dd_pct > 0 else 0

            # Margin
            avg_margin = strat_df['margin'].mean() if 'margin' in strat_df.columns else 0

            # Kelly Criterion
            loss_rate = 1 - win_rate
            if avg_win > 0 and avg_loss > 0:
                kelly = (win_rate * avg_win - loss_rate * avg_loss) / avg_win
                kelly_pct = max(0, min(kelly, 1)) * 100  # Cap at 100%
            else:
                kelly_pct = 0

            # Expected Value per trade
            ev = (win_rate * avg_win) - (loss_rate * avg_loss)

            lines.append(f"""
### {strategy}
- **P&L**: ${total_pnl:,.0f} | **Trades**: {trades}
- **Win Rate**: {win_rate*100:.0f}% | **Profit Factor**: {profit_factor:.2f}
- **Avg Win**: ${avg_win:,.0f} | **Avg Loss**: ${avg_loss:,.0f}
- **Max Drawdown**: {max_dd_pct*100:.1f}% | **MAR**: {mar:.2f}
- **Kelly Criterion**: {kelly_pct:.1f}% | **Expected Value**: ${ev:,.0f}/trade
- **Avg Margin**: ${avg_margin:,.0f}
""")
            # Store for ranking
            strategy_stats.append({
                'name': strategy,
                'pnl': total_pnl,
                'mar': mar,
                'win_rate': win_rate,
                'profit_factor': profit_factor,
                'kelly': kelly_pct,
                'ev': ev
            })

        # Add ranking summary
        if strategy_stats:
            best_pnl = max(strategy_stats, key=lambda x: x['pnl'])
            worst_pnl = min(strategy_stats, key=lambda x: x['pnl'])
            best_mar = max(strategy_stats, key=lambda x: x['mar'])
            worst_mar = min(strategy_stats, key=lambda x: x['mar'])
            best_ev = max(strategy_stats, key=lambda x: x['ev'])
            best_kelly = max(strategy_stats, key=lambda x: x['kelly'])

            lines.append(f"""
## STRATEGY RANKING

**Best Strategy (by P&L)**: {best_pnl['name']} with ${best_pnl['pnl']:,.0f}
**Worst Strategy (by P&L)**: {worst_pnl['name']} with ${worst_pnl['pnl']:,.0f}
**Best Strategy (by MAR)**: {best_mar['name']} with MAR {best_mar['mar']:.2f}
**Worst Strategy (by MAR)**: {worst_mar['name']} with MAR {worst_mar['mar']:.2f}
**Best Strategy (by EV)**: {best_ev['name']} with ${best_ev['ev']:,.0f}/trade
**Highest Kelly Sizing**: {best_kelly['name']} suggests {best_kelly['kelly']:.1f}% (use 25-50% of this)
""")

        return "\n".join(lines)

    @staticmethod
    def build_correlation_context() -> str:
        """Build correlation context - from cache or computed."""
        # Try cache first
        corr = st.session_state.get('correlation_matrix')

        # If no cache, try to compute from DataFrame
        if corr is None:
            df = st.session_state.get('full_df', pd.DataFrame())
            if df is not None and not df.empty and 'strategy' in df.columns and 'timestamp' in df.columns:
                try:
                    pivot = df.pivot_table(
                        index=df['timestamp'].dt.date,
                        columns='strategy',
                        values='pnl',
                        aggfunc='sum'
                    ).fillna(0)
                    if len(pivot.columns) >= 2:
                        corr = pivot.corr()
                except Exception:
                    pass

        if corr is None or not isinstance(corr, pd.DataFrame):
            return ""

        # Find high correlations
        high_corr = []
        for i, col1 in enumerate(corr.columns):
            for j, col2 in enumerate(corr.columns):
                if i < j:
                    val = corr.loc[col1, col2]
                    if abs(val) > 0.7:
                        risk = "CRITICAL" if abs(val) > 0.85 else "WARNING"
                        high_corr.append(f"- {col1} ↔ {col2}: {val:.2f} ({risk})")

        if high_corr:
            return f"""
## CORRELATION ANALYSIS

**High correlations found:**
{chr(10).join(high_corr)}

⚠️ High correlation means cluster risk - multiple strategies lose simultaneously during market moves!
"""
        return ""

    @staticmethod
    def build_monte_carlo_context() -> str:
        """Build Monte Carlo context from cached results."""
        mc = st.session_state.get('mc_results')
        if not mc:
            return "\n## MONTE CARLO\n❌ Not yet executed. Go to 'Monte Carlo Punisher' to run simulation."

        return f"""
## MONTE CARLO SIMULATION

**Configuration**: {mc.get('n_sims', 'N/A')} simulations, {mc.get('sim_months', 'N/A')} months

**Return Scenarios**:
- Worst Case (P5): ${mc.get('p05', 0):,.0f}
- Expected (P50): ${mc.get('p50', 0):,.0f}
- Best Case (P95): ${mc.get('p95', 0):,.0f}

**Drawdown Scenarios**:
- Best Case DD: {mc.get('d05', 0)*100:.1f}%
- Typical DD: {mc.get('d50', 0)*100:.1f}%
- Worst Case DD: {mc.get('d95', 0)*100:.1f}%

**Key Metrics**:
- CAGR (expected): {mc.get('cagr', 0)*100:.1f}%
- MAR Ratio: {mc.get('mar', 0):.2f}
- Profit Probability: {mc.get('prob_profit', 0)*100:.0f}%
"""

    @staticmethod
    def build_full_context(current_page: Optional[str] = None) -> str:
        """
        Build complete context for an AI request.
        ALWAYS directly from DataFrame for reliability.

        Args:
            current_page: The current page (for context-specific help)

        Returns:
            Complete context string for the AI prompt
        """
        df = st.session_state.get('full_df', pd.DataFrame())

        # ALWAYS build context directly from DataFrame for reliability
        context_parts = [
            AIContextBuilder.build_portfolio_overview(df),
            AIContextBuilder.build_strategy_performance(df),
            AIContextBuilder.build_correlation_context(),
            AIContextBuilder.build_monte_carlo_context(),
        ]

        # Page-specific context
        if current_page:
            context_parts.append(f"\n## CURRENT CONTEXT\nUser is on page: **{current_page}**")

        return "\n".join(context_parts)

    @staticmethod
    def _build_precomputed_context() -> str:
        """Build context from precomputed data."""
        import precompute

        lines = ["## PRECOMPUTED PORTFOLIO DATA\n"]

        # Basic metrics
        basic = precompute.get_cached('basic_metrics', {})
        if basic:
            lines.append(f"""### Overview
- Strategies: {basic.get('strategy_count', 0)}
- Trades: {basic.get('total_trades', 0):,}
- Period: {basic.get('days', 0)} days
- Total P&L: ${basic.get('total_pnl', 0):,.0f}
- CAGR: {basic.get('cagr', 0)*100:.1f}%
- Sharpe: {basic.get('sharpe', 0):.2f}
- Max Drawdown: {basic.get('max_dd', 0)*100:.1f}%
- MAR: {basic.get('mar', 0):.2f}
""")

        # Strategy stats
        strat_stats = precompute.get_cached('strategy_stats', {})
        if strat_stats:
            lines.append("### Strategy Performance\n")
            for name, stats in strat_stats.items():
                lines.append(f"""**{name}**
- P&L: ${stats.get('total_pnl', 0):,.0f} | Trades: {stats.get('trades', 0)}
- Win Rate: {stats.get('win_rate', 0)*100:.0f}% | PF: {stats.get('profit_factor', 0):.2f}
- MAR: {stats.get('mar', 0):.2f} | Max DD: {stats.get('max_dd', 0)*100:.1f}%
""")

        # Correlation warnings
        corr = precompute.get_cached('correlation_matrix')
        if corr is not None and isinstance(corr, pd.DataFrame):
            high_corr = []
            for i, col1 in enumerate(corr.columns):
                for j, col2 in enumerate(corr.columns):
                    if i < j and abs(corr.loc[col1, col2]) > 0.7:
                        high_corr.append(f"- {col1} ↔ {col2}: {corr.loc[col1, col2]:.2f}")
            if high_corr:
                lines.append("### Correlation Warnings\n" + "\n".join(high_corr))

        return "\n".join(lines)

    @staticmethod
    def get_quick_stats() -> Dict[str, Any]:
        """Quick stats for sidebar display."""
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
