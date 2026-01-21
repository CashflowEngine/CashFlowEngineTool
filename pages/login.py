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

        /* Login page container */
        .login-container {
            display: flex;
            min-height: 85vh;
            margin: -1rem -1rem 0 -1rem;
        }

        /* Left panel - Login form */
        .login-left {
            flex: 1;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            padding: 60px 80px;
            background-color: #FFFFFF;
        }

        .login-form-wrapper {
            width: 100%;
            max-width: 380px;
        }

        .login-logo {
            margin-bottom: 40px;
            text-align: center;
        }

        .login-logo img {
            max-width: 220px;
            height: auto;
        }

        .welcome-text {
            font-family: 'Exo 2', sans-serif !important;
            font-size: 28px;
            font-weight: 600 !important;
            color: #302BFF;
            margin-bottom: 0;
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        .brand-title {
            font-family: 'Exo 2', sans-serif;
            font-size: 32px;
            font-weight: 800;
            color: #4B5563;
            margin-bottom: 30px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .session-message {
            font-family: 'Poppins', sans-serif;
            font-size: 13px;
            color: #FF2E4D;
            margin-bottom: 25px;
        }

        /* Right panel - Marketing content */
        .login-right {
            flex: 1.2;
            background: linear-gradient(135deg, #EEF2FF 0%, #E0E7FF 50%, #C7D2FE 100%);
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 60px;
            position: relative;
            overflow: hidden;
        }

        .marketing-wrapper {
            position: relative;
            width: 100%;
            max-width: 700px;
            height: 600px;
        }

        /* Feature cards */
        .feature-card {
            position: absolute;
            background: #FFFFFF;
            border-radius: 12px;
            padding: 20px 24px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
            font-family: 'Poppins', sans-serif;
        }

        .feature-card-highlight {
            font-family: 'Exo 2', sans-serif;
            font-size: 32px;
            font-weight: 800;
            color: #302BFF;
            line-height: 1;
            margin-bottom: 4px;
        }

        .feature-card-label {
            font-size: 14px;
            font-weight: 500;
            color: #4B5563;
        }

        .feature-card-desc {
            font-size: 12px;
            color: #6B7280;
            margin-top: 8px;
            line-height: 1.4;
        }

        /* Positioned cards */
        .card-strategies { top: 40px; left: 30px; }
        .card-time { top: 20px; right: 0; }
        .card-tool { bottom: 180px; left: 0; }
        .card-years { bottom: 40px; left: 50%; transform: translateX(-50%); }
        .card-experience { bottom: 100px; right: 0; }

        /* Icon in card */
        .card-icon {
            width: 40px;
            height: 40px;
            border-radius: 8px;
            background: #302BFF;
            display: flex;
            align-items: center;
            justify-content: center;
            margin-bottom: 12px;
            font-size: 20px;
        }

        /* Decorative curves */
        .curve-decoration {
            position: absolute;
            pointer-events: none;
        }

        .curve-1 {
            top: 10%;
            right: 15%;
            width: 200px;
            height: 200px;
            border: 3px solid #302BFF;
            border-radius: 50%;
            border-left-color: transparent;
            border-bottom-color: transparent;
            transform: rotate(-45deg);
            opacity: 0.3;
        }

        .curve-2 {
            bottom: 20%;
            left: 10%;
            width: 300px;
            height: 300px;
            border: 3px solid #302BFF;
            border-radius: 50%;
            border-right-color: transparent;
            border-top-color: transparent;
            transform: rotate(45deg);
            opacity: 0.3;
        }

        /* Screenshot/dashboard preview */
        .dashboard-preview {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            width: 500px;
            height: 300px;
            background: #FFFFFF;
            border-radius: 8px;
            box-shadow: 0 20px 60px rgba(48, 43, 255, 0.15);
            border: 1px solid #E5E7EB;
            overflow: hidden;
        }

        .dashboard-header {
            height: 40px;
            background: linear-gradient(90deg, #302BFF 0%, #7B2BFF 100%);
            display: flex;
            align-items: center;
            padding: 0 15px;
        }

        .dashboard-dot {
            width: 10px;
            height: 10px;
            border-radius: 50%;
            margin-right: 6px;
        }

        .dot-red { background: #FF2E4D; }
        .dot-yellow { background: #FFAB00; }
        .dot-green { background: #00D2BE; }

        .dashboard-content {
            padding: 20px;
            background: #F9FAFB;
            height: calc(100% - 40px);
        }

        .dashboard-chart {
            width: 100%;
            height: 80%;
            background: linear-gradient(180deg, rgba(0, 210, 190, 0.1) 0%, rgba(0, 210, 190, 0.3) 100%);
            border-radius: 4px;
            position: relative;
        }

        .chart-line {
            position: absolute;
            bottom: 30%;
            left: 0;
            width: 100%;
            height: 2px;
            background: linear-gradient(90deg, #00D2BE 0%, #302BFF 50%, #00D2BE 100%);
        }

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
                <div style="font-family: 'Exo 2', sans-serif !important; font-size: 36px; font-weight: 600; color: #302BFF; text-transform: uppercase; letter-spacing: 2px;">
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
