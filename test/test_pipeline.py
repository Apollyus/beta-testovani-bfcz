import json
import sys
import os
import glob
from datetime import datetime

# Add parent directory to Python path so we can import from utils
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.chunking import split_text_smart
from utils.embedding import get_embedding
from pprint import pprint

def save_results_to_json(results, original_path):
    """Uloží výsledky do JSON souboru"""
    # Vytvoříme adresář pro výstup, pokud neexistuje
    output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'processed_data'))
    os.makedirs(output_dir, exist_ok=True)
    
    # Vytvoříme název výstupního souboru
    base_name = os.path.basename(original_path)
    filename_without_ext = os.path.splitext(base_name)[0]
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    output_file = os.path.join(output_dir, f"{filename_without_ext}_processed_{timestamp}.json")
    
    # Uložíme výsledky do JSON souboru
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Výsledky uloženy do: {output_file}")
    return output_file

def process_article_json(json_path: str):
    with open(json_path, encoding="utf-8") as f:
        article = json.load(f)

    title = article.get("title", "bez titulku")
    content = article.get("content", "")
    url = article.get("url", "")
    date = article.get("date", "")
    # Try to determine source from filename
    source = article.get("source", "unknown")
    if source == "unknown" and "_article_" in json_path:
        source_prefix = os.path.basename(json_path).split("_article_")[0]
        if source_prefix:
            source = source_prefix

    if not content:
        print("⚠️ Článek neobsahuje obsah (content).")
        return

    print(f"🔎 Zpracovávám článek: {title}")
    chunks = split_text_smart(content)

    print(f"🧩 Vygenerováno {len(chunks)} chunků.")

    results = []
    for i, chunk in enumerate(chunks):
        embedding = get_embedding(chunk)
        meta = {
            "title": title,
            "url": url,
            "date": date,
            "source": source,
            "chunk_index": i,
            "chunk_length": len(chunk),
        }
        results.append({
            "chunk": chunk,
            "embedding": embedding,
            "metadata": meta
        })

    print("📊 Ukázka prvních 2 chunků:")
    pprint(results[:2])
    
    # Uložíme výsledky
    output_file = save_results_to_json(results, json_path)
    return output_file

def find_similar_file(partial_path):
    """Pokusí se najít podobný soubor, pokud přesný název není nalezen"""
    directory = os.path.dirname(partial_path)
    filename = os.path.basename(partial_path)
    
    # Vytvoříme vzor pro hledání - zachováme první část názvu před '_article_'
    if "_article_" in filename:
        prefix = filename.split("_article_")[0]
        pattern = os.path.join(directory, f"{prefix}_article_*.json")
        
        # Najdeme všechny soubory odpovídající vzoru
        matching_files = glob.glob(pattern)
        if matching_files:
            return matching_files[0]  # Vrátíme první odpovídající soubor
    
    return None

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Použití: python test_pipeline.py \"cesta/k/clanku.json\"")
        sys.exit(1)
        
    # Pokud je více argumentů, spojíme je - to řeší problém s mezerami v názvu souboru
    if len(sys.argv) > 2:
        json_path = ' '.join(sys.argv[1:])
    else:
        json_path = sys.argv[1]
        
    # Zkontrolujeme, zda soubor existuje
    if not os.path.exists(json_path):
        print(f"⚠️ Soubor nenalezen: {json_path}")
        
        # Pokusíme se najít podobný soubor
        similar_file = find_similar_file(json_path)
        if similar_file:
            print(f"✅ Nalezen podobný soubor: {similar_file}")
            json_path = similar_file
        else:
            # Další pokus - zkusíme odstranit diakritiku
            try:
                import unicodedata
                simplified_path = ''.join(c for c in unicodedata.normalize('NFD', json_path) 
                                         if unicodedata.category(c) != 'Mn')
                if os.path.exists(simplified_path):
                    print(f"✅ Nalezen soubor bez diakritiky: {simplified_path}")
                    json_path = simplified_path
                else:
                    sys.exit(1)
            except:
                sys.exit(1)
    
    process_article_json(json_path)