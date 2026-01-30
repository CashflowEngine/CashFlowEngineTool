"""
Gemini AI Client for CashFlow Engine
Handles communication with Gemini 3 Flash API.
"""

import streamlit as st
from typing import Generator, Optional, List, Dict
import os

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
        return os.environ.get('GEMINI_API_KEY') or os.environ.get('GOOGLE_API_KEY')

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
            return f"AI nicht verfügbar: {self.error_message}"

        try:
            if self.is_new_sdk:
                return self._generate_new_sdk(prompt, system_instruction, chat_history, temperature, max_tokens)
            else:
                return self._generate_old_sdk(prompt, system_instruction, chat_history, temperature, max_tokens)
        except Exception as e:
            return f"Fehler bei der AI-Anfrage: {str(e)}"

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
    if _client_instance is None:
        _client_instance = GeminiClient()
    return _client_instance


def reset_client():
    """Reset the client (e.g., if API key changes)."""
    global _client_instance
    _client_instance = None
