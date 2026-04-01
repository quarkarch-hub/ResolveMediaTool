# Resolve Media Tool

A self-contained PyQt6 desktop application for Linux that upscales images using Real-ESRGAN and converts media files into DaVinci Resolve-compatible formats.

---

## Overview

This is a GUI application with two tabs:

1. **Upscaler** — Upscale images using Real-ESRGAN with bundled models
2. **Converter** — Convert MP4 videos and images into Resolve-compatible `.mov` files

The application bundles all of its own dependencies (Real-ESRGAN, PyTorch, ffmpeg bindings) — no external venv or pre-installed tools required beyond ffmpeg being available on the system.

---

## Tech Stack

- **Language:** Python
- **GUI Framework:** PyQt6
- **Image Upscaling:** Real-ESRGAN (PyTorch + CUDA)
- **Media Conversion:** ffmpeg (called via subprocess)
- **Packaging:** Single installable package with all Python dependencies bundled (e.g., PyInstaller or similar)

---

## Tab 1: Upscaler

### Features

- File picker or drag-and-drop to select one or more images (PNG, JPG, WEBP)
- Mode selector: **Upscale** or **Downscale**

**Upscale mode:**
- Model selection dropdown:
  - `RealESRGAN_x4plus_anime_6B` — optimized for anime/illustration
  - `RealESRGAN_x4plus` — general purpose (photos, textures, real-world images)
- Target resolution picker: dropdown of common presets plus a custom entry field
  - Presets: 1280×720, 1920×1080, 2560×1440, 3840×2160, 7680×4320
  - Custom: free-entry width × height fields
  - The app internally runs ESRGAN at 4x then downsamples to the exact target resolution using Lanczos
- Tile size setting (default 512) to manage VRAM usage

**Downscale mode:**
- No AI model needed — uses Pillow with Lanczos resampling
- Target resolution picker: same preset dropdown + custom width × height fields as upscale mode

**Both modes:**
- Output directory picker (defaults to same directory as input)
- Output format selection: PNG or JPG
- Progress bar per image
- On first run (upscale only), download models automatically to `~/.local/share/resolve-media-tool/models/` if not already present

### Model URLs

- Anime: `https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.2.4/RealESRGAN_x4plus_anime_6B.pth`
- General: `https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth`

### Processing

- Run all processing in a background thread (QThread) so the GUI stays responsive
- **Upscale:** use the Real-ESRGAN inference pipeline; if a target resolution is specified, upscale to the next model output size then downsample to exact dimensions with Lanczos
- **Downscale:** use Pillow `Image.resize()` with `LANCZOS` resampling — no GPU required
- Use `--tile 512` by default to avoid CUDA OOM on 12GB cards (upscale only)
- Use fp16 (half precision) by default for speed (upscale only)

---

## Tab 2: Converter

### Features

- File picker or drag-and-drop to select one or more files
- Supported input types:
  - **Video:** MP4, MKV, AVI, WEBM
  - **Image:** PNG, JPG, WEBP, TIFF
- Output format: QuickTime `.mov` with MJPEG video codec and PCM s16le audio
- For images: convert to a single-frame `.mov` file (Resolve-compatible still)
- Output directory picker (defaults to same directory as input)
- Option to set output resolution (leave as source, or specify custom width x height)
- Progress bar per file
- Conversion direction selector: **To Resolve** or **To MP4**
- ffmpeg quality setting for MJPEG (default `-q:v 2`, lower = better quality, range 1-10)
- Quality preset for MP4 output: **Low** (CRF 28, fast), **Medium** (CRF 18, medium), **High** (CRF 0 lossless, slow)

### Conversion Modes

The converter tab supports two directions via a **To Resolve / To MP4** selector:

**To Resolve** — import-ready files for DaVinci Resolve
- Supported inputs: MP4, MKV, AVI, WEBM, PNG, JPG, WEBP, TIFF
- Output: QuickTime `.mov` with MJPEG video and PCM s16le audio
- Images become single-frame `.mov` stills
- Output filenames append `_resolve` (e.g. `clip_resolve.mov`)

