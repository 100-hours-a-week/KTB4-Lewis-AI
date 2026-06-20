import glob
import os

from app.config import DATA_DIR


def load_markdown_documents(data_dir: str = DATA_DIR) -> list[dict]:
    """data_dir 안의 모든 .md 파일을 읽어 {source, text} 리스트로 반환한다."""
    documents = []
    for path in sorted(glob.glob(os.path.join(data_dir, "*.md"))):
        with open(path, encoding="utf-8") as f:
            text = f.read()
        documents.append({"source": os.path.basename(path), "text": text})
    return documents
