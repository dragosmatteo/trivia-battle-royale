import re
from PyPDF2 import PdfReader


def extract_text_from_pdf(file_path: str) -> str:
    """Extract and clean text from a PDF file."""
    reader = PdfReader(file_path)
    raw_text = ""
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            raw_text += page_text + "\n"

    cleaned = _clean_text(raw_text)
    return cleaned


def _clean_text(text: str) -> str:
    """Remove headers, footers, page numbers, and irrelevant artifacts."""
    lines = text.split("\n")
    cleaned_lines = []
    for line in lines:
        stripped = line.strip()
        # Skip empty lines
        if not stripped:
            continue
        # Skip page numbers (standalone numbers)
        if re.match(r'^\d{1,3}$', stripped):
            continue
        # Skip very short lines that are likely headers/footers
        if len(stripped) < 3:
            continue
        cleaned_lines.append(stripped)

    return "\n".join(cleaned_lines)


def chunk_text(text: str, chunk_size: int = 2000, overlap: int = 200) -> list[str]:
    """Split text into overlapping chunks for RAG processing."""
    words = text.split()
    chunks = []
    start = 0
    words_per_chunk = chunk_size // 5  # approximate words per chunk

    while start < len(words):
        end = min(start + words_per_chunk, len(words))
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        start = end - (overlap // 5)  # overlap

    return chunks
