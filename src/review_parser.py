"""Parses the LLM JSON response into structured review comments."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass

from pydantic import BaseModel, Field


class RawComment(BaseModel):
    file: str = Field(alias="file")
    line: int = Field(default=0)
    severity: str = Field(default="info")  # critical | warning | info | nit
    category: str = Field(default="general")  # bug | security | performance | style | logic
    body: str = Field(default="")


class RawReview(BaseModel):
    summary: str = ""
    comments: list[RawComment] = Field(default_factory=list)


@dataclass
class ReviewComment:
    path: str
    line: int
    severity: str
    category: str
    body: str


@dataclass
class ReviewResult:
    summary: str
    comments: list[ReviewComment]


def _extract_json(text: str) -> str:
    """Best-effort extraction of JSON from LLM output that may contain markdown fences."""
    # Try to find a fenced JSON block
    match = re.search(r"```(?:json)?\s*\n?(.*?)```", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    # Try to find raw JSON object
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        return match.group(0)
    return text


def parse_review(raw: str) -> ReviewResult:
    """Parse the raw LLM response string into a ReviewResult."""
    cleaned = _extract_json(raw)

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        return ReviewResult(
            summary="⚠️ PRSensei could not parse the LLM response. Raw output:\n\n" + raw[:1000],
            comments=[],
        )

    try:
        review = RawReview.model_validate(data)
    except Exception:
        return ReviewResult(
            summary="⚠️ PRSensei received an unexpected response format.",
            comments=[],
        )

    comments = [
        ReviewComment(
            path=c.file,
            line=c.line,
            severity=c.severity,
            category=c.category,
            body=_format_body(c),
        )
        for c in review.comments
        if c.body and c.line > 0
    ]

    return ReviewResult(summary=review.summary, comments=comments)


def _format_body(c: RawComment) -> str:
    """Add severity/category badge to the comment body."""
    icons = {"critical": "🔴", "warning": "🟡", "info": "🔵", "nit": "⚪"}
    icon = icons.get(c.severity, "🔵")
    return f"{icon} **[{c.severity.upper()}]** _{c.category}_\n\n{c.body}"
