"""Shared database setup for fab-finder.

Every script imports get_collection() from here, so they all open the same
collection with the same embedding model and distance settings.
"""

from pathlib import Path

import chromadb
from chromadb.utils import embedding_functions
from dotenv import load_dotenv

# Store the database next to this file, so it's the same folder
# no matter which directory a script is run from.
STORE_PATH = str(Path(__file__).parent / "chroma_store")
COLLECTION_NAME = "fab_finder"
EMBEDDING_MODEL = "text-embedding-3-small"
API_KEY_ENV_VAR = "OPENAI_API_KEY"
DISTANCE = "cosine"


def get_collection():
    """Open (or create on first run) the fab_finder collection."""
    # Read OPENAI_API_KEY from .env into the environment.
    load_dotenv(Path(__file__).parent / ".env")

    client = chromadb.PersistentClient(path=STORE_PATH)

    embedder = embedding_functions.OpenAIEmbeddingFunction(
        model_name=EMBEDDING_MODEL,
        api_key_env_var=API_KEY_ENV_VAR,
    )

    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=embedder,
        configuration={"hnsw": {"space": DISTANCE}},
    )


if __name__ == "__main__":
    # Quick check: python db.py
    collection = get_collection()
    print(f"Opened '{COLLECTION_NAME}' at {STORE_PATH}")
    print("Items:", collection.count())
