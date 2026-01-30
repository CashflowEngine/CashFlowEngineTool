"""
AI Portfolio Analyst for CashFlow Engine
Interactive chat interface powered by Gemini 3 Flash.
"""

import streamlit as st
import ui_components as ui
from typing import List, Dict
from modules.ai_context import AIContextBuilder, CASHFLOW_ENGINE_KNOWLEDGE
from modules.ai_client import get_gemini_client, GeminiClient, get_usage_display, check_usage_limit


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
        col_status, col_model, col_data, col_usage = st.columns([2, 2, 2, 2])

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

        with col_usage:
            usage = get_usage_display()
            if usage['percent_used'] >= 90:
                st.error(f"**Budget**: ${usage['remaining']:.2f} left")
            elif usage['percent_used'] >= 70:
                st.warning(f"**Budget**: ${usage['remaining']:.2f} left")
            else:
                st.info(f"**Budget**: ${usage['remaining']:.2f} / ${usage['limit']:.2f}")

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

    # --- QUICK ACTIONS as text links ---
    st.markdown("""
    <style>
    .quick-action-link {
        color: #302BFF !important;
        text-decoration: none;
        cursor: pointer;
        font-size: 14px;
        padding: 2px 0;
        display: inline-block;
    }
    .quick-action-link:hover {
        text-decoration: underline;
    }
    .quick-action-category {
        font-weight: 600;
        font-size: 13px;
        color: #6B7280;
        margin-top: 12px;
        margin-bottom: 6px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    </style>
    """, unsafe_allow_html=True)

    with st.container(border=True):
        ui.section_header("QUICK ACTIONS", "Click a link for instant analysis")

        # Define quick actions with categories
        quick_actions = {
            "Portfolio Overview": [
                ("Portfolio Summary", "Give me a comprehensive overview of my portfolio. What are the key metrics, total P&L, and overall health?"),
                ("Top Performers by P&L", "Which strategies have the highest total P&L? List the top 5 and explain their characteristics."),
                ("Top Performers by MAR", "Which strategies have the best MAR ratio? Rank them and explain why they're efficient."),
                ("Underperforming Strategies", "Identify the worst performing strategies. What's dragging down performance?"),
            ],
            "Risk Analysis": [
                ("Find Portfolio Weaknesses", "Analyze my portfolio for weaknesses and biggest risks."),
                ("Correlation & Cluster Risks", "Analyze correlations between strategies. Are there cluster risks?"),
                ("Drawdown Analysis", "What are my max drawdowns? Which strategies have worst drawdown characteristics?"),
                ("Risk-Adjusted Returns", "Compare Sharpe, Sortino, and MAR across all strategies."),
            ],
            "Optimization": [
                ("Improvement Suggestions", "What concrete improvements would you recommend?"),
                ("Position Sizing Review", "Am I over- or under-allocated to any strategies?"),
                ("Kelly Criterion Sizing", "What would optimal Kelly Criterion sizing suggest?"),
                ("Diversification Check", "How well diversified is my portfolio?"),
            ],
            "Monte Carlo": [
                ("MC Results Summary", "Summarize Monte Carlo results and probability distributions."),
                ("Worst Case Scenarios", "What worst-case scenarios should I prepare for?"),
                ("Target Probability", "What's the probability of reaching my target returns?"),
            ],
        }

        # Render quick actions as text links in a compact format
        for category, actions in quick_actions.items():
            st.markdown(f'<div class="quick-action-category">{category}</div>', unsafe_allow_html=True)

            # Create columns for text link buttons
            link_cols = st.columns(len(actions))
            for idx, (label, prompt) in enumerate(actions):
                with link_cols[idx]:
                    # Use a minimal button styled as text
                    if st.button(f"→ {label}", key=f"qa_{category}_{idx}", type="tertiary"):
                        st.session_state.pending_quick_action = prompt
                        st.rerun()

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

RESPONSE FORMAT RULES:
- Respond in the user's language (German if German, English if English)
- Use simple formatting only: headers with ##, lists with -, bold with **text**
- NO complex markdown, NO tables, NO code blocks unless showing code
- Write numbers clearly: $100,000 not $100.000
- Keep responses concise and scannable
- Use bullet points for lists
- Reference specific data from the context above
- If data is missing, explain which analysis to run
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
