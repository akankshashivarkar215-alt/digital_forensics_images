from PIL import Image, ExifTags
from pathlib import Path

def extract_metadata(image_path: Path):
    img = Image.open(image_path)

    exif_data = {}
    software_detected = False

    try:
        raw_exif = img.getexif()
        for key, value in raw_exif.items():
            tag = ExifTags.TAGS.get(key, str(key))
            try:
                value = str(value)
            except Exception:
                value = repr(value)
            exif_data[tag] = value

        software_detected = bool(
            exif_data.get("Software") or
            exif_data.get("ProcessingSoftware")
        )
    except Exception:
        pass

    stat = image_path.stat()

    return {
        "format": img.format or "Unknown",
        "mode": img.mode,
        "width": img.width,
        "height": img.height,
        "file_size_bytes": stat.st_size,
        "file_size_kb": round(stat.st_size / 1024, 2),
        "software_detected": software_detected,
        "exif": exif_data
    }
