"""Centralised configuration loaded from GitHub Actions environment."""

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class Config:
    github_token: str
    llm_api_key: str
    llm_provider: str  # "groq" | "openai"
    model: str
    max_files: int
    review_scope: str

    # Populated from the GitHub event payload
    repo_owner: str = ""
    repo_name: str = ""
    pr_number: int = 0
    base_sha: str = ""
    head_sha: str = ""

    @property
    def repo_full_name(self) -> str:
        return f"{self.repo_owner}/{self.repo_name}"

    @property
    def llm_base_url(self) -> str | None:
        if self.llm_provider == "groq":
            return "https://api.groq.com/openai/v1"
        return None  # OpenAI default


def _require_env(key: str) -> str:
    value = os.environ.get(key, "").strip()
    if not value:
        print(f"::error::Missing required environment variable: {key}")
        sys.exit(1)
    return value


def load_config() -> Config:
    """Build a Config from INPUT_* env vars and the GitHub event payload."""

    github_token = _require_env("INPUT_GITHUB_TOKEN")
    llm_api_key = _require_env("INPUT_LLM_API_KEY")
    llm_provider = os.environ.get("INPUT_LLM_PROVIDER", "groq").strip().lower()
    model = os.environ.get("INPUT_MODEL", "llama-3.3-70b-versatile").strip()
    max_files = int(os.environ.get("INPUT_MAX_FILES", "20"))
    review_scope = os.environ.get("INPUT_REVIEW_SCOPE", "changed-only").strip()

    # --- Parse GitHub event payload ---
    event_path = os.environ.get("GITHUB_EVENT_PATH", "")
    repo_owner, repo_name, pr_number, base_sha, head_sha = "", "", 0, "", ""

    if event_path and Path(event_path).exists():
        with open(event_path) as f:
            event = json.load(f)

        pr = event.get("pull_request", {})
        repo_owner = event.get("repository", {}).get("owner", {}).get("login", "")
        repo_name = event.get("repository", {}).get("name", "")
        pr_number = pr.get("number", 0)
        base_sha = pr.get("base", {}).get("sha", "")
        head_sha = pr.get("head", {}).get("sha", "")

    return Config(
        github_token=github_token,
        llm_api_key=llm_api_key,
        llm_provider=llm_provider,
        model=model,
        max_files=max_files,
        review_scope=review_scope,
        repo_owner=repo_owner,
        repo_name=repo_name,
        pr_number=pr_number,
        base_sha=base_sha,
        head_sha=head_sha,
    )
