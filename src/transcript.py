import glob
import os
import re
import subprocess
import tempfile
from urllib.parse import parse_qs, urlparse

from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import NoTranscriptFound, TranscriptsDisabled, VideoUnavailable


TRANSCRIPT_DEBUG = []


def transcript_debug(message: str):
    print(message)
    TRANSCRIPT_DEBUG.append(message)


def get_transcript_debug_events() -> list[str]:
    return TRANSCRIPT_DEBUG


def extract_video_id(video_url: str) -> str:
    parsed = urlparse(video_url)
    if parsed.hostname in {"youtu.be", "www.youtu.be"}:
        return parsed.path.lstrip("/")
    if parsed.query:
        qs = parse_qs(parsed.query)
        if "v" in qs and qs["v"]:
            return qs["v"][0]
    if "/shorts/" in parsed.path:
        return parsed.path.split("/shorts/", 1)[1].split("/", 1)[0]
    return video_url.rsplit("/", 1)[-1]


def get_transcript(video_url: str) -> str:
    video_id = extract_video_id(video_url)

    api_text = get_transcript_from_api(video_id)
    if api_text:
        return api_text

    return get_transcript_from_ytdlp(video_url)


def get_transcript_from_api(video_id: str) -> str:
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=["en", "en-US", "en-GB"])
        text = " ".join(item.get("text", "") for item in transcript)
        text = clean_plain_text(text)
        transcript_debug(f"Transcript API success for {video_id}. Length={len(text)}")
        return text
    except (NoTranscriptFound, TranscriptsDisabled, VideoUnavailable) as exc:
        transcript_debug(f"Transcript API unavailable for {video_id}: {type(exc).__name__}")
        return ""
    except Exception as exc:
        transcript_debug(f"Transcript API error for {video_id}: {type(exc).__name__}: {exc}")
        return ""


def get_transcript_from_ytdlp(video_url: str) -> str:
    with tempfile.TemporaryDirectory() as tmp:
        cmd = [
            "yt-dlp",
            "--skip-download",
            "--write-auto-subs",
            "--write-subs",
            "--sub-lang", "en.*",
            "--sub-format", "vtt",
            "-o", os.path.join(tmp, "%(id)s.%(ext)s"),
            video_url,
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
        if result.returncode != 0:
            transcript_debug(f"yt-dlp subtitle error for {video_url}: {result.stderr[:500]}")

        files = glob.glob(os.path.join(tmp, "*.vtt"))
        transcript_debug(f"yt-dlp subtitle files for {video_url}: {len(files)}")
        if not files:
            return ""

        texts = []
        for file in files:
            with open(file, "r", encoding="utf-8") as f:
                texts.append(clean_vtt(f.read()))

        text = clean_plain_text(" ".join(texts))
        transcript_debug(f"yt-dlp subtitle success for {video_url}. Length={len(text)}")
        return text


def clean_plain_text(raw: str) -> str:
    text = raw.replace("&amp;", "&")
    text = re.sub(r"\[[^\]]*\]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def clean_vtt(raw: str) -> str:
    lines = []
    previous = None
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith("WEBVTT"):
            continue
        if "-->" in line:
            continue
        if line.isdigit():
            continue
        if line.startswith("Kind:") or line.startswith("Language:"):
            continue
        line = re.sub(r"<[^>]+>", "", line)
        line = clean_plain_text(line)
        if not line or line == previous:
            continue
        previous = line
        lines.append(line)

    return clean_plain_text(" ".join(lines))
