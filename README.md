# Resolve Media Tool

A Linux desktop app for DaVinci Resolve creators. Combines AI image upscaling via Real-ESRGAN (CUDA accelerated) with a media converter — video/image to Resolve-compatible `.mov` and back to H.264 MP4. Standalone executable, no setup required.

---

## Requirements

- Linux x86_64
- NVIDIA GPU with CUDA (falls back to CPU if not available)
- `ffmpeg` installed (`sudo pacman -S ffmpeg` on Arch)

---

## Installation

The executable must be built from source due to the size of the PyTorch dependency (~2GB).

1. Clone the repo:

```bash
git clone https://github.com/quarkarch-hub/ResolveMediaTool.git
cd ResolveMediaTool
```

2. Create a Python 3.12 virtual environment and install dependencies:

```bash
python3.12 -m venv .venv
source .venv/bin/activate  # or activate.fish for fish shell
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
pip install basicsr realesrgan facexlib gfpgan opencv-python-headless Pillow numpy PyQt6 pyinstaller
```

3. Build the executable:

```bash
pyinstaller resolve-media-tool.spec
```

4. Install to your app launcher:

```bash
./install.sh
```

Launch from your app menu or run directly:

```bash
./dist/resolve-media-tool/resolve-media-tool
```

---

## Usage

### Upscaler Tab

1. Add images using **Add Files…** or drag and drop (PNG, JPG, WEBP supported)
2. Choose **Upscale** or **Downscale** mode
3. **Upscale options:**
   - **Model:** `RealESRGAN_x4plus_anime_6B` for anime/illustrations, `RealESRGAN_x4plus` for photos
   - **Tile size:** Lower values use less VRAM (default 512, auto-reduces on out-of-memory)
   - **FP16:** Keep enabled for faster processing on NVIDIA GPUs
4. Pick a **target resolution** from the preset dropdown or enter a custom size
5. Set an **output directory** (defaults to same folder as input)
6. Choose output format: **PNG** or **JPG**
7. Hit **Start** — the processed image will open automatically when done

> On first use, models are downloaded automatically to `~/.local/share/resolve-media-tool/models/` (~64MB each)

---

### Converter Tab

1. Select conversion direction:
   - **To Resolve** — converts video/images to Resolve-compatible `.mov` (MJPEG)
   - **To MP4** — converts Resolve `.mov` exports to H.264 MP4
2. Add files using **Add Files…** or drag and drop
3. **To Resolve options:**
   - MJPEG quality: 1 (best) to 10 (worst), default 2
4. **To MP4 options:**
   - Quality: Low (CRF 28), Medium (CRF 18), High (lossless)
5. Optionally set an output resolution
6. Set an output directory (defaults to same folder as input)
7. Hit **Start** — the converted file will open automatically when done

---

## Building from Source

```bash
python3.12 -m venv .venv
source .venv/bin/activate  # or activate.fish for fish shell
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
pip install basicsr realesrgan facexlib gfpgan opencv-python-headless Pillow numpy PyQt6 pyinstaller
pyinstaller resolve-media-tool.spec
./install.sh
```

---

## Output Files

| Operation | Suffix |
|---|---|
| Upscale | `filename_upscaled.png` |
| Downscale | `filename_downscaled.png` |
| To Resolve | `filename_resolve.mov` |
| To MP4 | `filename_export.mp4` |

Source files are never modified or overwritten.
