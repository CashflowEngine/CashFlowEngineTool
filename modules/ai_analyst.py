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
        "Ask the AI about your portfolio - in English or German"
    )

    # Initialize chat history in session state
    if 'ai_chat_history' not in st.session_state:
        st.session_state.ai_chat_history = []

    if 'ai_context_built' not in st.session_state:
        st.session_state.ai_context_built = False

    # Initialize pending quick action
    if 'pending_quick_action' not in st.session_state:
        st.session_state.pending_quick_action = None

    # Get Gemini client
    client = get_gemini_client()
    client_status = client.get_status()

    # --- STATUS BAR ---
    with st.container(border=True):
        col_status, col_model, col_data = st.columns([2, 2, 2])

        with col_status:
            if client_status['available']:
                st.success("**AI Status**: Ready")
            else:
                st.error("**AI Status**: Not available")
                if client_status['error']:
                    st.caption(f"Error: {client_status['error']}")

        with col_model:
            if client_status['model']:
                st.info(f"**Model**: {client_status['model']}")
            else:
                st.warning("**Model**: Not configured")

        with col_data:
            stats = AIContextBuilder.get_quick_stats()
            if stats['status'] == 'ready':
                st.success(f"**Data**: {stats['strategies']} strategies, {stats['trades']:,} trades")
            else:
                st.warning("**Data**: No data loaded")

    # --- API KEY INPUT (if not configured) ---
    if not client_status['has_api_key']:
        with st.container(border=True):
            st.warning("No API key found. Please enter your Gemini API key:")
            api_key_input = st.text_input(
                "Gemini API Key",
                type="password",
                help="You can find your API key at https://aistudio.google.com/app/apikey"
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
            st.warning("Please upload data first so the AI can analyze your portfolio.")
            st.page_link("pages/landing.py", label="Go to Start & Data", icon="📊")
        return

    # --- DATA AVAILABILITY INFO ---
    with st.expander("Available Data for Analysis", expanded=False):
        st.markdown(AIContextBuilder.get_availability_summary())

    # --- QUICK ACTIONS ---
    with st.container(border=True):
        ui.section_header("QUICK ACTIONS", "Click a link for instant analysis")

        # Define quick actions with categories
        quick_actions = {
            "Portfolio Overview": [
                ("📊 Portfolio Summary", "Give me a comprehensive overview of my portfolio. What are the key metrics, total P&L, and overall health?"),
                ("📈 Best Performing Strategies", "Which strategies in my portfolio are performing best? Rank them by MAR ratio and explain why they're successful."),
                ("📉 Underperforming Strategies", "Identify the worst performing strategies in my portfolio. What's dragging down performance?"),
            ],
            "Risk Analysis": [
                ("⚠️ Find Weaknesses", "Analyze my portfolio for weaknesses. Which strategies perform poorly and where are the biggest risks?"),
                ("🔗 Correlation Risks", "Analyze the correlations between my strategies. Are there cluster risks I should be aware of?"),
                ("💥 Drawdown Analysis", "What are my maximum drawdowns? Which strategies have the worst drawdown characteristics?"),
                ("📊 Risk-Adjusted Returns", "Compare the risk-adjusted returns (Sharpe, Sortino, MAR) across all my strategies."),
            ],
            "Optimization": [
                ("💡 Improvement Suggestions", "What concrete improvements would you recommend for my portfolio?"),
                ("⚖️ Position Sizing Review", "Analyze my position sizing. Am I over- or under-allocated to any strategies?"),
                ("🎯 Kelly Criterion Analysis", "Based on my win rates and profit factors, what would optimal Kelly Criterion sizing suggest?"),
                ("🔄 Diversification Check", "How well diversified is my portfolio? What's missing for better risk distribution?"),
            ],
            "Monte Carlo & Projections": [
                ("🎲 Monte Carlo Summary", "Summarize my Monte Carlo simulation results. What are the probability distributions for future returns?"),
                ("📉 Worst Case Scenarios", "Based on Monte Carlo simulations, what are the worst-case scenarios I should prepare for?"),
                ("🎯 Probability of Targets", "What's the probability of reaching my target returns based on historical performance?"),
            ],
        }

        # Render quick actions as clickable text links
        for category, actions in quick_actions.items():
            st.markdown(f"**{category}**")
            cols = st.columns(len(actions))
            for idx, (label, prompt) in enumerate(actions):
                with cols[idx]:
                    if st.button(label, key=f"qa_{category}_{idx}", use_container_width=True, type="secondary"):
                        st.session_state.pending_quick_action = prompt
                        st.rerun()
            st.markdown("")  # Spacer

    # --- PROCESS PENDING QUICK ACTION ---
    if st.session_state.pending_quick_action and client_status['available']:
        pending_prompt = st.session_state.pending_quick_action
        st.session_state.pending_quick_action = None
        _process_user_input(pending_prompt, client, full_df)

    # --- CHAT INTERFACE ---
    with st.container(border=True):
        ui.section_header("CHAT", "Ask questions about your portfolio")

        # Display chat history
        chat_container = st.container(height=450)

        with chat_container:
            if not st.session_state.ai_chat_history:
                st.markdown("""
                <div style="text-align: center; padding: 40px; color: #6B7280;">
                    <div style="font-size: 48px; margin-bottom: 16px;">💬</div>
                    <div style="font-size: 16px;">
                        Ask a question about your portfolio.<br>
                        The AI has access to all your data and analyses.
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                for message in st.session_state.ai_chat_history:
                    role = message.get("role", "user")
                    content = message.get("content", "")

                    if role == "user":
                        with st.chat_message("user", avatar="👤"):
                            st.markdown(content)
                    else:
                        with st.chat_message("assistant", avatar="🤖"):
                            st.markdown(content)

        # Chat input
        user_input = st.chat_input("Enter your question...")

        if user_input:
            _process_user_input(user_input, client, full_df)

    # --- CLEAR CHAT ---
    col_clear, col_space = st.columns([1, 4])
    with col_clear:
        if st.button("Clear Chat", type="secondary"):
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

IMPORTANT:
- Respond in the user's language (German if German question, English if English question)
- Reference the specific data and numbers from the context
- Provide concrete, actionable recommendations
- If data is missing, explain which analysis the user should run
- Format your response clearly with Markdown
"""

    # Convert chat history for API
    chat_history = [
        {"role": msg["role"], "content": msg["content"]}
        for msg in st.session_state.ai_chat_history[:-1]  # Exclude current message
    ]

    # Generate response
    with st.spinner("Analyzing..."):
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
                "content": f"Sorry, there was an error processing your request: {str(e)}"
            })

    st.rerun()
