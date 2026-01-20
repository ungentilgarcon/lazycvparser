# CV Markdown to PDF Conversion Workflow

This project provides a robust workflow for converting a CV from PDF to structured Markdown, and then rendering that Markdown as a well-formatted PDF. The scripts are designed to handle complex layouts, tables, and date formatting, ensuring high-quality output suitable for professional use.

## Workflow Overview

1. **Convert PDF to Structured Markdown and PDF**
   - **Script:** `convert_pdf_to_structured_md_and_pdf.py`
   - **Input:** Original CV PDF file
   - **Output:**
     - Structured Markdown file (`result/CV_GB_UNI_2020_structured.md`)
     - Rendered PDF file (`result/CV_GB_UNI_2020_structured.pdf`)
   - **Features:**
     - Extracts and normalizes text, tables, and periods (including handling "En cours" as a period)
     - Prevents duplicate headers
     - Renders Markdown tables as real tables in the PDF
     - Handles page breaks, row heights, and non-breaking spaces for date ranges (e.g., "Février 2017")
     - Ensures no overlapping text or blank pages

2. **Render PDF Directly from Markdown**
   - **Script:** `render_md_to_pdf.py`
   - **Input:** Structured Markdown file
   - **Output:** Rendered PDF file
   - **Usage:**
     - Use this script if you only need to render a PDF from an already structured Markdown file, without parsing the original PDF.

## Usage

### 1. Convert PDF to Markdown and PDF

```bash
python convert_pdf_to_structured_md_and_pdf.py
```
- This will generate both the structured Markdown and the PDF in the `result/` directory.

### 2. Render PDF from Markdown Only

```bash
python render_md_to_pdf.py
```
- This will read the Markdown file from `result/CV_GB_UNI_2020_structured.md` and generate the PDF in the same directory.

## Key Implementation Details

- **Table Rendering:** Markdown tables are parsed and rendered as real tables in the PDF, with proper column widths and bold headers.
- **Date Handling:** Date ranges (e.g., "Octobre 2016 à Février 2017") are kept on a single line using non-breaking spaces.
- **Font Support:** Uses DejaVu fonts for Unicode compatibility. Handles font registration and bolding.
- **Layout:** Prevents overlapping text and blank pages by calculating row heights and checking for page breaks.
- **No Duplicate Headers:** Ensures the title and contact info are not repeated in the output.

## File Structure

- `convert_pdf_to_structured_md_and_pdf.py` — Main script for PDF to Markdown and PDF conversion
- `render_md_to_pdf.py` — Script for rendering PDF from Markdown only
- `result/` — Output directory for Markdown and PDF files
- `CV_GB_UNI_2020_structured.md` — Structured Markdown output
- `CV_GB_UNI_2020_structured.pdf` — Final PDF output

## Requirements

- Python 3.8+
- [fpdf2](https://pypi.org/project/fpdf2/)
- [PyPDF2](https://pypi.org/project/PyPDF2/) (if parsing PDFs)

Install dependencies with:

```bash
pip install fpdf2 PyPDF2
```

## Tips

- If you only want to adjust the PDF layout, edit the Markdown and re-run `render_md_to_pdf.py`.
- For new CVs, start with `convert_pdf_to_structured_md_and_pdf.py` to generate the structured Markdown.
- The scripts are designed to be robust to various CV layouts, but manual Markdown tweaks may be needed for best results.

## Version Control

- Commit your changes with a clear message describing the update.
- Push to your remote repository to back up your work.

---

**Author:** [Your Name]
**Last updated:** January 20, 2026
