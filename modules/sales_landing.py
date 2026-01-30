import streamlit as st
import os
import base64

# --- CORPORATE IDENTITY COLORS ---
COLOR_BLUE = "#302BFF"   # Electric Blue
COLOR_TEAL = "#00D2BE"   # Turbo Teal (Profit)
COLOR_CORAL = "#FF2E4D"  # Radical Coral (Loss)
COLOR_GREY = "#4B5563"   # Space Grey
COLOR_ICE = "#F0F4FF"    # Ice Tint (Backgrounds)
COLOR_AMBER = "#FFAB00"  # Amber Flux (Warning)
COLOR_PURPLE = "#7B2BFF" # Electric Violet (Hover)

def _get_logo_base64():
    """Load logo as base64 for reliable rendering."""
    logo_file = "CashflowEnginelogo.png"
    if os.path.exists(logo_file):
        try:
            with open(logo_file, "rb") as f:
                data = f.read()
                if data[:4] == b'\x89PNG':
                    return base64.b64encode(data).decode()
        except Exception:
            pass
    return None

def show_sales_landing():
    """Render the sales landing page."""

    logo_b64 = _get_logo_base64()
    logo_html = ""
    if logo_b64:
        logo_html = f'<img src="data:image/png;base64,{logo_b64}" width="280" alt="Cashflow Engine Logo" />'
    else:
        logo_html = f'<div style="font-family: \'Exo 2\', sans-serif; font-weight: 800; font-size: 32px; color: {COLOR_BLUE};">CASHFLOW ENGINE</div>'

    # Full page styling
    st.markdown(f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Exo+2:wght@400;500;600;700;800;900&family=Poppins:wght@300;400;500;600;700&display=swap');

        .sales-page {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }}

        .hero-section {{
            text-align: center;
            padding: 60px 20px 40px;
        }}

        .hero-title {{
            font-family: 'Exo 2', sans-serif;
            font-weight: 800;
            font-size: 2.8rem;
            color: {COLOR_GREY};
            text-transform: uppercase;
            letter-spacing: 1px;
            margin: 30px 0 16px;
            line-height: 1.2;
        }}

        .hero-subtitle {{
            font-family: 'Poppins', sans-serif;
            font-size: 1.2rem;
            color: #6B7280;
            max-width: 700px;
            margin: 0 auto 30px;
            line-height: 1.6;
        }}

        .section-title {{
            font-family: 'Exo 2', sans-serif;
            font-weight: 800;
            font-size: 1.8rem;
            color: {COLOR_GREY};
            text-transform: uppercase;
            letter-spacing: 1px;
            text-align: center;
            margin: 60px 0 40px;
        }}

        .section-subtitle {{
            font-family: 'Poppins', sans-serif;
            font-size: 1rem;
            color: #6B7280;
            text-align: center;
            max-width: 600px;
            margin: -30px auto 40px;
        }}

        .features-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(340px, 1fr));
            gap: 24px;
            margin: 40px 0;
        }}

        .feature-card {{
            background: #FFFFFF;
            border: 1px solid #E5E7EB;
            border-radius: 12px;
            padding: 28px;
            transition: all 0.3s ease;
            position: relative;
        }}

        .feature-card:hover {{
            border-color: {COLOR_BLUE};
            box-shadow: 0 8px 24px rgba(48, 43, 255, 0.1);
            transform: translateY(-2px);
        }}

        .feature-icon {{
            font-size: 36px;
            margin-bottom: 16px;
        }}

        .feature-title {{
            font-family: 'Exo 2', sans-serif;
            font-weight: 700;
            font-size: 1.1rem;
            color: {COLOR_GREY};
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 12px;
        }}

        .feature-desc {{
            font-family: 'Poppins', sans-serif;
            font-size: 0.95rem;
            color: #6B7280;
            line-height: 1.6;
        }}

        .feature-list {{
            margin-top: 16px;
            padding-left: 0;
            list-style: none;
        }}

        .feature-list li {{
            font-family: 'Poppins', sans-serif;
            font-size: 0.85rem;
            color: #6B7280;
            padding: 4px 0 4px 20px;
            position: relative;
        }}

        .feature-list li::before {{
            content: "\\2713";
            color: {COLOR_TEAL};
            font-weight: 700;
            position: absolute;
            left: 0;
        }}

        .badge {{
            display: inline-block;
            font-size: 10px;
            font-weight: 600;
            padding: 3px 8px;
            border-radius: 4px;
            text-transform: uppercase;
            margin-left: 8px;
            vertical-align: middle;
        }}

        .badge-beta {{
            background-color: #FEF3C7;
            color: #D97706;
        }}

        .badge-coming {{
            background-color: #E5E7EB;
            color: #6B7280;
        }}

        .pricing-section {{
            background: {COLOR_ICE};
            border-radius: 16px;
            padding: 50px 30px;
            margin: 60px 0;
            text-align: center;
        }}

        .pricing-cards {{
            display: flex;
            justify-content: center;
            gap: 30px;
            flex-wrap: wrap;
            margin-top: 40px;
        }}

        .pricing-card {{
            background: #FFFFFF;
            border: 2px solid #E5E7EB;
            border-radius: 12px;
            padding: 32px;
            width: 280px;
            text-align: center;
            position: relative;
        }}

        .pricing-card.featured {{
            border-color: {COLOR_BLUE};
            box-shadow: 0 8px 32px rgba(48, 43, 255, 0.15);
        }}

        .pricing-label {{
            font-family: 'Exo 2', sans-serif;
            font-weight: 700;
            font-size: 1rem;
            color: {COLOR_GREY};
            text-transform: uppercase;
            margin-bottom: 16px;
        }}

        .pricing-amount {{
            font-family: 'Exo 2', sans-serif;
            font-weight: 800;
            font-size: 2.5rem;
            color: {COLOR_BLUE};
        }}

        .pricing-period {{
            font-family: 'Poppins', sans-serif;
            font-size: 0.9rem;
            color: #9CA3AF;
        }}

        .pricing-original {{
            font-family: 'Poppins', sans-serif;
            font-size: 1rem;
            color: #9CA3AF;
            text-decoration: line-through;
            margin-top: 8px;
        }}

        .pricing-savings {{
            font-family: 'Poppins', sans-serif;
            font-size: 0.85rem;
            color: {COLOR_TEAL};
            font-weight: 600;
            margin-top: 4px;
        }}

        .launch-banner {{
            background: linear-gradient(135deg, {COLOR_BLUE} 0%, {COLOR_PURPLE} 100%);
            color: #FFFFFF;
            padding: 16px 24px;
            border-radius: 8px;
            margin-bottom: 30px;
            display: inline-block;
        }}

        .launch-banner-text {{
            font-family: 'Exo 2', sans-serif;
            font-weight: 700;
            font-size: 1.1rem;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}

        .philosophy-section {{
            background: #FFFFFF;
            border: 1px solid #E5E7EB;
            border-radius: 12px;
            padding: 40px;
            margin: 60px 0;
            text-align: center;
        }}

        .philosophy-text {{
            font-family: 'Poppins', sans-serif;
            font-size: 1.05rem;
            color: #6B7280;
            line-height: 1.8;
            max-width: 800px;
            margin: 0 auto;
        }}

        .cta-section {{
            text-align: center;
            padding: 40px 20px 60px;
        }}

        .cta-button {{
            display: inline-block;
            background-color: {COLOR_BLUE};
            color: #FFFFFF;
            font-family: 'Poppins', sans-serif;
            font-weight: 600;
            font-size: 1rem;
            text-transform: uppercase;
            letter-spacing: 1px;
            padding: 16px 48px;
            border-radius: 8px;
            text-decoration: none;
            box-shadow: 0 4px 12px rgba(48, 43, 255, 0.3);
            transition: all 0.3s ease;
        }}

        .cta-button:hover {{
            background-color: #2521c9;
            box-shadow: 0 6px 20px rgba(48, 43, 255, 0.4);
            transform: translateY(-2px);
        }}

        .metrics-highlight {{
            display: flex;
            justify-content: center;
            gap: 40px;
            flex-wrap: wrap;
            margin: 40px 0;
        }}

        .metric-item {{
            text-align: center;
        }}

        .metric-value {{
            font-family: 'Exo 2', sans-serif;
            font-weight: 800;
            font-size: 2rem;
            color: {COLOR_BLUE};
        }}

        .metric-label {{
            font-family: 'Poppins', sans-serif;
            font-size: 0.85rem;
            color: #6B7280;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}

        .disclaimer {{
            font-family: 'Poppins', sans-serif;
            font-size: 0.75rem;
            color: #9CA3AF;
            text-align: center;
            margin-top: 60px;
            padding: 20px;
            border-top: 1px solid #E5E7EB;
            line-height: 1.6;
        }}
    </style>
    """, unsafe_allow_html=True)

    # Main content
    st.markdown(f"""
    <div class="sales-page">

        <!-- Hero Section -->
        <div class="hero-section">
            {logo_html}
            <h1 class="hero-title">Options Trading Analytics &<br>Backtesting Platform</h1>
            <p class="hero-subtitle">
                Backteste deine 0DTE Strategien, simuliere Portfolio-Risiken mit Monte Carlo Simulationen
                und optimiere deine Iron Condor & Credit Spread Performance - basierend auf echten Daten, nicht auf Bauchgefühl.
            </p>

            <!-- SEO Keywords (hidden but crawlable) -->
            <p style="position: absolute; left: -9999px; opacity: 0;">
                Options Backtesting Software | 0DTE Options Trading | Iron Condor Strategy |
                Monte Carlo Simulation Trading | Portfolio Analytics | Credit Spread Analysis |
                Automated Options Trading | Trading Journal | Options Performance Tracker |
                SPX SPY QQQ Options | Wheel Strategy | Options Risk Management
            </p>

            <div class="metrics-highlight">
                <div class="metric-item">
                    <div class="metric-value">8+</div>
                    <div class="metric-label">Analyse-Module</div>
                </div>
                <div class="metric-item">
                    <div class="metric-value">30+</div>
                    <div class="metric-label">Metriken</div>
                </div>
                <div class="metric-item">
                    <div class="metric-value">1000+</div>
                    <div class="metric-label">Simulationen</div>
                </div>
            </div>
        </div>

        <!-- Features Section -->
        <h2 class="section-title">Professionelle Options Trading Tools</h2>
        <p class="section-subtitle">
            Backtesting, Monte Carlo Simulation, Portfolio Analytics und mehr -
            entwickelt für 0DTE Trader, Iron Condor Strategien und Credit Spread Optimierung.
        </p>

        <div class="features-grid">

            <!-- Portfolio Analytics -->
            <div class="feature-card">
                <div class="feature-icon">📊</div>
                <div class="feature-title">Portfolio Analytics & Performance Tracking</div>
                <div class="feature-desc">
                    Professionelle Trading Performance Analyse für Options-Trader. Tracke deine Backtest-
                    und Live-Ergebnisse mit institutionellen Metriken.
                </div>
                <ul class="feature-list">
                    <li>CAGR, Volatilität, Sharpe & Sortino Ratio</li>
                    <li>Maximum Drawdown Analyse (% und absolut)</li>
                    <li>MAR & MART Ratio für Risk-Adjusted Returns</li>
                    <li>Monatliche Return-Matrix</li>
                    <li>Equity-Kurve mit SPX-Benchmark</li>
                    <li>0DTE & Multi-Strategie Filter</li>
                </ul>
            </div>

            <!-- Portfolio Builder -->
            <div class="feature-card">
                <div class="feature-icon">🏗️</div>
                <div class="feature-title">Portfolio Builder & Optimierung</div>
                <div class="feature-desc">
                    Konstruiere und optimiere dein Multi-Strategie Options Portfolio. Ideal für
                    Iron Condor, Credit Spread und Wheel Strategy Kombinationen.
                </div>
                <ul class="feature-list">
                    <li>Interaktive Kontrakt-Allokation</li>
                    <li>Kelly Criterion Position Sizing</li>
                    <li>Margin-Simulation</li>
                    <li>Iron Condor & Credit Spread Portfolio Mix</li>
                    <li>Kapitaleffizienz-Analyse</li>
                </ul>
            </div>

            <!-- Monte Carlo -->
            <div class="feature-card">
                <div class="feature-icon">🎲</div>
                <div class="feature-title">Monte Carlo Simulation & Stresstest</div>
                <div class="feature-desc">
                    Portfolio Stresstest mit Monte Carlo Simulation. Analysiere Drawdown-
                    Wahrscheinlichkeiten und CVaR für deine 0DTE und Options-Strategien.
                </div>
                <ul class="feature-list">
                    <li>Tausende randomisierte Trading-Szenarien</li>
                    <li>Black-Swan-Event-Simulation</li>
                    <li>Maximum Drawdown Wahrscheinlichkeiten</li>
                    <li>CVaR & Risk-at-Value Analyse</li>
                    <li>Konfidenzintervalle für Returns</li>
                    <li>1-120 Monate Simulationszeitraum</li>
                </ul>
            </div>

            <!-- Reality Check -->
            <div class="feature-card">
                <div class="feature-icon">🔍</div>
                <div class="feature-title">Live vs Backtest Vergleich</div>
                <div class="feature-desc">
                    Trading Journal für Options-Trader. Vergleiche Live-Execution mit Backtest-
                    Ergebnissen und identifiziere Slippage bei 0DTE und Credit Spreads.
                </div>
                <ul class="feature-list">
                    <li>Live Trading vs. Backtest Analyse</li>
                    <li>Automatisches Strategie-Matching</li>
                    <li>Slippage & Fill-Rate Tracking</li>
                    <li>Abweichungs-Heatmaps</li>
                    <li>Execution-Quality Score</li>
                </ul>
            </div>

            <!-- MEIC Deep Dive -->
            <div class="feature-card">
                <div class="feature-icon">🔬</div>
                <div class="feature-title">Iron Condor Analyse (MEIC)</div>
                <div class="feature-desc">
                    Spezialisierte Backtesting-Analyse für Iron Condor Strategien.
                    Optimiere Entry-Zeiten, Delta-Settings und 0DTE Parameter.
                </div>
                <ul class="feature-list">
                    <li>Iron Condor Entry-Time Analyse</li>
                    <li>Performance Heatmaps nach Parameter</li>
                    <li>Delta & Strike Optimierung</li>
                    <li>VIX & Marktbedingungs-Korrelation</li>
                    <li>0DTE vs Multi-Day Vergleich</li>
                </ul>
            </div>

            <!-- MEIC Optimizer -->
            <div class="feature-card">
                <div class="feature-icon">⚡</div>
                <div class="feature-title">MEIC Optimizer <span class="badge badge-beta">Beta</span></div>
                <div class="feature-desc">
                    Option Omega Signalgenerierung und Parameter-Optimierung.
                    Analysiere und vergleiche verschiedene Backtest-Konfigurationen.
                </div>
                <ul class="feature-list">
                    <li>Signal-Generierung</li>
                    <li>Parameter-Set-Vergleich</li>
                    <li>Batch-Analyse</li>
                    <li>CSV-Export für externes Backtesting</li>
                </ul>
            </div>

            <!-- AI Analyst -->
            <div class="feature-card">
                <div class="feature-icon">🤖</div>
                <div class="feature-title">AI Analyst <span class="badge badge-coming">Coming Soon</span></div>
                <div class="feature-desc">
                    Stelle Fragen zu deinem Portfolio in natürlicher Sprache.
                    Der KI-Analyst identifiziert Muster und gibt Verbesserungsvorschläge.
                </div>
                <ul class="feature-list">
                    <li>Natural Language Queries</li>
                    <li>Automatische Performance-Analyse</li>
                    <li>Risikofaktor-Identifikation</li>
                    <li>Mehrsprachige Unterstützung</li>
                </ul>
            </div>

            <!-- Data Management -->
            <div class="feature-card">
                <div class="feature-icon">💾</div>
                <div class="feature-title">Daten-Management</div>
                <div class="feature-desc">
                    Importiere deine Daten einfach per CSV oder Excel.
                    Speichere Analysen in der Cloud und greife jederzeit darauf zu.
                </div>
                <ul class="feature-list">
                    <li>CSV & XLSX Import</li>
                    <li>Multi-File-Unterstützung</li>
                    <li>Cloud-basierte Speicherung</li>
                    <li>Analyse-Management</li>
                    <li>Automatische Datenbereinigung</li>
                </ul>
            </div>

        </div>

        <!-- Philosophy Section -->
        <div class="philosophy-section">
            <h2 class="section-title" style="margin-top: 0;">Von Options-Tradern für Options-Trader</h2>
            <p class="philosophy-text">
                Die Cashflow Engine wurde von aktiven 0DTE und Iron Condor Tradern entwickelt.
                Wir glauben an datengetriebene Entscheidungen statt Bauchgefühl.
                Jedes Backtesting-Tool, jede Monte Carlo Simulation und jede Performance-Analyse dient einem Zweck:
                Dir zu helfen, deine Options-Strategien objektiv zu bewerten und fundierte Entscheidungen zu treffen.
                <br><br>
                Keine übertriebenen Versprechen - nur professionelle Analytics-Tools
                für SPX, SPY und QQQ Options-Trader, die ihre Credit Spread und Iron Condor Performance verbessern wollen.
            </p>
        </div>

        <!-- Pricing Section -->
        <div class="pricing-section">
            <div class="launch-banner">
                <span class="launch-banner-text">Launch-Angebot: Kostenloser Zugang</span>
            </div>

            <h2 class="section-title" style="margin-top: 20px; color: {COLOR_GREY};">Preisgestaltung</h2>

            <div class="pricing-cards">

                <div class="pricing-card">
                    <div class="pricing-label">Monatlich</div>
                    <div class="pricing-amount">0 €</div>
                    <div class="pricing-period">pro Monat</div>
                    <div class="pricing-original">regulär 4,97 €/Monat</div>
                    <div class="pricing-savings">Launch-Preis</div>
                </div>

                <div class="pricing-card featured">
                    <div class="pricing-label">Jährlich</div>
                    <div class="pricing-amount">0 €</div>
                    <div class="pricing-period">pro Jahr</div>
                    <div class="pricing-original">regulär 47 €/Jahr</div>
                    <div class="pricing-savings">Launch-Preis</div>
                </div>

            </div>

            <p style="font-family: 'Poppins', sans-serif; font-size: 0.9rem; color: #6B7280; margin-top: 30px;">
                Während der Launch-Phase ist die Cashflow Engine vollständig kostenlos nutzbar.<br>
                Alle Features, keine Einschränkungen.
            </p>
        </div>

        <!-- CTA Section -->
        <div class="cta-section">
            <h2 class="section-title">Starte jetzt mit Options Backtesting & Analytics</h2>
            <p style="font-family: 'Poppins', sans-serif; font-size: 1rem; color: #6B7280; margin-bottom: 30px;">
                Registriere dich kostenlos und analysiere deine 0DTE, Iron Condor und Credit Spread Strategien
                mit professionellen Tools.
            </p>
        </div>

        <!-- Disclaimer -->
        <div class="disclaimer">
            <strong>HINWEIS:</strong> Diese Anwendung dient ausschließlich zu Bildungs- und Informationszwecken.
            Sie stellt keine Finanzberatung dar. Der Handel mit Optionen birgt erhebliche Risiken und ist nicht
            für alle Anleger geeignet. Vergangene Performance ist kein Indikator für zukünftige Ergebnisse.
        </div>

    </div>
    """, unsafe_allow_html=True)

    # Add actual Streamlit button for navigation
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("JETZT KOSTENLOS STARTEN", use_container_width=True, type="primary"):
            st.session_state.show_sales_page = False
            st.rerun()
