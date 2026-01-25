"""
Login Page for CashFlow Engine.
Supports Email OTP (passwordless) and Google OAuth authentication.
"""
import streamlit as st
import os
import base64

# Import auth module
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.auth import (
    init_auth_session_state,
    send_email_otp,
    verify_email_otp,
    get_google_oauth_url,
    is_authenticated
)


def _get_image_base64(file_path):
    """Load image as base64 for reliable high-quality rendering."""
    if os.path.exists(file_path):
        try:
            with open(file_path, "rb") as f:
                data = f.read()
                if b'PNG' in data[:16]:
                    return base64.b64encode(data).decode()
        except Exception:
            pass
    return None


def show_login_page():
    """
    Login Page: Professional two-column layout with Email OTP and Google OAuth.
    """
    # Initialize auth session state
    init_auth_session_state()

    # --- CUSTOM LOGIN PAGE STYLES (Full-height right panel layout) ---
    st.markdown("""
    <style>
        /* Hide default Streamlit elements on login page */
        [data-testid="stSidebar"] { display: none !important; }
        section[data-testid="stSidebar"] { display: none !important; }

        /* Remove ALL padding/margin from Streamlit containers for full-height layout */
        .stApp > header { display: none !important; }
        .stApp {
            margin: 0 !important;
            padding: 0 !important;
        }
        .stMainBlockContainer, .block-container, [data-testid="stAppViewBlockContainer"] {
            padding: 0 !important;
            margin: 0 !important;
            max-width: 100% !important;
        }
        .stMain {
            padding: 0 !important;
        }

        /* Full viewport height for columns */
        [data-testid="stHorizontalBlock"] {
            min-height: 100vh !important;
            gap: 0 !important;
        }

        /* Left column - Login form (1/3 width) */
        [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:first-child {
            padding: 60px 50px !important;
            display: flex !important;
            flex-direction: column !important;
            justify-content: center !important;
            background-color: #FFFFFF !important;
        }

        /* Right column - Marketing image (2/3 width, full height) */
        [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:last-child {
            padding: 0 !important;
            margin: 0 !important;
            overflow: hidden !important;
        }

        /* Marketing panel - full height image container */
        .marketing-panel {
            position: fixed;
            top: 0;
            right: 0;
            width: 66.67%;
            height: 100vh;
            background: linear-gradient(135deg, #EEF2FF 0%, #E0E7FF 50%, #C7D2FE 100%);
            display: flex;
            justify-content: center;
            align-items: center;
            overflow: hidden;
        }

        .marketing-panel img {
            width: 100%;
            height: 100%;
            object-fit: cover;
            object-position: center;
        }

        /* Google button styling */
        .google-btn {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 12px;
            width: 100%;
            padding: 14px 24px;
            background-color: #FFFFFF;
            border: 2px solid #E5E7EB;
            border-radius: 8px;
            font-family: 'Poppins', sans-serif;
            font-size: 15px;
            font-weight: 500;
            color: #4B5563;
            cursor: pointer;
            transition: all 0.2s ease;
            text-decoration: none;
        }

        .google-btn:hover {
            border-color: #302BFF;
            background-color: #F9FAFB;
            box-shadow: 0 2px 8px rgba(48, 43, 255, 0.1);
        }

        /* Divider */
        .divider {
            display: flex;
            align-items: center;
            margin: 28px 0;
        }

        .divider-line {
            flex: 1;
            height: 1px;
            background-color: #E5E7EB;
        }

        .divider-text {
            padding: 0 16px;
            font-family: 'Poppins', sans-serif;
            font-size: 13px;
            color: #9CA3AF;
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        /* Success message */
        .success-message {
            background-color: #ECFDF5;
            border: 1px solid #00D2BE;
            border-radius: 8px;
            padding: 16px 20px;
            margin-bottom: 20px;
        }

        .success-message p {
            color: #047857;
            font-family: 'Poppins', sans-serif;
            font-size: 14px;
            margin: 0;
        }

        /* Error message */
        .error-message {
            background-color: #FEF2F2;
            border: 1px solid #FF2E4D;
            border-radius: 8px;
            padding: 16px 20px;
            margin-bottom: 20px;
        }

        .error-message p {
            color: #DC2626;
            font-family: 'Poppins', sans-serif;
            font-size: 14px;
            margin: 0;
        }

        /* Privacy checkbox */
        .privacy-notice {
            font-family: 'Poppins', sans-serif;
            font-size: 12px;
            color: #6B7280;
            margin-top: 20px;
            line-height: 1.6;
        }

        .privacy-notice a {
            color: #302BFF;
            text-decoration: none;
        }

        .privacy-notice a:hover {
            text-decoration: underline;
        }
    </style>
    """, unsafe_allow_html=True)

    # --- TWO COLUMN LAYOUT (1/3 login, 2/3 image) ---
    col_left, col_right = st.columns([1, 2], gap="small")

    with col_left:
        # --- WELCOME TEXT (Exo 2 font with JS enforcement, blue color) ---
        st.markdown("""
            <link rel="preconnect" href="https://fonts.googleapis.com">
            <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
            <link href="https://fonts.googleapis.com/css2?family=Exo+2:ital,wght@0,100..900;1,100..900&display=swap" rel="stylesheet">
            <style>
                @import url('https://fonts.googleapis.com/css2?family=Exo+2:ital,wght@0,100..900;1,100..900&display=swap');

                .welcome-text-exo2 {
                    font-family: 'Exo 2', sans-serif !important;
                    font-size: 28px !important;
                    font-weight: 600 !important;
                    color: #302BFF !important;
                    text-transform: uppercase !important;
                    letter-spacing: 2px !important;
                    text-align: center;
                    margin-bottom: 20px;
                }
            </style>
            <div class="welcome-text-exo2">Welcome to</div>
            <script>
                // Force Exo 2 font after load
                function applyExo2ToWelcome() {
                    var el = document.querySelector('.welcome-text-exo2');
                    if (el) {
                        el.style.setProperty('font-family', "'Exo 2', sans-serif", 'important');
                        el.style.setProperty('font-weight', '600', 'important');
                    }
                }
                if (document.fonts && document.fonts.ready) {
                    document.fonts.ready.then(applyExo2ToWelcome);
                }
                setTimeout(applyExo2ToWelcome, 100);
                setTimeout(applyExo2ToWelcome, 500);
                setTimeout(applyExo2ToWelcome, 1000);
            </script>
        """, unsafe_allow_html=True)

        # --- LOGO (310px) ---
        logo_b64 = _get_image_base64("CashflowEnginelogo.png")
        if logo_b64:
            st.markdown(f"""
                <div style="text-align: center; margin-bottom: 15px;">
                    <img src="data:image/png;base64,{logo_b64}"
                         style="width: 310px; height: auto; max-width: 100%;"
                         alt="Cashflow Engine Logo" />
                </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
                <div style="text-align: center; margin-bottom: 15px;">
                    <div class="welcome-text-exo2" style="font-size: 28px !important;">
                        CASHFLOW ENGINE
                    </div>
                </div>
            """, unsafe_allow_html=True)

        # --- SUCCESS MESSAGE (OTP Code Sent) ---
        if st.session_state.get('otp_sent'):
            st.markdown("""
                <div class="success-message">
                    <p><strong>Check your email!</strong><br>
                    We've sent you a verification code. Enter it below to sign in.</p>
                </div>
            """, unsafe_allow_html=True)

        # --- ERROR MESSAGE ---
        if st.session_state.get('auth_error'):
            st.markdown(f"""
                <div class="error-message">
                    <p>{st.session_state.get('auth_error')}</p>
                </div>
            """, unsafe_allow_html=True)
            # Clear error after displaying
            st.session_state['auth_error'] = None

        # --- INTRO TEXT + LOGIN FORM (no extra spacing) ---
        if not st.session_state.get('otp_sent'):
            st.markdown("""
                <div style="text-align: center; margin-bottom: 5px; margin-top: 0;">
                    <span style="font-family: 'Poppins', sans-serif; font-size: 14px; color: #6B7280;">
                        Sign in to access your portfolio analytics
                    </span>
                </div>
            """, unsafe_allow_html=True)

        # --- GOOGLE SIGN-IN BUTTON (directly below, no columns) ---
        if not st.session_state.get('otp_sent'):
            google_url = get_google_oauth_url()
            if google_url:
                st.markdown(f"""
                    <a href="{google_url}" class="google-btn" target="_self">
                        <svg width="20" height="20" viewBox="0 0 24 24">
                            <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                            <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                            <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                            <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                        </svg>
                        Continue with Google
                    </a>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                    <div style="text-align: center; padding: 14px; background-color: #F3F4F6;
                                border-radius: 8px;">
                        <span style="font-family: 'Poppins', sans-serif; font-size: 14px; color: #6B7280;">
                            Use email verification below to sign in
                        </span>
                    </div>
                """, unsafe_allow_html=True)

            # --- DIVIDER ---
            st.markdown("""
                <div class="divider">
                    <div class="divider-line"></div>
                    <span class="divider-text">or</span>
                    <div class="divider-line"></div>
                </div>
            """, unsafe_allow_html=True)

        # --- EMAIL OTP FORM ---
        if not st.session_state.get('otp_sent'):
            # Step 1: Enter email and request code
            email = st.text_input(
                "Email Address",
                placeholder="Enter your email address",
                key="login_email",
                label_visibility="collapsed"
            )

            # Privacy checkbox
            privacy_accepted = st.checkbox(
                "I accept the [Privacy Policy](?page=privacy)",
                key="privacy_checkbox",
                value=st.session_state.get('privacy_accepted', False)
            )

            # Send Code Button
            if st.button("Send Verification Code", use_container_width=True, type="primary", key="send_otp_button"):
                if not email:
                    st.session_state['auth_error'] = "Please enter your email address."
                    st.rerun()
                elif not privacy_accepted:
                    st.session_state['auth_error'] = "Please accept the Privacy Policy to continue."
                    st.rerun()
                elif '@' not in email or '.' not in email:
                    st.session_state['auth_error'] = "Please enter a valid email address."
                    st.rerun()
                else:
                    # Send OTP code
                    result = send_email_otp(email)
                    if result['success']:
                        st.session_state['otp_sent'] = True
                        st.session_state['otp_email'] = email
                        st.session_state['privacy_accepted'] = True
                    else:
                        st.session_state['auth_error'] = result['message']
                    st.rerun()

            # Privacy notice
            st.markdown("""
                <div class="privacy-notice">
                    By signing in, you agree to our <a href="?page=privacy">Privacy Policy</a>.
                    We use your email only for authentication and will never share it with third parties.
                </div>
            """, unsafe_allow_html=True)

        else:
            # Step 2: Enter OTP code
            st.markdown(f"""
                <div style="text-align: center; padding: 10px 0;">
                    <p style="font-family: 'Poppins', sans-serif; font-size: 14px; color: #4B5563;">
                        Code sent to: <strong>{st.session_state.get('otp_email', '')}</strong>
                    </p>
                </div>
            """, unsafe_allow_html=True)

            # OTP Code input (Supabase sends 6-8 digit codes)
            otp_code = st.text_input(
                "Verification Code",
                placeholder="Enter verification code",
                key="otp_code_input",
                max_chars=8,
                label_visibility="collapsed"
            )

            # Verify button
            if st.button("Verify & Sign In", use_container_width=True, type="primary", key="verify_otp_button"):
                if not otp_code:
                    st.session_state['auth_error'] = "Please enter the verification code."
                    st.rerun()
                elif len(otp_code) < 6:
                    st.session_state['auth_error'] = "Please enter the complete verification code."
                    st.rerun()
                else:
                    # Verify OTP code
                    result = verify_email_otp(st.session_state.get('otp_email', ''), otp_code)
                    if result['success']:
                        st.session_state['otp_sent'] = False
                        st.session_state['otp_email'] = None
                        st.session_state.navigate_to_page = "Start & Data"
                        st.rerun()
                    else:
                        st.session_state['auth_error'] = result['message']
                        st.rerun()

            # Resend code button
            if st.button("Resend Code", use_container_width=True, type="secondary"):
                email = st.session_state.get('otp_email', '')
                if email:
                    result = send_email_otp(email)
                    if result['success']:
                        st.session_state['auth_error'] = None
                        st.success("New code sent! Check your email.")
                    else:
                        st.session_state['auth_error'] = result['message']
                st.rerun()

            if st.button("Use Different Email", use_container_width=True, type="tertiary"):
                st.session_state['otp_sent'] = False
                st.session_state['otp_email'] = None
                st.rerun()

    # --- RIGHT PANEL: FULL-HEIGHT MARKETING IMAGE ---
    with col_right:
        marketing_image_b64 = _get_image_base64("login_marketing_panel.png")

        if marketing_image_b64:
            # Full-height image panel (like PowerX Optimizer)
            st.markdown(f"""
                <div class="marketing-panel">
                    <img src="data:image/png;base64,{marketing_image_b64}"
                         alt="Cashflow Engine Features" />
                </div>
            """, unsafe_allow_html=True)
        else:
            # Fallback - gradient background with features
            st.markdown("""
                <div class="marketing-panel">
                    <div style="text-align: center; padding: 40px;">
                        <div style="font-family: 'Exo 2', sans-serif; font-size: 48px; font-weight: 800;
                                    color: #302BFF; margin-bottom: 20px;">
                            8+
                        </div>
                        <div style="font-family: 'Poppins', sans-serif; font-size: 20px; font-weight: 600;
                                    color: #4B5563; margin-bottom: 40px;">
                            Analysis Modules
                        </div>
                        <div style="display: flex; flex-wrap: wrap; gap: 15px; justify-content: center; max-width: 450px; margin: 0 auto;">
                            <div style="background: white; padding: 14px 24px; border-radius: 12px;
                                        box-shadow: 0 4px 20px rgba(0,0,0,0.08);">
                                <span style="font-family: 'Poppins', sans-serif; font-size: 14px; color: #4B5563;">
                                    Portfolio Analytics
                                </span>
                            </div>
                            <div style="background: white; padding: 14px 24px; border-radius: 12px;
                                        box-shadow: 0 4px 20px rgba(0,0,0,0.08);">
                                <span style="font-family: 'Poppins', sans-serif; font-size: 14px; color: #4B5563;">
                                    Monte Carlo
                                </span>
                            </div>
                            <div style="background: white; padding: 14px 24px; border-radius: 12px;
                                        box-shadow: 0 4px 20px rgba(0,0,0,0.08);">
                                <span style="font-family: 'Poppins', sans-serif; font-size: 14px; color: #4B5563;">
                                    Portfolio Builder
                                </span>
                            </div>
                            <div style="background: white; padding: 14px 24px; border-radius: 12px;
                                        box-shadow: 0 4px 20px rgba(0,0,0,0.08);">
                                <span style="font-family: 'Poppins', sans-serif; font-size: 14px; color: #4B5563;">
                                    MEIC Optimizer
                                </span>
                            </div>
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
