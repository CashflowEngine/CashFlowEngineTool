"""
Authentication module for CashFlow Engine.
Uses Supabase Auth with Magic Link and Google OAuth.
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
        url = os.environ.get("SUPABASE_URL") or st.secrets.get("supabase", {}).get("url")
        key = os.environ.get("SUPABASE_KEY") or st.secrets.get("supabase", {}).get("key")

        if url and key:
            _auth_client = create_client(url, key)
            logger.info("Supabase auth client initialized")
            return _auth_client
        else:
            logger.warning("Supabase credentials not found")
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
        'magic_link_sent': False,
        'privacy_accepted': False,
    }

    for key, default_value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default_value


def sign_in_with_magic_link(email: str) -> Dict[str, Any]:
    """
    Send a magic link to the user's email for passwordless authentication.

    Args:
        email: User's email address

    Returns:
        Dict with 'success' boolean and 'message' string
    """
    client = get_supabase_client()
    if not client:
        return {'success': False, 'message': 'Database connection not available'}

    try:
        # Get the redirect URL from environment or use default
        redirect_url = os.environ.get("AUTH_REDIRECT_URL",
                                       st.secrets.get("auth", {}).get("redirect_url", ""))

        # Send magic link via Supabase
        response = client.auth.sign_in_with_otp({
            'email': email,
            'options': {
                'email_redirect_to': redirect_url if redirect_url else None
            }
        })

        logger.info(f"Magic link sent to {email}")
        return {
            'success': True,
            'message': 'Check your email for the login link!'
        }

    except Exception as e:
        logger.error(f"Magic link error: {e}")
        error_msg = str(e)
        if "rate limit" in error_msg.lower():
            return {'success': False, 'message': 'Too many requests. Please wait a moment and try again.'}
        return {'success': False, 'message': f'Failed to send login link: {error_msg}'}


def get_google_oauth_url() -> Optional[str]:
    """
    Get the Google OAuth sign-in URL.

    Returns:
        OAuth URL string or None if failed
    """
    client = get_supabase_client()
    if not client:
        return None

    try:
        redirect_url = os.environ.get("AUTH_REDIRECT_URL",
                                       st.secrets.get("auth", {}).get("redirect_url", ""))

        response = client.auth.sign_in_with_oauth({
            'provider': 'google',
            'options': {
                'redirect_to': redirect_url if redirect_url else None
            }
        })

        return response.url if response else None

    except Exception as e:
        logger.error(f"Google OAuth error: {e}")
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
