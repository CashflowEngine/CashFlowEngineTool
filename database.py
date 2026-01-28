import streamlit as st
import pandas as pd
import numpy as np
import os
import logging
from supabase import create_client

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- DATABASE SETUP ---
DB_AVAILABLE = False
supabase = None
try:
    # Railway Environment Variables OR Streamlit Secrets
    url = os.environ.get("SUPABASE_URL") or st.secrets.get("supabase", {}).get("url")
    key = os.environ.get("SUPABASE_KEY") or st.secrets.get("supabase", {}).get("key")

    if url and key:
        supabase = create_client(url, key)
        DB_AVAILABLE = True
        logger.info("Database connected successfully")
    else:
        logger.warning("No Supabase credentials found - database features disabled")
except ImportError:
    logger.warning("Supabase library not installed - database features disabled")
except Exception as e:
    logger.error(f"Database connection failed: {e}")


# --- USER CONTEXT HELPERS ---

def get_current_user_id():
    """Get the current authenticated user's ID from session state."""
    return st.session_state.get('user_id')


def get_authenticated_client():
    """
    Get Supabase client with user authentication context.
    Uses the access token from session state for RLS policies.
    """
    global supabase

    if not DB_AVAILABLE or not supabase:
        return None

    access_token = st.session_state.get('access_token')

    if access_token:
        try:
            # Set the auth header for RLS
            supabase.postgrest.auth(access_token)
        except Exception as e:
            logger.warning(f"Failed to set auth context: {e}")

    return supabase

# --- DATABASE HELPER FUNCTIONS ---

def clean_df_for_json(df):
    """Convert DataFrame to JSON-serializable format."""
    if df is None or df.empty:
        return []
    df_clean = df.copy()
    for col in df_clean.select_dtypes(include=['datetime64', 'datetimetz']).columns:
        df_clean[col] = df_clean[col].astype(str)
    df_clean = df_clean.replace({np.nan: None})
    return df_clean.to_dict(orient='records')

def repair_df_dates(df):
    """Repair and validate date columns with logging."""
    if df is None or df.empty:
        return pd.DataFrame()
    
    original_len = len(df)
    for col in ['timestamp', 'date', 'date_open', 'timestamp_open', 'timestamp_close']:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')
    
    if 'timestamp' in df.columns:
        df = df.dropna(subset=['timestamp'])
        dropped = original_len - len(df)
        if dropped > 0:
            logger.warning(f"Dropped {dropped} rows with invalid timestamps")
    
    return df

def save_analysis_to_db(name, bt_df, live_df=None):
    """Save analysis to database (legacy wrapper)."""
    return save_analysis_to_db_enhanced(name, bt_df, live_df)

def save_analysis_to_db_enhanced(name, bt_df, live_df=None, description="", tags=None):
    """Enhanced save with metadata and user association."""
    if not DB_AVAILABLE:
        st.error("Database not connected.")
        return False

    # Get current user ID for multi-user support
    user_id = get_current_user_id()
    access_token = st.session_state.get('access_token')

    logger.info(f"Save attempt - user_id: {user_id}, has_access_token: {access_token is not None}")

    if not user_id:
        logger.warning("No user_id found - saving without user association")
        st.warning("Warning: Not logged in. Data may not be saved to your account.")

    try:
        bt_json = clean_df_for_json(bt_df)
        live_json = clean_df_for_json(live_df)

        # Calculate metadata stats
        trade_count = len(bt_df) if bt_df is not None and not bt_df.empty else 0
        total_pnl = float(bt_df['pnl'].sum()) if bt_df is not None and not bt_df.empty else 0
        strategies = list(bt_df['strategy'].unique()) if bt_df is not None and not bt_df.empty else []

        date_start = None
        date_end = None
        if bt_df is not None and not bt_df.empty and 'timestamp' in bt_df.columns:
            date_start = str(bt_df['timestamp'].min().date())
            date_end = str(bt_df['timestamp'].max().date())

        metadata = {
            "description": description,
            "tags": tags or [],
            "trade_count": trade_count,
            "total_pnl": total_pnl,
            "strategies": strategies[:10],
            "date_start": date_start,
            "date_end": date_end,
            "has_live": live_df is not None and not live_df.empty
        }

        payload = {
            "version": 3,
            "backtest": bt_json,
            "live": live_json,
            "metadata": metadata
        }

        # Build insert data with optional user_id
        insert_data = {
            "name": name,
            "data_json": payload
        }

        # Add user_id if authenticated (for RLS and data isolation)
        if user_id:
            insert_data["user_id"] = user_id

        # Use authenticated client for RLS
        client = get_authenticated_client() or supabase
        client.table('analyses').insert(insert_data).execute()

        logger.info(f"Analysis '{name}' saved successfully for user {user_id}")

        # Clear cache to show new entry immediately
        get_analysis_list_for_user.clear()

        return True
    except Exception as e:
        logger.error(f"Enhanced save error: {e}")
        st.error(f"Save Error: {e}")
        return False

def get_analysis_list():
    """Retrieve list of saved analyses for the current user."""
    # Pass user_id for cache separation - each user gets their own cache
    user_id = get_current_user_id()
    return get_analysis_list_for_user(user_id=user_id)


