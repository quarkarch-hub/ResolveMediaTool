from __future__ import annotations

from pathlib import Path
from typing import Optional

import cv2
import numpy as np
from PIL import Image

# torch is imported lazily so the application starts without GPU initialisation.


class Upscaler:
    """Wraps RealESRGAN for upscaling and provides a pure-Pillow downscaler.

    Args:
        model_name: Name of the RealESRGAN model (must match a key in
            core.model_manager.MODEL_URLS).
        tile_size: Tile size used by RealESRGANer to limit VRAM usage.
        use_fp16: Whether to use half-precision inference on CUDA.
    """

    def __init__(
        self,
        model_name: str,
        tile_size: int = 512,
        use_fp16: bool = True,
    ) -> None:
        self.model_name = model_name
        self.tile_size = tile_size
        self.use_fp16 = use_fp16
        self._current_tile = tile_size
        self._model = self._load_model(tile_size)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def upscale(
        self,
        input_path: Path,
        output_path: Path,
        target_w: int,
        target_h: int,
        output_format: str,
    ) -> None:
        """Upscale *input_path* to *target_w* x *target_h* and save it.

        Steps:
          1. Run RealESRGAN at 4x.
          2. Downsample to (target_w, target_h) with Pillow LANCZOS.
          3. Save as PNG or JPG.

        On CUDA out-of-memory the operation is retried with progressively
        smaller tile sizes (256, then 128).
        """
        for tile in [self.tile_size, 256, 128]:
            try:
                return self._upscale_attempt(
                    input_path, output_path, target_w, target_h, output_format, tile
                )
            except RuntimeError as exc:
                if "out of memory" in str(exc).lower():
                    # Rebuild model with smaller tile and retry.
                    self._model = self._load_model(tile)
                    continue
                raise

        # Final attempt with tile=128 (already tried in loop, but guard).
        self._upscale_attempt(
            input_path, output_path, target_w, target_h, output_format, 128
        )

    def downscale(
        self,
        input_path: Path,
        output_path: Path,
        target_w: int,
        target_h: int,
        output_format: str,
    ) -> None:
        """Downscale *input_path* to *target_w* x *target_h* using Pillow LANCZOS."""
        img = Image.open(input_path).convert("RGB")
        img = img.resize((target_w, target_h), Image.LANCZOS)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        _save_image(img, output_path, output_format)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _load_model(self, tile_size: int):
        """Instantiate and return a RealESRGANer."""
        import torch
        from basicsr.archs.rrdbnet_arch import RRDBNet
        from realesrgan import RealESRGANer

        use_cuda = torch.cuda.is_available()
        device = torch.device("cuda" if use_cuda else "cpu")

        # Select architecture based on model name.
        if "anime_6B" in self.model_name:
            model = RRDBNet(
                num_in_ch=3,
                num_out_ch=3,
                num_feat=64,
                num_block=6,
                num_grow_ch=32,
                scale=4,
            )
        else:
            model = RRDBNet(
                num_in_ch=3,
                num_out_ch=3,
                num_feat=64,
                num_block=23,
                num_grow_ch=32,
                scale=4,
            )

        from core.model_manager import get_model_path

        model_path = get_model_path(self.model_name)

        upsampler = RealESRGANer(
            scale=4,
            model_path=str(model_path),
            model=model,
            tile=tile_size,
            tile_pad=10,
            pre_pad=0,
            half=self.use_fp16 and use_cuda,
            device=device,
        )
        return upsampler

    def _upscale_attempt(
        self,
        input_path: Path,
        output_path: Path,
        target_w: int,
        target_h: int,
        output_format: str,
        tile_size: int,
    ) -> None:
        if self._current_tile != tile_size:
            self._model = self._load_model(tile_size)
            self._current_tile = tile_size

        # Read with OpenCV (BGR) as RealESRGANer expects numpy uint8.
        bgr = cv2.imread(str(input_path), cv2.IMREAD_UNCHANGED)
        if bgr is None:
            raise FileNotFoundError(f"Cannot read image: {input_path}")

        # enhance() returns BGR numpy array.
        output_bgr, _ = self._model.enhance(bgr, outscale=4)

        # Convert to PIL RGB for resizing and saving.
        rgb = cv2.cvtColor(output_bgr, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(rgb)

        # Downsample to exact target resolution.
        img = img.resize((target_w, target_h), Image.LANCZOS)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        _save_image(img, output_path, output_format)


# ---------------------------------------------------------------------------
# Module-level helpers
# ---------------------------------------------------------------------------

def _save_image(img: Image.Image, path: Path, fmt: str) -> None:
    """Save *img* to *path* in the requested format ('png' or 'jpg')."""
    fmt_lower = fmt.lower()
    if fmt_lower == "jpg":
        img = img.convert("RGB")
        img.save(path, format="JPEG", quality=95)
    else:
        img.save(path, format="PNG")
