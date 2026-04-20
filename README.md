# Old Nepali Music Refiner

A Flask app for improving old Nepali songs with restoration presets, preview clips, and optional advanced controls.

## What it does

- Upload an old recording
- Start from ready-made restoration presets
- Compare a short before/after preview on the page
- Switch to professional mode for manual tuning
- Download the full enhanced MP3

This app uses a practical `ffmpeg`-based restoration pipeline, not AI source separation or studio-grade mastering.

## Hosted vs local

There are two intended modes:

- Hosted/shared app:
  Upload audio files only. This is the practical public setup.
- Local app on your own machine:
  Optional YouTube importing can be enabled if you want to experiment with it.

The reason for this split is simple: public hosting providers are frequently blocked by YouTube anti-bot checks, even when `yt-dlp` is configured correctly. Because of that, YouTube importing is disabled by default in the deployed app.

## Run locally

1. Create a virtual environment:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Start the app:

   ```bash
   python3 app.py
   ```

4. Open `http://127.0.0.1:5000`

## Enable YouTube importing locally

YouTube support is off by default. To enable it on your own machine:

```bash
ENABLE_YOUTUBE_DOWNLOADS=true python3 app.py
```

This is intended for local use only. It is not reliable for a public deployed app.

## Deploy on Render

This repo includes `render.yaml` for Render deployment.

After deployment, the shared app should be treated as upload-first:

- upload an audio file
- choose a preset
- preview before/after
- download the enhanced result

Do not rely on YouTube URL importing in the public deployment.

## Requirements

- Python 3.9+
- `ffmpeg` available on your system path
- Node.js 20+ if you enable YouTube importing locally

## Notes

- Supported input types: `mp3`, `wav`, `flac`, `m4a`, `aac`, `ogg`
- Preview clips are written to `previews/`
- Max upload size is 100 MB
- Processed files are written to `processed/`
- `yt-dlp[default]` is included only for local YouTube importing

## Why YouTube is disabled on the deployed app

`yt-dlp` can work locally because it can sometimes reuse your browser session and local network context. On a public host, that breaks down:

- the server IP is different from your browser IP
- browser cookies are not safely available to the server
- YouTube often returns bot/auth challenges to hosted environments

So the practical product decision is:

- shared deployment = file upload workflow
- local machine = optional YouTube workflow
