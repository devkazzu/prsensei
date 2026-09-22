"""Tests for the GitHub client module."""

import pytest
from unittest.mock import patch, MagicMock

from src.config import Config
from src.github_client import GitHubClient


def _make_config() -> Config:
    return Config(
        github_token="ghp_test",
        llm_api_key="gsk_test",
        llm_provider="groq",
        model="llama3",
        max_files=10,
        review_scope="changed-only",
        repo_owner="octocat",
        repo_name="hello-world",
        pr_number=42,
    )


class TestGitHubClient:
    @patch("src.github_client.requests.Session")
    def test_get_pr_files(self, mock_session_cls):
        mock_session = MagicMock()
        mock_session_cls.return_value = mock_session

        mock_resp = MagicMock()
        mock_resp.json.return_value = [
            {"filename": "app.py", "status": "modified", "patch": "@@ -1 +1 @@"}
        ]
        mock_resp.raise_for_status = MagicMock()
        mock_session.get.return_value = mock_resp

        client = GitHubClient(_make_config())
        files = client.get_pr_files()

        assert len(files) == 1
        assert files[0].filename == "app.py"

    @patch("src.github_client.requests.Session")
    def test_post_review(self, mock_session_cls):
        mock_session = MagicMock()
        mock_session_cls.return_value = mock_session

        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_session.post.return_value = mock_resp

        client = GitHubClient(_make_config())
        client.post_review("LGTM", [{"path": "a.py", "line": 5, "body": "nice"}])

        mock_session.post.assert_called_once()
        call_kwargs = mock_session.post.call_args
        assert call_kwargs[1]["json"]["event"] == "COMMENT"
