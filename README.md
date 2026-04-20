# Old Nepali Music Refiner

A small local web app for improving old Nepali songs with `ffmpeg`.

## What it does

- Upload an old recording
- Paste a YouTube link for a song
- Start from ready-made restoration presets
- Compare a short before/after preview on the page
- Switch to professional mode for manual tuning
- Download the full enhanced MP3

This is an MVP. It uses a practical filter chain, not AI source separation or studio-grade restoration.

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

## Requirements

- Python 3.9+
- `ffmpeg` available on your system path
- Internet access when downloading from YouTube

## Notes

- Supported input types: `mp3`, `wav`, `flac`, `m4a`, `aac`, `ogg`
- YouTube downloads are handled through `yt-dlp[default]`
- Max upload size is 100 MB
- Processed files are written to `processed/`
- Short preview clips are written to `previews/`

## YouTube 403 note

If YouTube downloading fails with `HTTP Error 403: Forbidden`, reinstall the app dependencies:

```bash
pip install -r requirements.txt
```

This app expects:

- `yt-dlp[default]`
- Node.js 20 or newer on your `PATH`

That follows the current `yt-dlp` guidance for YouTube's JavaScript challenge flow.

If a public YouTube URL still fails, try the browser cookie selector in the UI and choose the browser where you are already signed in to YouTube. `yt-dlp` supports browser-cookie loading, and recent issue reports indicate this can succeed when plain requests are blocked:

- https://github.com/yt-dlp/yt-dlp/blob/master/yt_dlp/YoutubeDL.py
- https://github.com/yt-dlp/yt-dlp/issues/12912
