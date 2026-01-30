"""
AI Context Builder for CashFlow Engine
Collects all cached data and prepares it for the AI.
"""

import streamlit as st
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional

# ============================================================================
# KNOWLEDGE BASE - Complete App Documentation & Financial Knowledge
# ============================================================================

CASHFLOW_ENGINE_KNOWLEDGE = """
## CRITICAL RULES

1. Use ONLY the definitions in this document - not your general knowledge
2. Never use WORKHORSE, AIRBAG, OPPORTUNIST as performance labels (they are user categories)
3. Use simple formatting: headers, bullet points, bold for emphasis
4. Write numbers American style: $100,000 (comma for thousands)

---

## CASHFLOW ENGINE APP DOCUMENTATION

### What is CashFlow Engine?

CashFlow Engine is a portfolio analysis tool for options traders. It analyzes backtested trading data from platforms like Optionomega, calculates performance metrics, runs Monte Carlo simulations, and helps optimize portfolio allocation.

### App Pages and Functions

PAGE: Start & Data
- Upload backtest CSV files from trading platforms
- View raw data preview
- Data validation and cleaning
- Required columns: timestamp, strategy, pnl, margin
- Optional: ticker, delta, iv, dte

PAGE: Portfolio Analytics
- Overview of portfolio performance
- Key metrics displayed: Total P/L, CAGR, Max Drawdown, MAR, Sharpe, Sortino
- Equity curve chart showing growth over time
- Drawdown chart showing underwater periods
- Monthly returns heatmap
- Strategy breakdown table
- Buttons: Download Report, Compare to SPX

PAGE: Portfolio Builder
- Optimize allocation across strategies
- Slider for each strategy weight (0-100%)
- Optimization targets: Max MAR, Max MART, Min Correlation, Max Sharpe
- Correlation matrix heatmap
- Efficient frontier visualization
- Result: Suggested allocation percentages

PAGE: Monte Carlo Punisher
- Simulate future portfolio paths
- Inputs: Number of simulations (1000-10000), Months to simulate (12-60)
- Buttons: Run Simulation, Reset
- Outputs: Return distribution chart, Drawdown distribution, Percentile table (P5, P25, P50, P75, P95)
- Profit probability percentage

PAGE: Backtest vs Live
- Compare backtest performance to live trading
- Upload live trading data
- Side-by-side metrics comparison
- Identify strategy decay or improvement
- Slippage analysis

PAGE: MEIC Analysis
- Monthly Expected Income Calculator
- Project monthly income based on historical data
- Confidence intervals for income projections

PAGE: AI Portfolio Analyst (this page)
- Chat interface for portfolio questions
- Quick action buttons for common analyses
- Data availability indicator
- Usage budget display

### User-Defined Strategy Categories

WORKHORSE (typically 60% of portfolio)
- User assigns this label to daily income strategies
- NOT a performance ranking
- Example strategies: Iron Condors, Credit Spreads

AIRBAG (typically 25% of portfolio)
- User assigns this label to hedge/protection strategies
- NOT a safety rating
- Example strategies: Long Puts, VIX Calls

OPPORTUNIST (typically 15% of portfolio)
- User assigns this label to occasional trades
- NOT a risk indicator
- Example strategies: Earnings plays, Momentum trades

When discussing performance, say "top performers" or "best by MAR" - never call something a "Workhorse performer".

---

## ALL CALCULATED METRICS

### Return Metrics

Total P/L: Sum of all trade profits and losses in dollars

CAGR (Compound Annual Growth Rate):
- Formula: ((End Value / Start Value) ^ (365 / Days)) - 1
- Meaning: Annualized return percentage
- Example: $100k to $150k in 2 years = 22.5% CAGR

### Drawdown Metrics

Maximum Drawdown Percent (Max DD %):
- Formula: (Peak Equity - Trough) / Peak Equity
- Meaning: Largest percentage drop from any high point
- Example: Peak $150k, low $120k = 20% drawdown

Maximum Drawdown Dollars (Max DD $):
- The actual dollar amount lost from peak to trough
- Example: Peak $150k, low $120k = $30,000 drawdown

### Risk-Adjusted Returns

MAR Ratio (Managed Account Ratio):
- Formula: CAGR / Maximum Drawdown %
- Drawdown basis: Relative to CURRENT equity peak
- Targets: Above 2.0 excellent, 1.5-2.0 good, 1.0-1.5 acceptable
- Example: 30% CAGR with 15% Max DD = MAR of 2.0

MART Ratio (MAR based on Total/Initial):
- Formula: CAGR / (Max DD Dollars / Initial Account)
- Drawdown basis: Relative to STARTING capital (fixed)
- More conservative than MAR
- Used in Portfolio Builder optimization
- Example: 30% CAGR, $30k DD on $100k start = MART of 1.0

Key difference MAR vs MART:
- MAR uses rolling peak (grows as account grows)
- MART uses initial account (stays fixed)
- MART is stricter for accounts that have grown significantly

Sharpe Ratio:
- Formula: (Return - Risk Free Rate) / Standard Deviation
- Risk Free Rate used: 4%
- Measures excess return per unit of total volatility
- Targets: Above 1.5 good, above 2.0 very good

Sortino Ratio:
- Formula: (Return - Target) / Downside Deviation
- Only penalizes downside volatility
- Better for options because it ignores upside spikes
- Usually higher than Sharpe for good strategies

Alpha:
- Excess return above market benchmark (SPX)
- Positive alpha means outperforming the market

Beta:
- Portfolio sensitivity to market moves
- Beta 1.0 = moves with market
- Beta below 1.0 = less volatile than market
- Beta negative = inverse to market

Volatility:
- Annualized standard deviation of daily returns
- Formula: Daily StdDev times sqrt(252)
- Lower volatility = more consistent returns

### Trade Statistics

Win Rate: Winning trades divided by total trades
- Options selling typical: 70-85%

Profit Factor: Sum of wins divided by sum of losses
- Above 1.5 = sustainable
- 1.0-1.5 = marginal
- Below 1.0 = losing money

Average Win: Mean profit of winning trades

Average Loss: Mean loss of losing trades (as positive number)

Best Trade: Largest single winning trade

Worst Trade: Largest single losing trade

Win Streak: Most consecutive wins

Loss Streak: Most consecutive losses

### Position Sizing

Kelly Criterion:
- Formula: (Win% x AvgWin - Loss% x AvgLoss) / AvgWin
- CRITICAL: Use only 25-50% of calculated Kelly
- Example: Kelly says 20%, use 5-10% position size

Expected Value (EV):
- Formula: (Win% x AvgWin) - (Loss% x AvgLoss)
- Must be positive for profitable strategy
- Shown as dollars per trade

### Margin Metrics

Peak Margin: Maximum margin used at any point

Average Margin: Mean margin across all positions

Return on Margin: P/L divided by margin used

### Correlation

Portfolio Correlation: Average pairwise correlation between strategies
- Below 0.5 = good diversification
- Above 0.7 = cluster risk warning
- Above 0.85 = critical concentration

---

## OPTIONS FUNDAMENTALS

### Option Basics

Call Option: Right to BUY at strike price
- Buyer is bullish
- Seller collects premium, wants price below strike

Put Option: Right to SELL at strike price
- Buyer is bearish
- Seller collects premium, wants price above strike

### The Greeks

Delta: Price sensitivity to underlying move
- Call delta: 0 to +1.0
- Put delta: -1.0 to 0
- ATM options have delta around 0.50

Gamma: Rate of delta change
- Highest at-the-money near expiration
- Short options have negative gamma (bad)

Theta: Daily time decay in dollars
- Sellers benefit from theta
- Accelerates near expiration

Vega: Sensitivity to implied volatility
- Long options: positive vega
- Short options: negative vega

### Implied Volatility

IV: Market's expectation of future volatility
- High IV = expensive options
- Low IV = cheap options

IV Rank: Where current IV sits in past year range
- Formula: (Current - 52wk Low) / (52wk High - 52wk Low)
- Above 50% = good time to sell premium

IV Percentile: Percent of days with lower IV
- Different calculation than IV Rank

### Moneyness

ITM (In-The-Money): Has intrinsic value
OTM (Out-of-The-Money): No intrinsic value
ATM (At-The-Money): Strike equals current price

---

## OPTIONS STRATEGIES

### Credit Strategies (Premium Selling)

Short Put: Sell put, collect premium
- Bullish, wants stock above strike
- Risk: Stock drops significantly

Covered Call: Sell call against shares owned
- Neutral to slightly bullish
- Limits upside, generates income

Bull Put Spread: Sell higher put, buy lower put
- Defined risk bullish trade
- Max loss = spread width minus credit

Bear Call Spread: Sell lower call, buy higher call
- Defined risk bearish trade
- Max loss = spread width minus credit

Iron Condor: Bull put spread + Bear call spread
- Profit if stock stays in range
- Manage at 50% profit or 21 DTE

Short Strangle: Sell OTM put and OTM call
- Undefined risk on both sides
- Higher premium than iron condor

### Debit Strategies (Premium Buying)

Long Call: Buy call for bullish exposure
Long Put: Buy put for bearish exposure or protection
Debit Spreads: Reduce cost by selling further OTM option

### Calendar and Diagonal Spreads

Calendar: Same strike, different expirations
- Profits from faster near-term decay

Diagonal: Different strikes and expirations
- Combines directional bias with time decay

### Advanced Strategies

Wheel Strategy:
1. Sell cash-secured puts
2. If assigned, sell covered calls
3. If called away, repeat

Jade Lizard: Short put + short call spread
- No upside risk if structured correctly

---

## RISK MANAGEMENT

### Position Sizing Rules

Fixed Percentage: Risk 1-2% per trade
Kelly-Based: Use 25-50% of Kelly calculation
Volatility-Based: Smaller size when IV is high

### DTE Management

45 DTE Entry: Sweet spot for premium selling
21 DTE Exit: Close or roll before gamma risk increases
0 DTE: Maximum risk, requires constant monitoring

### Rolling

Roll Out: Same strike, later expiration
Roll Up/Down: Different strike
Always try to roll for a credit

### Exit Rules

Profit Target: 50% of max profit for spreads
Loss Limit: 2x credit received is common stop

---

## MONTE CARLO INTERPRETATION

P5 (5th percentile): Worst realistic case - only 5% of outcomes are worse
P25: Below average but possible
P50 (Median): Expected typical outcome
P75: Above average scenario
P95: Best realistic case - only 5% of outcomes are better

How to use results:
- Plan for P5 drawdown scenario
- Expect P50 returns
- Ignore P95 for planning (too optimistic)
- Profit probability below 70% = proceed with caution

---

## PLATFORM INTEGRATIONS

Optionomega: Options backtesting, export trade history
Optionstrat: Options visualization, P/L diagrams
Trade Automation Toolbox: Automated trading for TastyTrade
Tradestuart: Income strategy backtesting

---

## RESPONSE GUIDELINES

- Answer in the user's language
- Use specific numbers from their portfolio data
- Give actionable recommendations
- Warn about risks proactively
- Say which analysis to run if data is missing
- Use neutral terms for performance (not category names)
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

        lines = ["## Data Availability\n"]

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
            status = "Ready" if avail.get(key) else "Not available"
            lines.append(f"- {name}: {status} ({desc})")

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
## Portfolio Overview

Strategies: {len(strategies)} ({', '.join(strategies[:5])}{'...' if len(strategies) > 5 else ''})
Total Trades: {total_trades:,}
Period: {start_date} to {end_date} ({days} days, {years:.1f} years)
Total P/L: ${total_pnl:,.0f}

Portfolio Metrics:
- Win Rate: {portfolio_win_rate*100:.1f}%
- Profit Factor: {portfolio_pf:.2f}
- CAGR: {cagr*100:.1f}%
- Max Drawdown: {max_dd_pct*100:.1f}%
- MAR Ratio: {mar:.2f}
"""

    @staticmethod
    def build_strategy_performance(df: pd.DataFrame) -> str:
        """Build performance table per strategy."""
        if df is None or df.empty or 'strategy' not in df.columns:
            return "No strategy data available."

        lines = ["\n## Strategy Performance\n"]
        lines.append(f"Number of strategies: {len(df['strategy'].unique())}\n")

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
                kelly_pct = max(0, min(kelly, 1)) * 100
            else:
                kelly_pct = 0

            # Expected Value per trade
            ev = (win_rate * avg_win) - (loss_rate * avg_loss)

            lines.append(f"""
### {strategy}
- P/L: ${total_pnl:,.0f} | Trades: {trades}
- Win Rate: {win_rate*100:.0f}% | Profit Factor: {profit_factor:.2f}
- Avg Win: ${avg_win:,.0f} | Avg Loss: ${avg_loss:,.0f}
- Max Drawdown: {max_dd_pct*100:.1f}% | MAR: {mar:.2f}
- Kelly: {kelly_pct:.1f}% | EV: ${ev:,.0f}/trade
- Avg Margin: ${avg_margin:,.0f}
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
## Strategy Rankings

Best by P/L: {best_pnl['name']} with ${best_pnl['pnl']:,.0f}
Worst by P/L: {worst_pnl['name']} with ${worst_pnl['pnl']:,.0f}
Best by MAR: {best_mar['name']} with {best_mar['mar']:.2f}
Worst by MAR: {worst_mar['name']} with {worst_mar['mar']:.2f}
Best by EV: {best_ev['name']} with ${best_ev['ev']:,.0f}/trade
Highest Kelly: {best_kelly['name']} suggests {best_kelly['kelly']:.1f}% (use 25-50% of this)
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
                        high_corr.append(f"- {col1} and {col2}: {val:.2f} ({risk})")

        if high_corr:
            return f"""
## Correlation Analysis

High correlations found:
{chr(10).join(high_corr)}

Note: High correlation means cluster risk - multiple strategies may lose at the same time.
"""
        return ""

    @staticmethod
    def build_monte_carlo_context() -> str:
        """Build Monte Carlo context from cached results."""
        mc = st.session_state.get('mc_results')
        if not mc:
            return "\n## Monte Carlo\nNot yet executed. Go to Monte Carlo Punisher to run simulation."

        return f"""
## Monte Carlo Results

Configuration: {mc.get('n_sims', 'N/A')} simulations, {mc.get('sim_months', 'N/A')} months

Return Scenarios:
- Worst Case (P5): ${mc.get('p05', 0):,.0f}
- Expected (P50): ${mc.get('p50', 0):,.0f}
- Best Case (P95): ${mc.get('p95', 0):,.0f}

Drawdown Scenarios:
- Best Case DD: {mc.get('d05', 0)*100:.1f}%
- Typical DD: {mc.get('d50', 0)*100:.1f}%
- Worst Case DD: {mc.get('d95', 0)*100:.1f}%

Key Metrics:
- Expected CAGR: {mc.get('cagr', 0)*100:.1f}%
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
            context_parts.append(f"\n## Current Context\nUser is on page: {current_page}")

        return "\n".join(context_parts)

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
