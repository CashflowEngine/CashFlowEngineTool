"""
Login Page for CashFlow Engine.
Supports Magic Link (passwordless) and Google OAuth authentication.
"""
import streamlit as st
import os
import base64
from urllib.parse import parse_qs, urlparse

# Import auth module
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.auth import (
    init_auth_session_state,
    sign_in_with_magic_link,
    get_google_oauth_url,
    handle_auth_callback,
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


def _handle_oauth_callback():
    """Check URL for OAuth/Magic Link callback parameters."""
    try:
        # Get query parameters from URL
        query_params = st.query_params

        # Check for access_token and refresh_token (from OAuth or Magic Link)
        access_token = query_params.get('access_token')
        refresh_token = query_params.get('refresh_token')

        if access_token and refresh_token:
            # Handle the callback
            if handle_auth_callback(access_token, refresh_token):
                # Clear the URL parameters
                st.query_params.clear()
                st.session_state.navigate_to_page = "Start & Data"
                return True

        # Check for error in callback
        error = query_params.get('error')
        if error:
            error_description = query_params.get('error_description', 'Authentication failed')
            st.session_state['auth_error'] = error_description
            st.query_params.clear()

    except Exception as e:
        st.session_state['auth_error'] = f"Authentication error: {str(e)}"

    return False


def show_login_page():
    """
    Login Page: Professional two-column layout with Magic Link and Google OAuth.
    """
    # Initialize auth session state
    init_auth_session_state()

    # Check for OAuth callback in URL
    if _handle_oauth_callback():
        st.rerun()

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

        .google-btn img {
            width: 20px;
            height: 20px;
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
    </style>
    """, unsafe_allow_html=True)

    # --- TWO COLUMN LAYOUT ---
    col_left, col_right = st.columns([1, 1.3], gap="small")

    with col_left:
        st.write("")
        st.write("")

        # --- WELCOME TEXT ---
        st.markdown("""
            <link rel="preconnect" href="https://fonts.googleapis.com">
            <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
            <link href="https://fonts.googleapis.com/css2?family=Exo+2:wght@400;500;600;700;800;900&display=swap" rel="stylesheet">
            <div style="text-align: center; margin-bottom: 30px;">
                <div class="exo2-heading" style="font-family: 'Exo 2', sans-serif !important; font-size: 36px; font-weight: 700 !important; color: #302BFF; text-transform: uppercase; letter-spacing: 2px;">
                    Welcome to
                </div>
            </div>
        """, unsafe_allow_html=True)

        # --- LOGO ---
        logo_b64 = _get_image_base64("CashflowEnginelogo.png")
        if logo_b64:
            st.markdown(f"""
                <div style="text-align: center; margin-bottom: 40px;">
                    <img src="data:image/png;base64,{logo_b64}"
                         style="width: 384px; height: auto; max-width: 100%;"
                         alt="Cashflow Engine Logo" />
                </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
                <div style="text-align: center; margin-bottom: 40px;">
                    <div style="font-family: 'Exo 2', sans-serif !important; font-size: 32px; font-weight: 800 !important;
                                color: #302BFF; text-transform: uppercase; letter-spacing: 1px;">
                        CASHFLOW ENGINE
                    </div>
                </div>
            """, unsafe_allow_html=True)

        # --- SUCCESS MESSAGE (Magic Link Sent) ---
        if st.session_state.get('magic_link_sent'):
            st.markdown("""
                <div class="success-message">
                    <p><strong>Check your email!</strong><br>
                    We've sent you a secure login link. Click it to sign in instantly.</p>
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

        # --- INTRO TEXT ---
        if not st.session_state.get('magic_link_sent'):
            st.markdown("""
                <div style="text-align: center; margin-bottom: 25px;">
                    <span style="font-family: 'Poppins', sans-serif; font-size: 14px; color: #6B7280;">
                        Sign in to access your portfolio analytics
                    </span>
                </div>
            """, unsafe_allow_html=True)

        st.write("")

        # --- LOGIN FORM ---
        form_col1, form_col2, form_col3 = st.columns([0.3, 3, 0.3])

        with form_col2:
            # --- GOOGLE SIGN-IN BUTTON ---
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
                # Fallback if Google OAuth not configured
                if st.button("Continue with Google", use_container_width=True, type="secondary", disabled=True):
                    pass
                st.caption("Google Sign-In not configured")

            # --- DIVIDER ---
            st.markdown("""
                <div class="divider">
                    <div class="divider-line"></div>
                    <span class="divider-text">or</span>
                    <div class="divider-line"></div>
                </div>
            """, unsafe_allow_html=True)

            # --- MAGIC LINK FORM ---
            if not st.session_state.get('magic_link_sent'):
                email = st.text_input(
                    "Email Address",
                    placeholder="Enter your email address",
                    key="login_email",
                    label_visibility="collapsed"
                )

                st.write("")

                # Privacy checkbox
                privacy_accepted = st.checkbox(
                    "I accept the [Privacy Policy](/privacy)",
                    key="privacy_checkbox",
                    value=st.session_state.get('privacy_accepted', False)
                )

                st.write("")

                # Send Magic Link Button
                if st.button("Send Magic Link", use_container_width=True, type="primary", key="magic_link_button"):
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
                        # Send magic link
                        result = sign_in_with_magic_link(email)
                        if result['success']:
                            st.session_state['magic_link_sent'] = True
                            st.session_state['user_email'] = email
                            st.session_state['privacy_accepted'] = True
                        else:
                            st.session_state['auth_error'] = result['message']
                        st.rerun()

                # Privacy notice
                st.markdown("""
                    <div class="privacy-notice">
                        By signing in, you agree to our <a href="/privacy">Privacy Policy</a>.
                        We use your email only for authentication and will never share it with third parties.
                    </div>
                """, unsafe_allow_html=True)

            else:
                # Magic link was sent - show confirmation
                st.markdown(f"""
                    <div style="text-align: center; padding: 20px 0;">
                        <p style="font-family: 'Poppins', sans-serif; font-size: 14px; color: #4B5563;">
                            Sent to: <strong>{st.session_state.get('user_email', '')}</strong>
                        </p>
                    </div>
                """, unsafe_allow_html=True)

                # Resend button
                col_a, col_b, col_c = st.columns([1, 2, 1])
                with col_b:
                    if st.button("Send New Link", use_container_width=True, type="secondary"):
                        st.session_state['magic_link_sent'] = False
                        st.rerun()

                    st.write("")

                    if st.button("Use Different Email", use_container_width=True, type="tertiary"):
                        st.session_state['magic_link_sent'] = False
                        st.session_state['user_email'] = None
                        st.rerun()

    # --- RIGHT PANEL: MARKETING ---
    with col_right:
        marketing_image_b64 = _get_image_base64("login_marketing_panel.png")

        if marketing_image_b64:
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
            # Fallback marketing content
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
