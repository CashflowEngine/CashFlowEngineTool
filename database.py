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


def clean_value_for_json(value):
    """Convert a value to JSON-serializable format."""
    if value is None:
        return None
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, (np.int64, np.int32)):
        return int(value)
    if isinstance(value, (np.float64, np.float32)):
        if np.isnan(value) or np.isinf(value):
            return None
        return float(value)
    if isinstance(value, pd.Series):
        return clean_df_for_json(value.to_frame())
    if isinstance(value, pd.DataFrame):
        return clean_df_for_json(value)
    if isinstance(value, dict):
        return {k: clean_value_for_json(v) for k, v in value.items()}
    if isinstance(value, list):
        return [clean_value_for_json(v) for v in value]
    if isinstance(value, (pd.Timestamp, np.datetime64)):
        return str(value)
    return value


def gather_calculation_results():
    """
    Gather all calculation results from session_state for saving.
    Returns a dict with all computed results.
    """
    results = {}

    # --- Monte Carlo Results ---
    if 'mc_results' in st.session_state and st.session_state.mc_results:
        mc = st.session_state.mc_results
        # Don't save the full paths array (too large), just the summary stats
        results['monte_carlo'] = {
            'profit': clean_value_for_json(mc.get('profit')),
            'cagr': clean_value_for_json(mc.get('cagr')),
            'dd_mean': clean_value_for_json(mc.get('dd_mean')),
            'mar': clean_value_for_json(mc.get('mar')),
            'mart': clean_value_for_json(mc.get('mart')),
            'p95': clean_value_for_json(mc.get('p95')),
            'p50': clean_value_for_json(mc.get('p50')),
            'p05': clean_value_for_json(mc.get('p05')),
            'cagr_p95': clean_value_for_json(mc.get('cagr_p95')),
            'cagr_p50': clean_value_for_json(mc.get('cagr_p50')),
            'cagr_p05': clean_value_for_json(mc.get('cagr_p05')),
            'd95': clean_value_for_json(mc.get('d95')),
            'd50': clean_value_for_json(mc.get('d50')),
            'd05': clean_value_for_json(mc.get('d05')),
            'start_cap': clean_value_for_json(mc.get('start_cap')),
            'sim_months': clean_value_for_json(mc.get('sim_months')),
            'n_sims': clean_value_for_json(mc.get('n_sims')),
            'n_steps': clean_value_for_json(mc.get('n_steps')),
            'prob_profit': clean_value_for_json(mc.get('prob_profit')),
            'injected_count': clean_value_for_json(mc.get('injected_count')),
            'n_stress_per_sim': clean_value_for_json(mc.get('n_stress_per_sim')),
            'injection_mode': mc.get('injection_mode'),
        }
        # Save end values distribution (smaller than full paths)
        if 'end_vals' in mc and mc['end_vals'] is not None:
            results['monte_carlo']['end_vals_percentiles'] = {
                'p1': float(np.percentile(mc['end_vals'], 1)),
                'p5': float(np.percentile(mc['end_vals'], 5)),
                'p10': float(np.percentile(mc['end_vals'], 10)),
                'p25': float(np.percentile(mc['end_vals'], 25)),
                'p50': float(np.percentile(mc['end_vals'], 50)),
                'p75': float(np.percentile(mc['end_vals'], 75)),
                'p90': float(np.percentile(mc['end_vals'], 90)),
                'p95': float(np.percentile(mc['end_vals'], 95)),
                'p99': float(np.percentile(mc['end_vals'], 99)),
            }

    # Monte Carlo stress test strategies
    if 'stress_test_selected_strategies' in st.session_state:
        if 'monte_carlo' not in results:
            results['monte_carlo'] = {}
        results['monte_carlo']['stress_test_strategies'] = st.session_state.stress_test_selected_strategies

    # --- Portfolio Builder Results ---
    if 'portfolio_allocation' in st.session_state and st.session_state.portfolio_allocation:
        results['portfolio_builder'] = {
            'allocation': clean_value_for_json(st.session_state.portfolio_allocation),
            'category_overrides': clean_value_for_json(st.session_state.get('category_overrides', {})),
            'kelly_pct': clean_value_for_json(st.session_state.get('kelly_pct')),
            'builder_account': clean_value_for_json(st.session_state.get('builder_account')),
            'builder_dates': clean_value_for_json(st.session_state.get('builder_dates')),
        }

    # --- MEIC Analysis Settings ---
    meic_keys = ['meic_entry_time_filter', 'meic_equity_strategies', 'meic_source',
                 'meic_dates', 'meic_account', 'meic_strats', 'meic_chart_metric',
                 'meic_monthly_mode', 'meic_heatmap_metric']
    meic_data = {}
    for key in meic_keys:
        if key in st.session_state and st.session_state[key] is not None:
            meic_data[key] = clean_value_for_json(st.session_state[key])
    if meic_data:
        results['meic_analysis'] = meic_data

    # --- Strategy DNA Cache ---
    if 'dna_cache' in st.session_state and st.session_state.dna_cache:
        results['dna_cache'] = clean_value_for_json(st.session_state.dna_cache)

    logger.info(f"Gathered calculation results: {list(results.keys())}")
    return results


