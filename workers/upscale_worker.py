from __future__ import annotations

import re
import sys
from io import StringIO
from pathlib import Path

from PyQt6.QtCore import QThread, pyqtSignal


class UpscaleWorker(QThread):
    """Background worker that upscales or downscales a list of images.

    Signals:
        progress(file_index, pct):        0-100 per-file progress.
        file_done(file_index, out_path):  emitted when a file finishes successfully.
        file_error(file_index, msg):      emitted when a file fails.
        all_done():                       emitted when the entire batch is complete.
    """

    progress = pyqtSignal(int, int)    # (file_index, pct 0-100)
    file_done = pyqtSignal(int, str)   # (file_index, output_path)
    file_error = pyqtSignal(int, str)  # (file_index, error message)
    all_done = pyqtSignal()

    def __init__(
        self,
        files: list[Path],
        output_dir: Path,
        mode: str,              # "upscale" or "downscale"
        target_w: int,
        target_h: int,
        output_format: str,     # "png" or "jpg"
        model_name: str = "RealESRGAN_x4plus",
        tile_size: int = 512,
        use_fp16: bool = True,
    ) -> None:
        super().__init__()
        self.files = files
        self.output_dir = output_dir
        self.mode = mode
        self.target_w = target_w
        self.target_h = target_h
        self.output_format = output_format
        self.model_name = model_name
        self.tile_size = tile_size
        self.use_fp16 = use_fp16
        self._cancelled = False

    def cancel(self) -> None:
        self._cancelled = True

    def run(self) -> None:
        from core.upscaler import Upscaler

        upscaler: Upscaler | None = None

        for idx, src in enumerate(self.files):
            if self._cancelled:
                break

            try:
                suffix = f".{self.output_format.lower()}"
                label = "_upscaled" if self.mode == "upscale" else "_downscaled"
                out_path = self.output_dir / (src.stem + label + suffix)

                self.progress.emit(idx, 0)

                if self.mode == "upscale":
                    if upscaler is None:
                        upscaler = Upscaler(
                            model_name=self.model_name,
                            tile_size=self.tile_size,
                            use_fp16=self.use_fp16,
                        )
                    # Intercept stdout to capture "Tile X/Y" lines.
                    tile_stream = _TileStream(
                        lambda pct: self.progress.emit(idx, pct)
                    )
                    old_stdout = sys.stdout
                    sys.stdout = tile_stream
                    try:
                        upscaler.upscale(
                            src, out_path, self.target_w, self.target_h, self.output_format
                        )
                    finally:
                        sys.stdout = old_stdout
                else:
                    from PIL import Image
                    from core.upscaler import _save_image

                    img = Image.open(src).convert("RGB")
                    img = img.resize((self.target_w, self.target_h), Image.LANCZOS)
                    out_path.parent.mkdir(parents=True, exist_ok=True)
                    _save_image(img, out_path, self.output_format)

                self.progress.emit(idx, 100)
                self.file_done.emit(idx, str(out_path))

            except Exception as exc:  # noqa: BLE001
                self.file_error.emit(idx, str(exc))

        self.all_done.emit()


_TILE_RE = re.compile(r"Tile\s+(\d+)/(\d+)", re.IGNORECASE)


class _TileStream:
    """Stdout replacement that parses 'Tile X/Y' lines and calls a progress callback."""

    def __init__(self, callback) -> None:
        self._callback = callback
        self._buf = ""

    def write(self, text: str) -> int:
        self._buf += text
        for line in self._buf.splitlines(keepends=True):
            if line.endswith("\n"):
                m = _TILE_RE.search(line)
                if m:
                    current, total = int(m.group(1)), int(m.group(2))
                    if total > 0:
                        self._callback(int(current / total * 99))
        # Keep only the last incomplete line.
        lines = self._buf.splitlines(keepends=True)
        self._buf = lines[-1] if lines and not lines[-1].endswith("\n") else ""
        return len(text)

    def flush(self) -> None:
        pass
