     # 🧘 PRSensei

AI-powered pull request reviews, running entirely inside GitHub Actions.

## Quick Start

1. Add your LLM API key as a repository secret (`GROQ_API_KEY` or `OPENAI_API_KEY`).
2. Create `.github/workflows/pr-sensei.yml`:mnbm

```yaml
name: PRSensei
on:b
  pull_request:
    types: [opened, synchronize, reopened]

permissions:
  contents: read
  pull-requests: write

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: your-org/pr-sensei@v1
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          llm_api_key: ${{ secrets.GROQ_API_KEY }}
          llm_provider: groq
          model: llama-3.3-70b-versatile
