"""
Centralized LLM client with rate limiting and error handling.
"""
import time
import logging
from typing import Optional, List, Dict, Any
from openai import OpenAI
from app.config import settings

logger = logging.getLogger(__name__)

# Simple in-memory rate limiter
_request_timestamps: List[float] = []


def _rate_limit_check():
    """Enforce rate limiting on LLM API calls."""
    now = time.time()
    global _request_timestamps
    # Remove timestamps older than 60 seconds
    _request_timestamps = [ts for ts in _request_timestamps if now - ts < 60]
    if len(_request_timestamps) >= settings.RATE_LIMIT_PER_MINUTE:
        wait_time = 60 - (now - _request_timestamps[0])
        raise Exception(f"LLM rate limit exceeded. Please wait {wait_time:.0f} seconds.")
    _request_timestamps.append(now)


def get_llm_active_provider() -> str:
    """Determine if we are using 'openai' or 'ollama'."""
    api_key = settings.OPENAI_API_KEY
    if api_key and api_key.lower() != "ollama" and api_key.strip() != "":
        return "openai"
    return "ollama"


def get_llm_client() -> OpenAI:
    """Get an LLM client instance."""
    provider = get_llm_active_provider()
    if provider == "openai":
        return OpenAI(api_key=settings.OPENAI_API_KEY)
    else:
        return OpenAI(
            api_key="ollama",
            base_url=settings.LLM_BASE_URL,
        )


def get_active_model() -> str:
    """Get the model name for the active provider."""
    provider = get_llm_active_provider()
    if provider == "openai":
        # Check if a specific OpenAI model is provided in settings, otherwise default
        if settings.LLM_MODEL and not settings.LLM_MODEL.startswith("llama"):
             return settings.LLM_MODEL
        return "gpt-4o"
    return settings.LLM_MODEL



def call_llm(
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.3,
    max_tokens: int = 4096,
    response_format: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Make a rate-limited call to the LLM API.

    Args:
        system_prompt: System message for context
        user_prompt: User message with the actual request
        temperature: LLM temperature (lower = more deterministic)
        max_tokens: Maximum response tokens
        response_format: Optional response format specification

    Returns:
        The LLM response text
    """
    _rate_limit_check()

    client = get_llm_client()
    model = get_active_model()

    kwargs = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    if response_format:
        kwargs["response_format"] = response_format

    try:
        response = client.chat.completions.create(**kwargs)
        content = response.choices[0].message.content
        logger.info(f"LLM call successful. Tokens used: {response.usage.total_tokens}")
        return content
    except Exception as e:
        logger.error(f"LLM API call failed: {str(e)}")
        raise


def call_llm_with_history(
    system_prompt: str,
    messages: List[Dict[str, str]],
    temperature: float = 0.3,
    max_tokens: int = 4096,
) -> str:
    """
    Make a rate-limited LLM call with conversation history.

    Args:
        system_prompt: System message for context
        messages: List of {"role": "user"|"assistant", "content": "..."} messages
        temperature: LLM temperature
        max_tokens: Maximum response tokens

    Returns:
        The LLM response text
    """
    _rate_limit_check()

    client = get_llm_client()
    model = get_active_model()

    full_messages = [{"role": "system", "content": system_prompt}]
    full_messages.extend(messages)

    try:
        response = client.chat.completions.create(
            model=model,
            messages=full_messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"LLM API call failed: {str(e)}")
        raise
