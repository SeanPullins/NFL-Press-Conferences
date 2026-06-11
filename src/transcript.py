import glob
import os
import re
import subprocess
import tempfile


def get_transcript(video_url: str) -> str:
    with tempfile.TemporaryDirectory() as tmp:
        cmd = [
            "yt-dlp",
            "--skip-download",
            "--write-auto-subs",
            "--write-subs",
            "--sub-lang", "en",
            "--sub-format", "vtt",
            "-o", os.path.join(tmp, "%(id)s.%(ext)s"),
            video_url,
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)

        files = glob.glob(os.path.join(tmp, "*.vtt"))
        if not files:
            return ""

        with open(files[0], "r", encoding="utf-8") as f:
            raw = f.read()

        return clean_vtt(raw)


def clean_vtt(raw: str) -> str:
    lines = []
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
        line = line.replace("&amp;", "&")
        lines.append(line)

    text = " ".join(lines)
    text = re.sub(r"\s+", " ", text).strip()
    return text
