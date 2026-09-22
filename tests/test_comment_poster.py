"""Tests for the comment poster module."""

from unittest.mock import MagicMock

from src.comment_poster import post_review, _should_skip
from src.review_parser import ReviewResult, ReviewComment


class TestShouldSkip:
    def test_skips_lock_files(self):
        assert _should_skip("package-lock.json") is True
        assert _should_skip("yarn.lock") is True

    def test_skips_binaries(self):
        assert _should_skip("logo.png") is True

    def test_allows_source(self):
        assert _should_skip("main.py") is False


class TestPostReview:
    def test_posts_to_github(self):
        mock_client = MagicMock()
        result = ReviewResult(
            summary="Good PR",
            comments=[
                ReviewComment("app.py", 10, "warning", "bug", "Fix this"),
            ],
        )
        post_review(mock_client, result)
        mock_client.post_review.assert_called_once()

    def test_skips_empty(self):
        mock_client = MagicMock()
        result = ReviewResult(summary="", comments=[])
        post_review(mock_client, result)
        mock_client.post_review.assert_not_called()
