import os
from dotenv import load_dotenv
import openai
from typing import List

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
LLM_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")

# 🧱 Heuristické rozdělení po 2 odstavcích s překryvem
def split_text_heuristically(text: str, chunk_size: int = 2, overlap: float = 0.3) -> List[str]:
    paragraphs = [p.strip() for p in text.split("\n") if p.strip()]
    if not paragraphs:
        return []

    step = max(1, int(chunk_size * (1 - overlap)))
    chunks = []

    for i in range(0, len(paragraphs), step):
        chunk = "\n".join(paragraphs[i:i + chunk_size])
        if chunk:
            chunks.append(chunk.strip())

    return chunks

# 🤖 Pokud chunk vypadá podezřele, pošleme ho do LLM pro lepší rozdělení
def llm_refine_chunk(text: str) -> List[str]:
    prompt = f"""
Rozděl následující text na kratší ucelené bloky (chunky) tak, aby každý obsahoval logicky propojené informace. Každý blok může obsahovat 1–3 odstavce. Přidej 1–2 věty překryvu mezi bloky, pokud je to vhodné.

Vrať pouze seznam chunků jako JSON pole řetězců.

Text:
{text.strip()}
"""
    try:
        response = openai.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.4
        )
        raw_output = response.choices[0].message.content.strip()
        chunks = eval(raw_output)  # quick & dirty – můžeš nahradit json.loads pokud výstup bude JSON string
        if isinstance(chunks, list) and all(isinstance(c, str) for c in chunks):
            return chunks
    except Exception as e:
        print(f"❌ LLM refine error: {e}")
    return [text.strip()]

# 🔀 Kombinace obou přístupů
def split_text_smart(text: str, chunk_size: int = 2, overlap: float = 0.3) -> List[str]:
    initial_chunks = split_text_heuristically(text, chunk_size, overlap)
    final_chunks = []

    for chunk in initial_chunks:
        num_lines = chunk.count("\n")
        length = len(chunk)

        # Podezřelé chunk-y: příliš dlouhé, příliš krátké nebo bez odstavců
        if length > 1800 or length < 200 or num_lines < 1:
            print("⚠️ Refining chunk pomocí LLM...")
            refined = llm_refine_chunk(chunk)
            final_chunks.extend(refined)
        else:
            final_chunks.append(chunk)

    return final_chunks
