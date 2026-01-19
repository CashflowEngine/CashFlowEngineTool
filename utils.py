import streamlit as st
import pandas as pd
import numpy as np
import os
import yfinance as yf
import json
import datetime
import logging
import time
import re
from supabase import create_client

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
COLOR_TEAL = "#00D2BE"
COLOR_CORAL = "#FF2E4D"
COLOR_BLUE = "#302BFF"
COLOR_GREY = "#4B5563"
COLOR_PURPLE = "#7B2BFF"

# --- DATABASE SETUP ---
DB_AVAILABLE = False
supabase = None
try:
    # Railway Environment Variables ODER Streamlit Secrets
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

# --- DATA LOADING FUNCTIONS ---

@st.cache_data(show_spinner=False)
def load_and_clean(_file_content, file_name):
    """
    Load and clean uploaded file.
    Note: We pass file content instead of file object for proper caching.
    """
    try:
        import io
        if file_name.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(io.BytesIO(_file_content))
        else:
            df = pd.read_csv(io.BytesIO(_file_content))

        df.columns = df.columns.str.strip()
        
        # Build column mapping efficiently
        col_map = {}
        for col in df.columns:
            c_low = col.lower()
            if c_low in ['profit/loss', 'p/l', 'net profit', 'pnl', 'profit']:
                col_map[col] = 'pnl'
            elif c_low in ['margin', 'margin req', 'margin req.', 'margin requirement']:
                col_map[col] = 'margin'
            elif 'no. of contracts' in c_low or c_low in ['contracts', 'quantity', 'qty', 'size']:
                col_map[col] = 'contracts'
            elif 'time closed' in c_low:
                col_map[col] = 'time'
            elif c_low in ['date closed', 'exit date', 'close date', 'date/time', 'date']:
                col_map[col] = 'date'
            elif 'time opened' in c_low:
                col_map[col] = 'time_open'
            elif c_low in ['date opened', 'entry date', 'open date']:
                col_map[col] = 'date_open'
            elif 'strategy' in c_low:
                col_map[col] = 'strategy'
            elif 'legs' in c_low:
                col_map[col] = 'legs'

        df.rename(columns=col_map, inplace=True)

        # Options App specific columns
        if 'Entry Time' in df.columns:
            df.rename(columns={'Entry Time': 'timestamp_open'}, inplace=True)
        if 'Close Time' in df.columns:
            df.rename(columns={'Close Time': 'timestamp_close'}, inplace=True)
        if 'Profit' in df.columns and 'pnl' not in df.columns:
            df.rename(columns={'Profit': 'pnl'}, inplace=True)

        if 'Strategy' in df.columns and 'strategy' not in df.columns:
            df['strategy'] = df['Strategy'].astype(str).str.replace('SPX: ', '', regex=False)
        elif 'Name' in df.columns and 'strategy' not in df.columns:
            df['strategy'] = df['Name']

        if 'pnl' not in df.columns:
            logger.warning(f"No PnL column found in {file_name}")
            return None

        # Clean numeric columns efficiently
        for col in ['pnl', 'margin']:
            if col in df.columns and df[col].dtype == object:
                df[col] = pd.to_numeric(
                    df[col].astype(str).str.replace(r'[$,]', '', regex=True),
                    errors='coerce'
                )

        if 'margin' not in df.columns:
            df['margin'] = 0.0
        else:
            df['margin'] = df['margin'].abs().fillna(0)

        # Date handling
        if 'timestamp_open' in df.columns:
            df['timestamp_open'] = pd.to_datetime(df['timestamp_open'], errors='coerce')

        if 'timestamp_close' in df.columns:
            df['timestamp_close'] = pd.to_datetime(df['timestamp_close'], errors='coerce')
            df['timestamp'] = df['timestamp_close'].fillna(df.get('timestamp_open', df['timestamp_close']))
        elif 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'], errors='coerce')
            if 'time' in df.columns:
                df['timestamp_close'] = pd.to_datetime(
                    df['date'].astype(str) + ' ' + df['time'].astype(str), errors='coerce'
                ).fillna(df['date'])
            else:
                df['timestamp_close'] = df['date']
            df['timestamp'] = df['timestamp_close']

            if 'date_open' in df.columns:
                df['date_open'] = pd.to_datetime(df['date_open'], errors='coerce')
                if 'time_open' in df.columns:
                    df['timestamp_open'] = pd.to_datetime(
                        df['date_open'].astype(str) + ' ' + df['time_open'].astype(str), errors='coerce'
                    ).fillna(df['date_open'])
                else:
                    df['timestamp_open'] = df['date_open']
            else:
                df['timestamp_open'] = df['timestamp_close']
        else:
            df['timestamp'] = pd.to_datetime(df.index)

        if not np.issubdtype(df['timestamp'].dtype, np.datetime64):
            df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')

        df = df.dropna(subset=['timestamp'])

        if 'strategy' not in df.columns:
            df['strategy'] = file_name.rsplit('.', 1)[0]

        cols = ['pnl', 'margin', 'contracts', 'timestamp', 'timestamp_open', 'timestamp_close', 'strategy']
        optional = ['legs', 'date', 'Open']
        cols.extend([c for c in optional if c in df.columns])
        
        return df[[c for c in cols if c in df.columns]]

    except Exception as e:
        logger.error(f"Error loading file {file_name}: {e}")
        return None

