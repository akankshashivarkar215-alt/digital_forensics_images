from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pathlib import Path
from datetime import datetime
import uuid
import shutil
import json

from services.metadata import extract_metadata
from services.hashing import calculate_hashes
from services.ela import perform_ela
from services.copy_move import detect_copy_move
from services.noise import analyze_noise
from services.report import generate_report


BASE_DIR = Path(__file__).resolve().parent

UPLOAD_DIR = BASE_DIR / "uploads"
RESULT_DIR = BASE_DIR / "results"

UPLOAD_DIR.mkdir(exist_ok=True)
RESULT_DIR.mkdir(exist_ok=True)


ALLOWED = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp"
}


app = FastAPI(
    title="Digital Image Forensics API",
    description="Digital image forensic analysis API",
    version="2.0"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {
        "message": "Digital Image Forensics API is running"
    }


def calculate_forensic_score(
    ela_score,
    copy_result,
    noise_result,
    metadata
):
    """
    Calculate an overall forensic confidence score.
    """

    score = 0

    # ELA contribution
    if ela_score >= 35:
        score += 35
    elif ela_score >= 20:
        score += 20
    elif ela_score >= 10:
        score += 10

    # Copy-move contribution
    if copy_result.get("possible_forgery"):
        score += 40

    # Noise contribution
    if noise_result.get("possible_inconsistency"):
        score += 20

    # Metadata contribution
    if metadata.get("software_detected"):
        score += 5

    score = min(score, 100)

    if score >= 70:
        risk = "HIGH"
    elif score >= 35:
        risk = "MEDIUM"
    else:
        risk = "LOW"

    return score, risk


@app.post("/api/analyze")
async def analyze_image(
    file: UploadFile = File(...)
):

    suffix = Path(
        file.filename or ""
    ).suffix.lower()

    if suffix not in ALLOWED:
        raise HTTPException(
            status_code=400,
            detail=(
                "Unsupported file. "
                "Please upload JPG, JPEG, PNG or WEBP."
            )
        )

    if (
        not file.content_type
        or not file.content_type.startswith("image/")
    ):
        raise HTTPException(
            status_code=400,
            detail="The uploaded file is not an image."
        )

    # --------------------------------------------------
    # CREATE CASE ID
    # --------------------------------------------------

    analysis_id = uuid.uuid4().hex

    case_id = (
        "DF-"
        + datetime.now().strftime("%Y")
        + "-"
        + analysis_id[:8].upper()
    )

    safe_name = f"{analysis_id}{suffix}"

    image_path = UPLOAD_DIR / safe_name

    # Save uploaded image
    with image_path.open("wb") as buffer:
        shutil.copyfileobj(
            file.file,
            buffer
        )

    try:

        # --------------------------------------------------
        # METADATA
        # --------------------------------------------------

        metadata = extract_metadata(
            image_path
        )

        # --------------------------------------------------
        # HASHES
        # --------------------------------------------------

        hashes = calculate_hashes(
            image_path
        )

        # --------------------------------------------------
        # ELA
        # --------------------------------------------------

        ela_file, ela_score = perform_ela(
            image_path,
            RESULT_DIR / f"{analysis_id}_ela.jpg"
        )

        # --------------------------------------------------
        # COPY-MOVE
        # --------------------------------------------------

        copy_result, copy_file = detect_copy_move(
            image_path,
            RESULT_DIR / f"{analysis_id}_copy_move.jpg"
        )

        # --------------------------------------------------
        # NOISE ANALYSIS
        # --------------------------------------------------

        noise_result, noise_file = analyze_noise(
            image_path,
            RESULT_DIR / f"{analysis_id}_noise.jpg"
        )

        # --------------------------------------------------
        # FORENSIC SCORE
        # --------------------------------------------------

        forensic_score, risk = calculate_forensic_score(
            ela_score,
            copy_result,
            noise_result,
            metadata
        )

        # --------------------------------------------------
        # CONCLUSION
        # --------------------------------------------------

        if forensic_score >= 70:

            conclusion = (
                "Multiple manipulation indicators detected."
            )

        elif forensic_score >= 35:

            conclusion = (
                "Potential manipulation indicators detected."
            )

        else:

            conclusion = (
                "No strong manipulation indicators detected."
            )

        # --------------------------------------------------
        # FINAL RESULT
        # --------------------------------------------------

        result = {

            "analysis_id": analysis_id,

            "case_id": case_id,

            "filename": file.filename,

            "analysis_time": datetime.now().isoformat(),

            "metadata": metadata,

            "hashes": hashes,

            "ela": {

                "image_url":
                    f"/results/{Path(ela_file).name}",

                "score":
                    ela_score
            },

            "copy_move": copy_result,

            "copy_move_image_url":
                (
                    f"/results/{Path(copy_file).name}"
                    if copy_file
                    else None
                ),

            "noise": noise_result,

            "noise_image_url":
                f"/results/{Path(noise_file).name}",

            "forensic_score":
                forensic_score,

            "risk":
                risk,

            "conclusion":
                conclusion
        }

        # --------------------------------------------------
        # SAVE JSON
        # --------------------------------------------------

        json_path = (
            RESULT_DIR
            / f"{analysis_id}.json"
        )

        json_path.write_text(
            json.dumps(
                result,
                indent=2
            ),
            encoding="utf-8"
        )

        return result

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {exc}"
        )


@app.get("/results/{filename}")
def get_result_file(
    filename: str
):

    path = (
        RESULT_DIR
        / Path(filename).name
    )

    if not path.exists():

        raise HTTPException(
            status_code=404,
            detail="Result file not found."
        )

    return FileResponse(path)


@app.post("/api/report/{analysis_id}")
def create_report(
    analysis_id: str
):

    json_path = (
        RESULT_DIR
        / f"{analysis_id}.json"
    )

    if not json_path.exists():

        raise HTTPException(
            status_code=404,
            detail="Analysis not found."
        )

    result = json.loads(
        json_path.read_text(
            encoding="utf-8"
        )
    )

    report_path = (
        RESULT_DIR
        / f"{analysis_id}_forensic_report.pdf"
    )

    generate_report(
        result,
        report_path
    )

    return {
        "download_url":
            f"/results/{report_path.name}"
    }