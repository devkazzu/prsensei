"""Unified LLM client supporting Groq and OpenAI via the OpenAI SDK."""

from __future__ import annotations

import json
import sys
import time

from openai import OpenAI

from .config import Config


class LLMClient:
    def __init__(self, config: Config) -> None:
        self.config = config
        self.client = OpenAI(
            api_key=config.llm_api_key,
            base_url=config.llm_base_url,
        )
        self.max_retries = 2

    def chat(self, system_prompt: str, user_prompt: str) -> str:
        """Send a chat completion request and return the assistant message."""
        last_error: Exception | None = None

        for attempt in range(1, self.max_retries + 1):
            try:
                response = self.client.chat.completions.create(
                    model=self.config.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=0.2,
                    response_format={"type": "json_object"},
                )
                content = response.choices[0].message.content
                if content:
                    return content
                raise ValueError("Empty response from LLM")

            except Exception as exc:
                last_error = exc
                print(f"::warning::LLM attempt {attempt} failed: {exc}")
                if attempt < self.max_retries:
                    time.sleep(2 ** attempt)

        print(f"::error::LLM call failed after {self.max_retries} attempts")
        raise last_error  # type: ignore[misc]
