from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".tiff", ".tif"}
VIDEO_EXTENSIONS = {".mp4", ".mkv", ".avi", ".webm"}
MOV_EXTENSIONS = {".mov"}

# Maps UI quality label -> (crf, preset)
MP4_QUALITY_PRESETS: dict[str, tuple[int, str]] = {
    "Low": (28, "fast"),
    "Medium": (18, "medium"),
    "High": (0, "slow"),
}


def check_ffmpeg() -> bool:
    """Return True if ffmpeg is available on PATH."""
    return shutil.which("ffmpeg") is not None


def to_resolve(
    input_path: Path,
    output_path: Path,
    quality: int = 2,
    target_w: int | None = None,
    target_h: int | None = None,
) -> None:
    """Convert *input_path* to a Resolve-compatible .mov file.

    Args:
        input_path: Source file (video or image).
        output_path: Destination .mov file.
        quality: MJPEG quality (1–10, lower = better).
        target_w: Optional output width in pixels.
        target_h: Optional output height in pixels.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    suffix = input_path.suffix.lower()

    scale_filter = _scale_filter(target_w, target_h)

    if suffix in IMAGE_EXTENSIONS:
        cmd = _image_to_resolve_cmd(input_path, output_path, quality, scale_filter)
    elif suffix in VIDEO_EXTENSIONS:
        cmd = _video_to_resolve_cmd(input_path, output_path, quality, scale_filter)
    else:
        raise ValueError(f"Unsupported input format: {suffix}")

    _run(cmd)


def to_mp4(
    input_path: Path,
    output_path: Path,
    quality_label: str = "Medium",
    target_w: int | None = None,
    target_h: int | None = None,
) -> None:
    """Convert a .mov file to H.264 MP4.

    Args:
        input_path: Source .mov file.
        output_path: Destination .mp4 file.
        quality_label: One of "Low", "Medium", "High".
        target_w: Optional output width in pixels.
        target_h: Optional output height in pixels.
    """
    if quality_label not in MP4_QUALITY_PRESETS:
        raise ValueError(
            f"Unknown quality preset '{quality_label}'. "
            f"Choose from {list(MP4_QUALITY_PRESETS.keys())}"
        )

    crf, preset = MP4_QUALITY_PRESETS[quality_label]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    scale_filter = _scale_filter(target_w, target_h)

    cmd = _mov_to_mp4_cmd(input_path, output_path, crf, preset, scale_filter)
    _run(cmd)


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _scale_filter(w: int | None, h: int | None) -> list[str]:
    """Return ffmpeg -vf scale args if dimensions are set, else empty list."""
    if w and h:
        return ["-vf", f"scale={w}:{h}"]
    return []


def _image_to_resolve_cmd(
    src: Path, dst: Path, quality: int, scale_filter: list[str]
) -> list[str]:
    cmd = [
        "ffmpeg", "-y",
        "-loop", "1",
        "-i", str(src),
        "-t", "1",
        "-c:v", "mjpeg",
        "-q:v", str(quality),
        "-an",
    ]
    cmd.extend(scale_filter)
    cmd.append(str(dst))
    return cmd


def _video_to_resolve_cmd(
    src: Path, dst: Path, quality: int, scale_filter: list[str]
) -> list[str]:
    cmd = [
        "ffmpeg", "-y",
        "-i", str(src),
        "-c:v", "mjpeg",
        "-q:v", str(quality),
        "-c:a", "pcm_s16le",
    ]
    cmd.extend(scale_filter)
    cmd.append(str(dst))
    return cmd


def _mov_to_mp4_cmd(
    src: Path,
    dst: Path,
    crf: int,
    preset: str,
    scale_filter: list[str],
) -> list[str]:
    cmd = [
        "ffmpeg", "-y",
        "-i", str(src),
        "-c:v", "libx264",
        "-crf", str(crf),
        "-preset", preset,
        "-c:a", "aac",
        "-b:a", "320k",
    ]
    cmd.extend(scale_filter)
    cmd.append(str(dst))
    return cmd


def _run(cmd: list[str]) -> None:
    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"ffmpeg exited with code {result.returncode}:\n"
            + result.stderr.decode(errors="replace")
        )
