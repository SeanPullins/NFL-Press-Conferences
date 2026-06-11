from datetime import datetime, timezone
from pathlib import Path


REPORT_DIR = Path("data/reports")


def _fmt_list(items):
    if not items:
        return "- None found.\n"
    return "".join(f"- {item}\n" for item in items)


def build_markdown_report(items: list[dict]) -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = []
    lines.append("# NFL Press Conference Quote Miner\n")
    lines.append(f"Updated: {now}\n")

    if not items:
        lines.append("No new press conference analysis was generated in this run.\n")
        return "\n".join(lines)

    lines.append("## Top League Quotes\n")
    for item in items:
        analysis = item.get("analysis", {})
        video = item.get("video", {})
        lines.append(f"### {analysis.get('team', video.get('team_name', 'Unknown Team'))}: {analysis.get('video_title', video.get('title', 'Untitled'))}\n")
        lines.append(f"Source: {analysis.get('video_url', video.get('url', ''))}\n")
        lines.append(f"Signal score: {analysis.get('overall_signal_score', 0)}\n")
        lines.append(f"Summary: {analysis.get('summary', '')}\n")

        for quote in analysis.get("top_quotes", [])[:5]:
            q = quote.get("quote", "")
            lines.append(f"> {q}\n")
            lines.append(f"- Why it matters: {quote.get('why_it_matters', '')}\n")
            lines.append(f"- Category: {quote.get('category', '')}\n")
            lines.append(f"- Signal: {quote.get('signal_score', 0)}\n")
            lines.append(f"- Browns relevance: {quote.get('browns_relevance', '')}\n")
            lines.append(f"- League relevance: {quote.get('league_relevance', '')}\n")
            lines.append(f"- Tweet angle: {quote.get('tweet_angle', '')}\n")

    lines.append("## QB Watch\n")
    qb_notes = []
    for item in items:
        qb_notes.extend(item.get("analysis", {}).get("qb_notes", []))
    lines.append(_fmt_list(qb_notes))

    lines.append("## Injury Watch\n")
    injury_notes = []
    for item in items:
        injury_notes.extend(item.get("analysis", {}).get("injury_notes", []))
    lines.append(_fmt_list(injury_notes))

    lines.append("## Roster Watch\n")
    roster_notes = []
    for item in items:
        roster_notes.extend(item.get("analysis", {}).get("roster_notes", []))
    lines.append(_fmt_list(roster_notes))

    lines.append("## Scheme Notes\n")
    scheme_notes = []
    for item in items:
        scheme_notes.extend(item.get("analysis", {}).get("scheme_notes", []))
    lines.append(_fmt_list(scheme_notes))

    lines.append("## Draft Notes\n")
    draft_notes = []
    for item in items:
        draft_notes.extend(item.get("analysis", {}).get("draft_notes", []))
    lines.append(_fmt_list(draft_notes))

    lines.append("## Nothing Burgers / Coach-Speak\n")
    for item in items:
        analysis = item.get("analysis", {})
        for low in analysis.get("coach_speak", [])[:5]:
            lines.append(f"- {analysis.get('team', '')}: \"{low.get('quote', '')}\" — {low.get('reason_low_signal', '')}\n")

    lines.append("## Best Tweet Drafts\n")
    tweets = []
    for item in items:
        tweets.extend(item.get("analysis", {}).get("best_tweet_drafts", []))
    lines.append(_fmt_list(tweets))

    return "\n".join(lines)


def write_reports(new_items: list[dict], all_items: list[dict]):
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    latest = build_markdown_report(new_items)
    digest = build_markdown_report(all_items[-25:])

    (REPORT_DIR / "latest.md").write_text(latest, encoding="utf-8")
    (REPORT_DIR / "notebooklm-digest.md").write_text(digest, encoding="utf-8")
