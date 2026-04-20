from __future__ import annotations

import re
from pathlib import Path

from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError


class YoutubeAudioError(RuntimeError):
    """Raised when a YouTube audio download fails."""


def sanitize_stem(name: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "-", name).strip("-._")
    return cleaned or "youtube-track"


def build_ydl_options(
    output_template: str,
    browser: str | None,
    player_clients: list[str],
    skip: list[str] | None = None,
    format_selector: str | None = None,
) -> dict:
    options: dict = {
        "format": "bestaudio/best",
        "outtmpl": output_template,
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "js_runtimes": {"node": {}},
        "remote_components": ["ejs:github"],
        "extractor_args": {
            "youtube": {
                "player_client": player_clients,
            }
        },
    }

    if skip:
        options["extractor_args"]["youtube"]["skip"] = skip

    if format_selector:
        options["format"] = format_selector

    if browser:
        options["cookiesfrombrowser"] = (browser,)

    return options


def download_youtube_audio(url: str, target_dir: Path, token: str, browser: str | None = None) -> Path:
    target_dir.mkdir(parents=True, exist_ok=True)
    output_template = str(target_dir / f"%(title)s-{token}.%(ext)s")

    strategies = [
        {
            "player_clients": ["web_music", "mweb", "web"],
            "skip": ["hls", "dash"],
            "format_selector": "bestaudio[protocol!=m3u8][protocol!=http_dash_segments]/bestaudio/best",
        },
        {
            "player_clients": ["tv", "tv_downgraded", "mweb"],
            "skip": ["hls", "dash"],
            "format_selector": "bestaudio[protocol!=m3u8][protocol!=http_dash_segments]/bestaudio/best",
        },
        {
            "player_clients": ["android_vr", "android", "mweb"],
            "skip": None,
            "format_selector": "bestaudio/best",
        },
    ]

    last_error: Exception | None = None
    for strategy in strategies:
        try:
            options = build_ydl_options(
                output_template=output_template,
                browser=browser,
                player_clients=strategy["player_clients"],
                skip=strategy["skip"],
                format_selector=strategy["format_selector"],
            )
            with YoutubeDL(options) as ydl:
                info = ydl.extract_info(url, download=True)
                downloaded_path = Path(ydl.prepare_filename(info))
            break
        except DownloadError as exc:
            last_error = exc
            continue
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            continue
    else:
        message = "Unable to download audio from the provided YouTube link."
        if last_error is not None:
            raw_message = str(last_error)
            if "403" in raw_message or "Forbidden" in raw_message:
                if browser:
                    message = (
                        f"YouTube still returned HTTP 403 even when using {browser} browser cookies "
                        "and multiple downloader strategies. This is likely an upstream YouTube block "
                        "for this video or your current network session."
                    )
                else:
                    message = (
                        "YouTube returned HTTP 403 across multiple downloader strategies. Try again with "
                        "browser cookies enabled. Chrome usually works best if you are already signed in there."
                    )
            else:
                message = raw_message
        raise YoutubeAudioError(message) from last_error

    safe_title = sanitize_stem(info.get("title", "youtube-track"))
    final_path = downloaded_path.with_name(f"{safe_title}-{token}{downloaded_path.suffix.lower()}")

    if downloaded_path != final_path and downloaded_path.exists():
        downloaded_path.rename(final_path)

    return final_path
