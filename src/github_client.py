"""Thin wrapper around the GitHub REST API for PR operations."""

from __future__ import annotations

import sys
from dataclasses import dataclass

import requests

from .config import Config


@dataclass
class PRFile:
    filename: str
    status: str  # added, modified, removed, renamed
    patch: str  # the unified diff hunk for this file


class GitHubClient:
    BASE = "https://api.github.com"

    def __init__(self, config: Config) -> None:
        self.config = config
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {config.github_token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            }
        )

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    def get_pr_diff(self) -> str:
        """Return the full unified diff for the PR."""
        url = f"{self.BASE}/repos/{self.config.repo_full_name}/pulls/{self.config.pr_number}"
        resp = self.session.get(url, headers={"Accept": "application/vnd.github.v3.diff"})
        resp.raise_for_status()
        return resp.text

    def get_pr_files(self) -> list[PRFile]:
        """Return metadata + patch for every file changed in the PR."""
        url = (
            f"{self.BASE}/repos/{self.config.repo_full_name}"
            f"/pulls/{self.config.pr_number}/files"
            f"?per_page=100"
        )
        resp = self.session.get(url)
        resp.raise_for_status()

        files: list[PRFile] = []
        for item in resp.json():
            files.append(
                PRFile(
                    filename=item["filename"],
                    status=item["status"],
                    patch=item.get("patch", ""),
                )
            )
        return files

    def post_review(self, body: str, comments: list[dict]) -> None:
        """Create a PR review with optional inline comments.

        Each comment dict must contain: path, line, body.
        """
        url = (
            f"{self.BASE}/repos/{self.config.repo_full_name}"
            f"/pulls/{self.config.pr_number}/reviews"
        )
        payload: dict = {
            "body": body,
            "event": "COMMENT",
            "comments": [
                {
                    "path": c["path"],
                    "line": c["line"],
                    "side": "RIGHT",
                    "body": c["body"],
                }
                for c in comments
                if c.get("line") and c.get("path")
            ],
        }
        resp = self.session.post(url, json=payload)
        if not resp.ok:
            print(f"::warning::Failed to post review: {resp.status_code} {resp.text}")
        else:
            print(f"::notice::Review posted successfully ({len(payload['comments'])} inline comments)")