def restore_calculation_results(calculations):
    """
    Restore calculation results to session_state after loading.
    """
    if not calculations:
        return

    # --- Restore Monte Carlo Results ---
    if 'monte_carlo' in calculations:
        mc = calculations['monte_carlo']
        st.session_state.mc_results = mc
        if 'stress_test_strategies' in mc:
            st.session_state.stress_test_selected_strategies = mc['stress_test_strategies']
        logger.info("Restored Monte Carlo results")

    # --- Restore Portfolio Builder ---
    if 'portfolio_builder' in calculations:
        pb = calculations['portfolio_builder']
        if 'allocation' in pb:
            st.session_state.portfolio_allocation = pb['allocation']
        if 'category_overrides' in pb:
            st.session_state.category_overrides = pb['category_overrides']
        if 'kelly_pct' in pb:
            st.session_state.kelly_pct = pb['kelly_pct']
        if 'builder_account' in pb:
            st.session_state.builder_account = pb['builder_account']
        if 'builder_dates' in pb:
            st.session_state.builder_dates = tuple(pb['builder_dates']) if pb['builder_dates'] else None
        logger.info("Restored Portfolio Builder settings")

    # --- Restore MEIC Analysis ---
    if 'meic_analysis' in calculations:
        for key, value in calculations['meic_analysis'].items():
            if key == 'meic_dates' and value:
                st.session_state[key] = tuple(value)
            else:
                st.session_state[key] = value
        logger.info("Restored MEIC Analysis settings")

    # --- Restore DNA Cache ---
    if 'dna_cache' in calculations:
        st.session_state.dna_cache = calculations['dna_cache']
        logger.info("Restored DNA cache")

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
    """Enhanced save with metadata, user association, and all analysis results."""
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

        # Gather all calculation results from session_state
        calculations = gather_calculation_results()
        has_calculations = bool(calculations)
        metadata["has_calculations"] = has_calculations

        payload = {
            "version": 4,  # Bumped version for calculations support
            "backtest": bt_json,
            "live": live_json,
            "metadata": metadata,
            "calculations": calculations  # NEW: All calculation results
        }

        logger.info(f"Saving with calculations: {list(calculations.keys()) if calculations else 'none'}")

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


