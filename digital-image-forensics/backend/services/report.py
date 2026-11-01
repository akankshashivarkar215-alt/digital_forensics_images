from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from pathlib import Path

def generate_report(result, output_path: Path):
    doc = SimpleDocTemplate(str(output_path), pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("DIGITAL IMAGE FORENSICS REPORT", styles["Title"]))
    story.append(Spacer(1, 15))

    story.append(Paragraph(
        "This report presents automated forensic indicators for the submitted image. "
        "The findings are not a definitive determination of authenticity.",
        styles["BodyText"]
    ))
    story.append(Spacer(1, 15))

    meta = result["metadata"]
    info = [
        ["File Name", result["filename"]],
        ["Format", meta["format"]],
        ["Resolution", f'{meta["width"]} x {meta["height"]}'],
        ["File Size", f'{meta["file_size_kb"]} KB'],
        ["Risk", result["risk"]],
        ["Conclusion", result["conclusion"]],
    ]

    table = Table(info, colWidths=[130, 350])
    table.setStyle(TableStyle([
        ("GRID", (0,0), (-1,-1), 0.5, colors.grey),
        ("BACKGROUND", (0,0), (0,-1), colors.lightgrey),
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("PADDING", (0,0), (-1,-1), 7),
    ]))
    story.append(table)
    story.append(Spacer(1, 15))

    story.append(Paragraph("HASHES", styles["Heading2"]))
    story.append(Paragraph(f'MD5: {result["hashes"]["md5"]}', styles["BodyText"]))
    story.append(Paragraph(f'SHA-256: {result["hashes"]["sha256"]}', styles["BodyText"]))
    story.append(Spacer(1, 12))

    story.append(Paragraph("ELA ANALYSIS", styles["Heading2"]))
    story.append(Paragraph(
        f'ELA score: {result["ela"]["score"]} / 100',
        styles["BodyText"]
    ))

    ela_path = output_path.parent / Path(result["ela"]["image_url"]).name
    if ela_path.exists():
        story.append(Spacer(1, 8))
        story.append(RLImage(str(ela_path), width=360, height=250))

    story.append(Spacer(1, 15))
    story.append(Paragraph("COPY-MOVE ANALYSIS", styles["Heading2"]))
    story.append(Paragraph(
        f'Matches: {result["copy_move"]["matches"]}',
        styles["BodyText"]
    ))
    story.append(Paragraph(
        result["copy_move"]["message"],
        styles["BodyText"]
    ))

    story.append(Spacer(1, 15))
    story.append(Paragraph("EXIF METADATA", styles["Heading2"]))

    exif = meta.get("exif", {})
    rows = [["Tag", "Value"]]
    for key, value in list(exif.items())[:30]:
        rows.append([str(key), str(value)[:100]])

    if len(rows) == 1:
        rows.append(["-", "No EXIF metadata available"])

    exif_table = Table(rows, colWidths=[150, 330])
    exif_table.setStyle(TableStyle([
        ("GRID", (0,0), (-1,-1), 0.4, colors.grey),
        ("BACKGROUND", (0,0), (-1,0), colors.lightgrey),
        ("PADDING", (0,0), (-1,-1), 5),
    ]))
    story.append(exif_table)

    doc.build(story)
