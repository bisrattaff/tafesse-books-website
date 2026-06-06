"""
PDF Text Extractor — Tafesse Books
Run this script locally to extract text from each PDF and save as .txt files.
Then upload the .txt files to your S3 bucket under the 'book-text/' folder.

Requirements:
  pip install pdfplumber

Usage:
  python extract_pdf_text.py <path_to_books_folder> <output_folder>

Example:
  python extract_pdf_text.py "C:/path/to/show/books" "./book-text-output"

After running, upload all .txt files in the output folder to:
  s3://your-bucket/book-text/
"""

import os
import sys

try:
    import pdfplumber
except ImportError:
    print("ERROR: pdfplumber not installed. Run:  pip install pdfplumber")
    sys.exit(1)


# Maps PDF filename -> output .txt filename
# Must match the filenames in lambda_function.py BOOKS dict
BOOK_MAP = {
    'Scientistoch.pdf':                         'Scientistoch.txt',
    'Ye_Haimanotoch_Liyunet.pdf':               'Ye_Haimanotoch_Liyunet.txt',
    'Ye_Nuclear_Hail.pdf':                      'Ye_Nuclear_Hail.txt',
    'Pillars_Of_Creation_[English].pdf':        'Pillars_Of_Creation_English.txt',
    'Pillars_Of_Creation_[French].pdf':         'Pillars_Of_Creation_French.txt',
    'Leloch_Alemat.pdf':                        'Leloch_Alemat.txt',
    'Ye_Chess_Tibeb.pdf':                       'Ye_Chess_Tibeb.txt',
    'Endet_New_Yemiseraw.pdf':                  'Endet_New_Yemiseraw.txt',
    'Reflection.pdf':                           'Reflection.txt',
    'Chronology_Of_The_Universe.pdf':           'Chronology_Of_The_Universe.txt',
    'If_I_Were_Black_American.pdf':             'If_I_Were_Black_American.txt',
    'Life_In_Las_Vegas.pdf':                    'Life_In_Las_Vegas.txt',
    'My_Spiritual_Life.pdf':                    'My_Spiritual_Life.txt',
    'Turtles_All_The_Way.pdf':                  'Turtles_All_The_Way.txt',
    'All_Religions_Lead_The_Same_Way.pdf':      'All_Religions_Lead_The_Same_Way.txt',
    'Whence Life and Consciousness.pdf':        'Whence_Life_And_Consciousness.txt',
    'My_Encounter_With_Telepathy.pdf':          'My_Encounter_With_Telepathy.txt',
}


def extract_text_from_pdf(pdf_path):
    """Extract all text from a PDF. Returns (text, page_count, char_count)."""
    pages_text = []
    with pdfplumber.open(pdf_path) as pdf:
        page_count = len(pdf.pages)
        for page in pdf.pages:
            text = page.extract_text()
            if text and text.strip():
                pages_text.append(text.strip())
    full_text = '\n\n'.join(pages_text)
    return full_text, page_count, len(full_text)


def main():
    books_dir  = sys.argv[1] if len(sys.argv) > 1 else './books'
    output_dir = sys.argv[2] if len(sys.argv) > 2 else './book-text-output'

    if not os.path.isdir(books_dir):
        print(f"ERROR: books folder not found: {books_dir}")
        sys.exit(1)

    os.makedirs(output_dir, exist_ok=True)
    print(f"\nExtracting text from PDFs in: {books_dir}")
    print(f"Saving .txt files to:         {output_dir}\n")

    success, skipped, failed = 0, 0, 0

    for pdf_name, txt_name in BOOK_MAP.items():
        pdf_path = os.path.join(books_dir, pdf_name)
        txt_path = os.path.join(output_dir, txt_name)

        if not os.path.exists(pdf_path):
            print(f"  SKIP (not found): {pdf_name}")
            skipped += 1
            continue

        try:
            text, pages, chars = extract_text_from_pdf(pdf_path)

            if chars < 100:
                print(f"  WARN (very little text — may be scanned/image PDF): {pdf_name}")
                print(f"       Only {chars} characters extracted from {pages} pages.")
                print(f"       OCR would be needed for this book.")

            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write(text)

            print(f"  OK  {pages} pages, {chars:,} chars -> {txt_name}")
            success += 1

        except Exception as e:
            print(f"  FAIL: {pdf_name} — {e}")
            failed += 1

    print(f"\nDone. {success} extracted, {skipped} skipped, {failed} failed.")
    if success > 0:
        print(f"\nNext step: upload all .txt files from '{output_dir}' to:")
        print(f"  s3://YOUR_BUCKET_NAME/book-text/")
        print(f"\nUsing AWS CLI:")
        print(f'  aws s3 cp "{output_dir}" s3://YOUR_BUCKET_NAME/book-text/ --recursive')


if __name__ == '__main__':
    main()
