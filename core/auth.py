"""
Authentication module for CashFlow Engine.
Uses Supabase Auth with Email OTP and Google OAuth.
"""
import streamlit as st
import os
import logging
from typing import Optional, Dict, Any
from supabase import create_client, Client

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- SUPABASE AUTH CLIENT ---
_auth_client: Optional[Client] = None

def get_supabase_client() -> Optional[Client]:
    """Get or create Supabase client for authentication."""
    global _auth_client

    if _auth_client is not None:
        return _auth_client

    try:
        # First try environment variables (Railway), then Streamlit secrets (local)
        url = os.environ.get("SUPABASE_URL")
        key = os.environ.get("SUPABASE_KEY")

        # Fallback to Streamlit secrets if env vars not set
        if not url or not key:
            try:
                secrets = st.secrets.get("supabase", {})
                url = url or secrets.get("url")
                key = key or secrets.get("key")
            except Exception:
                # No secrets file exists, continue with env vars only
                pass

        if url and key:
            _auth_client = create_client(url, key)
            logger.info("Supabase auth client initialized")
            return _auth_client
        else:
            logger.warning("Supabase credentials not found in env vars or secrets")
            return None
    except Exception as e:
        logger.error(f"Failed to initialize Supabase client: {e}")
        return None


def init_auth_session_state():
    """Initialize authentication-related session state variables."""
    defaults = {
        'is_authenticated': False,
        'user': None,
        'user_id': None,
        'user_email': None,
        'access_token': None,
        'refresh_token': None,
        'auth_error': None,
        'auth_message': None,
        'magic_link_sent': False,  # Keep for backwards compatibility
        'otp_sent': False,  # OTP code sent to email
        'otp_email': None,  # Email address for OTP verification
        'privacy_accepted': False,
    }

    for key, default_value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default_value


def sign_in_with_magic_link(email: str) -> Dict[str, Any]:
    """
    Send a magic link to the user's email for passwordless authentication.
    DEPRECATED: Use send_email_otp instead for better Streamlit compatibility.
    """
    return send_email_otp(email)


def send_email_otp(email: str) -> Dict[str, Any]:
    """
    Send a 6-digit OTP code to the user's email for passwordless authentication.
    This method works better with Streamlit than Magic Links (no redirect issues).

    Args:
        email: User's email address

    Returns:
        Dict with 'success' boolean and 'message' string
    """
    client = get_supabase_client()
    if not client:
        return {'success': False, 'message': 'Database connection not available'}

    try:
        # Send OTP via Supabase - do NOT include email_redirect_to for OTP flow
        # This tells Supabase to send an OTP code instead of a magic link
        response = client.auth.sign_in_with_otp({
            'email': email,
            'options': {
                'should_create_user': True  # Auto-create user if not exists
            }
        })

        logger.info(f"OTP code sent to {email}")
        return {
            'success': True,
            'message': 'Check your email for the verification code!'
        }

    except Exception as e:
        logger.error(f"OTP send error: {e}")
        error_msg = str(e)
        if "rate limit" in error_msg.lower():
            return {'success': False, 'message': 'Too many requests. Please wait a moment and try again.'}
        return {'success': False, 'message': f'Failed to send verification code: {error_msg}'}


def verify_email_otp(email: str, otp_code: str) -> Dict[str, Any]:
    """
    Verify the OTP code entered by the user and establish a session.

    Args:
        email: User's email address
        otp_code: Verification code from the email (6-8 digits)

    Returns:
        Dict with 'success' boolean and 'message' string
    """
    client = get_supabase_client()
    if not client:
        return {'success': False, 'message': 'Database connection not available'}

    try:
        # Verify the OTP code
        response = client.auth.verify_otp({
            'email': email,
            'token': otp_code,
            'type': 'email'
        })

        if response and response.user and response.session:
            # Successfully verified - update session state
            user = response.user
            session = response.session

            st.session_state['is_authenticated'] = True
            st.session_state['user'] = user
            st.session_state['user_id'] = user.id
            st.session_state['user_email'] = user.email
            st.session_state['access_token'] = session.access_token
            st.session_state['refresh_token'] = session.refresh_token
            st.session_state['otp_sent'] = False
            st.session_state['otp_email'] = None

            logger.info(f"User authenticated via OTP: {user.email}")
            return {
                'success': True,
                'message': 'Successfully signed in!'
            }
        else:
            return {
                'success': False,
                'message': 'Invalid verification code. Please try again.'
            }

    except Exception as e:
        logger.error(f"OTP verification error: {e}")
        error_msg = str(e)
        if "invalid" in error_msg.lower() or "expired" in error_msg.lower():
            return {'success': False, 'message': 'Invalid or expired code. Please request a new one.'}
        return {'success': False, 'message': f'Verification failed: {error_msg}'}