**To MP4** — export Resolve output to a distributable MP4
- Supported inputs: `.mov` (ProRes, DNxHR, or any Resolve export)
- Output: H.264 MP4 with AAC 320k audio
- Quality presets:
  - **Low:** `-crf 28 -preset fast`
  - **Medium:** `-crf 18 -preset medium`
  - **High:** `-crf 0 -preset slow` (lossless)
- Output filenames append `_export` (e.g. `clip_export.mp4`)

### Processing

- Call ffmpeg via `subprocess.run()`
- To-Resolve video command: `ffmpeg -i input.mp4 -c:v mjpeg -q:v 2 -c:a pcm_s16le output.mov`
- To-Resolve image command: `ffmpeg -loop 1 -i input.png -t 1 -c:v mjpeg -q:v 2 -an output.mov`
- To-MP4 command: `ffmpeg -i input.mov -c:v libx264 -crf {0|18|28} -preset {slow|medium|fast} -c:a aac -b:a 320k output.mp4`
- Run in background thread so GUI stays responsive
- Validate that ffmpeg is installed on launch; show error dialog if missing

---

## Application Structure

```
resolve-media-tool/
├── main.py                  # Entry point, launches PyQt6 app
├── ui/
│   ├── main_window.py       # Main window with tab widget
│   ├── upscaler_tab.py      # Upscaler tab UI and logic
│   └── converter_tab.py     # Converter tab UI and logic
├── core/
│   ├── upscaler.py          # Real-ESRGAN inference wrapper
│   ├── converter.py         # ffmpeg subprocess wrapper
│   └── model_manager.py     # Download and manage ESRGAN models
├── workers/
│   ├── upscale_worker.py    # QThread worker for upscaling
│   └── convert_worker.py    # QThread worker for conversion
├── assets/
│   └── icon.png             # App icon (optional)
├── requirements.txt         # All Python dependencies
├── setup.py                 # Package setup
└── README.md                # Usage instructions
```

---

## Dependencies (requirements.txt)

```
PyQt6
torch
torchvision
basicsr
realesrgan
facexlib
gfpgan
numpy
opencv-python-headless
Pillow
```

**System dependency:** `ffmpeg` must be installed (`sudo pacman -S ffmpeg`)

---

## Packaging

Use PyInstaller to create a single distributable binary:

```bash
pyinstaller --onefile --windowed --name resolve-media-tool main.py
```

This produces a standalone executable in `dist/resolve-media-tool` that can be run without a Python installation. The binary will be Linux x86_64 only.

Alternatively, create a `.desktop` file for integration with KDE application launcher:

```ini
[Desktop Entry]
Name=Resolve Media Tool
Comment=Upscale images and convert media for DaVinci Resolve
Exec=/path/to/resolve-media-tool
Icon=/path/to/icon.png
Terminal=false
Type=Application
Categories=AudioVideo;Video;Graphics;
```

---

## Behavior Notes

- The app should remember the last used output directory between sessions (store in `~/.config/resolve-media-tool/config.json`)
- The app should detect available CUDA GPUs and fall back to CPU if none found
- Show estimated time remaining during processing if possible
- All file operations should be non-destructive (never overwrite source files)
- Output filenames: append `_upscaled` for upscaler, `_resolve` for converter (e.g., `image_upscaled.png`, `video_resolve.mov`)

---

## Error Handling

- If CUDA OOM: automatically retry with smaller tile size (512 → 256 → 128)
- If ffmpeg not found: show dialog with install instructions (`sudo pacman -S ffmpeg`)
- If model download fails: show retry option with error details
- If input file is corrupted or unsupported: skip with error message in log area, continue processing remaining files

---

## Future Considerations

- Batch processing with queue
- Additional Real-ESRGAN models (animevideov3 for video frames)
- Direct export to MP4 via ffmpeg after Resolve export (ProRes → H.264 pipeline)
- Dark theme toggle
- Preset profiles (e.g., "Anime Wallpaper 1440p", "Photo 4K")
