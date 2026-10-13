"""Verify final deck structure, evidence values and embedded asset identities.

This complements, rather than replaces, visual review and native-data replay.
It does not claim that PowerPoint itself was executed.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET
from zipfile import ZipFile

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[2]
NS = {"a": "http://schemas.openxmlformats.org/drawingml/2006/main",
      "p": "http://schemas.openxmlformats.org/presentationml/2006/main"}


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify():
    out = ROOT / "presentations"
    assets = out / "assets"
    pptx = out / "SolarJEPA_Final_Time_Series_Presentation.pptx"
    pdf = pptx.with_suffix(".pdf")
    evidence = json.loads((out / "slide_evidence.json").read_text())
    chart_manifest = json.loads((assets / "chart_manifest.json").read_text())
    captures = json.loads((assets / "dashboard_capture_metadata.json").read_text())
    assert evidence["source_commit"] == "abe4b79d2fe7549552b0a1f467be1cd949b652a7"
    assert chart_manifest["source_commit"] == captures["source_commit"] == evidence["source_commit"]
    assert evidence["dataset"]["source_files"] == 123
    assert evidence["dataset"]["rows"] == 177120
    assert evidence["payload_sha256"] == "69935892e311ef4aacd00a7e9e6ccb055aac8abb1cda7ee988195d6f2fcc5675"
    for row in chart_manifest["charts"]:
        assert sha256(assets / row["path"]) == row["output_sha256"], row["path"]
    for row in captures["captures"]:
        assert sha256(ROOT / row["file"]) == row["sha256"], row["file"]

    tables = []
    expected_assets = ["chart_log.png", "chart_scatter.png", "chart_histogram.png",
                       "chart_qq.png", "chart_transform.png", "chart_stl.png",
                       "chart_acf.png", "chart_pacf.png", "chart_forecast.png",
                       "dashboard_explorer.png", "dashboard_replay_detail.png"]
    with ZipFile(pptx) as package:
        assert package.testzip() is None
        slides = [n for n in package.namelist() if re.fullmatch(r"ppt/slides/slide\d+\.xml", n)]
        notes = [n for n in package.namelist() if re.fullmatch(r"ppt/notesSlides/notesSlide\d+\.xml", n)]
        assert len(slides) == len(notes) == 20
        size = ET.fromstring(package.read("ppt/presentation.xml")).find("p:sldSz", NS)
        assert (size.get("cx"), size.get("cy")) == ("12192000", "6858000")
        slide_text = {}
        note_lengths = []
        for number in range(1, 21):
            page = ET.fromstring(package.read(f"ppt/slides/slide{number}.xml"))
            slide_text[number] = " ".join(t.text or "" for t in page.findall(".//a:t", NS))
            assert f"{number:02d} / 20" in slide_text[number]
            if page.findall(".//a:tbl", NS):
                tables.append(number)
            note = ET.fromstring(package.read(f"ppt/notesSlides/notesSlide{number}.xml"))
            note_text = " ".join(t.text or "" for t in note.findall(".//a:t", NS))
            assert len(note_text) > 400, number
            assert evidence["source_commit"] in note_text, number
            note_lengths.append(len(note_text))
        assert tables == [2, 7, 8, 13, 14, 16, 20], tables
        for value in ["-12311.066", "-12299.136", "-20686.728", "-20668.832"]:
            assert value in slide_text[14], value
        for value in ["0.218835", "0.256635", "0.094347", "0.109055"]:
            assert value in slide_text[16], value
        assert "do not represent overall forecasting skill" in slide_text[16]
        assert "SARIMA deferred" in slide_text[20]
        assert "#8 remains partial" in slide_text[20]
        embedded = {hashlib.sha256(package.read(n)).hexdigest() for n in package.namelist()
                    if n.startswith("ppt/media/") and not n.endswith("/")}
        for filename in expected_assets:
            assert sha256(assets / filename) in embedded, filename

    reader = PdfReader(pdf)
    assert len(reader.pages) == 20
    for page in reader.pages:
        assert tuple(float(x) for x in page.mediabox) == (0, 0, 960, 540)
        resources = page["/Resources"]["/XObject"].get_object()
        images = [v.get_object() for v in resources.values()
                  if v.get_object().get("/Subtype") == "/Image"]
        assert len(images) == 1
        assert (images[0]["/Width"], images[0]["/Height"]) == (2560, 1440)
    return {
        "status": "PASS", "slides": 20, "speaker_notes": 20,
        "minimum_note_characters": min(note_lengths), "native_table_slides": tables,
        "embedded_verified_scientific_figures": 9, "embedded_real_dashboard_captures": 2,
        "chart_files_hash_checked": len(chart_manifest["charts"]),
        "dashboard_files_hash_checked": len(captures["captures"]),
        "source_commit": evidence["source_commit"], "payload_sha256": evidence["payload_sha256"],
        "pdf_pages": 20, "pdf_format": "192-dpi rendered-slide facsimile, 16:9",
        "outputs": {p.name: {"sha256": sha256(p), "bytes": p.stat().st_size} for p in (pptx, pdf)},
        "claim_boundary": "Package, values and asset identities only. Visual review and scientific replay are separate checks. Native PowerPoint was not executed.",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    result = verify()
    rendered = json.dumps(result, indent=2) + "\n"
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(rendered)
    print(rendered)
