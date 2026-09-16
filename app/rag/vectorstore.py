import time

from pinecone import Pinecone, ServerlessSpec
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_pinecone import PineconeVectorStore

from app.core.config import get_settings


settings = get_settings()

_embeddings = None
_vectorstore = None


EMBEDDING_DIMENSIONS = {
    "sentence-transformers/all-MiniLM-L6-v2": 384,
    "all-minilm-l6-v2": 384,
    "text-embedding-3-small": 1536,
}


def get_embedding_dimension(model_name: str | None = None) -> int:
    name = (model_name or settings.embedding_model or "").strip()

    if not name:
        raise RuntimeError("Embedding model is not configured")

    normalized = name.lower()

    if normalized in EMBEDDING_DIMENSIONS:
        return EMBEDDING_DIMENSIONS[normalized]

    if "all-minilm" in normalized:
        return 384

    if "text-embedding-3-small" in normalized:
        return 1536

    raise ValueError(
        f"Unknown embedding model '{model_name}'."
    )


def get_embeddings():
    global _embeddings

    if _embeddings is None:
        _embeddings = HuggingFaceEmbeddings(
            model_name=settings.embedding_model,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )

    return _embeddings


def ensure_index():
    if not settings.pinecone_api_key:
        raise RuntimeError(
            "PINECONE_API_KEY is not configured."
        )

    pc = Pinecone(
        api_key=settings.pinecone_api_key
    )

    existing_indexes = pc.list_indexes().names()

    dimension = get_embedding_dimension(
        settings.embedding_model
    )

    if settings.pinecone_index_name not in existing_indexes:
        pc.create_index(
            name=settings.pinecone_index_name,
            dimension=dimension,
            metric="cosine",
            spec=ServerlessSpec(
                cloud="aws",
                region="us-east-1",
            ),
        )

        time.sleep(2)

    return pc.Index(
        settings.pinecone_index_name
    )


def get_vectorstore():
    global _vectorstore

    if _vectorstore is None:
        index = ensure_index()

        _vectorstore = PineconeVectorStore(
            index=index,
            embedding=get_embeddings(),
            namespace=settings.pinecone_namespace,
        )

    return _vectorstore


def get_retriever():
    return get_vectorstore().as_retriever(
        search_kwargs={"k": settings.top_k}
    )


def add_documents(chunks):
    vectorstore = get_vectorstore()
    return vectorstore.add_documents(chunks)