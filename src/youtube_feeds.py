import json
import subprocess

import feedparser


def get_channel_feed(channel_id: str):
    url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
    return feedparser.parse(url)


def _matches_keywords(title: str, keywords: list[str]) -> bool:
    if not keywords:
        return True
    title_lower = title.lower()
    return any(keyword.lower() in title_lower for keyword in keywords)


def find_videos_from_rss(team_key: str, team: dict, limit: int = 10):
    channel_id = team.get("youtube_channel_id")
    if not channel_id:
        return []

    feed = get_channel_feed(channel_id)
    keywords = team.get("keywords", [])
    videos = []

    for entry in feed.entries[:limit]:
        title = getattr(entry, "title", "")
        if not _matches_keywords(title, keywords):
            continue

        videos.append({
            "team_key": team_key,
            "team_name": team["name"],
            "title": title,
            "url": getattr(entry, "link", ""),
            "video_id": getattr(entry, "yt_videoid", ""),
            "published": getattr(entry, "published", ""),
            "source": "rss",
        })

    return videos


def find_videos_from_ytdlp(team_key: str, team: dict, limit: int = 10):
    youtube_url = team.get("youtube_url")
    if not youtube_url:
        return []

    url = youtube_url.rstrip("/") + "/videos"
    cmd = [
        "yt-dlp",
        "--flat-playlist",
        "--dump-single-json",
        "--playlist-end",
        str(limit),
        url,
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    if result.returncode != 0 or not result.stdout.strip():
        print(f"yt-dlp discovery failed for {team.get('name', team_key)}: {result.stderr[:500]}")
        return []

    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError:
        print(f"yt-dlp discovery returned invalid JSON for {team.get('name', team_key)}")
        return []

    keywords = team.get("keywords", [])
    videos = []

    for entry in payload.get("entries", [])[:limit]:
        title = entry.get("title", "")
        if not _matches_keywords(title, keywords):
            continue

        video_id = entry.get("id") or entry.get("url") or ""
        video_url = entry.get("url") or ""
        if video_url and not video_url.startswith("http"):
            video_url = f"https://www.youtube.com/watch?v={video_url}"
        elif not video_url and video_id:
            video_url = f"https://www.youtube.com/watch?v={video_id}"

        videos.append({
            "team_key": team_key,
            "team_name": team["name"],
            "title": title,
            "url": video_url,
            "video_id": video_id,
            "published": entry.get("timestamp") or entry.get("upload_date") or "",
            "source": "yt-dlp",
        })

    return videos


def find_candidate_videos(team_key: str, team: dict, limit: int = 10):
    # Prefer RSS when a verified channel ID exists, then fall back to yt-dlp using the channel handle URL.
    videos = find_videos_from_rss(team_key, team, limit=limit)
    if videos:
        print(f"Found {len(videos)} candidate videos for {team.get('name', team_key)} via RSS")
        return videos

    videos = find_videos_from_ytdlp(team_key, team, limit=limit)
    print(f"Found {len(videos)} candidate videos for {team.get('name', team_key)} via yt-dlp")
    return videos
