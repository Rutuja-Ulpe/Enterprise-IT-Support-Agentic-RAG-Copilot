from pathlib import Path

from app.services.ingestion import load_file, chunk_documents
from app.rag.vectorstore import add_documents


BASE_DIR = Path(__file__).resolve().parent
KB_DIR = BASE_DIR / "data" / "sample_kb"

all_docs = []
file_count = 0

for path in KB_DIR.iterdir():
    if path.is_file() and path.suffix.lower() in {
        ".pdf",
        ".txt",
        ".md",
        ".docx",
    }:
        print(f"Loading: {path.name}")

        documents = load_file(path)
        all_docs.extend(documents)
        file_count += 1

chunks = chunk_documents(all_docs)

print(f"Total chunks created: {len(chunks)}")

add_documents(chunks)

print(
    f"Indexed {file_count} files → "
    f"{len(chunks)} chunks → "
    f"{len(chunks)} Pinecone vectors"
)