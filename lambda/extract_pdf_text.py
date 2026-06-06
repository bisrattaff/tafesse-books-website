"""
PDF Text Extractor — Tafesse Books (with Amharic OCR fallback)
===============================================================
For each PDF page:
  1. Try pdfplumber (fast, perfect for digitally-created PDFs)
  2. If no text found, fall back to Tesseract OCR (handles scanned pages,
     supports Amharic Ge'ez script via the 'amh' language pack)

REQUIREMENTS — install before running:
  pip install pdfplumber pytesseract pdf2image Pillow

You also need two system installs (done once, not via pip):

  1. Tesseract OCR engine
     Windows: https://github.com/UB-Mannheim/tesseract/wiki
       - Run the installer, note the install path (e.g. C:\\Program Files\\Tesseract-OCR)
       - During install, check "Additional language data" → select "Amharic"
       OR manually download amh.traineddata from:
           https://github.com/tesseract-ocr/tessdata/blob/main/amh.traineddata
       and copy it into your Tesseract tessdata folder.

  2. Poppler (required by pdf2image to convert PDF pages to images)
     Windows: https://github.com/oschwartz10612/poppler-windows/releases
       - Download, unzip, and add the 'bin' folder to your system PATH
       OR pass poppler_path= argument in the script (see POPPLER_PATH below).

USAGE:
  python extract_pdf_text.py <books_folder> <output_folder>

  Example:
    python extract_pdf_text.py "C:/path/to/show/books" "./book-text-output"

After running, upload all .txt files to S3:
  aws s3 cp "./book-text-output" s3://YOUR_BUCKET/book-text/ --recursive
"""

import os
import sys

# ── Optional: set this if Poppler is not on your PATH (Windows) ──────────────
POPPLER_PATH = None   # e.g. r"C:\poppler\Library\bin"  or leave None

# ── Optional: set this if Tesseract is not on your PATH (Windows) ────────────
TESSERACT_CMD = None  # e.g. r"C:\Program Files\Tesseract-OCR\tesseract.exe"
# ─────────────────────────────────────────────────────────────────────────────

# Minimum characters from pdfplumber before we consider a page "has text"
TEXT_THRESHOLD = 50

# Tesseract language: amh = Amharic, eng = English.
# Using both handles mixed-language PDFs.
OCR_LANG = 'amh+eng'

# Maps PDF filename → output .txt filename (must match lambda_function.py BOOKS dict)
BOOK_MAP = {
    'Scientistoch.pdf':                         'Scientistoch.txt',
    'Ye_Haimanotoch_Liyunet.pdf':               'Ye_Haimanotoch_Liyunet.txt',
    'Ye_Nuclear_Hail.pdf':                       'Ye_Nuclear_Hail.txt',
    'Pillars_Of_Creation_[English].pdf':         'Pillars_Of_Creation_English.txt',
    'Pillars_Of_Creation_[French].pdf':          'Pillars_Of_Creation_French.txt',
    'Leloch_Alemat.pdf':                         'Leloch_Alemat.txt',
    'Ye_Chess_Tibeb.pdf':                        'Ye_Chess_Tibeb.txt',
    'Endet_New_Yemiseraw.pdf':                   'Endet_New_Yemiseraw.txt',
    'Reflection.pdf':                            'Reflection.txt',
    'Chronology_Of_The_Universe.pdf':            'Chronology_Of_The_Universe.txt',
    'If_I_Were_Black_American.pdf':              'If_I_Were_Black_American.txt',
    'Life_In_Las_Vegas.pdf':                     'Life_In_Las_Vegas.txt',
    'My_Spiritual_Life.pdf':                     'My_Spiritual_Life.txt',
    'Turtles_All_The_Way.pdf':                   'Turtles_All_The_Way.txt',
    'All_Religions_Lead_The_Same_Way.pdf':       'All_Religions_Lead_The_Same_Way.txt',
    'Whence Life and Consciousness.pdf':         'Whence_Life_And_Consciousness.txt',
    'My_Encounter_With_Telepathy.pdf':           'My_Encounter_With_Telepathy.txt',
}


# ── Dependency checks ─────────────────────────────────────────────────────────

try:
    import pdfplumber
