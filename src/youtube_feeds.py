import feedparser


def get_channel_feed(channel_id: str):
    url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
    return feedparser.parse(url)


def find_candidate_videos(team_key: str, team: dict, limit: int = 10):
    feed = get_channel_feed(team["youtube_channel_id"])
    keywords = [k.lower() for k in team.get("keywords", [])]
    videos = []

    for entry in feed.entries[:limit]:
        title = getattr(entry, "title", "")
        title_lower = title.lower()

        if keywords and not any(keyword in title_lower for keyword in keywords):
            continue

        videos.append({
            "team_key": team_key,
            "team_name": team["name"],
            "title": title,
            "url": getattr(entry, "link", ""),
            "video_id": getattr(entry, "yt_videoid", ""),
            "published": getattr(entry, "published", ""),
        })

    return videos
