"""Tests for the LLM client module."""

import pytest
from unittest.mock import MagicMock, patch

from src.config import Config
from src.llm_client import LLMClient


def _make_config(**overrides) -> Config:
    defaults = dict(
        github_token="ghp_test",
        llm_api_key="gsk_test",
        llm_provider="groq",
        model="llama3-8b-8192",
        max_files=10,
        review_scope="changed-only",
    )
    defaults.update(overrides)
    return Config(**defaults)


class TestLLMClient:
    @patch("src.llm_client.OpenAI")
    def test_chat_returns_content(self, mock_openai_cls):
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '{"summary":"ok","comments":[]}'
        mock_client.chat.completions.create.return_value = mock_response

        client = LLMClient(_make_config())
        result = client.chat("system", "user")

        assert '"summary"' in result
        mock_client.chat.completions.create.assert_called_once()

    @patch("src.llm_client.OpenAI")
    def test_chat_retries_on_failure(self, mock_openai_cls):
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client

        mock_client.chat.completions.create.side_effect = [
            Exception("rate limit"),
            MagicMock(
                choices=[MagicMock(message=MagicMock(content='{"summary":"retry ok"}'))]
            ),
        ]

        client = LLMClient(_make_config())
        result = client.chat("sys", "usr")
        assert "retry ok" in result
        assert mock_client.chat.completions.create.call_count == 2