def _collect_analysis_results():
    """Collect all analysis results from session state for saving."""
    results = {}

    # Monte Carlo results
    mc_results = st.session_state.get('mc_results')
    if mc_results:
        results['mc_results'] = mc_results

    # Portfolio Builder results
    portfolio_allocation = st.session_state.get('portfolio_allocation')
    if portfolio_allocation:
        results['portfolio_allocation'] = portfolio_allocation

    selected_strategies = st.session_state.get('selected_strategies')
    if selected_strategies:
        results['selected_strategies'] = list(selected_strategies) if not isinstance(selected_strategies, list) else selected_strategies

    # Correlation matrix (convert to dict for JSON serialization)
    correlation_matrix = st.session_state.get('correlation_matrix')
    if correlation_matrix is not None and hasattr(correlation_matrix, 'to_dict'):
        results['correlation_matrix'] = correlation_matrix.to_dict()

    # MEIC/DNA analysis results
    dna_cache = st.session_state.get('dna_cache')
    if dna_cache:
        results['dna_cache'] = dna_cache

    # Strategy base stats
    strategy_base_stats = st.session_state.get('strategy_base_stats')
    if strategy_base_stats:
        results['strategy_base_stats'] = strategy_base_stats

    # Daily P&L series (convert to dict for JSON)
    daily_pnl_series = st.session_state.get('daily_pnl_series')
    if daily_pnl_series is not None and hasattr(daily_pnl_series, 'to_dict'):
        results['daily_pnl_series'] = daily_pnl_series.to_dict()

    # Precomputed data from precompute module
    precompute_cache = st.session_state.get('precompute_cache')
    if precompute_cache:
        results['precompute_cache'] = precompute_cache

    logger.info(f"Collected analysis results: {list(results.keys())}")
    return results


def _restore_analysis_results(analysis_results):
    """Restore analysis results to session state after loading."""
    if not analysis_results:
        return

    # Monte Carlo results
    if 'mc_results' in analysis_results:
        st.session_state['mc_results'] = analysis_results['mc_results']

    # Portfolio Builder results
    if 'portfolio_allocation' in analysis_results:
        st.session_state['portfolio_allocation'] = analysis_results['portfolio_allocation']

    if 'selected_strategies' in analysis_results:
        st.session_state['selected_strategies'] = analysis_results['selected_strategies']

    # Correlation matrix (convert from dict back to DataFrame)
    if 'correlation_matrix' in analysis_results:
        st.session_state['correlation_matrix'] = pd.DataFrame(analysis_results['correlation_matrix'])

    # MEIC/DNA analysis results
    if 'dna_cache' in analysis_results:
        st.session_state['dna_cache'] = analysis_results['dna_cache']

    # Strategy base stats
    if 'strategy_base_stats' in analysis_results:
        st.session_state['strategy_base_stats'] = analysis_results['strategy_base_stats']

    # Daily P&L series (convert from dict back to Series)
    if 'daily_pnl_series' in analysis_results:
        st.session_state['daily_pnl_series'] = pd.Series(analysis_results['daily_pnl_series'])

    # Precomputed data
    if 'precompute_cache' in analysis_results:
        st.session_state['precompute_cache'] = analysis_results['precompute_cache']

    logger.info(f"Restored analysis results: {list(analysis_results.keys())}")

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
def load_analysis_from_db(analysis_id, _user_id=None, restore_calculations=True):
    """
    Load analysis from database.
    CACHED: Expensive JSON parsing and dataframe creation is cached indefinitely for specific ID.
    Note: _user_id prefixed with underscore to exclude from cache key but enables per-user caching.

    Returns: (bt_df, live_df, has_calculations)
    If restore_calculations=True, also restores calculation results to session_state.
    """
    if not DB_AVAILABLE:
        return None, None, False

    # Security check - must have user_id
    if not _user_id:
        logger.warning("load_analysis_from_db called without user_id")
        _user_id = get_current_user_id()
        if not _user_id:
            logger.error("Cannot load analysis - no user logged in")
            return None, None, False

    try:
        # Get cached raw data
        json_data = _load_analysis_data_cached(analysis_id, _user_id)

        if json_data is None:
            return None, None

        # Handle legacy list format
        if isinstance(json_data, list):
            bt_df = pd.DataFrame(json_data)
            return repair_df_dates(bt_df), None

        # Handle dict format (version 3+)
        elif isinstance(json_data, dict):
            bt_data = json_data.get('backtest', [])
            live_data = json_data.get('live', [])
            bt_df = pd.DataFrame(bt_data) if bt_data else pd.DataFrame()
            live_df = pd.DataFrame(live_data) if live_data else None

            # Restore analysis results (version 4+)
            analysis_results = json_data.get('analysis_results', {})
            if analysis_results:
                _restore_analysis_results(analysis_results)
                logger.info(f"Restored {len(analysis_results)} analysis result categories")

            return repair_df_dates(bt_df), repair_df_dates(live_df) if live_df is not None else None

        if response.data:
            json_data = response.data[0]['data_json']
            has_calculations = False

            if isinstance(json_data, list):
                # Legacy format (version 1)
                bt_df = pd.DataFrame(json_data)
                return repair_df_dates(bt_df), None, False

            elif isinstance(json_data, dict):
                bt_data = json_data.get('backtest', [])
                live_data = json_data.get('live', [])
                bt_df = pd.DataFrame(bt_data) if bt_data else pd.DataFrame()
                live_df = pd.DataFrame(live_data) if live_data else None

                # Version 4+: Restore calculations if present
                calculations = json_data.get('calculations', {})
                if calculations and restore_calculations:
                    restore_calculation_results(calculations)
                    has_calculations = True
                    logger.info(f"Restored calculations: {list(calculations.keys())}")

                return (
                    repair_df_dates(bt_df),
                    repair_df_dates(live_df) if live_df is not None else None,
                    has_calculations
                )

        return None, None, False
    except Exception as e:
        logger.error(f"Load Error: {e}")
        st.error(f"Load Error: {e}")
        return None, None, False


