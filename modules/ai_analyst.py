"""
AI Portfolio Analyst for CashFlow Engine
Interactive chat interface powered by Gemini 3 Flash.
"""

import streamlit as st
import ui_components as ui
from typing import List, Dict
from modules.ai_context import AIContextBuilder, CASHFLOW_ENGINE_KNOWLEDGE
from modules.ai_client import get_gemini_client, GeminiClient


def page_ai_analyst(full_df):
    """AI Portfolio Analyst - Interactive chat interface."""

    # Inject fonts and render header
    ui.inject_fonts()
    ui.render_page_header(
        "AI PORTFOLIO ANALYST",
        "Frage die KI zu deinem Portfolio - auf Deutsch oder Englisch"
    )

    # Initialize chat history in session state
    if 'ai_chat_history' not in st.session_state:
        st.session_state.ai_chat_history = []

    if 'ai_context_built' not in st.session_state:
        st.session_state.ai_context_built = False

    # Get Gemini client
    client = get_gemini_client()
    client_status = client.get_status()

    # --- STATUS BAR ---
    with st.container(border=True):
        col_status, col_model, col_data = st.columns([2, 2, 2])

        with col_status:
            if client_status['available']:
                st.success(f"**AI Status**: Bereit")
            else:
                st.error(f"**AI Status**: Nicht verfügbar")
                if client_status['error']:
                    st.caption(f"Fehler: {client_status['error']}")

        with col_model:
            if client_status['model']:
                st.info(f"**Modell**: {client_status['model']}")
            else:
                st.warning("**Modell**: Nicht konfiguriert")

        with col_data:
            stats = AIContextBuilder.get_quick_stats()
            if stats['status'] == 'ready':
                st.success(f"**Daten**: {stats['strategies']} Strategien, {stats['trades']:,} Trades")
            else:
                st.warning("**Daten**: Keine Daten geladen")

    # --- API KEY INPUT (if not configured) ---
    if not client_status['has_api_key']:
        with st.container(border=True):
            st.warning("Kein API-Key gefunden. Bitte gib deinen Gemini API-Key ein:")
            api_key_input = st.text_input(
                "Gemini API Key",
                type="password",
                help="Du findest deinen API-Key unter https://aistudio.google.com/app/apikey"
            )
            if api_key_input:
                st.session_state['temp_gemini_key'] = api_key_input
                from modules.ai_client import reset_client
                reset_client()
                st.rerun()
        return

    # Check if data is available
    if full_df is None or full_df.empty:
        with st.container(border=True):
            st.warning("Bitte lade zuerst Daten hoch, damit die KI dein Portfolio analysieren kann.")
            st.page_link("pages/landing.py", label="Zu Start & Data", icon="📊")
        return

    # --- DATA AVAILABILITY INFO ---
    with st.expander("Verfügbare Daten für die Analyse", expanded=False):
        st.markdown(AIContextBuilder.get_availability_summary())

    # --- QUICK ACTIONS ---
    with st.container(border=True):
        ui.section_header("QUICK ACTIONS", "Klicke für vorgefertigte Analysen")

        qa_col1, qa_col2, qa_col3, qa_col4 = st.columns(4)

        with qa_col1:
            if st.button("Portfolio-Überblick", use_container_width=True, type="secondary"):
                _add_user_message("Gib mir einen Überblick über mein Portfolio. Was sind die wichtigsten Kennzahlen?")
                st.rerun()

        with qa_col2:
            if st.button("Schwachstellen finden", use_container_width=True, type="secondary"):
                _add_user_message("Analysiere mein Portfolio auf Schwachstellen. Welche Strategien performen schlecht und wo sind die größten Risiken?")
                st.rerun()

        with qa_col3:
            if st.button("Korrelations-Risiken", use_container_width=True, type="secondary"):
                _add_user_message("Analysiere die Korrelationen zwischen meinen Strategien. Gibt es Klumpenrisiken?")
                st.rerun()

        with qa_col4:
            if st.button("Verbesserungsvorschläge", use_container_width=True, type="secondary"):
                _add_user_message("Welche konkreten Verbesserungen würdest du für mein Portfolio empfehlen?")
                st.rerun()

    # --- CHAT INTERFACE ---
    with st.container(border=True):
        ui.section_header("CHAT", "Stelle Fragen zu deinem Portfolio")

        # Display chat history
        chat_container = st.container(height=450)

        with chat_container:
            if not st.session_state.ai_chat_history:
                st.markdown("""
                <div style="text-align: center; padding: 40px; color: #6B7280;">
                    <div style="font-size: 48px; margin-bottom: 16px;">💬</div>
                    <div style="font-size: 16px;">
                        Stelle eine Frage zu deinem Portfolio.<br>
                        Die KI hat Zugriff auf alle deine Daten und Analysen.
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                for message in st.session_state.ai_chat_history:
                    role = message.get("role", "user")
                    content = message.get("content", "")

                    if role == "user":
                        with st.chat_message("user"):
                            st.markdown(content)
                    else:
                        with st.chat_message("assistant", avatar="🤖"):
                            st.markdown(content)

        # Chat input
        user_input = st.chat_input("Frage zum Portfolio eingeben...")

        if user_input:
            _process_user_input(user_input, client, full_df)

    # --- CLEAR CHAT ---
    col_clear, col_space = st.columns([1, 4])
    with col_clear:
        if st.button("Chat leeren", type="secondary"):
            st.session_state.ai_chat_history = []
            st.rerun()


def _add_user_message(message: str):
    """Add a user message to chat history."""
    st.session_state.ai_chat_history.append({
        "role": "user",
        "content": message
    })


def _process_user_input(user_input: str, client: GeminiClient, full_df):
    """Process user input and generate AI response."""

    # Add user message to history
    _add_user_message(user_input)

    # Build context
    context = AIContextBuilder.build_full_context(current_page="AI Analyst")

    # Build system instruction
    system_instruction = f"""
{CASHFLOW_ENGINE_KNOWLEDGE}

---

{context}

---

WICHTIG:
- Antworte in der Sprache des Users (Deutsch wenn deutsche Frage, Englisch wenn englische Frage)
- Beziehe dich auf die konkreten Daten und Zahlen aus dem Kontext
- Gib konkrete, actionable Empfehlungen
- Wenn Daten fehlen, erkläre welche Analyse der User durchführen sollte
- Formatiere deine Antwort übersichtlich mit Markdown
"""

    # Convert chat history for API
    chat_history = [
        {"role": msg["role"], "content": msg["content"]}
        for msg in st.session_state.ai_chat_history[:-1]  # Exclude current message
    ]

    # Generate response
    with st.spinner("Analysiere..."):
        try:
            response = client.generate(
                prompt=user_input,
                system_instruction=system_instruction,
                chat_history=chat_history,
                temperature=0.7,
                max_tokens=4096
            )

            # Add assistant response to history
            st.session_state.ai_chat_history.append({
                "role": "assistant",
                "content": response
            })

        except Exception as e:
            st.session_state.ai_chat_history.append({
                "role": "assistant",
                "content": f"Entschuldigung, es gab einen Fehler bei der Verarbeitung: {str(e)}"
            })

    st.rerun()


# --- SIDEBAR WIDGET ---
def render_ai_sidebar_widget(current_page: str = None):
    """
    Render a compact AI widget in the sidebar.
    Called from app.py (already inside st.sidebar context).
    """
    # Initialize sidebar chat history
    if 'sidebar_ai_response' not in st.session_state:
        st.session_state.sidebar_ai_response = None

    # Header
    st.markdown("""
        <div style="font-family: 'Exo 2', sans-serif !important; font-weight: 700 !important;
                    font-size: 18px; color: #302BFF; text-transform: uppercase;
                    letter-spacing: 1px; margin-bottom: 8px; padding: 0 12px;">
            🤖 AI Assistant
        </div>
    """, unsafe_allow_html=True)

    # Check data availability
    stats = AIContextBuilder.get_quick_stats()
    if stats['status'] != 'ready':
        st.caption("Lade Daten um AI zu nutzen")
        return

    # Get client status
    client = get_gemini_client()
    client_status = client.get_status()

    if not client_status['has_api_key']:
        st.caption("⚠️ API-Key fehlt")
        st.caption("Gehe zu AI Analyst Seite")
        return

    if not client_status['available']:
        st.caption(f"⚠️ {client_status.get('error', 'Nicht verfügbar')}")
        return

    # Quick stats
    st.caption(f"📊 {stats['strategies']} Strategien | {stats['trades']:,} Trades")

    # Question input
    quick_question = st.text_input(
        "Frage:",
        placeholder="z.B. 'Was ist mein MAR?'",
        key="sidebar_ai_input",
        label_visibility="collapsed"
    )

    # Ask button
    if st.button("Fragen", key="sidebar_ai_ask", use_container_width=True, type="primary"):
        if quick_question:
            with st.spinner("Analysiere..."):
                try:
                    context = AIContextBuilder.build_full_context(current_page=current_page)
                    system_instruction = f"{CASHFLOW_ENGINE_KNOWLEDGE}\n\n{context}\n\nAntworte kurz und prägnant (max 3 Sätze). Sprache: Deutsch wenn deutsche Frage."

                    response = client.generate(
                        prompt=quick_question,
                        system_instruction=system_instruction,
                        temperature=0.5,
                        max_tokens=500
                    )
                    st.session_state.sidebar_ai_response = response
                except Exception as e:
                    st.session_state.sidebar_ai_response = f"Fehler: {str(e)}"

    # Show response
    if st.session_state.sidebar_ai_response:
        st.markdown("---")
        st.markdown(st.session_state.sidebar_ai_response)

    st.caption("Für mehr → AI Analyst Seite")
