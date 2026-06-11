import json
import os
from pathlib import Path

import yaml
from dotenv import load_dotenv

from quote_miner import analyze_transcript
from report import write_reports
from transcript import get_transcript
from youtube_feeds import find_candidate_videos


DATA_DIR = Path("data")
SEEN_FILE = DATA_DIR / "seen_videos.json"
QUOTES_FILE = DATA_DIR / "quotes.json"


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

    max_videos_per_team = int(os.getenv("MAX_VIDEOS_PER_TEAM", "5"))
    min_transcript_chars = int(os.getenv("MIN_TRANSCRIPT_CHARS", "500"))

    with open(DATA_DIR / "teams.yml", "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    seen = set(load_json(SEEN_FILE, []))
    all_quotes = load_json(QUOTES_FILE, [])
    new_items = []

    for team_key, team in config.get("teams", {}).items():
        try:
            videos = find_candidate_videos(team_key, team, limit=max_videos_per_team)
        except Exception as exc:
            print(f"Feed error for {team.get('name', team_key)}: {exc}")
            continue

        for video in videos:
            video_id = video.get("video_id")
            if not video_id or video_id in seen:
                continue

            print(f"Processing: {video['team_name']} - {video['title']}")

            try:
                transcript = get_transcript(video["url"])
            except Exception as exc:
                print(f"Transcript error for {video.get('url')}: {exc}")
                seen.add(video_id)
                continue

            if not transcript or len(transcript) < min_transcript_chars:
                print("No usable transcript found or transcript too short.")
                seen.add(video_id)
                continue

            try:
                analysis = analyze_transcript(
                    team_name=video["team_name"],
                    video_title=video["title"],
                    video_url=video["url"],
                    transcript=transcript,
                )
            except Exception as exc:
                print(f"LLM analysis error: {exc}")
                seen.add(video_id)
                continue

            item = {
                "video": video,
                "analysis": analysis,
            }

            new_items.append(item)
            all_quotes.append(item)
            seen.add(video_id)

    save_json(QUOTES_FILE, all_quotes)
    save_json(SEEN_FILE, sorted(list(seen)))
    write_reports(new_items, all_quotes)

    print(f"Processed {len(new_items)} new videos.")


if __name__ == "__main__":
    main()
