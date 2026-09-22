"""Tests for the prompt builder module."""

from src.prompt_builder import build_user_prompt, chunk_files
from src.github_client import PRFile


def _make_file(name: str, patch_size: int = 100) -> PRFile:
    return PRFile(filename=name, status="modified", patch="+" * patch_size)


class TestBuildUserPrompt:
    def test_contains_pr_title(self):
        files = [_make_file("main.py")]
        prompt = build_user_prompt("Fix login bug", "Details here", files)
        assert "Fix login bug" in prompt
        assert "main.py" in prompt

    def test_truncates_large_diff(self):
        files = [_make_file("huge.py", patch_size=100_000)]
        prompt = build_user_prompt("Big PR", "", files)
        assert "truncated" in prompt


class TestChunkFiles:
    def test_single_chunk_small(self):
        files = [_make_file(f"f{i}.py", 100) for i in range(5)]
        chunks = chunk_files(files, max_chars=10_000)
        assert len(chunks) == 1

    def test_splits_large_files(self):
        files = [_make_file(f"f{i}.py", 30_000) for i in range(4)]
        chunks = chunk_files(files, max_chars=50_000)
        assert len(chunks) >= 2

    def test_empty_input(self):
        assert chunk_files([]) == []s