def load_analysis_legacy(analysis_id, _user_id=None):
    """
    Legacy wrapper for backward compatibility.
    Returns only (bt_df, live_df) for code that expects 2 return values.
    """
    bt_df, live_df, _ = load_analysis_from_db(analysis_id, _user_id)
    return bt_df, live_df


# ============================================================
# GLOBAL STRATEGY DNA DATABASE
# Shared classifications across all users
# ============================================================

@st.cache_data(ttl=300, show_spinner=False)  # Cache for 5 minutes
def load_global_strategy_dna():
    """
    Load all strategy DNA from the global database.
    Returns a dict: {strategy_name: {category, option_strategy, deltas, etc.}}
    This is shared across all users.
    """
    if not DB_AVAILABLE:
        return {}

    try:
        client = get_authenticated_client() or supabase
        response = client.table('strategy_dna').select("*").execute()

        dna_dict = {}
        for item in response.data:
            strategy_name = item.get('strategy_name')
            if strategy_name:
                dna_dict[strategy_name] = {
                    'category': item.get('category'),
                    'option_strategy': item.get('option_strategy'),
                    'delta_long': item.get('delta_long'),
                    'delta_short': item.get('delta_short'),
                    'gamma_exposure': item.get('gamma_exposure'),
                    'theta_exposure': item.get('theta_exposure'),
                    'vega_exposure': item.get('vega_exposure'),
                    'avg_dte': item.get('avg_dte'),
                    'typical_margin': item.get('typical_margin'),
                    'notes': item.get('notes'),
                    'confidence_score': item.get('confidence_score', 1),
                }

        logger.info(f"Loaded {len(dna_dict)} strategies from global DNA database")
        return dna_dict

    except Exception as e:
        logger.error(f"Failed to load global DNA: {e}")
        return {}


