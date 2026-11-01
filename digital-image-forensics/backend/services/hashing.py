import hashlib
from pathlib import Path

def calculate_hashes(path: Path):
    md5 = hashlib.md5()
    sha256 = hashlib.sha256()

    with path.open("rb") as f:
        while chunk := f.read(1024 * 1024):
            md5.update(chunk)
            sha256.update(chunk)

    return {
        "md5": md5.hexdigest(),
        "sha256": sha256.hexdigest()
    }
