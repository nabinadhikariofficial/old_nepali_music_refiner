from __future__ import annotations

import subprocess
from pathlib import Path


class AudioEnhancementError(RuntimeError):
    """Raised when ffmpeg fails to process an input file."""


PRESETS = {
    "balanced_restore": {
        "label": "Balanced Restore",
        "description": "Best default for most old Nepali songs. Cleans hiss without stripping too much character.",
        "noise_reduction": 18,
        "warmth": 2,
        "presence": 3,
        "normalize": True,
    },
    "warm_vinyl": {
        "label": "Warm Vinyl",
        "description": "Keeps more nostalgic body and softness for classic analog sounding recordings.",
        "noise_reduction": 14,
        "warmth": 4,
        "presence": 1,
        "normalize": True,
    },
    "vocal_focus": {
        "label": "Vocal Focus",
        "description": "Pushes singers and melody forward for muddy cassette or radio transfers.",
        "noise_reduction": 20,
        "warmth": 1,
        "presence": 5,
        "normalize": True,
    },
    "clean_bright": {
        "label": "Clean Bright",
        "description": "A firmer cleanup for noisy uploads that need extra clarity and sharper top-end control.",
        "noise_reduction": 24,
        "warmth": 0,
        "presence": 4,
        "normalize": True,
    },
}


def get_preset_settings(preset_key: str) -> dict:
    return PRESETS.get(preset_key, PRESETS["balanced_restore"]).copy()


def build_audio_filter(
    noise_reduction: int,
    warmth: int,
    presence: int,
    normalize: bool,
) -> str:
    """Build an ffmpeg filter chain tuned for old music restoration."""
    filters = [
        "highpass=f=55",
        "lowpass=f=12000",
        f"afftdn=nr={noise_reduction}:nf=-28",
        "deesser=i=0.4:m=0.5:f=0.5:s=0.3",
        f"equalizer=f=180:t=q:w=1.0:g={warmth}",
        f"equalizer=f=2800:t=q:w=1.1:g={presence}",
        "acompressor=threshold=-18dB:ratio=2.5:attack=25:release=180:makeup=2",
    ]

    if normalize:
        filters.append("loudnorm=I=-16:TP=-1.5:LRA=11")

    filters.append("alimiter=limit=-1.2dB")
    return ",".join(filters)


def enhance_audio(
    input_path: Path,
    output_path: Path,
    noise_reduction: int,
    warmth: int,
    presence: int,
    normalize: bool,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    filter_chain = build_audio_filter(
        noise_reduction=noise_reduction,
        warmth=warmth,
        presence=presence,
        normalize=normalize,
    )

    command = [
        "ffmpeg",
        "-y",
        "-i",
        str(input_path),
        "-vn",
        "-af",
        filter_chain,
        "-ar",
        "44100",
        "-c:a",
        "libmp3lame",
        "-b:a",
        "192k",
        str(output_path),
    ]

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=False,
    )

    if result.returncode != 0:
        raise AudioEnhancementError(result.stderr.strip() or "ffmpeg processing failed")


def create_preview_clip(
    input_path: Path,
    output_path: Path,
    start_seconds: int = 15,
    duration_seconds: int = 18,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    command = [
        "ffmpeg",
        "-y",
        "-ss",
        str(start_seconds),
        "-i",
        str(input_path),
        "-t",
        str(duration_seconds),
        "-vn",
        "-c:a",
        "libmp3lame",
        "-b:a",
        "160k",
        str(output_path),
    ]

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=False,
    )

    if result.returncode != 0:
        raise AudioEnhancementError(result.stderr.strip() or "ffmpeg preview generation failed")
