"""
AI Context Builder for CashFlow Engine
Collects all cached data and prepares it for the AI.
"""

import streamlit as st
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional

# ============================================================================
# KNOWLEDGE BASE - Complete definitions and calculation methods
# ============================================================================

CASHFLOW_ENGINE_KNOWLEDGE = """
## CRITICAL INSTRUCTIONS

YOU MUST USE THE DEFINITIONS PROVIDED BELOW. Do NOT use your own general knowledge.
When asked about any metric (MAR, MART, Sharpe, etc.), use ONLY the definitions in this document.
When describing strategy performance, use neutral terms - never use "Workhorse", "Airbag", "Opportunist" as performance labels.

---

## ALL METRICS IN CASHFLOW ENGINE

### Return Metrics

**Total P/L (Profit & Loss)**
- Definition: Sum of all trade profits and losses
- Displayed in USD ($)
- Compared against SPX benchmark return

**CAGR (Compound Annual Growth Rate)**
- Definition: CAGR = ((End Value / Start Value) ^ (365 / Days)) - 1
- Interpretation: Annualized return percentage
- Example: $100k → $150k over 2 years = 22.5% CAGR
- Compared against SPX CAGR for benchmark

### Risk Metrics

**Maximum Drawdown % (Max DD %)**
- Definition: Max DD = (Peak - Trough) / Peak
- Interpretation: Largest percentage decline from any peak
- Example: Peak $150k, Trough $120k = 20% drawdown
- Warning levels: <20% good, 20-30% acceptable, >30% concerning
- Compared against SPX Max DD

**Maximum Drawdown $ (Max DD $)**
- Definition: The dollar amount of the largest decline
- Example: Peak $150k, Trough $120k = $30,000 drawdown
- Important for understanding actual capital at risk

**Volatility (Vol)**
- Definition: Annualized standard deviation of daily returns
- Formula: Daily StdDev × √252
- Interpretation: How much returns fluctuate
- Lower = more consistent returns
- Compared against SPX Volatility

### Risk-Adjusted Return Metrics

**MAR Ratio (Managed Account Ratio)**
- Definition: MAR = CAGR / |Maximum Drawdown %|
- Drawdown Basis: Relative to CURRENT equity peak
- Example: 30% CAGR, 15% Max DD = MAR 2.0
- Targets: >2.0 excellent, 1.5-2.0 good, 1.0-1.5 acceptable, <1.0 needs work
- Compared against SPX MAR

**MART Ratio (MAR based on Initial Account)**
- Definition: MART = CAGR / (Max Drawdown $ / Initial Account Size)
- Drawdown Basis: Relative to INITIAL account size (fixed baseline)
- Example: 30% CAGR, $30k DD on $100k account = MART 1.0
- Difference from MAR: More conservative, uses starting capital
- Use Case: Better for comparing across different time periods
- Used in Portfolio Builder for MART optimization

**Sharpe Ratio**
- Definition: Sharpe = (Portfolio Return - Risk Free Rate) / Standard Deviation
- Risk Free Rate: 4% (current US Treasury approximation)
- Interpretation: Excess return per unit of total risk
- Targets: >1.5 good, >2.0 very good, >3.0 excellent
- Limitation: Penalizes upside volatility equally
- Compared against SPX Sharpe

**Sortino Ratio**
- Definition: Sortino = (Return - Target) / Downside Deviation
- Interpretation: Like Sharpe but only considers downside volatility
- Better for Options: Doesn't penalize large winning trades
- Generally higher than Sharpe for good options strategies

**Alpha (vs SPX)**
- Definition: Excess return above what market beta would predict
- Formula: Portfolio Return - (Beta × Market Return)
- Positive Alpha: Outperforming the market on risk-adjusted basis
- Displayed as annualized percentage

**Beta (vs SPX)**
- Definition: Sensitivity to market movements
- Beta = 1.0: Moves with market
- Beta < 1.0: Less volatile than market
- Beta > 1.0: More volatile than market
- Beta < 0: Moves opposite to market (hedging strategies)

### Trade Statistics

**Total Trades**
- Definition: Count of all closed trades in the dataset
- Used for statistical significance assessment

**Win Rate**
- Definition: Win Rate = Winning Trades / Total Trades
- Options selling typically: 70-85%
- Warning: High win rate doesn't guarantee profitability
- Must consider: Win Rate × Avg Win vs Loss Rate × Avg Loss

**Profit Factor (PF)**
- Definition: PF = Sum of All Wins / |Sum of All Losses|
- Example: $50k wins, $30k losses = PF 1.67
- Targets: >1.5 sustainable, 1.0-1.5 marginal, <1.0 losing money
- Options selling typically: 1.2-2.5

**Win Streak**
- Definition: Maximum consecutive winning trades
- Shows best run of the strategy

**Loss Streak**
- Definition: Maximum consecutive losing trades
- Important for psychological preparation and drawdown planning

**Average Win**
- Definition: Mean profit of all winning trades
- Used in Kelly Criterion and EV calculations

**Average Loss**
- Definition: Mean loss of all losing trades (absolute value)
- Used in Kelly Criterion and EV calculations

**Best/Worst Trade**
- Definition: Largest single winning and losing trade
- Shows tail risk and potential outliers

### Position Sizing Metrics

**Kelly Criterion**
- Definition: Kelly% = (Win% × Avg Win - Loss% × Avg Loss) / Avg Win
- Alternative: Kelly% = Win% - (Loss% / Win-Loss Ratio)
- CRITICAL: Always use 25-50% of full Kelly (Half-Kelly or Quarter-Kelly)
- Example: Full Kelly 20% → Use 5-10% position size
- Why fractional: Full Kelly is too aggressive, small errors compound badly

**Expected Value (EV)**
- Definition: EV = (Win% × Avg Win) - (Loss% × Avg Loss)
- Must be positive for profitable strategy
- Higher EV = stronger edge
- Displayed as $/trade

### Margin Metrics

**Peak Margin**
- Definition: Maximum margin used at any point
- Displayed as $ and % of account
- Warning: >80% leaves little buffer for adverse moves

**Average Margin**
- Definition: Mean margin utilization across all positions
- Displayed as $ and % of account
- Target: Keep average <50% for safety

**Avg Return on Margin**
- Definition: Average P&L divided by margin used
- Shows capital efficiency

### Correlation Metrics

**Portfolio Correlation**
- Definition: Average pairwise correlation between strategies
- Target: <0.5 for true diversification
- Warning levels: >0.7 cluster risk, >0.85 critical
- High correlation = strategies move together = concentrated risk

---

## STRATEGY CATEGORIES (User-Defined)

IMPORTANT: These are USER-ASSIGNED portfolio categories, NOT performance labels.
Never use these terms to describe strategy performance.

**WORKHORSE (typically 60% allocation)**
- User category for: Daily, consistent income strategies
- Examples: Iron Condors, Credit Spreads on SPX/RUT
- Meaning: "Core income strategy" - NOT "best performer"

**AIRBAG (typically 25% allocation)**
- User category for: Hedging/protection strategies
- Examples: Long Puts, Bear Call Spreads, VIX calls
- Meaning: "Crash protection" - NOT "safe strategy"

**OPPORTUNIST (typically 15% allocation)**
- User category for: Occasional high-conviction trades
- Examples: Earnings plays, momentum strategies
- Meaning: "Opportunistic entry" - NOT "risky strategy"

When describing performance, use neutral terms:
- "Top performers by P&L"
- "Best risk-adjusted strategies by MAR"
- "Underperforming strategies"
- "Strategies needing attention"

---

## OPTIONS FUNDAMENTALS

### What is an Option?

**Call Option**
- Right (not obligation) to BUY underlying at strike price
- Buyer pays premium, seller collects premium
- Call buyer: Bullish, wants price to rise
- Call seller: Neutral/bearish, wants price to stay below strike

**Put Option**
- Right (not obligation) to SELL underlying at strike price
- Buyer pays premium, seller collects premium
- Put buyer: Bearish, wants price to fall
- Put seller: Neutral/bullish, wants price to stay above strike

### The Greeks

**Delta (Δ)**
- Definition: Rate of change of option price vs underlying price
- Range: -1.0 to +1.0
- Call delta: 0 to +1.0 (ATM ≈ 0.50)
- Put delta: -1.0 to 0 (ATM ≈ -0.50)
- Use: Position directional exposure, hedge ratio
- 100 shares = 1.0 delta

**Gamma (Γ)**
- Definition: Rate of change of delta vs underlying price
- Highest at-the-money, near expiration
- Long options: Positive gamma (delta moves in your favor)
- Short options: Negative gamma (delta moves against you)
- Gamma risk increases dramatically near expiration

**Theta (Θ)**
- Definition: Rate of time decay per day
- Displayed as $/day the option loses
- Accelerates as expiration approaches
- Sellers benefit from theta (collect time decay)
- Buyers fight against theta

**Vega (ν)**
- Definition: Sensitivity to 1% change in implied volatility
- High vega: Option price sensitive to IV changes
- Long options: Positive vega (benefit from IV increase)
- Short options: Negative vega (benefit from IV decrease)

**Rho (ρ)**
- Definition: Sensitivity to interest rate changes
- Usually minor for short-term options
- More relevant for LEAPS

### Implied Volatility (IV)

**What is IV?**
- Market's expectation of future volatility
- Derived from option prices (not historical)
- Higher IV = more expensive options
- Lower IV = cheaper options

**IV Rank (IVR)**
- Definition: Where current IV sits relative to past year
- Formula: (Current IV - 52wk Low) / (52wk High - 52wk Low)
- Range: 0-100%
- High IVR (>50%): Good time to sell premium
- Low IVR (<30%): Consider buying strategies

**IV Percentile (IVP)**
- Definition: % of days in past year with lower IV
- IVP 80% = IV higher than 80% of past year
- Often confused with IV Rank but calculated differently

**Volatility Skew**
- OTM puts typically have higher IV than OTM calls
- Due to crash protection demand
- Creates pricing asymmetry in spreads

### Options Pricing Basics

**Intrinsic Value**
- Call: Max(0, Stock Price - Strike Price)
- Put: Max(0, Strike Price - Stock Price)
- ITM options have intrinsic value
- OTM options have zero intrinsic value

**Extrinsic Value (Time Value)**
- Option Price - Intrinsic Value
- Decays to zero at expiration
- Affected by: Time to expiration, IV, interest rates

**Moneyness**
- ITM (In-The-Money): Has intrinsic value
- ATM (At-The-Money): Strike ≈ current price
- OTM (Out-of-The-Money): No intrinsic value

---

## OPTIONS STRATEGIES

### Credit Strategies (Premium Selling)

**Short Put (Cash-Secured Put)**
- Sell put, collect premium
- Profit: Premium if stock stays above strike
- Max Loss: Strike - Premium (if assigned)
- Use: Bullish, want to buy stock at lower price
- Margin: Cash to cover assignment or margin requirement

**Short Call (Covered Call)**
- Sell call against owned stock
- Profit: Premium + stock gains up to strike
- Max Loss: Stock drops (unlimited downside)
- Use: Neutral/slightly bullish, generate income
- Requires: 100 shares per contract

**Bull Put Spread (Put Credit Spread)**
- Sell higher strike put, buy lower strike put
- Profit: Net credit if stock stays above short strike
- Max Loss: Width - Credit received
- Use: Bullish, defined risk
- Example: Sell 100P, Buy 95P for $1.50 credit, Max loss $3.50

**Bear Call Spread (Call Credit Spread)**
- Sell lower strike call, buy higher strike call
- Profit: Net credit if stock stays below short strike
- Max Loss: Width - Credit received
- Use: Bearish, defined risk

**Iron Condor**
- Bull put spread + Bear call spread
- Sell OTM put spread AND OTM call spread
- Profit: Both credits if stock stays in range
- Max Loss: Wider spread width - Total credit
- Use: Neutral, expect range-bound market
- Management: Close at 50% profit or 21 DTE

**Iron Butterfly**
- Sell ATM straddle + buy OTM strangle
- Sell ATM put + ATM call, buy OTM put + OTM call
- Max Profit: Total credit (if exactly at short strikes)
- Use: Very neutral, expect no movement

**Short Strangle**
- Sell OTM put + OTM call (no protection)
- Undefined risk on both sides
- Higher premium than iron condor
- Requires active management
- Use: Larger accounts only, high conviction neutral

**Short Straddle**
- Sell ATM put + ATM call
- Maximum theta decay (ATM options)
- Undefined risk, high maintenance
- Use: Very high conviction, expect no movement

### Debit Strategies (Premium Buying)

**Long Call**
- Buy call, pay premium
- Profit: Stock rises above strike + premium
- Max Loss: Premium paid
- Use: Bullish, limited risk

**Long Put**
- Buy put, pay premium
- Profit: Stock falls below strike - premium
- Max Loss: Premium paid
- Use: Bearish, portfolio protection

**Call Debit Spread (Bull Call Spread)**
- Buy lower strike call, sell higher strike call
- Profit: Stock rises to/above short strike
- Max Loss: Net debit paid
- Use: Moderately bullish, reduce cost

**Put Debit Spread (Bear Put Spread)**
- Buy higher strike put, sell lower strike put
- Profit: Stock falls to/below short strike
- Max Loss: Net debit paid
- Use: Moderately bearish

**Long Straddle**
- Buy ATM put + ATM call
- Profit: Large move in either direction
- Max Loss: Total premium paid
- Use: Expect big move, direction unknown

**Long Strangle**
- Buy OTM put + OTM call
- Cheaper than straddle, needs bigger move
- Use: Expect very large move

### Calendar & Diagonal Spreads

**Calendar Spread (Time Spread)**
- Sell short-term option, buy longer-term same strike
- Profits from faster decay of short-term option
- Best when: Stock stays near strike, IV increases
- Risk: Large move away from strike

**Diagonal Spread**
- Calendar spread with different strikes
- More directional bias than pure calendar
- Example: Sell 30-day 105C, Buy 60-day 100C

### Advanced Strategies

**Wheel Strategy**
1. Sell cash-secured puts on stock you want to own
2. If assigned, sell covered calls on shares
3. If called away, start over with puts
- Systematic income generation
- Best on: Stocks you'd want to own anyway

**Jade Lizard**
- Short put + short call spread (no upside risk)
- Credit from put > width of call spread
- No risk to upside, risk on downside

**Broken Wing Butterfly**
- Unbalanced butterfly for credit
- Skewed risk profile

---

## RISK MANAGEMENT

### Position Sizing

**Fixed Percentage Rule**
- Risk 1-2% of portfolio per trade
- Simple, consistent approach
- Doesn't account for edge variation

**Kelly-Based Sizing**
- Use 25-50% of theoretical Kelly
- Adjusts for strategy edge
- Requires accurate win rate data

**Volatility-Based Sizing**
- Smaller positions when IV is high
- Larger when IV is low (cheaper premium)

### DTE (Days to Expiration) Management

**45 DTE Entry**
- Sweet spot for premium selling
- Good theta decay, manageable gamma
- Time to adjust if needed

**21 DTE Rule**
- Consider closing or rolling at 21 DTE
- Gamma risk accelerates
- Less time to recover from adverse moves

**0 DTE Trading**
- Same-day expiration trading
- Maximum gamma, maximum risk
- Requires constant monitoring
- Not for beginners

### Adjustment Strategies

**Rolling**
- Close current position, open new one
- Roll out: Same strike, later expiration
- Roll up/down: Different strike, same/later expiration
- Roll for credit when possible

**When to Roll**
- Position tested (stock near short strike)
- Need more time for thesis to play out
- Can collect additional credit

**When NOT to Roll**
- Thesis is wrong, not just timing
- Can't roll for credit
- Better opportunities elsewhere

### Exit Rules

**Profit Targets**
- 50% of max profit: Common for credit spreads
- 25% for short-term trades
- Let winners run (with trailing stop) for directional

**Loss Limits**
- 2x credit received: Common stop loss
- At short strike test: Close or roll
- Portfolio heat: Max 5% daily loss

### Assignment Risk

**American vs European Options**
- American: Can be exercised anytime (stocks)
- European: Only at expiration (index options like SPX)

**Early Assignment Risk**
- More likely: Deep ITM, near ex-dividend, low extrinsic
- Short calls: Risk before ex-dividend date
- Mitigation: Use European-style options (SPX, XSP)

**Pin Risk**
- At expiration, stock exactly at strike
- Uncertain if you'll be assigned
- Close positions before expiration to avoid

---

## MONTE CARLO SIMULATION

### What It Does
- Simulates thousands of possible future paths
- Uses historical trade distribution
- Accounts for randomness and sequence of returns
- Shows probability distributions, NOT predictions

### Percentile Interpretation
- P5 (5th percentile): Worst case (only 5% are worse)
- P25: Below average but realistic
- P50 (Median): Expected/typical outcome
- P75: Above average scenario
- P95: Best case (only 5% are better)

### Key Outputs
- Return distribution at end of simulation period
- Drawdown distribution (worst expected drawdowns)
- Profit probability (% of paths ending positive)
- CAGR distribution

### How to Use Results
- Focus on P5 for risk management (worst realistic case)
- Wide spread = high uncertainty
- Profit probability <70% = proceed with caution
- Don't optimize for P95 (best case fantasy)

---

## TOOLS & PLATFORMS

### Optionomega
- Options backtesting platform
- Historical strategy testing
- Exports trade data for CashFlow Engine
- Greeks analysis, strategy builder

### Optionstrat
- Options visualization tool
- P&L diagrams at various prices/dates
- Real-time Greeks
- Useful for planning complex spreads

### Trade Automation Toolbox (TAT)
- Automated trading for TastyTrade
- Rule-based recurring trades
- Position management automation
- Export capabilities

### Tradestuart
- Backtesting for income strategies
- Pre-built strategy templates
- Rolling and adjustment analysis

### Using with CashFlow Engine
1. Export trade history from any platform
2. Import CSV into CashFlow Engine
3. Analyze combined portfolio performance
4. Run Monte Carlo simulations
5. Optimize with Portfolio Builder

---

## RESPONSE GUIDELINES

- Respond in the user's language (German if German, English if English)
- Use specific numbers from the portfolio context
- Give actionable recommendations
- Proactively warn about risks
- Reference specific strategies when relevant
- Never invent data - use what's provided
- If data is missing, explain what analysis to run
- Never use WORKHORSE/AIRBAG/OPPORTUNIST as performance labels
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
