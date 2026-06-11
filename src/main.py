import json
import os
from pathlib import Path

import yaml
from dotenv import load_dotenv

from quote_miner import analyze_transcript
from report import write_reports
from transcript import get_transcript, get_transcript_debug_events
from youtube_feeds import find_candidate_videos, get_debug_events


DATA_DIR = Path("data")
SEEN_FILE = DATA_DIR / "seen_videos.json"
QUOTES_FILE = DATA_DIR / "quotes.json"
DEBUG_FILE = DATA_DIR / "debug.json"


def load_json(path: Path, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return default


def save_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def main():
    load_dotenv()
    DATA_DIR.mkdir(exist_ok=True)

    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY is required.")

    max_videos_per_team = int(os.getenv("MAX_VIDEOS_PER_TEAM", "10"))
    min_transcript_chars = int(os.getenv("MIN_TRANSCRIPT_CHARS", "300"))

    with open(DATA_DIR / "teams.yml", "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    seen = set(load_json(SEEN_FILE, []))
    all_quotes = load_json(QUOTES_FILE, [])
    new_items = []
    run_debug = []

    for team_key, team in config.get("teams", {}).items():
        try:
            videos = find_candidate_videos(team_key, team, limit=max_videos_per_team)
            run_debug.append({
                "team": team.get("name", team_key),
                "candidate_count": len(videos),
                "candidates": videos,
            })
        except Exception as exc:
            msg = f"Discovery error for {team.get('name', team_key)}: {exc}"
            print(msg)
            run_debug.append({"team": team.get("name", team_key), "error": msg})
            continue

        for video in videos:
            video_id = video.get("video_id")
            if not video_id:
                run_debug.append({"team": video.get("team_name"), "title": video.get("title"), "skipped": "missing video_id"})
                continue
            if video_id in seen:
                run_debug.append({"team": video.get("team_name"), "title": video.get("title"), "skipped": "already seen"})
                continue

            print(f"Processing: {video['team_name']} - {video['title']}")

            try:
                transcript = get_transcript(video["url"])
            except Exception as exc:
                msg = f"Transcript error for {video.get('url')}: {exc}"
                print(msg)
                run_debug.append({"team": video.get("team_name"), "title": video.get("title"), "skipped": msg})
                continue

            if not transcript or len(transcript) < min_transcript_chars:
                msg = f"No usable transcript found or transcript too short. Length={len(transcript or '')}"
                print(msg)
                run_debug.append({"team": video.get("team_name"), "title": video.get("title"), "url": video.get("url"), "skipped": msg})
                continue

            try:
                analysis = analyze_transcript(
                    team_name=video["team_name"],
                    video_title=video["title"],
                    video_url=video["url"],
                    transcript=transcript,
                )
            except Exception as exc:
                msg = f"LLM analysis error: {exc}"
                print(msg)
                run_debug.append({"team": video.get("team_name"), "title": video.get("title"), "skipped": msg})
                continue

            item = {
                "video": video,
                "analysis": analysis,
            }

            new_items.append(item)
            all_quotes.append(item)
            seen.add(video_id)

    debug_payload = {
        "discovery_events": get_debug_events(),
        "transcript_events": get_transcript_debug_events(),
        "run_debug": run_debug,
    }

    save_json(QUOTES_FILE, all_quotes)
    save_json(SEEN_FILE, sorted(list(seen)))
    save_json(DEBUG_FILE, debug_payload)
    write_reports(new_items, all_quotes, debug_payload=debug_payload)

    print(f"Processed {len(new_items)} new videos.")


if __name__ == "__main__":
    main()
