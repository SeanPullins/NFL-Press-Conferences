from datetime import datetime, timezone
from pathlib import Path


REPORT_DIR = Path("data/reports")


def _fmt_list(items):
    if not items:
        return "- None found.\n"
    return "".join(f"- {item}\n" for item in items)


def _append_debug(lines: list[str], debug_payload: dict | None):
    if not debug_payload:
        return

    lines.append("## Debug / Discovery Notes\n")

    events = debug_payload.get("discovery_events", [])
    if events:
        lines.append("### Discovery Events\n")
        for event in events[:80]:
            lines.append(f"- {event}\n")

    run_debug = debug_payload.get("run_debug", [])
    if run_debug:
        lines.append("### Candidate / Skip Detail\n")
        for item in run_debug[:80]:
            team = item.get("team", "Unknown")
            if "candidate_count" in item:
                lines.append(f"- {team}: {item.get('candidate_count')} candidates found.\n")
                for candidate in item.get("candidates", [])[:5]:
                    lines.append(f"  - {candidate.get('title', 'Untitled')} — {candidate.get('url', '')}\n")
            elif item.get("skipped"):
                lines.append(f"- {team}: skipped {item.get('title', 'Untitled')} — {item.get('skipped')}\n")
            elif item.get("error"):
                lines.append(f"- {team}: {item.get('error')}\n")


def build_markdown_report(items: list[dict], debug_payload: dict | None = None) -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = []
    lines.append("# NFL Press Conference Quote Miner\n")
    lines.append(f"Updated: {now}\n")

    if not items:
        lines.append("No new press conference analysis was generated in this run.\n")
        _append_debug(lines, debug_payload)
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

    _append_debug(lines, debug_payload)
    return "\n".join(lines)


def write_reports(new_items: list[dict], all_items: list[dict], debug_payload: dict | None = None):
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    latest = build_markdown_report(new_items, debug_payload=debug_payload)
    digest_items = all_items[-25:]
    digest_debug = debug_payload if not digest_items else None
    digest = build_markdown_report(digest_items, debug_payload=digest_debug)

    (REPORT_DIR / "latest.md").write_text(latest, encoding="utf-8")
    (REPORT_DIR / "notebooklm-digest.md").write_text(digest, encoding="utf-8")
