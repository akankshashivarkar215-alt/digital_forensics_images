from PIL import Image, ImageChops, ImageEnhance
from pathlib import Path
import numpy as np

def perform_ela(image_path: Path, output_path: Path):
    original = Image.open(image_path).convert("RGB")

    # Re-compress at a controlled JPEG quality.
    temp_path = output_path.with_name(output_path.stem + "_temp.jpg")
    original.save(temp_path, "JPEG", quality=90)

    recompressed = Image.open(temp_path).convert("RGB")
    diff = ImageChops.difference(original, recompressed)

    extrema = diff.getextrema()
    max_diff = max(channel[1] for channel in extrema)
    scale = 255.0 / max(max_diff, 1)

    ela = ImageEnhance.Brightness(diff).enhance(scale)
    ela.save(output_path, "JPEG", quality=95)

    # A simple normalized average difference score.
    arr = np.asarray(diff, dtype=np.float32)
    score = float(np.mean(arr) / 255.0 * 100.0)

    try:
        temp_path.unlink()
    except Exception:
        pass

    return output_path, round(min(score, 100.0), 2)
