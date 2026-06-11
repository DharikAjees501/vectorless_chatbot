import fitz

def extract_pdf_pages(pdf_path, file_name):
    doc = fitz.open(pdf_path)
    pages = []

    for page_num, page in enumerate(doc, start=1):
        text = page.get_text()
        if text.strip():
            pages.append({
                "file_name": file_name,
                "page_number": page_num,
                "text": text
            })

    return pages