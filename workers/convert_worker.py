from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import QThread, pyqtSignal


class ConvertWorker(QThread):
    """Background worker that converts a list of media files via ffmpeg.

    Signals:
        progress(file_index, pct):   0-100 per-file progress (currently 0 then 100).
        file_done(file_index):       emitted when a file finishes successfully.
        file_error(file_index, msg): emitted when a file fails.
        all_done():                  emitted when the entire batch is complete.
    """

    progress = pyqtSignal(int, int)    # (file_index, pct 0-100)
    file_done = pyqtSignal(int, str)   # (file_index, output_path)
    file_error = pyqtSignal(int, str)  # (file_index, error message)
    all_done = pyqtSignal()

    def __init__(
        self,
        files: list[Path],
        output_dir: Path,
        direction: str,             # "to_resolve" or "to_mp4"
        mjpeg_quality: int = 2,     # 1-10, lower = better (to_resolve only)
        mp4_quality: str = "Medium",  # "Low" / "Medium" / "High" (to_mp4 only)
        target_w: int | None = None,
        target_h: int | None = None,
    ) -> None:
        super().__init__()
        self.files = files
        self.output_dir = output_dir
        self.direction = direction
        self.mjpeg_quality = mjpeg_quality
        self.mp4_quality = mp4_quality
        self.target_w = target_w
        self.target_h = target_h
        self._cancelled = False

    def cancel(self) -> None:
        self._cancelled = True

    def run(self) -> None:
        from core.converter import to_resolve, to_mp4

        for idx, src in enumerate(self.files):
            if self._cancelled:
                break

            try:
                self.progress.emit(idx, 0)

                if self.direction == "to_resolve":
                    out_path = self.output_dir / (src.stem + "_resolve.mov")
                    to_resolve(
                        src,
                        out_path,
                        quality=self.mjpeg_quality,
                        target_w=self.target_w,
                        target_h=self.target_h,
                    )
                else:
                    out_path = self.output_dir / (src.stem + "_export.mp4")
                    to_mp4(
                        src,
                        out_path,
                        quality_label=self.mp4_quality,
                        target_w=self.target_w,
                        target_h=self.target_h,
                    )

                self.progress.emit(idx, 100)
                self.file_done.emit(idx, str(out_path))

            except Exception as exc:  # noqa: BLE001
                self.file_error.emit(idx, str(exc))

        self.all_done.emit()
