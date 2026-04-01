from __future__ import annotations

from pathlib import Path

from PyQt6.QtWidgets import (
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
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from workers.convert_worker import ConvertWorker

VIDEO_FILTER = "Video Files (*.mp4 *.mkv *.avi *.webm)"
IMAGE_FILTER = "Image Files (*.png *.jpg *.jpeg *.webp *.tiff *.tif)"
MOV_FILTER = "QuickTime Files (*.mov)"

SUPPORTED_TO_RESOLVE = {".mp4", ".mkv", ".avi", ".webm", ".png", ".jpg", ".jpeg", ".webp", ".tiff", ".tif"}
SUPPORTED_TO_MP4 = {".mov"}


class ConverterTab(QWidget):
    def __init__(self, config: dict, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.config = config
        self._worker: ConvertWorker | None = None
        self._files: list[Path] = []
        self._setup_ui()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _setup_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setSpacing(8)

        # ---- Direction ----
        dir_group = QGroupBox("Conversion Direction")
        dg_lay = QHBoxLayout(dir_group)
        self._to_resolve_radio = QRadioButton("To Resolve")
        self._to_mp4_radio = QRadioButton("To MP4")
        self._to_resolve_radio.setChecked(True)
        self._to_resolve_radio.toggled.connect(self._on_direction_changed)
        dg_lay.addWidget(self._to_resolve_radio)
        dg_lay.addWidget(self._to_mp4_radio)
        dg_lay.addStretch()
        root.addWidget(dir_group)

        # ---- File list ----
        file_group = QGroupBox("Input Files")
        fg_lay = QVBoxLayout(file_group)

        self._file_list = QListWidget()
        self._file_list.setAcceptDrops(True)
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

        # ---- To-Resolve options ----
        self._resolve_group = QGroupBox("To-Resolve Options")
        rg_lay = QVBoxLayout(self._resolve_group)
        q_row = QHBoxLayout()
        q_row.addWidget(QLabel("MJPEG Quality (1=best, 10=worst):"))
        self._mjpeg_spin = QSpinBox()
        self._mjpeg_spin.setRange(1, 10)
        self._mjpeg_spin.setValue(2)
        q_row.addWidget(self._mjpeg_spin)
        q_row.addStretch()
        rg_lay.addLayout(q_row)
        root.addWidget(self._resolve_group)

        # ---- To-MP4 options ----
        self._mp4_group = QGroupBox("To-MP4 Options")
        mg_lay = QVBoxLayout(self._mp4_group)
        mp4_q_row = QHBoxLayout()
        mp4_q_row.addWidget(QLabel("Quality:"))
        self._mp4_quality_combo = QComboBox()
        self._mp4_quality_combo.addItems(["Low", "Medium", "High"])
        self._mp4_quality_combo.setCurrentText("Medium")
        mp4_q_row.addWidget(self._mp4_quality_combo)
        mp4_q_row.addStretch()
        mg_lay.addLayout(mp4_q_row)
        self._mp4_group.setVisible(False)
        root.addWidget(self._mp4_group)

        # ---- Resolution ----
        res_group = QGroupBox("Output Resolution (optional)")
        res_lay = QHBoxLayout(res_group)
        res_lay.addWidget(QLabel("Width:"))
        self._res_w = QSpinBox()
        self._res_w.setRange(0, 32768)
        self._res_w.setSpecialValueText("Source")
        self._res_w.setValue(0)
        res_lay.addWidget(self._res_w)
        res_lay.addWidget(QLabel("Height:"))
        self._res_h = QSpinBox()
        self._res_h.setRange(0, 32768)
        self._res_h.setSpecialValueText("Source")
        self._res_h.setValue(0)
        res_lay.addWidget(self._res_h)
        res_lay.addStretch()
        root.addWidget(res_group)

        # ---- Output directory ----
        out_group = QGroupBox("Output Directory")
        og_lay = QHBoxLayout(out_group)
        og_lay.addWidget(QLabel("Directory:"))
        self._out_dir_edit = QLineEdit()
        self._out_dir_edit.setPlaceholderText("Same as input")
        self._out_dir_edit.setText(self.config.get("last_output_dir", ""))
        og_lay.addWidget(self._out_dir_edit)
        browse_btn = QPushButton("Browse…")
        browse_btn.clicked.connect(self._browse_output)
        og_lay.addWidget(browse_btn)
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

    def _on_direction_changed(self, to_resolve: bool) -> None:
        self._resolve_group.setVisible(to_resolve)
        self._mp4_group.setVisible(not to_resolve)

    def _add_files(self) -> None:
        if self._to_resolve_radio.isChecked():
            f = f"{VIDEO_FILTER};;{IMAGE_FILTER}"
        else:
            f = MOV_FILTER
        paths, _ = QFileDialog.getOpenFileNames(self, "Select Files", "", f)
        for p in paths:
            path = Path(p)
            if path not in self._files:
                self._files.append(path)
                self._file_list.addItem(str(path))

    def _clear_files(self) -> None:
        self._files.clear()
        self._file_list.clear()

    def _browse_output(self) -> None:
        d = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if d:
            self._out_dir_edit.setText(d)

    def _start(self) -> None:
        if not self._files:
            QMessageBox.warning(self, "No Files", "Please add at least one file.")
            return

        direction = "to_resolve" if self._to_resolve_radio.isChecked() else "to_mp4"
        allowed = SUPPORTED_TO_RESOLVE if direction == "to_resolve" else SUPPORTED_TO_MP4
        invalid = [f for f in self._files if f.suffix.lower() not in allowed]
        if invalid:
            names = "\n".join(f.name for f in invalid[:5])
            QMessageBox.warning(
                self, "Unsupported Files",
                f"The following files are not supported for this direction:\n{names}"
            )
            return

        output_dir = self._resolve_output_dir()
        w = self._res_w.value() or None
        h = self._res_h.value() or None

        self._worker = ConvertWorker(
            files=list(self._files),
            output_dir=output_dir,
            direction=direction,
            mjpeg_quality=self._mjpeg_spin.value(),
            mp4_quality=self._mp4_quality_combo.currentText(),
            target_w=w,
            target_h=h,
        )
        self._worker.progress.connect(self._on_progress)
        self._worker.file_done.connect(self._on_file_done)
        self._worker.file_error.connect(self._on_file_error)
        self._worker.all_done.connect(self._on_all_done)

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
            # File just started — go indeterminate (pulsing bar).
            self._progress_bar.setRange(0, 0)
            self._progress_label.setText(f"Processing {file_idx + 1}/{total}: {name}")

    def _on_file_done(self, file_idx: int, out_path: str) -> None:
        import subprocess
        total = len(self._files)
        done = file_idx + 1
        self._progress_bar.setRange(0, total)
        self._progress_bar.setValue(done)
        self._progress_label.setText(f"Done {done}/{total}: {self._files[file_idx].name}")
        subprocess.Popen(["xdg-open", out_path])

    def _on_file_error(self, file_idx: int, msg: str) -> None:
        total = len(self._files)
        done = file_idx + 1
        self._progress_bar.setRange(0, total)
        self._progress_bar.setValue(done)
        QMessageBox.critical(
            self,
            "Error",
            f"Failed to convert {self._files[file_idx].name}:\n{msg}",
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
        direction = "to_resolve" if self._to_resolve_radio.isChecked() else "to_mp4"
        allowed = SUPPORTED_TO_RESOLVE if direction == "to_resolve" else SUPPORTED_TO_MP4
        for url in event.mimeData().urls():
            path = Path(url.toLocalFile())
            if path.suffix.lower() in allowed and path not in self._files:
                self._files.append(path)
                self._file_list.addItem(str(path))

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _resolve_output_dir(self) -> Path:
        text = self._out_dir_edit.text().strip()
        if text:
            return Path(text)
        if self._files:
            return self._files[0].parent
        return Path.home()