except ImportError:
    print("ERROR: pdfplumber not installed.  Run:  pip install pdfplumber")
    sys.exit(1)

try:
    import pytesseract
    from pdf2image import convert_from_path
    if TESSERACT_CMD:
        pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False
    print("NOTE: pytesseract or pdf2image not installed — OCR fallback disabled.")
    print("      Run:  pip install pytesseract pdf2image Pillow")
    print("      Scanned / Amharic pages will be skipped.\n")


# ── Extraction logic ──────────────────────────────────────────────────────────

def extract_page_with_ocr(pdf_path, page_number_1based):
    """Convert a single PDF page to an image and run Tesseract OCR."""
    kwargs = dict(first_page=page_number_1based, last_page=page_number_1based, dpi=300)
    if POPPLER_PATH:
        kwargs['poppler_path'] = POPPLER_PATH
    images = convert_from_path(pdf_path, **kwargs)
    if not images:
        return ''
    return pytesseract.image_to_string(images[0], lang=OCR_LANG)


def extract_book(pdf_path):
    """
    Extract text from every page of a PDF.
    Returns (full_text, stats_dict).
    """
    pages_text = []
    stats = {'plumber': 0, 'ocr': 0, 'empty': 0, 'total': 0}

    with pdfplumber.open(pdf_path) as pdf:
        stats['total'] = len(pdf.pages)

        for i, page in enumerate(pdf.pages, start=1):
            # Step 1: pdfplumber
            raw = page.extract_text() or ''
            raw = raw.strip()

            if len(raw) >= TEXT_THRESHOLD:
                pages_text.append(raw)
                stats['plumber'] += 1
                continue

            # Step 2: Tesseract OCR fallback
            if OCR_AVAILABLE:
                try:
                    ocr_text = extract_page_with_ocr(pdf_path, i).strip()
                    if ocr_text:
                        pages_text.append(ocr_text)
                        stats['ocr'] += 1
                        continue
                except Exception as e:
                    print(f"      OCR error page {i}: {e}")

            # Nothing worked for this page
            stats['empty'] += 1

    full_text = '\n\n'.join(pages_text)
    return full_text, stats


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    books_dir  = sys.argv[1] if len(sys.argv) > 1 else './books'
    output_dir = sys.argv[2] if len(sys.argv) > 2 else './book-text-output'

    if not os.path.isdir(books_dir):
        print(f"ERROR: books folder not found: {books_dir}")
        sys.exit(1)

    os.makedirs(output_dir, exist_ok=True)

    print(f"\nExtracting text from: {books_dir}")
    print(f"Output folder:        {output_dir}")
    print(f"OCR available:        {'Yes (amh+eng)' if OCR_AVAILABLE else 'No'}\n")

    success, skipped, failed = 0, 0, 0

    for pdf_name, txt_name in BOOK_MAP.items():
        pdf_path = os.path.join(books_dir, pdf_name)
        txt_path = os.path.join(output_dir, txt_name)

        if not os.path.exists(pdf_path):
            print(f"  SKIP  (not found): {pdf_name}")
            skipped += 1
            continue

        try:
            print(f"  Processing: {pdf_name}")
            text, stats = extract_book(pdf_path)
            chars = len(text)

            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write(text)

            tag = (
                f"pdfplumber:{stats['plumber']} "
                f"ocr:{stats['ocr']} "
                f"empty:{stats['empty']} "
                f"/ {stats['total']} pages"
            )
            print(f"  OK    {chars:,} chars  [{tag}]  -> {txt_name}")

            if stats['empty'] > 0 and not OCR_AVAILABLE:
                print(f"        ^ {stats['empty']} pages had no text. Install pytesseract+pdf2image for OCR.")

            success += 1

        except Exception as e:
            print(f"  FAIL  {pdf_name} — {e}")
            failed += 1

    print(f"\nDone: {success} extracted, {skipped} skipped, {failed} failed.")

    if success > 0:
        print(f"\nNext: upload .txt files to S3 under 'book-text/' folder.")
        print(f"  aws s3 cp \"{output_dir}\" s3://YOUR_BUCKET/book-text/ --recursive")


if __name__ == '__main__':
    main()
