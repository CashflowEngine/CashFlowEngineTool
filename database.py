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
    """Enhanced save with metadata."""
    if not DB_AVAILABLE:
        st.error("Database not connected.")
        return False
    
    try:
        bt_json = clean_df_for_json(bt_df)
        live_json = clean_df_for_json(live_df)
        
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
        
        supabase.table('analyses').insert({
            "name": name,
            "data_json": payload
        }).execute()
        
        logger.info(f"Analysis '{name}' saved successfully")
        return True
    except Exception as e:
        logger.error(f"Enhanced save error: {e}")
        st.error(f"Save Error: {e}")
        return False

def get_analysis_list():
    """Retrieve list of saved analyses (legacy wrapper)."""
    return get_analysis_list_enhanced()

def get_analysis_list_enhanced():
    """Get analysis list with metadata."""
    if not DB_AVAILABLE:
        return []
    
    try:
        response = supabase.table('analyses').select(
            "id, name, created_at, data_json"
        ).order('created_at', desc=True).execute()
        
        analyses = []
        for item in response.data:
            analysis = {
                'id': item['id'],
                'name': item['name'],
                'created_at': item['created_at']
            }
            
            data_json = item.get('data_json', {})
            if isinstance(data_json, dict):
                metadata = data_json.get('metadata', {})
                analysis['description'] = metadata.get('description', '')
                analysis['tags'] = metadata.get('tags', [])
                analysis['trade_count'] = metadata.get('trade_count', 0)
                analysis['total_pnl'] = metadata.get('total_pnl', 0)
                analysis['strategies'] = metadata.get('strategies', [])
                analysis['date_start'] = metadata.get('date_start', '')
                analysis['date_end'] = metadata.get('date_end', '')
                analysis['has_live'] = metadata.get('has_live', False)
            else:
                if isinstance(data_json, list):
                    analysis['trade_count'] = len(data_json)
                analysis['description'] = ''
                analysis['tags'] = []
            
            analyses.append(analysis)
        
        return analyses
    except Exception as e:
        logger.error(f"Failed to get enhanced list: {e}")
        return []

def delete_analysis_from_db(analysis_id):
    """Delete an analysis by ID."""
    if not DB_AVAILABLE:
        return False
    try:
        supabase.table('analyses').delete().eq('id', analysis_id).execute()
        logger.info(f"Analysis {analysis_id} deleted")
        return True
    except Exception as e:
        logger.error(f"Delete error: {e}")
        return False

def rename_analysis_in_db(analysis_id, new_name):
    """Rename an analysis."""
    if not DB_AVAILABLE:
        return False
    try:
        supabase.table('analyses').update({"name": new_name}).eq('id', analysis_id).execute()
        logger.info(f"Analysis {analysis_id} renamed to {new_name}")
        return True
    except Exception as e:
        logger.error(f"Rename error: {e}")
        return False

def load_analysis_from_db(analysis_id):
    """Load analysis from database."""
    if not DB_AVAILABLE:
        return None, None
    try:
        response = supabase.table('analyses').select("data_json").eq('id', analysis_id).execute()
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
