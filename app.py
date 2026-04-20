from __future__ import annotations

import secrets
from pathlib import Path

from flask import Flask, render_template, request, send_from_directory
from werkzeug.utils import secure_filename

from enhancer import (
    PRESETS,
    AudioEnhancementError,
    create_preview_clip,
    enhance_audio,
    get_preset_settings,
)
from youtube_audio import YoutubeAudioError, download_youtube_audio


BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"
PROCESSED_DIR = BASE_DIR / "processed"
PREVIEW_DIR = BASE_DIR / "previews"
ALLOWED_EXTENSIONS = {".mp3", ".wav", ".flac", ".m4a", ".aac", ".ogg"}
SUPPORTED_BROWSERS = {"chrome", "chromium", "firefox", "safari", "edge", "brave", "vivaldi"}

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 100 * 1024 * 1024


def allowed_file(filename: str) -> bool:
    return Path(filename).suffix.lower() in ALLOWED_EXTENSIONS


def default_form_values() -> dict:
    return {
        "youtube_url": "",
        "browser_cookies": "",
        "preset": "balanced_restore",
        "mode": "preset",
        "noise_reduction": PRESETS["balanced_restore"]["noise_reduction"],
        "warmth": PRESETS["balanced_restore"]["warmth"],
        "presence": PRESETS["balanced_restore"]["presence"],
        "normalize": PRESETS["balanced_restore"]["normalize"],
    }


def render_index(**context):
    values = default_form_values()
    values.update(context.pop("values", {}))
    return render_template("index.html", presets=PRESETS, values=values, **context)


@app.get("/")
def index():
    return render_index()


@app.get("/media/<folder>/<path:filename>")
def media(folder: str, filename: str):
    directories = {
        "uploads": UPLOAD_DIR,
        "processed": PROCESSED_DIR,
        "previews": PREVIEW_DIR,
    }
    target_dir = directories.get(folder)
    if target_dir is None:
        return "Not found", 404
    return send_from_directory(target_dir, filename)


@app.post("/enhance")
def enhance():
    uploaded_file = request.files.get("audio_file")
    youtube_url = request.form.get("youtube_url", "").strip()
    browser_cookies = request.form.get("browser_cookies", "").strip().lower()
    preset = request.form.get("preset", "balanced_restore")
    mode = request.form.get("mode", "preset")
    form_values = {
        "youtube_url": youtube_url,
        "browser_cookies": browser_cookies,
        "preset": preset,
        "mode": mode,
        "noise_reduction": request.form.get("noise_reduction", "18"),
        "warmth": request.form.get("warmth", "2"),
        "presence": request.form.get("presence", "3"),
        "normalize": request.form.get("normalize") == "on",
    }

    preset_settings = get_preset_settings(preset)
    if mode == "professional":
        noise_reduction = int(request.form.get("noise_reduction", preset_settings["noise_reduction"]))
        warmth = int(request.form.get("warmth", preset_settings["warmth"]))
        presence = int(request.form.get("presence", preset_settings["presence"]))
        normalize = request.form.get("normalize") == "on"
    else:
        noise_reduction = preset_settings["noise_reduction"]
        warmth = preset_settings["warmth"]
        presence = preset_settings["presence"]
        normalize = preset_settings["normalize"]
        form_values.update(
            {
                "noise_reduction": noise_reduction,
                "warmth": warmth,
                "presence": presence,
                "normalize": normalize,
            }
        )

    token = secrets.token_hex(6)

    if youtube_url:
        browser = browser_cookies if browser_cookies in SUPPORTED_BROWSERS else None
        try:
            input_path = download_youtube_audio(youtube_url, UPLOAD_DIR, token, browser=browser)
        except YoutubeAudioError as exc:
            return render_index(error=str(exc), values=form_values), 400
    else:
        if uploaded_file is None or uploaded_file.filename == "":
            return render_index(
                error="Provide a YouTube link or choose an audio file first.",
                values=form_values,
            ), 400

        if not allowed_file(uploaded_file.filename):
            return render_index(
                error="Unsupported file type. Use mp3, wav, flac, m4a, aac, or ogg.",
                values=form_values,
            ), 400

        original_name = secure_filename(uploaded_file.filename)
        stem = Path(original_name).stem or "track"
        input_path = UPLOAD_DIR / f"{stem}-{token}{Path(original_name).suffix.lower()}"

        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        uploaded_file.save(input_path)

    output_path = PROCESSED_DIR / f"{input_path.stem}-enhanced-{token}.mp3"
    input_preview_path = PREVIEW_DIR / f"{input_path.stem}-preview-{token}.mp3"
    output_preview_path = PREVIEW_DIR / f"{output_path.stem}-preview-{token}.mp3"

    try:
        enhance_audio(
            input_path=input_path,
            output_path=output_path,
            noise_reduction=noise_reduction,
            warmth=warmth,
            presence=presence,
            normalize=normalize,
        )
        create_preview_clip(input_path=input_path, output_path=input_preview_path)
        create_preview_clip(input_path=output_path, output_path=output_preview_path)
    except AudioEnhancementError as exc:
        return render_index(error=str(exc), values=form_values), 500

    result = {
        "download_name": output_path.name,
        "download_url": f"/media/processed/{output_path.name}",
        "input_preview_url": f"/media/previews/{input_preview_path.name}",
        "output_preview_url": f"/media/previews/{output_preview_path.name}",
        "preset_label": PRESETS.get(preset, PRESETS["balanced_restore"])["label"],
        "mode": mode,
    }

    return render_index(result=result, values=form_values)


if __name__ == "__main__":
    app.run(debug=True)
