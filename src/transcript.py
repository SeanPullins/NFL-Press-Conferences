import base64
import glob
import gzip
import os
import re
import subprocess
import tempfile
from pathlib import Path
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
    if parsed