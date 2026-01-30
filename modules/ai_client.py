"""
Gemini AI Client for CashFlow Engine
Handles communication with Gemini 3 Flash API.
Includes token tracking and usage limits.
"""

import streamlit as st
from typing import Generator, Optional, List, Dict, Tuple
import os
import re
from datetime import datetime, timedelta

# Try to import the new google-genai SDK
try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False

# Fallback to old SDK if new one not available
if not GENAI_AVAILABLE:
    try:
        import google.generativeai as genai_old
        GENAI_OLD_AVAILABLE = True
    except ImportError:
        GENAI_OLD_AVAILABLE = False
else:
    GENAI_OLD_AVAILABLE = False


# =============================================================================
# TOKEN USAGE TRACKING AND LIMITS
# =============================================================================

# Gemini Flash pricing (approximate):
# Input: $0.075 per 1M tokens
# Output: $0.30 per 1M tokens
PRICE_PER_INPUT_TOKEN = 0.075 / 1_000_000
PRICE_PER_OUTPUT_TOKEN = 0.30 / 1_000_000

# Monthly budget limit per user
MONTHLY_BUDGET_LIMIT = 1.00  # $1.00 per user per month


def estimate_tokens(text: str) -> int:
    """Estimate token count (roughly 4 chars = 1 token for English)."""
    if not text:
        return 0
    return len(text) // 4


def get_user_usage_key() -> str:
    """Get the session state key for current user's token usage."""
    user_id = st.session_state.get('user_id', 'anonymous')
    month_key = datetime.now().strftime('%Y-%m')
    return f"ai_usage_{user_id}_{month_key}"


def get_user_monthly_usage() -> Dict:
    """Get current user's monthly token usage."""
    key = get_user_usage_key()
    if key not in st.session_state:
        st.session_state[key] = {
            'input_tokens': 0,
            'output_tokens': 0,
            'total_cost': 0.0,
            'request_count': 0,
            'last_reset': datetime.now().isoformat()
        }
    return st.session_state[key]


def track_token_usage(input_tokens: int, output_tokens: int):
    """Track token usage for the current user."""
    usage = get_user_monthly_usage()
    usage['input_tokens'] += input_tokens
    usage['output_tokens'] += output_tokens
    usage['total_cost'] = (
        usage['input_tokens'] * PRICE_PER_INPUT_TOKEN +
        usage['output_tokens'] * PRICE_PER_OUTPUT_TOKEN
    )
    usage['request_count'] += 1


def check_usage_limit() -> Tuple[bool, str]:
    """
    Check if user is within usage limits.

    Returns:
        Tuple of (is_allowed, message)
    """
    usage = get_user_monthly_usage()
    remaining = MONTHLY_BUDGET_LIMIT - usage['total_cost']

    if remaining <= 0:
        return False, f"Monthly AI budget exhausted (${MONTHLY_BUDGET_LIMIT:.2f}/month). Resets next month."

    if remaining < 0.10:
        return True, f"Warning: Only ${remaining:.2f} remaining this month."

    return True, ""


def get_usage_display() -> Dict:
    """Get usage stats for display."""
    usage = get_user_monthly_usage()
    return {
        'requests': usage['request_count'],
        'cost': usage['total_cost'],
        'remaining': max(0, MONTHLY_BUDGET_LIMIT - usage['total_cost']),
        'limit': MONTHLY_BUDGET_LIMIT,
        'percent_used': min(100, (usage['total_cost'] / MONTHLY_BUDGET_LIMIT) * 100)
    }


# =============================================================================
# RESPONSE CLEANING
# =============================================================================

def clean_response(text: str) -> str:
    """
    Clean AI response to fix common markdown issues.
    """
    if not text:
        return text

    # Fix broken bold markers: ** text** or **text ** -> **text**
    text = re.sub(r'\*\*\s+', '**', text)
    text = re.sub(r'\s+\*\*', '**', text)

    # Fix broken italic markers: * text* -> *text*
    text = re.sub(r'(?<!\*)\*\s+', '*', text)
    text = re.sub(r'\s+\*(?!\*)', '*', text)

    # Fix orphaned asterisks (single * not part of markdown)
    text = re.sub(r'(?<!\*)\*(?!\*)', '', text)

    # Fix double spaces
    text = re.sub(r'  +', ' ', text)

    # Fix broken list items
    text = re.sub(r'\n\s*-\s*\n', '\n', text)

    # Ensure proper spacing around headers
    text = re.sub(r'(#{1,6})\s*([^\n]+)', r'\1 \2', text)

    return text.strip()


