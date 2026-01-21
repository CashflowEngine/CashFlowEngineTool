import streamlit as st
import ui_components as ui

def page_ai_analyst(full_df):
    """AI Analyst page - Coming Soon."""

    # Header with Exo 2 font
    st.markdown(f"""
        <h1 style="font-family: 'Exo 2', sans-serif !important; font-weight: 800 !important;
                   text-transform: uppercase; color: {ui.COLOR_GREY} !important; letter-spacing: 1px;">
            AI ANALYST
        </h1>
    """, unsafe_allow_html=True)

    # Coming Soon message
    st.markdown(f"""
        <div style="text-align: center; padding: 80px 40px; background: {ui.COLOR_ICE}; border-radius: 16px; margin: 40px 0;">
            <div style="font-size: 64px; margin-bottom: 24px;">🤖</div>
            <div style="font-family: 'Exo 2', sans-serif; font-weight: 800; font-size: 32px;
                        color: {ui.COLOR_GREY}; text-transform: uppercase; margin-bottom: 16px;">
                Coming Soon
            </div>
            <div style="font-family: 'Poppins', sans-serif; font-size: 16px; color: #6B7280;
                        max-width: 500px; margin: 0 auto; line-height: 1.6;">
                The AI Analyst will allow you to interact with your portfolio data using advanced AI.
                Ask questions about your performance, get insights on risk factors, and receive
                data-driven suggestions for improvement.
            </div>
        </div>
    """, unsafe_allow_html=True)

    # Feature preview
    with st.container(border=True):
        ui.section_header("Planned Features")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("""
            **Natural Language Queries**
            - Ask questions about your portfolio in plain English
            - Get instant insights without complex analysis

            **Performance Analysis**
            - Automated identification of strengths and weaknesses
            - Comparison with historical benchmarks
            """)

        with col2:
            st.markdown("""
            **Risk Assessment**
            - AI-powered risk factor identification
            - Correlation and diversification recommendations

            **Improvement Suggestions**
            - Data-driven optimization recommendations
            - Strategy allocation insights
            """)