def load_file_with_caching(uploaded_file):
    """
    Helper to load file with proper caching.
    Reads file content once, then passes to cached function.
    """
    content = uploaded_file.read()
    uploaded_file.seek(0)  # Reset file pointer
    return load_and_clean(content, uploaded_file.name)

@st.cache_data(ttl=3600, show_spinner=False)  # Cache for 1 hour
def fetch_spx_benchmark(start_date, end_date):
    """Fetch S&P 500 data with TTL caching."""
    try:
        # Extend start date by a few days to ensure we have data for alignment
        s_date = start_date - pd.Timedelta(days=5)
        s_str = s_date.strftime('%Y-%m-%d')
        e_str = end_date.strftime('%Y-%m-%d')
        
        data = yf.download("^GSPC", start=s_str, end=e_str, progress=False, auto_adjust=True)
        if data.empty:
            logger.warning("Empty SPX data returned from yfinance")
            return None
        
        # Handle MultiIndex columns (happens with some yfinance versions)
        if isinstance(data.columns, pd.MultiIndex):
            # Try to get Close column
            if 'Close' in data.columns.get_level_values(0):
                close_data = data['Close']
                if isinstance(close_data, pd.DataFrame):
                    close_data = close_data.iloc[:, 0]  # Get first column if still DataFrame
                return close_data
            else:
                return data.iloc[:, 0]  # Return first column
        else:
            if 'Close' in data.columns:
                return data['Close']
            return data.iloc[:, 0]  # Return first column if no Close
    except Exception as e:
        logger.error(f"Failed to fetch SPX data: {e}")
        return None

def parse_meic_filename(filename):
    """
    Extrahiert Parameter aus dem Dateinamen für den 4D Analyzer.
    Erwartet Format: MEIC_W{width}_SL{sl}_P{premium}.csv
    Beispiel: MEIC_W50_SL100_P2.5.csv
    """
    # Regex für W, SL, P (Premium kann Dezimalpunkt haben)
    width_match = re.search(r'W(\d+)', filename, re.IGNORECASE)
    sl_match = re.search(r'SL(\d+)', filename, re.IGNORECASE)
    prem_match = re.search(r'P(\d+\.?\d*)', filename, re.IGNORECASE)
    
    return {
        'Width': int(width_match.group(1)) if width_match else None,
        'SL': int(sl_match.group(1)) if sl_match else None,
        'Premium': float(prem_match.group(1)) if prem_match else None,
        'Filename': filename
    }

def generate_oo_signals(start_date, end_date, start_time="09:35", end_time="15:55", interval_min=5):
    """
    Generiert CSV für Option Omega Custom Signals.
    Format entspricht 'signals_open_only.csv': Header 'OPEN_DATETIME', Format 'YYYY-MM-DD HH:MM'
    """
    # Business Days Only
    dates = pd.date_range(start=start_date, end=end_date, freq='B') 
    
    signal_rows = []
    
    # Zeit-Range erstellen
    t_start = pd.to_datetime(start_time).time()
    t_end = pd.to_datetime(end_time).time()
    
    for d in dates:
        # Simple Holiday Skip (Hardcoded für die wichtigsten)
        if d.month == 12 and d.day == 25: continue # Christmas
        if d.month == 1 and d.day == 1: continue   # New Year
        if d.month == 7 and d.day == 4: continue   # Independence Day
        
        # Erstelle Zeitpunkte für den Tag
        current_ts = pd.Timestamp.combine(d.date(), t_start)
        end_ts = pd.Timestamp.combine(d.date(), t_end)
        
        while current_ts <= end_ts:
            signal_rows.append(current_ts)
            current_ts += pd.Timedelta(minutes=interval_min)
            
    df_signals = pd.DataFrame(signal_rows, columns=['OPEN_DATETIME'])
    # Formatierung exakt wie im Template
    df_signals['OPEN_DATETIME'] = df_signals['OPEN_DATETIME'].dt.strftime('%Y-%m-%d %H:%M')
    return df_signals
