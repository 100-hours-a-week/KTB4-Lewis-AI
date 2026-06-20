import re

MAX_CHUNK_CHARS = 800
OVERLAP_CHARS = 150


def _split_by_headers(text: str) -> list[dict]:
    """'## 제목' 단위로 문서를 섹션 분할한다."""
    pattern = re.compile(r"^##\s+(.+)$", re.MULTILINE)
    matches = list(pattern.finditer(text))

    if not matches:
        return [{"heading": None, "body": text.strip()}]

    sections = []
    for i, match in enumerate(matches):
        heading = match.group(1).strip()
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[start:end].strip()
        sections.append({"heading": heading, "body": body})
    return sections


def _split_long_text(text: str, max_chars: int, overlap: int) -> list[str]:
    """긴 텍스트를 max_chars 단위로, overlap만큼 겹치게 분할한다."""
    if len(text) <= max_chars:
        return [text]

    chunks = []
    start = 0
    while start < len(text):
        end = min(start + max_chars, len(text))
        chunks.append(text[start:end])
        if end == len(text):
            break
        start = end - overlap
    return chunks


def split_document(source: str, text: str) -> list[dict]:
    """문서를 섹션(## 헤더) 단위로 자르고, 섹션이 길면 추가로 분할한다.

    각 청크는 {source, heading, text} 형태로 반환된다.
    """
    chunks = []
    for section in _split_by_headers(text):
        heading = section["heading"]
        body = section["body"]
        if not body:
            continue
        for piece in _split_long_text(body, MAX_CHUNK_CHARS, OVERLAP_CHARS):
            chunks.append({"source": source, "heading": heading, "text": piece})
    return chunks