@st.cache_data(ttl=60, show_spinner=False)
def get_analysis_list_for_user(user_id=None):
    """
    Get analysis list with metadata for the current user.
    OPTIMIZED: Fetches only the metadata field from the JSON column.
    NOTE: user_id (without underscore) IS included in cache key for per-user caching.
    """
    if not DB_AVAILABLE:
        return []

    logger.info(f"Fetching analyses for user_id: {user_id}")

    # Get authenticated client (RLS will filter by user automatically)
    client = get_authenticated_client() or supabase

    # If no RLS configured, filter by user_id manually
    # This is a fallback for when RLS policies are not yet set up

    try:
        # Build query with explicit user_id filter (required since RLS may not be configured)
        query = client.table('analyses').select(
            "id, name, created_at, user_id, data_json->metadata"
        )

        # CRITICAL: Always filter by user_id to ensure data isolation
        if user_id:
            query = query.eq('user_id', user_id)
            logger.info(f"Filtering analyses by user_id: {user_id}")
        else:
            logger.warning("No user_id provided - returning empty list for security")
            return []

        try:
            response = query.order('created_at', desc=True).execute()
            logger.info(f"Query returned {len(response.data)} records")
        except Exception as e:
            # Fallback for older Postgres versions or if JSON operator fails
            logger.warning(f"Optimized fetch failed: {e}, falling back to full fetch")
            response = client.table('analyses').select(
                "id, name, created_at, user_id, data_json"
            ).eq('user_id', user_id).order('created_at', desc=True).execute()

        analyses = []
        for item in response.data:
            analysis = {
                'id': item['id'],
                'name': item['name'],
                'created_at': item['created_at']
            }

            # Handle response structure (optimized vs full)
            if 'metadata' in item:
                # Optimized query result (it pulls the key up)
                metadata = item['metadata'] or {}
            elif 'data_json' in item:
                # Full query result or nested dict
                data_json = item['data_json'] or {}
                if isinstance(data_json, dict):
                    metadata = data_json.get('metadata', {})
                else:
                    metadata = {}
            else:
                metadata = {}

            # Ensure metadata is a dict (sometimes JSON columns return string if malformed)
            if not isinstance(metadata, dict):
                metadata = {}

            analysis['description'] = metadata.get('description', '')
            analysis['tags'] = metadata.get('tags', [])
            analysis['trade_count'] = metadata.get('trade_count', 0)
            analysis['total_pnl'] = metadata.get('total_pnl', 0)
            analysis['strategies'] = metadata.get('strategies', [])
            analysis['date_start'] = metadata.get('date_start', '')
            analysis['date_end'] = metadata.get('date_end', '')
            analysis['has_live'] = metadata.get('has_live', False)

            analyses.append(analysis)

        logger.info(f"Loaded {len(analyses)} analyses for user {user_id}")
        return analyses
    except Exception as e:
        logger.error(f"Failed to get enhanced list: {e}")
        return []

def delete_analysis_from_db(analysis_id):
    """Delete an analysis by ID. Filters by user_id for security."""
    if not DB_AVAILABLE:
        return False

    user_id = get_current_user_id()
    if not user_id:
        logger.error("Cannot delete - no user logged in")
        return False

    try:
        client = get_authenticated_client() or supabase
        # Filter by both analysis_id AND user_id for security
        client.table('analyses').delete().eq('id', analysis_id).eq('user_id', user_id).execute()
        logger.info(f"Analysis {analysis_id} deleted for user {user_id}")
        get_analysis_list_for_user.clear()  # Clear cache
        return True
    except Exception as e:
        logger.error(f"Delete error: {e}")
        return False


def rename_analysis_in_db(analysis_id, new_name):
    """Rename an analysis. Filters by user_id for security."""
    if not DB_AVAILABLE:
        return False

    user_id = get_current_user_id()
    if not user_id:
        logger.error("Cannot rename - no user logged in")
        return False

    try:
        # Use authenticated client for RLS
        client = get_authenticated_client() or supabase
        # Filter by both analysis_id AND user_id for security
        client.table('analyses').update({"name": new_name}).eq('id', analysis_id).eq('user_id', user_id).execute()
        logger.info(f"Analysis {analysis_id} renamed to {new_name} for user {user_id}")
        get_analysis_list_for_user.clear()  # Clear cache
        return True
    except Exception as e:
        logger.error(f"Rename error: {e}")
        return False


@st.cache_data(show_spinner=False)
def load_analysis_from_db(analysis_id, _user_id=None):
    """
    Load analysis from database.
    CACHED: Expensive JSON parsing and dataframe creation is cached indefinitely for specific ID.
    Note: _user_id prefixed with underscore to exclude from cache key but enables per-user caching.
    """
    if not DB_AVAILABLE:
        return None, None

    # Security check - must have user_id
    if not _user_id:
        logger.warning("load_analysis_from_db called without user_id")
        _user_id = get_current_user_id()
        if not _user_id:
            logger.error("Cannot load analysis - no user logged in")
            return None, None

    try:
        # Use authenticated client for RLS
        client = get_authenticated_client() or supabase

        # Filter by both analysis_id AND user_id for security
        logger.info(f"Loading analysis {analysis_id} for user {_user_id}")
        response = client.table('analyses').select("data_json, user_id").eq('id', analysis_id).eq('user_id', _user_id).execute()

        if response.data:
            json_data = response.data[0]['data_json']
            if isinstance(json_data, list):
                bt_df = pd.DataFrame(json_data)
                return repair_df_dates(bt_df), None
            elif isinstance(json_data, dict):
                bt_data = json_data.get('backtest', [])
                live_data = json_data.get('live', [])
                bt_df = pd.DataFrame(bt_data) if bt_data else pd.DataFrame()
                live_df = pd.DataFrame(live_data) if live_data else None
                return repair_df_dates(bt_df), repair_df_dates(live_df) if live_df is not None else None
        return None, None
    except Exception as e:
        logger.error(f"Load Error: {e}")
        st.error(f"Load Error: {e}")
        return None, None
