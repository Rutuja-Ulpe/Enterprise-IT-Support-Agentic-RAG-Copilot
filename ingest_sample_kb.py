from pathlib import Path

from app.services.ingestion import load_file, chunk_documents
from app.rag.vectorstore import add_documents


KB_DIR = Path("data/sample_kb")

all_docs = []
file_count = 0

for path in KB_DIR.iterdir():
    if path.is_file() and path.suffix.lower() in {".pdf", ".txt", ".md", ".docx"}:
        all_docs.extend(load_file(path))
        file_count += 1

chunks = chunk_documents(all_docs)

add_documents(chunks)

print(
    f"Indexed {file_count} files → "
    f"{len(chunks)} chunks → "
    f"{len(chunks)} Pinecone vectors"
)