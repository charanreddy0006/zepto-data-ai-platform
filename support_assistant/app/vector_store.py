from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer


# -------------------------------------------------------------------
# Paths
# -------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent
DOCS_DIR = BASE_DIR / "docs"
CHROMA_DIR = BASE_DIR / "data" / "chroma"

CHROMA_DIR.mkdir(parents=True, exist_ok=True)


# -------------------------------------------------------------------
# Embedding model
# -------------------------------------------------------------------

EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"

embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)


# -------------------------------------------------------------------
# ChromaDB
# -------------------------------------------------------------------

chroma_client = chromadb.PersistentClient(
    path=str(CHROMA_DIR)
)

collection = chroma_client.get_or_create_collection(
    name="zepto_policy_corpus",
    metadata={"hnsw:space": "cosine"},
)


# -------------------------------------------------------------------
# Document loading
# -------------------------------------------------------------------

def load_documents() -> list[dict]:
    """
    Load all policy documents from the docs directory.

    Each document becomes one chunk because the supplied
    policy documents are short enough for per-document chunking.
    """

    documents = []

    for file_path in sorted(DOCS_DIR.glob("doc_*.txt")):
        text = file_path.read_text(encoding="utf-8").strip()

        if not text:
            continue

        documents.append(
            {
                "id": file_path.stem,
                "text": text,
                "source": file_path.name,
            }
        )

    return documents


# -------------------------------------------------------------------
# Indexing
# -------------------------------------------------------------------

def build_index() -> int:
    """
    Embed all policy documents and store them in ChromaDB.

    Returns:
        Number of indexed documents.
    """

    documents = load_documents()

    if not documents:
        raise RuntimeError(
            f"No policy documents found in {DOCS_DIR}"
        )

    ids = [document["id"] for document in documents]
    texts = [document["text"] for document in documents]
    metadatas = [
        {"source": document["source"]}
        for document in documents
    ]

    embeddings = embedding_model.encode(
        texts,
        normalize_embeddings=True,
    ).tolist()

    collection.upsert(
        ids=ids,
        documents=texts,
        embeddings=embeddings,
        metadatas=metadatas,
    )

    return len(documents)


# -------------------------------------------------------------------
# Retrieval
# -------------------------------------------------------------------

def retrieve_documents(
    query: str,
    top_k: int = 3,
) -> dict:
    """
    Retrieve the top-k most similar policy chunks.

    ChromaDB uses cosine distance because the collection was
    configured with the cosine metric.
    """

    query_embedding = embedding_model.encode(
        [query],
        normalize_embeddings=True,
    ).tolist()[0]

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
    )

    return results


# -------------------------------------------------------------------
# Main test
# -------------------------------------------------------------------

if __name__ == "__main__":
    count = build_index()

    print(f"Indexed documents: {count}")
    print(f"Collection: {collection.name}")
    print(f"Embedding model: {EMBEDDING_MODEL_NAME}")
    print(f"ChromaDB path: {CHROMA_DIR}")

    test_query = "How much does priority delivery cost?"

    results = retrieve_documents(test_query, top_k=3)

    print("\nTest query:")
    print(test_query)

    print("\nRetrieved documents:")

    for index, document in enumerate(results["documents"][0], start=1):
        document_id = results["ids"][0][index - 1]
        distance = results["distances"][0][index - 1]

        print(f"\n{index}. {document_id}")
        print(f"Distance: {distance:.4f}")
        print(document[:250])