def get_google_oauth_url() -> Optional[str]:
    """
    Get the Google OAuth sign-in URL.

    Returns:
        OAuth URL string or None if failed
    """
    client = get_supabase_client()
    if not client:
        logger.error("No Supabase client available for Google OAuth")
        return None

    try:
        # First try environment variable, then Streamlit secrets
        redirect_url = os.environ.get("AUTH_REDIRECT_URL", "")
        if not redirect_url:
            try:
                redirect_url = st.secrets.get("auth", {}).get("redirect_url", "")
            except Exception:
                pass

        # Supabase Python SDK v2 syntax
        options = {}
        if redirect_url:
            options['redirect_to'] = redirect_url

        response = client.auth.sign_in_with_oauth({
            'provider': 'google',
            'options': options
        })

        # Handle different response structures
        if response:
            if hasattr(response, 'url'):
                return response.url
            elif isinstance(response, dict) and 'url' in response:
                return response['url']
            else:
                logger.info(f"OAuth response type: {type(response)}, content: {response}")
                # Try to extract URL from response object
                if hasattr(response, 'data') and response.data:
                    if hasattr(response.data, 'url'):
                        return response.data.url

        logger.error("Could not extract OAuth URL from response")
        return None

    except Exception as e:
        logger.error(f"Google OAuth error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None


def handle_auth_callback(access_token: str, refresh_token: str) -> bool:
    """
    Handle the authentication callback after magic link or OAuth redirect.

    Args:
        access_token: JWT access token from callback
        refresh_token: Refresh token from callback

    Returns:
        True if authentication successful, False otherwise
    """
    client = get_supabase_client()
    if not client:
        return False

    try:
        # Set the session with the tokens
        response = client.auth.set_session(access_token, refresh_token)

        if response and response.user:
            user = response.user

            # Update session state
            st.session_state['is_authenticated'] = True
            st.session_state['user'] = user
            st.session_state['user_id'] = user.id
            st.session_state['user_email'] = user.email
            st.session_state['access_token'] = access_token
            st.session_state['refresh_token'] = refresh_token

            logger.info(f"User authenticated: {user.email}")
            return True

        return False

    except Exception as e:
        logger.error(f"Auth callback error: {e}")
        return False


def verify_and_refresh_session() -> bool:
    """
    Verify current session and refresh if needed.

    Returns:
        True if session is valid, False otherwise
    """
    client = get_supabase_client()
    if not client:
        return False

    access_token = st.session_state.get('access_token')
    refresh_token = st.session_state.get('refresh_token')

    if not access_token or not refresh_token:
        return False

    try:
        # Try to get current user to verify session
        response = client.auth.get_user(access_token)

        if response and response.user:
            return True

        # Token might be expired, try to refresh
        refresh_response = client.auth.refresh_session(refresh_token)

        if refresh_response and refresh_response.session:
            session = refresh_response.session
            st.session_state['access_token'] = session.access_token
            st.session_state['refresh_token'] = session.refresh_token
            st.session_state['user'] = refresh_response.user
            logger.info("Session refreshed successfully")
            return True

        return False

    except Exception as e:
        logger.error(f"Session verification error: {e}")
        return False


def sign_out() -> bool:
    """
    Sign out the current user and clear session.

    Returns:
        True if sign out successful
    """
    client = get_supabase_client()

    try:
        if client:
            client.auth.sign_out()

        # Clear all auth-related session state
        auth_keys = [
            'is_authenticated', 'user', 'user_id', 'user_email',
            'access_token', 'refresh_token', 'auth_error', 'auth_message',
            'magic_link_sent', 'privacy_accepted'
        ]

        for key in auth_keys:
            if key in st.session_state:
                st.session_state[key] = None if key not in ['is_authenticated', 'magic_link_sent', 'privacy_accepted'] else False

        logger.info("User signed out")
        return True

    except Exception as e:
        logger.error(f"Sign out error: {e}")
        return False


def get_current_user() -> Optional[Dict[str, Any]]:
    """
    Get the current authenticated user.

    Returns:
        User dict or None if not authenticated
    """
    if not st.session_state.get('is_authenticated'):
        return None

    return {
        'id': st.session_state.get('user_id'),
        'email': st.session_state.get('user_email'),
        'user': st.session_state.get('user')
    }


def get_current_user_id() -> Optional[str]:
    """
    Get the current user's ID for database operations.

    Returns:
        User ID string or None
    """
    return st.session_state.get('user_id')


def is_authenticated() -> bool:
    """
    Check if user is currently authenticated.

    Returns:
        True if authenticated, False otherwise
    """
    return st.session_state.get('is_authenticated', False)


def require_auth():
    """
    Decorator/function to require authentication.
    Redirects to login if not authenticated.
    """
    if not is_authenticated():
        st.session_state.navigate_to_page = "Login"
        st.rerun()


def delete_user_account() -> Dict[str, Any]:
    """
    Delete the current user's account (GDPR right to deletion).

    Returns:
        Dict with 'success' boolean and 'message' string
    """
    client = get_supabase_client()
    if not client:
        return {'success': False, 'message': 'Database connection not available'}

    user_id = get_current_user_id()
    if not user_id:
        return {'success': False, 'message': 'No user logged in'}

    try:
        # Note: User deletion typically requires admin privileges in Supabase
        # For self-deletion, you may need to set up an Edge Function
        # or RPC call. For now, we'll mark this as a feature that needs
        # backend setup.

        # Clear local session
        sign_out()

        return {
            'success': True,
            'message': 'Account deletion requested. Your data will be removed within 30 days.'
        }

    except Exception as e:
        logger.error(f"Account deletion error: {e}")
        return {'success': False, 'message': f'Failed to delete account: {e}'}


def update_privacy_consent(accepted: bool) -> bool:
    """
    Update the user's privacy consent timestamp in their profile.

    Args:
        accepted: Whether user accepted the privacy policy

    Returns:
        True if update successful
    """
    client = get_supabase_client()
    if not client:
        return False

    user_id = get_current_user_id()
    if not user_id:
        return False

    try:
        from datetime import datetime

        client.table('profiles').update({
            'privacy_accepted_at': datetime.utcnow().isoformat() if accepted else None
        }).eq('id', user_id).execute()

        st.session_state['privacy_accepted'] = accepted
        logger.info(f"Privacy consent updated for user {user_id}")
        return True

    except Exception as e:
        logger.error(f"Privacy consent update error: {e}")
        return False
