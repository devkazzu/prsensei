"""Tests for the review parser module."""

import json
import pytest

from src.review_parser import parse_review, _extract_json


class TestExtractJson:
    def test_raw_json(self):
        raw = '{"summary": "ok", "comments": []}'
        assert _extract_json(raw) == raw

    def test_fenced_json(self):
        raw = '```json\n{"summary": "ok", "comments": []}\n```'
        assert '"summary"' in _extract_json(raw)

    def test_fenced_no_lang(self):
        raw = '```\n{"summary": "ok"}\n```'
        assert '"summary"' in _extract_json(raw)


class TestParseReview:
    def test_valid_response(self):
        data = {
            "summary": "Looks good overall.",
            "comments": [
                {
                    "file": "app.py",
                    "line": 10,
                    "severity": "warning",
                    "category": "bug",
                    "body": "Possible None dereference.",
                }
            ],
        }
        result = parse_review(json.dumps(data))
        assert result.summary == "Looks good overall."
        assert len(result.comments) == 1
        assert result.comments[0].path == "app.py"
        assert result.comments[0].line == 10

    def test_empty_comments(self):
        data = {"summary": "LGTM", "comments": []}
        result = parse_review(json.dumps(data))
        assert len(result.comments) == 0

    def test_invalid_json(self):
        result = parse_review("this is not json at all")
        assert "could not parse" in result.summary.lower()

    def test_skips_zero_line(self):
        data = {
            "summary": "test",
            "comments": [
                {"file": "a.py", "line": 0, "severity": "info", "category": "style", "body": "x"}
            ],
        }
        result = parse_review(json.dumps(data))
        assert len(result.comments) == 0

    def test_severity_badge(self):
        data = {
            "summary": "s",
            "comments": [
                {"file": "a.py", "line": 1, "severity": "critical", "category": "security", "body": "SQL injection"}
            ],
        }
        result = parse_review(json.dumps(data))
        assert "🔴" in result.comments[0].body
        assert "CRITICAL" in result.comments[0].body
