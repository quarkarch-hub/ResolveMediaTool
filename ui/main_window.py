from __future__ import annotations

import json
from pathlib import Path

from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QMainWindow, QMessageBox, QTabWidget

from ui.upscaler_tab import UpscalerTab
from ui.converter_tab import ConverterTab
from core.converter import check_ffmpeg

CONFIG_PATH = Path.home() / ".config" / "resolve-media-tool" / "config.json"
ICON_PATH = Path(__file__).parent.parent / "assets" / "icon.png"


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Resolve Media Tool")
        self.setMinimumSize(680, 600)

        if ICON_PATH.exists():
            self.setWindowIcon(QIcon(str(ICON_PATH)))

        self._config = self._load_config()
        self._check_ffmpeg()
        self._setup_ui()

    # ------------------------------------------------------------------
    # Setup
    # ------------------------------------------------------------------

    def _setup_ui(self) -> None:
        tabs = QTabWidget()
        tabs.addTab(UpscalerTab(self._config), "Upscaler")
        tabs.addTab(ConverterTab(self._config), "Converter")
        self.setCentralWidget(tabs)

    def _check_ffmpeg(self) -> None:
        if not check_ffmpeg():
            QMessageBox.critical(
                self,
                "ffmpeg Not Found",
                "ffmpeg is required but was not found on your PATH.\n\n"
                "Install it with:\n  sudo pacman -S ffmpeg\n\n"
                "The Converter tab will not work until ffmpeg is installed.",
            )

    # ------------------------------------------------------------------
    # Config persistence
    # ------------------------------------------------------------------

    def _load_config(self) -> dict:
        if CONFIG_PATH.exists():
            try:
                return json.loads(CONFIG_PATH.read_text())
            except Exception:
                pass
        return {}

    def closeEvent(self, event) -> None:
        self._save_config()
        super().closeEvent(event)

    def _save_config(self) -> None:
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        CONFIG_PATH.write_text(json.dumps(self._config, indent=2))
