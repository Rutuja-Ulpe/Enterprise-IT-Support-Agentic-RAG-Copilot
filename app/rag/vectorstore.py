import time

from pinecone import Pinecone, ServerlessSpec
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_pinecone import PineconeVectorStore

from app.core.config import get_settings


settings = get_settings()

_embeddings = None
_vectorstore = None


EMBEDDING_DIMENSIONS = {
    "text-embedding-3-small": 1536,
    "sentence-transformers/all-MiniLM-L6-v2": 384,
    "all-minilm-l6-v2": 384,
}


def get_embedding_dimension(model_name: str | None = None) -> int:
    name = (
        model_name or settings.embedding_model or ""
    ).strip()

    if not name:
        raise RuntimeError(
            "Embedding model is not configured"
        )

    normalized = name.lower()

    if normalized in EMBEDDING_DIMENSIONS:
        return EMBEDDING_DIMENSIONS[normalized]

    if "text-embedding-3-small" in normalized:
        return 1536

    if "text-embedding-3-large" in normalized:
        return 3072

    if "text-embedding-ada-002" in normalized:
        return 1536

    if "all-minilm" in normalized:
        return 384

    raise ValueError(
        f"Unsupported embedding model '{name}'. "
        "Add its dimension to EMBEDDING_DIMENSIONS."
    )


def get_embeddings():
    global _embeddings

    if _embeddings is None:
        _embeddings = HuggingFaceEmbeddings(
            model_name=settings.embedding_model,
            model_kwargs={
                "device": "cpu",
            },
            encode_kwargs={
                "normalize_embeddings": True,
            },
        )

    return _embeddings


def ensure_index():
    if not settings.pinecone_api_key:
        raise RuntimeError(
            "PINECONE_API_KEY is missing"
        )

    desired_dimension = get_embedding_dimension()

    pinecone_client = Pinecone(
        api_key=settings.pinecone_api_key
    )

    index_names = [
        item["name"]
        for item in pinecone_client.list_indexes()
    ]

    index_name = settings.pinecone_index_name

    if index_name in index_names:
        index_info = pinecone_client.describe_index(
            index_name
        )

        current_dimension = getattr(
            index_info,
            "dimension",
            None,
        )

        if current_dimension is None and isinstance(
            index_info,
            dict,
        ):
            current_dimension = index_info.get(
                "dimension"
            )

        if (
            current_dimension is not None
            and current_dimension != desired_dimension
        ):
            raise RuntimeError(
                f"Pinecone index '{index_name}' has "
                f"dimension {current_dimension}, but "
                f"the embedding model requires "
                f"dimension {desired_dimension}. "
                "Create a new index or update the "
                "embedding model."
            )

    else:
        pinecone_client.create_index(
            name=index_name,
            dimension=desired_dimension,
            metric="cosine",
            spec=ServerlessSpec(
                cloud="aws",
                region="us-east-1",
            ),
        )

        print(
            f"Creating Pinecone index '{index_name}'..."
        )

        while True:
            status = pinecone_client.describe_index(
                index_name
            ).status

            if status["ready"]:
                break

            time.sleep(1)

    return pinecone_client.Index(index_name)


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
        search_kwargs={
            "k": settings.top_k,
        }
    )


def add_documents(chunks):
    if not chunks:
        return []

    store = get_vectorstore()
    return store.add_documents(chunks)