"""
Clause-aware PDF parser.

Most RAG tutorials split documents by fixed token windows — this destroys
legal document structure. This parser detects clause/section boundaries
and keeps them intact as semantic units, which dramatically improves
retrieval quality.
"""
import io
import re
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
from dataclasses import dataclass


@dataclass
class Clause:
    text: str
    page: int
    clause_number: str | None   # e.g. "3.2.1"
    section_title: str | None
    char_start: int
    char_end: int


# Patterns that indicate the start of a new clause/section
CLAUSE_PATTERNS = [
    r"^\s*(\d+\.\d+(?:\.\d+)*)\s+[A-Z]",       # 1.1 Title or 3.2.1 Something
    r"^\s*([A-Z]{1,3})\.\s+[A-Z]",              # A. Title or IV. Title
    r"^\s*(SECTION|ARTICLE|CLAUSE)\s+\d+",       # SECTION 4
    r"^\s*(\d+)\.\s{2,}[A-Z]",                  # 4.  Title (double space)
    r"^\s*(SCHEDULE|EXHIBIT|ANNEX)\s+[A-Z\d]+",  # SCHEDULE A
]

CLAUSE_REGEX = re.compile("|".join(CLAUSE_PATTERNS), re.MULTILINE)


def _extract_page_text(page) -> str:
    """
    Try multiple PyMuPDF extraction methods to handle various PDF encodings.
    Falls back progressively if the primary method returns no text.
    """
    # Method 1: standard text extraction
    text = page.get_text("text")
    if text.strip():
        return text

    # Method 2: extract from block structure (handles some unusual encodings)
    try:
        blocks = page.get_text("blocks")
        text = "\n".join(b[4] for b in blocks if len(b) > 4 and isinstance(b[4], str))
        if text.strip():
            return text
    except Exception:
        pass

    # Method 3: extract from word-level data
    try:
        words = page.get_text("words")
        text = " ".join(w[4] for w in words if len(w) > 4 and isinstance(w[4], str))
        if text.strip():
            return text
    except Exception:
        pass

    # Method 4: raw dict — catches text with unusual font/encoding
    try:
        raw = page.get_text("rawdict")
        parts = []
        for block in raw.get("blocks", []):
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    parts.append(span.get("text", ""))
        text = " ".join(parts)
        if text.strip():
            return text
    except Exception:
        pass

    # Method 5: Render page as image and OCR with pytesseract
    try:
        mat = fitz.Matrix(300 / 72, 300 / 72)  # 300 DPI
        pix = page.get_pixmap(matrix=mat)
        img = Image.open(io.BytesIO(pix.tobytes("png")))
        text = pytesseract.image_to_string(img, lang="eng")
        if text.strip():
            return text
    except Exception:
        pass

    return ""


def parse_pdf(file_bytes: bytes) -> list[Clause]:
    """
    Parse a PDF into clause-aware chunks.
    Returns a list of Clause objects preserving document structure.
    """
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    clauses = []

    for page_num, page in enumerate(doc, start=1):
        text = _extract_page_text(page)
        clauses.extend(_extract_clauses_from_page(text, page_num))

    doc.close()

    # Merge very short clauses (< 100 chars) with the next one
    # Short "clauses" are usually just headers, not standalone semantic units
    clauses = _merge_short_clauses(clauses)

    return clauses


def _extract_clauses_from_page(text: str, page_num: int) -> list[Clause]:
    clauses = []
    matches = list(CLAUSE_REGEX.finditer(text))

    if not matches:
        # No clause structure detected — treat whole page as one chunk
        if text.strip():
            clauses.append(Clause(
                text=text.strip(),
                page=page_num,
                clause_number=None,
                section_title=None,
                char_start=0,
                char_end=len(text),
            ))
        return clauses

    for i, match in enumerate(matches):
        start = match.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        chunk_text = text[start:end].strip()

        if not chunk_text:
            continue

        clause_number = _extract_clause_number(match.group())
        section_title = _extract_section_title(chunk_text)

        clauses.append(Clause(
            text=chunk_text,
            page=page_num,
            clause_number=clause_number,
            section_title=section_title,
            char_start=start,
            char_end=end,
        ))

    return clauses


def _extract_clause_number(match_text: str) -> str | None:
    number_match = re.match(r"[\s]*(\d+(?:\.\d+)*|[A-Z]{1,3})", match_text.strip())
    return number_match.group(1) if number_match else None


def _extract_section_title(text: str) -> str | None:
    first_line = text.split("\n")[0].strip()
    if len(first_line) < 100:
        return first_line
    return None


def _merge_short_clauses(clauses: list[Clause], min_length: int = 100) -> list[Clause]:
    if not clauses:
        return clauses

    merged = []
    buffer = clauses[0]

    for clause in clauses[1:]:
        if len(buffer.text) < min_length:
            # Merge current buffer into next clause
            buffer = Clause(
                text=buffer.text + "\n\n" + clause.text,
                page=buffer.page,
                clause_number=buffer.clause_number or clause.clause_number,
                section_title=buffer.section_title or clause.section_title,
                char_start=buffer.char_start,
                char_end=clause.char_end,
            )
        else:
            merged.append(buffer)
            buffer = clause

    merged.append(buffer)
    return merged


def get_page_count(file_bytes: bytes) -> int:
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    count = doc.page_count
    doc.close()
    return count
