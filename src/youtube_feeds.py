import json
import subprocess

import feedparser


DEBUG_EVENTS = []


def debug(message: str):
    print(message)
    DEBUG_EVENTS.append(message)


def get_debug_events() -> list[str]:
    return DEBUG_EVENTS


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
        debug(f"{team.get('name', team_key)}: no RSS channel ID configured")
        return []

    feed = get_channel_feed(channel_id)
    keywords = team.get("keywords", [])
    videos = []
    entries = list(getattr(feed, "entries", []))
    debug(f"{team.get('name', team_key)} RSS entries found: {len(entries)}")

    for entry in entries[:limit]:
        title = getattr(entry, "title", "")
        if not _matches_keywords(title, keywords):
            debug(f"{team.get('name', team_key)} RSS skipped by keyword: {title}")
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


def find_videos_from_ytdlp_channel(team_key: str, team: dict, limit: int = 10):
    youtube_url = team.get("youtube_url")
    if not youtube_url:
        debug(f"{team.get('name', team_key)}: no YouTube URL configured")
        return []

    url = youtube_url.rstrip("/") + "/videos"
    return _find_videos_with_ytdlp_url(team_key, team, url, limit, source="yt-dlp-channel")


def find_videos_from_ytdlp_search(team_key: str, team: dict, limit: int = 10):
    queries = team.get("search_queries") or [f"{team.get('name', team_key)} press conference"]
    all_videos = []
    seen_ids = set()

    for query in queries:
        url = f"ytsearch{limit}:{query}"
        videos = _find_videos_with_ytdlp_url(team_key, team, url, limit, source=f"ytsearch:{query}", ignore_keywords=True)
        for video in videos:
            vid = video.get("video_id")
            if vid and vid not in seen_ids:
                seen_ids.add(vid)
                all_videos.append(video)

    return all_videos[:limit]


def _find_videos_with_ytdlp_url(team_key: str, team: dict, url: str, limit: int, source: str, ignore_keywords: bool = False):
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
        debug(f"{team.get('name', team_key)} {source} discovery failed: {result.stderr[:500]}")
        return []

    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError:
        debug(f"{team.get('name', team_key)} {source} returned invalid JSON")
        return []

    keywords = team.get("keywords", [])
    entries = payload.get("entries", []) or []
    debug(f"{team.get('name', team_key)} {source} entries found: {len(entries)}")
    videos = []

    for entry in entries[:limit]:
        title = entry.get("title", "")
        if not ignore_keywords and not _matches_keywords(title, keywords):
            debug(f"{team.get('name', team_key)} {source} skipped by keyword: {title}")
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
            "source": source,
        })

    return videos


def find_candidate_videos(team_key: str, team: dict, limit: int = 10):
    videos = find_videos_from_rss(team_key, team, limit=limit)
    if videos:
        debug(f"Found {len(videos)} candidate videos for {team.get('name', team_key)} via RSS")
        return videos

    videos = find_videos_from_ytdlp_channel(team_key, team, limit=limit)
    if videos:
        debug(f"Found {len(videos)} candidate videos for {team.get('name', team_key)} via channel URL")
        return videos

    videos = find_videos_from_ytdlp_search(team_key, team, limit=limit)
    debug(f"Found {len(videos)} candidate videos for {team.get('name', team_key)} via YouTube search fallback")
    return videos
