import json
import os
from openai import OpenAI


SYSTEM_PROMPT = """
You are an expert NFL press conference analyst.

Your job:
- Extract important quotes from NFL press conference transcripts.
- Separate real signal from generic coach-speak.
- Identify QB, injury, roster, scheme, coaching, front office, draft, and Browns-relevant implications.
- Create useful tweet drafts for human review.
- Do not overstate vague comments.
- Return valid JSON only.
"""


def get_client() -> OpenAI:
    base_url = os.getenv("OPENAI_BASE_URL") or None
    return OpenAI(api_key=os.getenv("OPENAI_API_KEY"), base_url=base_url)


def analyze_transcript(team_name: str, video_title: str, video_url: str, transcript: str) -> dict:
    client = get_client()
    model = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")

    user_prompt = f"""
Team: {team_name}
Video title: {video_title}
Video URL: {video_url}

Transcript:
{transcript[:30000]}

Return valid JSON only in this structure:

{{
  "team": "{team_name}",
  "video_title": "{video_title}",
  "video_url": "{video_url}",
  "speaker_guess": "",
  "overall_signal_score": 0,
  "summary": "",
  "top_quotes": [
    {{
      "quote": "",
      "why_it_matters": "",
      "category": "",
      "signal_score": 0,
      "browns_relevance": "",
      "league_relevance": "",
      "tweet_angle": ""
    }}
  ],
  "coach_speak": [
    {{
      "quote": "",
      "reason_low_signal": ""
    }}
  ],
  "injury_notes": [],
  "qb_notes": [],
  "roster_notes": [],
  "scheme_notes": [],
  "draft_notes": [],
  "best_tweet_drafts": []
}}
"""

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.2,
    )

    raw = response.choices[0].message.content.strip()
    if raw.startswith("```"):
        raw = raw.strip("`")
        raw = raw.replace("json\n", "", 1)

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {
            "team": team_name,
            "video_title": video_title,
            "video_url": video_url,
            "speaker_guess": "",
            "overall_signal_score": 0,
            "summary": "LLM returned invalid JSON.",
            "top_quotes": [],
            "coach_speak": [],
            "injury_notes": [],
            "qb_notes": [],
            "roster_notes": [],
            "scheme_notes": [],
            "draft_notes": [],
            "best_tweet_drafts": [],
            "raw_model_output": raw,
        }