class GeminiClient:
    """Client for Gemini 3 Flash API with fallback to older versions."""

    # Model priority (newest to oldest)
    MODEL_PRIORITY = [
        "gemini-3-flash-preview",      # Newest - Gemini 3 Flash
        "gemini-2.5-flash-preview",    # Gemini 2.5 Flash
        "gemini-2.0-flash",            # Gemini 2.0 Flash
        "gemini-1.5-flash",            # Gemini 1.5 Flash (stable)
        "gemini-pro",                  # Legacy fallback
    ]

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Gemini client.

        Args:
            api_key: Optional API key. If not provided, reads from secrets/env.
        """
        self.api_key = api_key or self._get_api_key()
        self.client = None
        self.model_name = None
        self.is_new_sdk = GENAI_AVAILABLE
        self.is_available = False
        self.error_message = None

        if self.api_key:
            self._initialize_client()

    def _get_api_key(self) -> Optional[str]:
        """Get API key from various sources."""
        # Try Streamlit secrets first (with error handling)
        try:
            if hasattr(st, 'secrets') and st.secrets:
                if 'GEMINI_API_KEY' in st.secrets:
                    return st.secrets['GEMINI_API_KEY']
                if 'GOOGLE_API_KEY' in st.secrets:
                    return st.secrets['GOOGLE_API_KEY']
        except Exception:
            pass  # No secrets file, continue to env vars

        # Try environment variables
        api_key = os.environ.get('GEMINI_API_KEY') or os.environ.get('GOOGLE_API_KEY')

        # Also try without underscore (common mistake)
        if not api_key:
            api_key = os.environ.get('GEMINI_APIKEY') or os.environ.get('GOOGLEAPIKEY')

        return api_key

    def _initialize_client(self):
        """Initialize the appropriate client based on available SDK."""
        if GENAI_AVAILABLE:
            self._init_new_sdk()
        elif GENAI_OLD_AVAILABLE:
            self._init_old_sdk()
        else:
            self.error_message = "Neither google-genai nor google-generativeai package is installed."

    def _init_new_sdk(self):
        """Initialize with new google-genai SDK."""
        try:
            self.client = genai.Client(api_key=self.api_key)

            # Try to find a working model
            for model in self.MODEL_PRIORITY:
                try:
                    # Quick test to see if model is available
                    self.model_name = model
                    self.is_available = True
                    break
                except Exception:
                    continue

            if not self.is_available:
                self.error_message = "No compatible Gemini model found."

        except Exception as e:
            self.error_message = f"Failed to initialize Gemini client: {str(e)}"

    def _init_old_sdk(self):
        """Initialize with old google-generativeai SDK."""
        try:
            genai_old.configure(api_key=self.api_key)
            self.model_name = "gemini-pro"
            self.is_available = True
        except Exception as e:
            self.error_message = f"Failed to initialize legacy Gemini client: {str(e)}"

    def generate(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        chat_history: Optional[List[Dict]] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096
    ) -> str:
        """
        Generate a response from Gemini.

        Args:
            prompt: The user's message
            system_instruction: System prompt/context
            chat_history: Previous messages in the conversation
            temperature: Creativity (0.0-1.0)
            max_tokens: Maximum response length

        Returns:
            The generated response text
        """
        if not self.is_available:
            return f"AI not available: {self.error_message}"

        # Check usage limit
        allowed, limit_msg = check_usage_limit()
        if not allowed:
            return limit_msg

        try:
            # Estimate input tokens
            input_text = (system_instruction or "") + prompt
            if chat_history:
                input_text += " ".join(msg.get("content", "") for msg in chat_history)
            input_tokens = estimate_tokens(input_text)

            # Generate response
            if self.is_new_sdk:
                response = self._generate_new_sdk(prompt, system_instruction, chat_history, temperature, max_tokens)
            else:
                response = self._generate_old_sdk(prompt, system_instruction, chat_history, temperature, max_tokens)

            # Track usage
            output_tokens = estimate_tokens(response)
            track_token_usage(input_tokens, output_tokens)

            # Clean and return response
            return clean_response(response)

        except Exception as e:
            return f"Error processing AI request: {str(e)}"

    def _generate_new_sdk(
        self,
        prompt: str,
        system_instruction: Optional[str],
        chat_history: Optional[List[Dict]],
        temperature: float,
        max_tokens: int
    ) -> str:
        """Generate using new SDK."""
        # Build contents
        contents = []

        # Add chat history if provided
        if chat_history:
            for msg in chat_history:
                role = "user" if msg.get("role") == "user" else "model"
                contents.append(types.Content(
                    role=role,
                    parts=[types.Part(text=msg.get("content", ""))]
                ))

        # Add current prompt
        contents.append(types.Content(
            role="user",
            parts=[types.Part(text=prompt)]
        ))

        # Build config
        config = types.GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
            system_instruction=system_instruction if system_instruction else None
        )

        # Generate
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=contents,
            config=config
        )

        return response.text

    def _generate_old_sdk(
        self,
        prompt: str,
        system_instruction: Optional[str],
        chat_history: Optional[List[Dict]],
        temperature: float,
        max_tokens: int
    ) -> str:
        """Generate using old SDK (fallback)."""
        # Combine system instruction with prompt for old SDK
        full_prompt = ""
        if system_instruction:
            full_prompt = f"{system_instruction}\n\n---\n\n"

        # Add chat history
        if chat_history:
            for msg in chat_history:
                role = "User" if msg.get("role") == "user" else "Assistant"
                full_prompt += f"{role}: {msg.get('content', '')}\n\n"

        full_prompt += f"User: {prompt}\n\nAssistant:"

        model = genai_old.GenerativeModel(self.model_name)
        response = model.generate_content(
            full_prompt,
            generation_config={
                'temperature': temperature,
                'max_output_tokens': max_tokens,
            }
        )

        return response.text

    def generate_stream(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        chat_history: Optional[List[Dict]] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096
    ) -> Generator[str, None, None]:
        """
        Generate a streaming response from Gemini.

        Yields:
            Chunks of the response text
        """
        if not self.is_available:
            yield f"AI nicht verfügbar: {self.error_message}"
            return

        try:
            if self.is_new_sdk:
                yield from self._generate_stream_new_sdk(prompt, system_instruction, chat_history, temperature, max_tokens)
            else:
                # Old SDK doesn't support streaming well, fall back to regular
                yield self._generate_old_sdk(prompt, system_instruction, chat_history, temperature, max_tokens)
        except Exception as e:
            yield f"Fehler bei der AI-Anfrage: {str(e)}"

    def _generate_stream_new_sdk(
        self,
        prompt: str,
        system_instruction: Optional[str],
        chat_history: Optional[List[Dict]],
        temperature: float,
        max_tokens: int
    ) -> Generator[str, None, None]:
        """Stream generate using new SDK."""
        # Build contents
        contents = []

        if chat_history:
            for msg in chat_history:
                role = "user" if msg.get("role") == "user" else "model"
                contents.append(types.Content(
                    role=role,
                    parts=[types.Part(text=msg.get("content", ""))]
                ))

        contents.append(types.Content(
            role="user",
            parts=[types.Part(text=prompt)]
        ))

        config = types.GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
            system_instruction=system_instruction if system_instruction else None
        )

        # Stream response
        for chunk in self.client.models.generate_content_stream(
            model=self.model_name,
            contents=contents,
            config=config
        ):
            if chunk.text:
                yield chunk.text

    def get_status(self) -> Dict:
        """Get client status information."""
        return {
            'available': self.is_available,
            'model': self.model_name,
            'sdk': 'google-genai (new)' if self.is_new_sdk else 'google-generativeai (legacy)',
            'error': self.error_message,
            'has_api_key': self.api_key is not None,
        }


# Singleton instance for reuse
_client_instance: Optional[GeminiClient] = None


def get_gemini_client() -> GeminiClient:
    """Get or create the Gemini client singleton."""
    global _client_instance

    # If client exists but has no API key, try to recreate it
    # (API key might have been added to environment after first load)
    if _client_instance is not None and not _client_instance.api_key:
        # Check if API key is now available
        test_key = (
            os.environ.get('GEMINI_API_KEY') or
            os.environ.get('GOOGLE_API_KEY') or
            os.environ.get('GEMINI_APIKEY')
        )
        if test_key:
            _client_instance = None  # Reset to recreate

    if _client_instance is None:
        _client_instance = GeminiClient()

    return _client_instance


def reset_client():
    """Reset the client (e.g., if API key changes)."""
    global _client_instance
    _client_instance = None
