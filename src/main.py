#!/usr/bin/env python3
"""PRSensei entry point — orchestrates the full review pipeline."""

from __future__ import annotations

import sys

from .config import load_config
from .github_client import GitHubClient
from .llm_client import LLMClient
from .prompt_builder import build_user_prompt, chunk_files, load_system_prompt
from .review_parser import parse_review
from .comment_poster import post_review


def main() -> None:
    print("::group::PRSensei — Initialising")
    config = load_config()
    print(f"  Provider : {config.llm_provider}")
    print(f"  Model    : {config.model}")
    print(f"  Repo     : {config.repo_full_name}")
    print(f"  PR       : #{config.pr_number}")
    print("::endgroup::")

    if not config.pr_number:
        print("::warning::No PR number found in event payload — nothing to review.")
        return

    # --- GitHub ---
    gh = GitHubClient(config)

    print("::group::Fetching PR files")
    all_files = gh.get_pr_files()
    files = all_files[: config.max_files]
    print(f"  {len(all_files)} changed file(s), reviewing {len(files)}")
    print("::endgroup::")

    if not files:
        print("::notice::No reviewable files — skipping.")
        return

    # --- LLM ---
    llm = LLMClient(config)
    system_prompt = load_system_prompt()

    chunks = chunk_files(files)
    print(f"::notice::Processing {len(chunks)} diff chunk(s)")

    all_summaries: list[str] = []
    all_comments = []

    for i, chunk in enumerate(chunks, 1):
        print(f"::group::Chunk {i}/{len(chunks)}")
        user_prompt = build_user_prompt(
            pr_title=f"PR #{config.pr_number}",
            pr_body="",
            files=chunk,
        )

        raw_response = llm.chat(system_prompt, user_prompt)
        result = parse_review(raw_response)

        all_summaries.append(result.summary)
        all_comments.extend(result.comments)
        print(f"  → {len(result.comments)} comment(s)")
        print("::endgroup::")

    # --- Post ---
    from .review_parser import ReviewResult

    combined = ReviewResult(
        summary="\n\n".join(s for s in all_summaries if s),
        comments=all_comments,
    )

    print("::group::Posting review")
    post_review(gh, combined)
    print("::endgroup::")

    print("::notice::PRSensei review complete ✅")


if __name__ == "__main__":
    main()
