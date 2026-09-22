"""Posts the structured review back to GitHub as a PR review."""

from __future__ import annotations

from .github_client import GitHubClient
from .review_parser import ReviewResult


# Files we never comment on
IGNORED_EXTENSIONS = {
    ".lock", ".min.js", ".min.css", ".png", ".jpg", ".gif",
    ".ico", ".woff", ".woff2", ".ttf", ".eot", ".svg",
}

IGNORED_PATHS = {"package-lock.json", "yarn.lock", "poetry.lock", "Pipfile.lock"}


def _should_skip(path: str) -> bool:
    if path in IGNORED_PATHS:
        return True
    return any(path.endswith(ext) for ext in IGNORED_EXTENSIONS)


def post_review(client: GitHubClient, result: ReviewResult) -> None:
    """Filter, format, and post the review to GitHub."""
    filtered = [c for c in result.comments if not _should_skip(c.path)]

    if not filtered and not result.summary:
        print("::notice::No actionable review comments — skipping.")
        return

    api_comments = [
        {"path": c.path, "line": c.line, "body": c.body}
        for c in filtered
    ]

    header = "## 🧘 PRSensei Review\n\n"
    body = header + (result.summary or "No summary provided.") + "\n"

    if filtered:
        body += f"\n---\n📝 **{len(filtered)} inline comment(s)** posted below.\n"

    client.post_review(body=body, comments=api_comments)
