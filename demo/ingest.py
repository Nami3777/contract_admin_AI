"""Quick PyMuPDF ingestion - bypasses Docling entirely"""
import fitz
from pathlib import Path

pdf_dir = Path(".")
output_dir = Path("markdown_output")
output_dir.mkdir(exist_ok=True)

for pdf in sorted(pdf_dir.glob("*DWR*.pdf")):
    print(f"Processing: {pdf.name}")
    doc = fitz.open(pdf)
    markdown = ""
    for page_num, page in enumerate(doc, 1):
        text = page.get_text()
        markdown += f"## Page {page_num}\n\n{text}\n\n"
    doc.close()

    # Build output filename matching the pattern extract expects
    stem = pdf.stem
    if "__CA__" in stem or "(CA" in stem:
        source = "CA"
    elif "Contractor" in stem:
        source = "Contractor"
    else:
        source = "Unknown"

    # Extract CO number
    import re
    co_match = re.search(r'CO-(\d+)', stem)
    co = f"CO-{co_match.group(1)}" if co_match else "CO-XX"

    # Extract date
    date_match = re.search(r'(\d{4})[._](\d{2})[._](\d{2})', stem)
    date_str = f"{date_match.group(1)}.{date_match.group(2)}.{date_match.group(3)}" if date_match else "unknown"

    # Extract DWR number
    dwr_match = re.search(r'DWR-(\d+)', stem)
    dwr_num = dwr_match.group(1) if dwr_match else "000"

    out_name = f"2020-4091-DWR-{dwr_num} ({source}, {date_str} {co}).md"
    out_path = output_dir / out_name

    with open(out_path, "w", encoding="utf-8", errors="replace") as f:
        f.write(markdown)

    print(f"  -> {out_name} ({len(markdown)} chars)")

print(f"\nDone: {len(list(output_dir.glob('*.md')))} files in {output_dir}/")