"""Constructs system and user prompts for the LLM review."""

from __future__ import annotations

from pathlib import Path

from .github_client import PRFile

SYSTEM_PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "review_system_prompt.md"

# Rough token estimate: 1 token ≈ 4 chars
MAX_CHARS_PER_CHUNK = 48_000  # ~12k tokens, safe for most models


def load_system_prompt() -> str:
    """Read the externalised system prompt from disk."""
    if SYSTEM_PROMPT_PATH.exists():
        return SYSTEM_PROMPT_PATH.read_text(encoding="utf-8")
    # Fallback minimal prompt
    return (
        "You are a senior code reviewer. "
        "Respond ONLY with valid JSON matching the requested schema."
    )


def build_user_prompt(pr_title: str, pr_body: str, files: list[PRFile]) -> str:
    """Build the user message containing PR context and file diffs."""
    parts = [
        f"## Pull Request\n**Title:** {pr_title}\n**Description:**\n{pr_body or 'No description.'}\n",
        "## Changed Files\n",
    ]

    for f in files:
        parts.append(f"### `{f.filename}` ({f.status})\n```diff\n{f.patch}\n```\n")

    full = "\n".join(parts)

    # Truncate if dangerously large
    if len(full) > MAX_CHARS_PER_CHUNK:
        full = full[:MAX_CHARS_PER_CHUNK] + "\n\n... (diff truncated due to size)"

    return full


def chunk_files(files: list[PRFile], max_chars: int = MAX_CHARS_PER_CHUNK) -> list[list[PRFile]]:
    """Split files into chunks that each fit within the character budget."""
    chunks: list[list[PRFile]] = []
    current: list[PRFile] = []
    current_size = 0

    for f in files:
        file_size = len(f.patch) + len(f.filename) + 50  # overhead
        if current_size + file_size > max_chars and current:
            chunks.append(current)
            current = []
            current_size = 0
        current.append(f)
        current_size += file_size

    if current:
        chunks.append(current)

    return chunks
