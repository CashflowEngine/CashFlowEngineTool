import streamlit as st
import ui_components as ui
import os
from PIL import Image

def show_login_page():
    """
    Login Page: Professional two-column layout with login form and marketing content.
    Similar to PowerX Optimizer design.
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
            font-family: 'Poppins', sans-serif;
            font-size: 28px;
            font-weight: 400;
            color: #302BFF;
            margin-bottom: 0;
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
        .forgot-password {
            text-align: right;
            margin-top: -10px;
            margin-bottom: 20px;
        }

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

        /* Error message styling */
        .login-error {
            background-color: rgba(255, 46, 77, 0.1);
            border: 1px solid #FF2E4D;
            border-radius: 6px;
            padding: 12px;
            margin-bottom: 20px;
            color: #FF2E4D;
            font-size: 13px;
        }

        /* Input styling for login */
        .login-input-container .stTextInput > div > div {
            border-radius: 6px !important;
            border: 1px solid #E5E7EB !important;
        }

        .login-input-container .stTextInput > div > div:focus-within {
            border-color: #302BFF !important;
            box-shadow: 0 0 0 2px rgba(48, 43, 255, 0.1) !important;
        }
    </style>
    """, unsafe_allow_html=True)

    # --- TWO COLUMN LAYOUT ---
    col_left, col_right = st.columns([1, 1.2], gap="small")

    with col_left:
        # Add spacing at top
        st.write("")
        st.write("")
        st.write("")

        # --- LOGO ---
        logo_col1, logo_col2, logo_col3 = st.columns([1, 2, 1])
        with logo_col2:
            logo_file = "CashflowEnginelogo.png"
            if os.path.exists(logo_file):
                try:
                    with Image.open(logo_file) as img:
                        img.verify()
                    st.image(logo_file, width=220)
                except Exception:
                    st.markdown(f"""
                        <div style="text-align: center; margin-bottom: 20px;">
                            <span style="font-size: 32px;">⚡</span>
                        </div>
                    """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                    <div style="text-align: center; margin-bottom: 20px;">
                        <span style="font-size: 32px;">⚡</span>
                    </div>
                """, unsafe_allow_html=True)

        st.write("")

        # --- WELCOME TEXT ---
        st.markdown(f"""
            <div style="text-align: center;">
                <div style="font-family: 'Poppins', sans-serif; font-size: 26px; font-weight: 400; color: #302BFF; margin-bottom: 0;">
                    Welcome to
                </div>
                <div style="font-family: 'Exo 2', sans-serif; font-size: 30px; font-weight: 800; color: #4B5563; text-transform: uppercase; letter-spacing: 0.5px;">
                    Cashflow Engine
                </div>
            </div>
        """, unsafe_allow_html=True)

        st.write("")

        # --- SESSION MESSAGE ---
        if st.session_state.get('login_error'):
            st.markdown(f"""
                <div style="text-align: center;">
                    <span style="font-family: 'Poppins', sans-serif; font-size: 13px; color: #FF2E4D;">
                        {st.session_state.get('login_error_message', 'Invalid credentials. Please try again.')}
                    </span>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
                <div style="text-align: center;">
                    <span style="font-family: 'Poppins', sans-serif; font-size: 13px; color: #6B7280;">
                        Please log in to continue.
                    </span>
                </div>
            """, unsafe_allow_html=True)

        st.write("")
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
        # --- MARKETING CONTENT - Right Panel ---
        st.markdown(f"""
            <div style="background: linear-gradient(135deg, #EEF2FF 0%, #E0E7FF 50%, #C7D2FE 100%);
                        border-radius: 20px; padding: 40px; min-height: 650px; position: relative; overflow: hidden;">

                <!-- Decorative curves -->
                <div style="position: absolute; top: 5%; right: 10%; width: 180px; height: 180px;
                            border: 3px solid #302BFF; border-radius: 50%; border-left-color: transparent;
                            border-bottom-color: transparent; transform: rotate(-45deg); opacity: 0.25;"></div>
                <div style="position: absolute; bottom: 15%; left: 5%; width: 250px; height: 250px;
                            border: 3px solid #302BFF; border-radius: 50%; border-right-color: transparent;
                            border-top-color: transparent; transform: rotate(45deg); opacity: 0.25;"></div>

                <!-- Feature Card: Strategies -->
                <div style="position: absolute; top: 40px; left: 30px; background: #FFFFFF; border-radius: 12px;
                            padding: 18px 22px; box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);">
                    <div style="font-family: 'Exo 2', sans-serif; font-size: 28px; font-weight: 800; color: #302BFF; line-height: 1;">8+</div>
                    <div style="font-family: 'Poppins', sans-serif; font-size: 13px; font-weight: 500; color: #4B5563;">Analysis Modules</div>
                </div>

                <!-- Feature Card: Time -->
                <div style="position: absolute; top: 30px; right: 30px; background: #FFFFFF; border-radius: 12px;
                            padding: 18px 22px; box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08); max-width: 180px;">
                    <div style="font-family: 'Exo 2', sans-serif; font-size: 24px; font-weight: 800; color: #302BFF; line-height: 1;">Monte Carlo</div>
                    <div style="font-family: 'Poppins', sans-serif; font-size: 12px; color: #6B7280; margin-top: 6px; line-height: 1.4;">
                        Advanced risk simulation for portfolio stress testing
                    </div>
                </div>

                <!-- Central Dashboard Preview -->
                <div style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);
                            width: 420px; background: #FFFFFF; border-radius: 10px;
                            box-shadow: 0 20px 60px rgba(48, 43, 255, 0.15); border: 1px solid #E5E7EB; overflow: hidden;">

                    <!-- Dashboard Header -->
                    <div style="height: 36px; background: linear-gradient(90deg, #302BFF 0%, #7B2BFF 100%);
                                display: flex; align-items: center; padding: 0 12px;">
                        <div style="width: 10px; height: 10px; border-radius: 50%; background: #FF2E4D; margin-right: 6px;"></div>
                        <div style="width: 10px; height: 10px; border-radius: 50%; background: #FFAB00; margin-right: 6px;"></div>
                        <div style="width: 10px; height: 10px; border-radius: 50%; background: #00D2BE;"></div>
                        <span style="margin-left: auto; color: white; font-size: 11px; font-family: 'Poppins', sans-serif;">Cashflow Engine</span>
                    </div>

                    <!-- Dashboard Content -->
                    <div style="padding: 15px; background: #F9FAFB; height: 200px;">
                        <!-- Mini metrics row -->
                        <div style="display: flex; gap: 10px; margin-bottom: 12px;">
                            <div style="flex: 1; background: #00D2BE; border-radius: 6px; padding: 10px; text-align: center;">
                                <div style="font-family: 'Exo 2', sans-serif; font-size: 14px; font-weight: 800; color: white;">+42.5%</div>
                                <div style="font-size: 9px; color: white; opacity: 0.9;">CAGR</div>
                            </div>
                            <div style="flex: 1; background: #302BFF; border-radius: 6px; padding: 10px; text-align: center;">
                                <div style="font-family: 'Exo 2', sans-serif; font-size: 14px; font-weight: 800; color: white;">78.2%</div>
                                <div style="font-size: 9px; color: white; opacity: 0.9;">Win Rate</div>
                            </div>
                            <div style="flex: 1; background: #FFFFFF; border: 1px solid #E5E7EB; border-radius: 6px; padding: 10px; text-align: center;">
                                <div style="font-family: 'Exo 2', sans-serif; font-size: 14px; font-weight: 800; color: #4B5563;">2.4</div>
                                <div style="font-size: 9px; color: #6B7280;">Profit Factor</div>
                            </div>
                        </div>
                        <!-- Mini chart area -->
                        <div style="width: 100%; height: 110px; background: linear-gradient(180deg, rgba(0, 210, 190, 0.05) 0%, rgba(0, 210, 190, 0.2) 100%);
                                    border-radius: 6px; position: relative; border: 1px solid #E5E7EB;">
                            <svg style="width: 100%; height: 100%;" viewBox="0 0 380 100" preserveAspectRatio="none">
                                <path d="M0,80 Q50,70 100,60 T200,40 T300,25 T380,15"
                                      stroke="#00D2BE" stroke-width="2" fill="none"/>
                                <path d="M0,80 Q50,70 100,60 T200,40 T300,25 T380,15 L380,100 L0,100 Z"
                                      fill="url(#gradient)" opacity="0.3"/>
                                <defs>
                                    <linearGradient id="gradient" x1="0%" y1="0%" x2="0%" y2="100%">
                                        <stop offset="0%" style="stop-color:#00D2BE;stop-opacity:0.5" />
                                        <stop offset="100%" style="stop-color:#00D2BE;stop-opacity:0" />
                                    </linearGradient>
                                </defs>
                            </svg>
                        </div>
                    </div>
                </div>

                <!-- Feature Card: Tool -->
                <div style="position: absolute; bottom: 180px; left: 25px; background: #FFFFFF; border-radius: 12px;
                            padding: 16px 20px; box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);">
                    <div style="width: 36px; height: 36px; border-radius: 8px; background: #302BFF;
                                display: flex; align-items: center; justify-content: center; margin-bottom: 10px; font-size: 18px;">
                        <span style="filter: brightness(0) invert(1);">📊</span>
                    </div>
                    <div style="font-family: 'Poppins', sans-serif; font-size: 13px; font-weight: 600; color: #4B5563;">Portfolio</div>
                    <div style="font-family: 'Poppins', sans-serif; font-size: 13px; font-weight: 600; color: #4B5563;">Analytics Tool</div>
                </div>

                <!-- Feature Card: Years -->
                <div style="position: absolute; bottom: 50px; left: 50%; transform: translateX(-50%); background: #FFFFFF;
                            border-radius: 12px; padding: 18px 24px; box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);">
                    <div style="font-family: 'Exo 2', sans-serif; font-size: 24px; font-weight: 800; color: #4B5563; line-height: 1;">AI Powered</div>
                    <div style="font-family: 'Poppins', sans-serif; font-size: 12px; color: #6B7280;">intelligent analysis insights</div>
                </div>

                <!-- Feature Card: Experience -->
                <div style="position: absolute; bottom: 130px; right: 25px; background: #FFFFFF; border-radius: 12px;
                            padding: 16px 20px; box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);">
                    <div style="width: 36px; height: 36px; border-radius: 8px; background: #00D2BE;
                                display: flex; align-items: center; justify-content: center; margin-bottom: 10px; font-size: 18px;">
                        <span style="filter: brightness(0) invert(1);">⚡</span>
                    </div>
                    <div style="font-family: 'Poppins', sans-serif; font-size: 13px; font-weight: 600; color: #4B5563;">Option Trading</div>
                    <div style="font-family: 'Poppins', sans-serif; font-size: 12px; color: #6B7280;">Specialized Analytics</div>
                </div>

            </div>
        """, unsafe_allow_html=True)
