import streamlit as st
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

def page_ai_analyst(full_df):
    st.markdown("<h1>🤖 AI ANALYST</h1>", unsafe_allow_html=True)
    
    if not GEMINI_AVAILABLE:
        st.error("Gemini not installed.")
        return

    key = st.text_input("API Key", type="password")
    if key:
        genai.configure(api_key=key)
        model = genai.GenerativeModel("gemini-pro")
        
        if "messages" not in st.session_state: st.session_state.messages = []
        
        for m in st.session_state.messages:
            st.chat_message(m["role"]).write(m["content"])
            
        if p := st.chat_input():
            st.session_state.messages.append({"role": "user", "content": p})
            st.chat_message("user").write(p)
            
            summary = full_df.groupby('strategy')['pnl'].sum().to_string()
            try:
                resp = model.generate_content(f"Portfolio:\n{summary}\nUser: {p}")
                st.session_state.messages.append({"role": "assistant", "content": resp.text})
                st.chat_message("assistant").write(resp.text)
            except Exception as e:
                st.error(e)
