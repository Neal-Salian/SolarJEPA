"""Make a PDF facsimile from the exact inspected 16:9 slide renders."""
import argparse
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from PIL import Image
from pypdf import PdfReader


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--render-dir", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    pages = sorted(args.render_dir.glob("slide-[0-9][0-9].png"))
    assert len(pages) == 20, len(pages)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    pdf = canvas.Canvas(str(args.output), pagesize=(960, 540), pageCompression=1)
    pdf.setTitle("SolarJEPA: Solar X-ray time-series analysis")
    pdf.setSubject("GOES-16 XRS May–August 2024, verified classical demonstration")
    pdf.setAuthor("SolarJEPA")
    for page in pages:
        with Image.open(page) as image:
            assert image.size == (2560, 1440), image.size
            pdf.drawImage(ImageReader(image), 0, 0, width=960, height=540)
        pdf.showPage()
    pdf.save()
    result = PdfReader(args.output)
    assert len(result.pages) == 20
    assert all(tuple(float(x) for x in p.mediabox) == (0, 0, 960, 540)
               for p in result.pages)
    print(f"PDF: {len(result.pages)} slides, 16:9, 192-dpi facsimile, {args.output}")


if __name__ == "__main__":
    main()
