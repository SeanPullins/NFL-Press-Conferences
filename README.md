# NFL Press Conferences

Automated NFL press conference quote miner.

This project watches NFL team YouTube feeds, finds new press conference/media availability videos, pulls available English transcripts, extracts high-signal quotes with an OpenAI-compatible LLM, and writes clean reports that can be fed into Google NotebookLM.

## What it creates

The automated run writes:

- `data/quotes.json` — structured quote analysis data
- `data/seen_videos.json` — processed YouTube video IDs
- `data/reports/latest.md` — human-readable daily report
- `data/reports/notebooklm-digest.md` — clean digest intended for NotebookLM

## Local setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` and add your API key/model settings.

Then run:

```bash
python src/main.py
```

## GitHub Actions setup

Add these repository secrets in GitHub:

- `OPENAI_API_KEY`
- optional: `OPENAI_BASE_URL`
- optional: `OPENAI_MODEL`

The workflow runs three times per day and can also be triggered manually from the Actions tab.

## NotebookLM workflow

Use this file as the primary source for NotebookLM:

```text
data/reports/notebooklm-digest.md
```

That file is designed to stay readable, source-linked, and updated after each automated run.

## Important note

This does **not** auto-post to social media. It only creates reports and tweet drafts for human review.
