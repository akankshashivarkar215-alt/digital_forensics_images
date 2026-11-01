import cv2
import numpy as np
from pathlib import Path


def analyze_noise(image_path: Path, output_path: Path):
    """
    Analyze local noise inconsistency in an image.

    Returns:
        dict: noise analysis result
        output_path: generated noise visualization
    """

    img = cv2.imread(str(image_path))

    if img is None:
        raise ValueError("Could not read image for noise analysis.")

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Resize large images for faster processing
    max_dimension = 1400
    h, w = gray.shape

    scale = min(1.0, max_dimension / max(h, w))

    if scale < 1.0:
        gray = cv2.resize(
            gray,
            None,
            fx=scale,
            fy=scale,
            interpolation=cv2.INTER_AREA
        )
        img = cv2.resize(
            img,
            None,
            fx=scale,
            fy=scale,
            interpolation=cv2.INTER_AREA
        )

    # Estimate noise using high-pass filtering
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    noise = cv2.absdiff(gray, blurred)

    # Divide image into blocks
    block_size = 32

    block_values = []

    for y in range(0, noise.shape[0] - block_size + 1, block_size):
        for x in range(0, noise.shape[1] - block_size + 1, block_size):

            block = noise[
                y:y + block_size,
                x:x + block_size
            ]

            value = float(np.mean(block))

            block_values.append({
                "x": x,
                "y": y,
                "value": value
            })

    if not block_values:
        cv2.imwrite(str(output_path), img)

        return {
            "possible_inconsistency": False,
            "score": 0,
            "message": "Not enough image area for noise analysis."
        }, output_path

    values = np.array(
        [item["value"] for item in block_values],
        dtype=np.float32
    )

    mean_noise = float(np.mean(values))
    std_noise = float(np.std(values))

    # Blocks significantly different from the global noise level
    threshold = mean_noise + (1.8 * std_noise)

    suspicious_blocks = [
        item for item in block_values
        if item["value"] > threshold
    ]

    # Limit extreme sensitivity
    suspicious_ratio = (
        len(suspicious_blocks) / len(block_values)
    )

    possible_inconsistency = (
        len(suspicious_blocks) >= 3
        and suspicious_ratio >= 0.01
    )

    # Create visualization
    result_img = img.copy()

    overlay = result_img.copy()

    for item in suspicious_blocks:
        x = item["x"]
        y = item["y"]

        cv2.rectangle(
            overlay,
            (x, y),
            (x + block_size, y + block_size),
            (0, 0, 255),
            -1
        )

    # Blend suspicious regions
    result_img = cv2.addWeighted(
        result_img,
        0.70,
        overlay,
        0.30,
        0
    )

    # Draw borders around suspicious blocks
    for item in suspicious_blocks:
        x = item["x"]
        y = item["y"]

        cv2.rectangle(
            result_img,
            (x, y),
            (x + block_size, y + block_size),
            (0, 0, 255),
            2
        )

    if possible_inconsistency:
        message = (
            "Noise-level inconsistency detected in some image regions."
        )
    else:
        message = (
            "No strong noise inconsistency detected."
        )

    cv2.imwrite(str(output_path), result_img)

    return {
        "possible_inconsistency": possible_inconsistency,
        "score": round(float(std_noise), 2),
        "mean_noise": round(mean_noise, 2),
        "suspicious_blocks": len(suspicious_blocks),
        "message": message
    }, output_path