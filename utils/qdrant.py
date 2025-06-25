import os
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.http.models import (
    PointStruct, VectorParams, Distance, CollectionStatus, CollectionInfo,
    CreateCollection
)
import uuid

# 🔐 Načti API klíč a URL z .env
load_dotenv()
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "articles")

# 🧠 Inicializace klienta
client = QdrantClient(
    url=QDRANT_URL,
    api_key=QDRANT_API_KEY
)

def ensure_collection_exists(collection_name: str = QDRANT_COLLECTION, vector_size: int = 1536):
    """
    Zkontroluje, jestli kolekce existuje – pokud ne, vytvoří ji.
    """
    if not client.collection_exists(collection_name):
        print(f"📁 Kolekce '{collection_name}' neexistuje, vytvářím...")
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE)
        )
    else:
        print(f"✅ Kolekce '{collection_name}' existuje.")

def upload_chunk(
    chunk: str,
    embedding: list[float],
    metadata: dict,
    collection_name: str = QDRANT_COLLECTION
):
    """
    Nahraje jeden chunk s embeddingem a metadaty do kolekce
    """
    point_id = str(uuid.uuid4())
    point = PointStruct(
        id=point_id,
        vector=embedding,
        payload={
            "chunk": chunk,
            **metadata  # např. title, url, source, date, etc.
        }
    )
    client.upsert(collection_name=collection_name, points=[point])
    print(f"🟢 Uložen chunk: {metadata.get('title', '')[:40]}...")

