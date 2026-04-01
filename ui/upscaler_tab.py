from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QRadioButton,
    QSizePolicy,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from workers.upscale_worker import UpscaleWorker

RESOLUTION_PRESETS: list[tuple[str, int, int]] = [
    ("1280 × 720",  1280,  720),
    ("1920 × 1080", 1920, 1080),
    ("2560 × 1440", 2560, 1440),
    ("3840 × 2160", 3840, 2160),
    ("7680 × 4320", 7680, 4320),
    ("Custom …", 0, 0),
]


class UpscalerTab(QWidget):
    def __init__(self, config: dict, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.config = config
        self._worker: UpscaleWorker | None = None
        self._files: list[Path] = []
        self._setup_ui()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _setup_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setSpacing(8)

        # ---- File list ----
        file_group = QGroupBox("Input Files")
        fg_lay = QVBoxLayout(file_group)

        self._file_list = QListWidget()
        self._file_list.setAcceptDrops(True)
        self._file_list.setSelectionMode(
            QListWidget.SelectionMode.ExtendedSelection
        )
        self._file_list.installEventFilter(self)
        self._file_list.dragEnterEvent = self._drag_enter
        self._file_list.dragMoveEvent = self._drag_move
        self._file_list.dropEvent = self._drop

        btn_row = QHBoxLayout()
        add_btn = QPushButton("Add Files…")
        add_btn.clicked.connect(self._add_files)
        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self._clear_files)
        btn_row.addWidget(add_btn)
        btn_row.addWidget(clear_btn)
        btn_row.addStretch()

        fg_lay.addWidget(self._file_list)
        fg_lay.addLayout(btn_row)
        root.addWidget(file_group)

        # ---- Mode ----
        mode_group = QGroupBox("Mode")
        mg_lay = QHBoxLayout(mode_group)
        self._upscale_radio = QRadioButton("Upscale")
        self._downscale_radio = QRadioButton("Downscale")
        self._upscale_radio.setChecked(True)
        self._upscale_radio.toggled.connect(self._on_mode_changed)
        mg_lay.addWidget(self._upscale_radio)
        mg_lay.addWidget(self._downscale_radio)
        mg_lay.addStretch()
        root.addWidget(mode_group)

        # ---- Upscale options ----
        self._upscale_group = QGroupBox("Upscale Options")
        ug_lay = QVBoxLayout(self._upscale_group)

        model_row = QHBoxLayout()
        model_row.addWidget(QLabel("Model:"))
        self._model_combo = QComboBox()
        self._model_combo.addItems(
            ["RealESRGAN_x4plus_anime_6B", "RealESRGAN_x4plus"]
        )
        model_row.addWidget(self._model_combo)
        model_row.addStretch()
        ug_lay.addLayout(model_row)

        tile_row = QHBoxLayout()
        tile_row.addWidget(QLabel("Tile size:"))
        self._tile_spin = QSpinBox()
        self._tile_spin.setRange(64, 2048)
        self._tile_spin.setSingleStep(64)
        self._tile_spin.setValue(512)
        tile_row.addWidget(self._tile_spin)
        tile_row.addStretch()
        ug_lay.addLayout(tile_row)

        fp16_row = QHBoxLayout()
        self._fp16_check = QCheckBox("Use FP16 (half precision)")
        self._fp16_check.setChecked(True)
        fp16_row.addWidget(self._fp16_check)
        fp16_row.addStretch()
        ug_lay.addLayout(fp16_row)

        root.addWidget(self._upscale_group)

        # ---- Resolution ----
        res_group = QGroupBox("Target Resolution")
        rg_lay = QVBoxLayout(res_group)

        res_row = QHBoxLayout()
        res_row.addWidget(QLabel("Preset:"))
        self._res_combo = QComboBox()
        for label, _, _ in RESOLUTION_PRESETS:
            self._res_combo.addItem(label)
        self._res_combo.setCurrentIndex(2)  # 1440p default
        self._res_combo.currentIndexChanged.connect(self._on_res_changed)
        res_row.addWidget(self._res_combo)
        res_row.addStretch()
        rg_lay.addLayout(res_row)

        self._custom_res_widget = QWidget()
        custom_row = QHBoxLayout(self._custom_res_widget)
        custom_row.setContentsMargins(0, 0, 0, 0)
        custom_row.addWidget(QLabel("Width:"))
        self._custom_w = QSpinBox()
        self._custom_w.setRange(1, 32768)
        self._custom_w.setValue(1920)
        custom_row.addWidget(self._custom_w)
        custom_row.addWidget(QLabel("Height:"))
        self._custom_h = QSpinBox()
        self._custom_h.setRange(1, 32768)
        self._custom_h.setValue(1080)
        custom_row.addWidget(self._custom_h)
        custom_row.addStretch()
        self._custom_res_widget.setVisible(False)
        rg_lay.addWidget(self._custom_res_widget)

        root.addWidget(res_group)

        # ---- Output ----
        out_group = QGroupBox("Output")
        og_lay = QVBoxLayout(out_group)

        dir_row = QHBoxLayout()
        dir_row.addWidget(QLabel("Directory:"))
        self._out_dir_edit = QLineEdit()
        self._out_dir_edit.setPlaceholderText("Same as input")
        self._out_dir_edit.setText(self.config.get("last_output_dir", ""))
        dir_row.addWidget(self._out_dir_edit)
        browse_btn = QPushButton("Browse…")
        browse_btn.clicked.connect(self._browse_output)
        dir_row.addWidget(browse_btn)
        og_lay.addLayout(dir_row)

        fmt_row = QHBoxLayout()
        fmt_row.addWidget(QLabel("Format:"))
        self._fmt_combo = QComboBox()
        self._fmt_combo.addItems(["PNG", "JPG"])
        fmt_row.addWidget(self._fmt_combo)
        fmt_row.addStretch()
        og_lay.addLayout(fmt_row)

        root.addWidget(out_group)

        # ---- Progress ----
        self._progress_bar = QProgressBar()
        self._progress_bar.setRange(0, 100)
        self._progress_bar.setValue(0)
        self._progress_label = QLabel("")
        root.addWidget(self._progress_bar)
        root.addWidget(self._progress_label)

        # ---- Start / Cancel ----
        action_row = QHBoxLayout()
        self._start_btn = QPushButton("Start")
        self._start_btn.clicked.connect(self._start)
        self._cancel_btn = QPushButton("Cancel")
        self._cancel_btn.setEnabled(False)
        self._cancel_btn.clicked.connect(self._cancel)
        action_row.addStretch()
        action_row.addWidget(self._start_btn)
        action_row.addWidget(self._cancel_btn)
        root.addLayout(action_row)

        root.addStretch()

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    def _add_files(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Images",
            "",
            "Images (*.png *.jpg *.jpeg *.webp)",
        )
        for p in paths:
            path = Path(p)
            if path not in self._files:
                self._files.append(path)
                self._file_list.addItem(str(path))

    def _clear_files(self) -> None:
        self._files.clear()
        self._file_list.clear()

    def _on_mode_changed(self, upscale: bool) -> None:
        self._upscale_group.setEnabled(upscale)

    def _on_res_changed(self, idx: int) -> None:
        is_custom = RESOLUTION_PRESETS[idx][0].startswith("Custom")
        self._custom_res_widget.setVisible(is_custom)

    def _browse_output(self) -> None:
        d = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if d:
            self._out_dir_edit.setText(d)

    def _start(self) -> None:
        if not self._files:
            QMessageBox.warning(self, "No Files", "Please add at least one image.")
            return

        target_w, target_h = self._resolve_resolution()
        if target_w == 0 or target_h == 0:
            QMessageBox.warning(self, "Invalid Resolution", "Please enter a valid resolution.")
            return

        output_dir = self._resolve_output_dir()

        mode = "upscale" if self._upscale_radio.isChecked() else "downscale"
        fmt = self._fmt_combo.currentText().lower()

        self._worker = UpscaleWorker(
            files=list(self._files),
            output_dir=output_dir,
            mode=mode,
            target_w=target_w,
            target_h=target_h,
            output_format=fmt,
            model_name=self._model_combo.currentText(),
            tile_size=self._tile_spin.value(),
            use_fp16=self._fp16_check.isChecked(),
        )
        self._worker.progress.connect(self._on_progress)
        self._worker.file_done.connect(self._on_file_done)
        self._worker.file_error.connect(self._on_file_error)
        self._worker.all_done.connect(self._on_all_done)
        self._last_output: str | None = None

        self._start_btn.setEnabled(False)
        self._cancel_btn.setEnabled(True)
        self._progress_bar.setRange(0, 100)
        self._progress_bar.setValue(0)
        self._progress_label.setText("Starting…")

        self.config["last_output_dir"] = str(output_dir)
        self._worker.start()

    def _cancel(self) -> None:
        if self._worker:
            self._worker.cancel()
        self._progress_label.setText("Cancelling…")

    def _on_progress(self, file_idx: int, pct: int) -> None:
        total = len(self._files)
        name = self._files[file_idx].name
        if pct == 0:
            self._progress_bar.setRange(0, 0)
            self._progress_label.setText(f"Processing {file_idx + 1}/{total}: {name}")
        else:
            # Real tile-based progress — switch to determinate.
            self._progress_bar.setRange(0, 100)
            self._progress_bar.setValue(pct)
            self._progress_label.setText(
                f"Processing {file_idx + 1}/{total}: {name} ({pct}%)"
            )

    def _on_file_done(self, file_idx: int, out_path: str) -> None:
        import subprocess
        total = len(self._files)
        done = file_idx + 1
        self._last_output = out_path
        self._progress_bar.setRange(0, total)
        self._progress_bar.setValue(done)
        self._progress_label.setText(f"Done {done}/{total}: {self._files[file_idx].name}")
        subprocess.Popen(["xdg-open", out_path])

    def _on_file_error(self, file_idx: int, msg: str) -> None:
        total = len(self._files)
        done = file_idx + 1
        self._progress_bar.setRange(0, total)
        self._progress_bar.setValue(done)
        self._progress_label.setText(f"Error on {self._files[file_idx].name}")
        QMessageBox.critical(
            self,
            "Error",
            f"Failed to process {self._files[file_idx].name}:\n{msg}",
        )

    def _on_all_done(self) -> None:
        total = len(self._files)
        self._start_btn.setEnabled(True)
        self._cancel_btn.setEnabled(False)
        self._progress_bar.setRange(0, total)
        self._progress_bar.setValue(total)
        self._progress_label.setText("All done.")

    # ------------------------------------------------------------------
    # Drag-and-drop
    # ------------------------------------------------------------------

    def _drag_enter(self, event) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def _drag_move(self, event) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def _drop(self, event) -> None:
        for url in event.mimeData().urls():
            path = Path(url.toLocalFile())
            if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"} and path not in self._files:
                self._files.append(path)
                self._file_list.addItem(str(path))

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _resolve_resolution(self) -> tuple[int, int]:
        idx = self._res_combo.currentIndex()
        label, w, h = RESOLUTION_PRESETS[idx]
        if label.startswith("Custom"):
            return self._custom_w.value(), self._custom_h.value()
        return w, h

    def _resolve_output_dir(self) -> Path:
        text = self._out_dir_edit.text().strip()
        if text:
            return Path(text)
        if self._files:
            return self._files[0].parent
        return Path.home()