def save_strategy_dna(strategy_name, category=None, option_strategy=None,
                      delta_long=None, delta_short=None, gamma_exposure=None,
                      theta_exposure=None, vega_exposure=None, avg_dte=None,
                      typical_margin=None, notes=None):
    """
    Save or update a strategy's DNA in the global database.
    If the strategy exists, updates it and increments confidence_score.
    """
    if not DB_AVAILABLE:
        return False

    user_id = get_current_user_id()
    if not user_id:
        logger.warning("Cannot save DNA - no user logged in")
        return False

    try:
        client = get_authenticated_client() or supabase

        # Check if strategy already exists
        existing = client.table('strategy_dna').select("id, confidence_score").eq(
            'strategy_name', strategy_name
        ).execute()

        dna_data = {
            'strategy_name': strategy_name,
            'updated_by': user_id,
        }

        # Only add non-None values
        if category is not None:
            dna_data['category'] = category
        if option_strategy is not None:
            dna_data['option_strategy'] = option_strategy
        if delta_long is not None:
            dna_data['delta_long'] = float(delta_long)
        if delta_short is not None:
            dna_data['delta_short'] = float(delta_short)
        if gamma_exposure is not None:
            dna_data['gamma_exposure'] = float(gamma_exposure)
        if theta_exposure is not None:
            dna_data['theta_exposure'] = float(theta_exposure)
        if vega_exposure is not None:
            dna_data['vega_exposure'] = float(vega_exposure)
        if avg_dte is not None:
            dna_data['avg_dte'] = int(avg_dte)
        if typical_margin is not None:
            dna_data['typical_margin'] = float(typical_margin)
        if notes is not None:
            dna_data['notes'] = notes

        if existing.data:
            # Update existing - increment confidence score
            current_confidence = existing.data[0].get('confidence_score', 1)
            dna_data['confidence_score'] = current_confidence + 1
            client.table('strategy_dna').update(dna_data).eq(
                'strategy_name', strategy_name
            ).execute()
            logger.info(f"Updated DNA for '{strategy_name}' (confidence: {dna_data['confidence_score']})")
        else:
            # Insert new
            dna_data['created_by'] = user_id
            dna_data['confidence_score'] = 1
            client.table('strategy_dna').insert(dna_data).execute()
            logger.info(f"Created new DNA entry for '{strategy_name}'")

        # Clear cache to reflect changes
        load_global_strategy_dna.clear()
        return True

    except Exception as e:
        logger.error(f"Failed to save strategy DNA: {e}")
        return False


def save_bulk_strategy_dna(dna_dict):
    """
    Save multiple strategy DNAs at once.
    dna_dict: {strategy_name: {category, option_strategy, ...}}
    """
    if not DB_AVAILABLE or not dna_dict:
        return False

    success_count = 0
    for strategy_name, dna in dna_dict.items():
        if save_strategy_dna(
            strategy_name=strategy_name,
            category=dna.get('category'),
            option_strategy=dna.get('option_strategy'),
            delta_long=dna.get('delta_long'),
            delta_short=dna.get('delta_short'),
            gamma_exposure=dna.get('gamma_exposure'),
            theta_exposure=dna.get('theta_exposure'),
            vega_exposure=dna.get('vega_exposure'),
            avg_dte=dna.get('avg_dte'),
            typical_margin=dna.get('typical_margin'),
            notes=dna.get('notes'),
        ):
            success_count += 1

    logger.info(f"Bulk saved {success_count}/{len(dna_dict)} strategy DNAs")
    return success_count > 0


def merge_global_dna_to_session():
    """
    Load global DNA and merge it into session_state.dna_cache.
    Global DNA provides defaults, user's local cache takes precedence.
    Call this when loading new data or starting a new session.
    """
    global_dna = load_global_strategy_dna()

    if not global_dna:
        return

    # Initialize dna_cache if not exists
    if 'dna_cache' not in st.session_state:
        st.session_state.dna_cache = {}

    # Merge: global DNA as base, user's cache overwrites
    merged = {}
    for strategy_name, dna in global_dna.items():
        merged[strategy_name] = dna.copy()

    # User's local cache takes precedence
    for strategy_name, dna in st.session_state.dna_cache.items():
        if strategy_name in merged:
            merged[strategy_name].update(dna)
        else:
            merged[strategy_name] = dna

    st.session_state.dna_cache = merged
    logger.info(f"Merged {len(global_dna)} global DNA entries into session (total: {len(merged)})")


def sync_session_dna_to_global():
    """
    Sync the user's local DNA cache to the global database.
    Call this when user saves an analysis or explicitly syncs.
    """
    if 'dna_cache' not in st.session_state or not st.session_state.dna_cache:
        return False

    return save_bulk_strategy_dna(st.session_state.dna_cache)
