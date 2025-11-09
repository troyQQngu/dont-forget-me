"""Utilities for interacting with large language models."""
from __future__ import annotations

import os
from typing import Optional, Protocol, Sequence, TypedDict


class ChatMessage(TypedDict):
    """Representation of a message passed to a chat completion API."""

    role: str
    content: str


class LLMClient(Protocol):
    """Protocol describing the minimal chat interface the assistant needs."""

    def complete(
        self,
        messages: Sequence[ChatMessage],
        *,
        response_format: Optional[str] = None,
    ) -> str:
        """Return the assistant message content for the given conversation."""


class OpenAIChatClient:
    """Concrete ``LLMClient`` implementation backed by the OpenAI API."""

    def __init__(
        self,
        *,
        model: str = "gpt-4o-mini",
        api_key: Optional[str] = None,
        default_system_prompt: Optional[str] = None,
    ) -> None:
        self.model = model
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise RuntimeError(
                "An OpenAI API key is required. Set the OPENAI_API_KEY environment variable "
                "or provide one explicitly."
            )
        self.default_system_prompt = default_system_prompt

    def complete(
        self,
        messages: Sequence[ChatMessage],
        *,
        response_format: Optional[str] = None,
    ) -> str:
        client_messages = list(messages)
        if self.default_system_prompt and (
            not client_messages or client_messages[0]["role"] != "system"
        ):
            client_messages = [
                {"role": "system", "content": self.default_system_prompt},
                *client_messages,
            ]

        request_kwargs = {
            "model": self.model,
            "messages": client_messages,
            "temperature": 0.2,
        }
        if response_format:
            request_kwargs["response_format"] = {"type": response_format}

        try:
            from openai import OpenAI  # type: ignore

            client = OpenAI(api_key=self.api_key)
            response = client.chat.completions.create(**request_kwargs)
            message = response.choices[0].message.content or ""
        except ImportError as exc:  # pragma: no cover - exercised only with real API
            raise RuntimeError(
                "The 'openai' package is required to call the OpenAI API. Install it with "
                "'pip install openai'."
            ) from exc
        except AttributeError:
            # Fallback for legacy ``openai`` package versions (<1.0.0).
            import openai  # type: ignore

            openai.api_key = self.api_key
            response = openai.ChatCompletion.create(**request_kwargs)
            message = response["choices"][0]["message"]["content"]
        return message


__all__ = ["ChatMessage", "LLMClient", "OpenAIChatClient"]
