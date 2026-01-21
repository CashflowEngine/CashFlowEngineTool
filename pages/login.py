import streamlit as st
import os
import base64

def _get_image_base64(file_path):
    """Load image as base64 for reliable high-quality rendering."""
    if os.path.exists(file_path):
        try:
            with open(file_path, "rb") as f:
                data = f.read()
                # Verify it's a PNG
                if b'PNG' in data[:16]:
                    return base64.b64encode(data).decode()
        except Exception:
            pass
    return None

def show_login_page():
    """
    Login Page: Professional two-column layout with login form and marketing content.
    """

    # --- CUSTOM LOGIN PAGE STYLES ---
    st.markdown("""
    <style>
        /* Hide default Streamlit elements on login page */
        [data-testid="stSidebar"] { display: none !important; }
        section[data-testid="stSidebar"] { display: none !important; }

        /* Forgot password link */
        .forgot-password a {
            font-family: 'Poppins', sans-serif;
            font-size: 13px;
            color: #6B7280;
            text-decoration: none;
        }

        .forgot-password a:hover {
            color: #302BFF;
            text-decoration: underline;
        }
    </style>
    """, unsafe_allow_html=True)

    # --- TWO COLUMN LAYOUT ---
    col_left, col_right = st.columns([1, 1.3], gap="small")

    with col_left:
        # Add spacing at top
        st.write("")
        st.write("")

        # --- WELCOME TEXT (at the very top) ---
        st.markdown("""
            <div style="text-align: center; margin-bottom: 10px;">
                <div style="font-family: 'Poppins', sans-serif; font-size: 28px; font-weight: 400; color: #302BFF;">
                    Welcome to
                </div>
            </div>
        """, unsafe_allow_html=True)

        # --- LOGO (centered, larger, replaces "Cashflow Engine" text) ---
        logo_b64 = _get_image_base64("CashflowEnginelogo.png")
        if logo_b64:
            st.markdown(f"""
                <div style="text-align: center; margin-bottom: 20px;">
                    <img src="data:image/png;base64,{logo_b64}"
                         style="width: 320px; height: auto; max-width: 100%;"
                         alt="Cashflow Engine Logo" />
                </div>
            """, unsafe_allow_html=True)
        else:
            # Fallback text if logo not available
            st.markdown("""
                <div style="text-align: center; margin-bottom: 20px;">
                    <div style="font-family: 'Exo 2', sans-serif; font-size: 32px; font-weight: 800;
                                color: #302BFF; text-transform: uppercase; letter-spacing: 1px;">
                        CASHFLOW ENGINE
                    </div>
                </div>
            """, unsafe_allow_html=True)

        # --- SESSION MESSAGE ---
        if st.session_state.get('login_error'):
            st.markdown(f"""
                <div style="text-align: center; margin-bottom: 15px;">
                    <span style="font-family: 'Poppins', sans-serif; font-size: 13px; color: #FF2E4D;">
                        {st.session_state.get('login_error_message', 'Invalid credentials. Please try again.')}
                    </span>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
                <div style="text-align: center; margin-bottom: 15px;">
                    <span style="font-family: 'Poppins', sans-serif; font-size: 13px; color: #6B7280;">
                        Please log in to continue.
                    </span>
                </div>
            """, unsafe_allow_html=True)

        st.write("")

        # --- LOGIN FORM ---
        form_col1, form_col2, form_col3 = st.columns([0.5, 3, 0.5])
        with form_col2:
            email = st.text_input("Email Address", placeholder="Email Address", key="login_email", label_visibility="collapsed")
            st.write("")
            password = st.text_input("Password", type="password", placeholder="Password", key="login_password", label_visibility="collapsed")

            # Forgot Password link
            st.markdown("""
                <div style="text-align: right; margin-top: 8px; margin-bottom: 20px;">
                    <a href="#" style="font-family: 'Poppins', sans-serif; font-size: 13px; color: #6B7280; text-decoration: none;">
                        Forgot Password?
                    </a>
                </div>
            """, unsafe_allow_html=True)

            # Login Button
            if st.button("Log In", use_container_width=True, type="primary", key="login_button"):
                # Simple validation - in a real app, this would check against a database
                if email and password:
                    # For demo purposes, accept any non-empty credentials
                    # In production, replace this with actual authentication
                    st.session_state['is_authenticated'] = True
                    st.session_state['user_email'] = email
                    st.session_state['login_error'] = False
                    st.session_state.navigate_to_page = "Start & Data"
                    st.rerun()
                else:
                    st.session_state['login_error'] = True
                    st.session_state['login_error_message'] = "Please enter both email and password."
                    st.rerun()

            # Back to product page link
            st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)
            if st.button("Zurück zur Produktübersicht", use_container_width=True, type="tertiary", key="back_to_sales"):
                st.session_state.show_sales_page = True
                st.rerun()

    with col_right:
        # --- MARKETING IMAGE - Right Panel ---
        marketing_image_b64 = _get_image_base64("login_marketing_panel.png")

        if marketing_image_b64:
            # Use the uploaded marketing image
            st.markdown(f"""
                <div style="display: flex; justify-content: center; align-items: center;
                            min-height: 650px; padding: 20px;">
                    <img src="data:image/png;base64,{marketing_image_b64}"
                         style="max-width: 100%; height: auto; border-radius: 16px;
                                box-shadow: 0 10px 40px rgba(48, 43, 255, 0.1);"
                         alt="Cashflow Engine Features" />
                </div>
            """, unsafe_allow_html=True)
        else:
            # Fallback: Show gradient background with feature highlights
            st.markdown("""
                <div style="background: linear-gradient(135deg, #EEF2FF 0%, #E0E7FF 50%, #C7D2FE 100%);
                            border-radius: 20px; padding: 60px 40px; min-height: 600px;
                            display: flex; flex-direction: column; justify-content: center; align-items: center;
                            text-align: center;">

                    <div style="font-family: 'Exo 2', sans-serif; font-size: 42px; font-weight: 800;
                                color: #302BFF; margin-bottom: 20px;">
                        8+
                    </div>
                    <div style="font-family: 'Poppins', sans-serif; font-size: 18px; font-weight: 600;
                                color: #4B5563; margin-bottom: 40px;">
                        Analysis Modules
                    </div>

                    <div style="display: flex; flex-wrap: wrap; gap: 15px; justify-content: center; max-width: 400px;">
                        <div style="background: white; padding: 12px 20px; border-radius: 10px;
                                    box-shadow: 0 4px 15px rgba(0,0,0,0.08);">
                            <span style="font-family: 'Poppins', sans-serif; font-size: 13px; color: #4B5563;">
                                Portfolio Analytics
                            </span>
                        </div>
                        <div style="background: white; padding: 12px 20px; border-radius: 10px;
                                    box-shadow: 0 4px 15px rgba(0,0,0,0.08);">
                            <span style="font-family: 'Poppins', sans-serif; font-size: 13px; color: #4B5563;">
                                Monte Carlo
                            </span>
                        </div>
                        <div style="background: white; padding: 12px 20px; border-radius: 10px;
                                    box-shadow: 0 4px 15px rgba(0,0,0,0.08);">
                            <span style="font-family: 'Poppins', sans-serif; font-size: 13px; color: #4B5563;">
                                AI Analyst
                            </span>
                        </div>
                        <div style="background: white; padding: 12px 20px; border-radius: 10px;
                                    box-shadow: 0 4px 15px rgba(0,0,0,0.08);">
                            <span style="font-family: 'Poppins', sans-serif; font-size: 13px; color: #4B5563;">
                                Portfolio Builder
                            </span>
                        </div>
                        <div style="background: white; padding: 12px 20px; border-radius: 10px;
                                    box-shadow: 0 4px 15px rgba(0,0,0,0.08);">
                            <span style="font-family: 'Poppins', sans-serif; font-size: 13px; color: #4B5563;">
                                MEIC Optimizer
                            </span>
                        </div>
                    </div>

                    <div style="margin-top: 50px;">
                        <div style="font-family: 'Poppins', sans-serif; font-size: 14px; color: #6B7280;">
                            Advanced Portfolio Analytics for Option Traders
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
