from __future__ import annotations

import urllib.request
from pathlib import Path
from typing import Callable, Optional

MODEL_URLS: dict[str, str] = {
    "RealESRGAN_x4plus_anime_6B": (
        "https://github.com/xinntao/Real-ESRGAN/releases/download/"
        "v0.2.2.4/RealESRGAN_x4plus_anime_6B.pth"
    ),
    "RealESRGAN_x4plus": (
        "https://github.com/xinntao/Real-ESRGAN/releases/download/"
        "v0.1.0/RealESRGAN_x4plus.pth"
    ),
}

MODELS_DIR: Path = (
    Path.home() / ".local" / "share" / "resolve-media-tool" / "models"
)


class ModelDownloadError(Exception):
    """Raised when a model download fails."""


def get_model_path(
    model_name: str,
    progress_callback: Optional[Callable[[int, int], None]] = None,
) -> Path:
    """Return the local path for *model_name*, downloading it if missing.

    Args:
        model_name: One of the keys in MODEL_URLS.
        progress_callback: Optional callable(bytes_downloaded, total_bytes).

    Returns:
        Path to the downloaded .pth file.

    Raises:
        ValueError: If *model_name* is not recognised.
        ModelDownloadError: If the download fails for any reason.
    """
    if model_name not in MODEL_URLS:
        raise ValueError(
            f"Unknown model '{model_name}'. "
            f"Available models: {list(MODEL_URLS.keys())}"
        )

    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    dest = MODELS_DIR / f"{model_name}.pth"

    if dest.exists():
        return dest

    url = MODEL_URLS[model_name]
    try:
        _download(url, dest, progress_callback)
    except Exception as exc:
        # Remove a partial file so the next attempt starts fresh.
        if dest.exists():
            dest.unlink()
        raise ModelDownloadError(
            f"Failed to download model '{model_name}' from {url}: {exc}"
        ) from exc

    return dest


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _download(
    url: str,
    dest: Path,
    progress_callback: Optional[Callable[[int, int], None]],
) -> None:
    """Download *url* to *dest*, calling *progress_callback* periodically."""

    request = urllib.request.Request(
        url,
        headers={"User-Agent": "resolve-media-tool/0.1.0"},
    )

    with urllib.request.urlopen(request) as response:
        total_bytes: int = int(response.headers.get("Content-Length", 0))
        downloaded: int = 0
        chunk_size: int = 1024 * 64  # 64 KiB

        with dest.open("wb") as fh:
            while True:
                chunk = response.read(chunk_size)
                if not chunk:
                    break
                fh.write(chunk)
                downloaded += len(chunk)
                if progress_callback is not None:
                    progress_callback(downloaded, total_bytes)
