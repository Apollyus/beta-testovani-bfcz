import os
from dotenv import load_dotenv
import openai

# 🔐 Načtení klíčů
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
EMBED_MODEL = os.getenv("OPENAI_EMBED_MODEL", "text-embedding-3-small")

# ⚠️ Ořez na max délku pro embedding model
MAX_TOKENS = 8191 if "3" in EMBED_MODEL else 8192  # fallback

def get_embedding(text: str) -> list[float]:
    if not text or not text.strip():
        raise ValueError("Text je prázdný")

    try:
        response = openai.embeddings.create(
            input=text.strip(),
            model=EMBED_MODEL
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"❌ Chyba při získávání embeddingu: {e}")
        return []
