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


def get_openai_client() -> OpenAI:
    """Get an OpenAI client instance."""
    if not settings.OPENAI_API_KEY:
        raise Exception("OPENAI_API_KEY is not configured")
    return OpenAI(api_key=settings.OPENAI_API_KEY)


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

    client = get_openai_client()

    kwargs = {
        "model": "gpt-4o",
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

    client = get_openai_client()

    full_messages = [{"role": "system", "content": system_prompt}]
    full_messages.extend(messages)

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=full_messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"LLM API call failed: {str(e)}")
        raise
