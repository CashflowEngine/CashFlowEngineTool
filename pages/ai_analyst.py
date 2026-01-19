import streamlit as st
import os
import pandas as pd

GEMINI_AVAILABLE = False
try:
    from google import genai
    from google.genai import types
    GEMINI_AVAILABLE = True
except ImportError:
    pass

def page_ai_analyst(full_df):
    st.markdown("<h1>🤖 AI ANALYST</h1>", unsafe_allow_html=True)
    
    if not GEMINI_AVAILABLE:
        st.error("Google GenAI SDK not installed. Please add `google-genai` to requirements.txt.")
        return

    # API Key Handling - Strictly from Environment/Secrets as per guidelines
    api_key = os.environ.get("API_KEY") or st.secrets.get("API_KEY") or os.environ.get("GOOGLE_API_KEY")
    
    if not api_key:
        st.warning("⚠️ API Key not found. Please set `API_KEY` in your environment variables or secrets.")
        st.info("The analyst cannot function without a valid API key configured in the server environment.")
        return

    # Initialize Client
    try:
        client = genai.Client(api_key=api_key)
    except Exception as e:
        st.error(f"Failed to initialize AI client: {e}")
        return

    # Chat Interface
    if "messages" not in st.session_state:
        st.session_state.messages = []
        
    # Display History
    for m in st.session_state.messages:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])
            
    # Input
    if p := st.chat_input("Ask about your portfolio..."):
        st.session_state.messages.append({"role": "user", "content": p})
        with st.chat_message("user"):
            st.markdown(p)
            
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            message_placeholder.markdown("Thinking...")
            
            try:
                # Prepare Context
                context_str = ""
                if full_df is not None and not full_df.empty:
                    # Summarize portfolio for context
                    stats = full_df.groupby('strategy')['pnl'].agg(['sum', 'count', 'mean']).reset_index()
                    stats.columns = ['Strategy', 'Total P/L', 'Trades', 'Avg P/L']
                    context_str = stats.to_markdown(index=False)
                    
                    total_pnl = full_df['pnl'].sum()
                    win_rate = (full_df['pnl'] > 0).mean()
                    context_str = f"Portfolio Summary:\nTotal P/L: ${total_pnl:,.2f}\nWin Rate: {win_rate:.1%}\n\nStrategy Breakdown:\n{context_str}"
                
                full_prompt = f"""
                You are a senior financial analyst reviewing an options trading portfolio.
                
                Current Portfolio Data:
                {context_str}
                
                User Question: {p}
                
                Provide a concise, professional, and data-driven answer. Use markdown for formatting.
                """
                
                # Generate Response
                response = client.models.generate_content(
                    model='gemini-2.0-flash-exp', # Using a capable flash model
                    contents=full_prompt
                )
                
                response_text = response.text
                message_placeholder.markdown(response_text)
                st.session_state.messages.append({"role": "assistant", "content": response_text})
                
            except Exception as e:
                message_placeholder.error(f"Analysis failed: {str(e)}")
