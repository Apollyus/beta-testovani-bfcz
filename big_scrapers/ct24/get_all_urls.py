# ct24_scraper_v9_final_accurate_stats.py
import requests
import time
import os
import json
import logging
import sys

# --- KONFIGURACE ---
TAG_ID_RANGE = range(1, 50000)

# Názvy souborů
STATE_FILE = "VYSTUP_state.json"
URL_OUTPUT_FILE = "VYSTUP_ct24_urls.txt"
STATS_FILE = "VYSTUP_category_stats.json"
REPORT_FILE = "VYSTUP_rubriky_report.txt"
LOG_FILE = "VYSTUP_scraper.log"

# Parametry API
API_ENDPOINT = "https://ct24.ceskatelevize.cz/api/articles"
BASE_ARTICLE_URL = "https://ct24.ceskatelevize.cz/clanek"
PAGE_SIZE = 24
REQUEST_TIMEOUT = 30
SLEEP_BETWEEN_REQUESTS = 1.0
SLEEP_ON_ERROR = 15

# --- NASTAVENÍ LOGOVÁNÍ ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler(LOG_FILE, encoding='utf-8'), logging.StreamHandler()]
)

# --- POMOCNÉ FUNKCE ---
def load_state():
    try:
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        logging.info(f"Stavový soubor '{STATE_FILE}' nenalezen, vytvářím nový.")
        return {"current_tag_in_progress": None, "next_page": 1, "completed_tags": []}

def save_state(state):
    with open(STATE_FILE, 'w') as f: json.dump(state, f, indent=4)

def load_existing_urls():
    if not os.path.exists(URL_OUTPUT_FILE): return set()
    with open(URL_OUTPUT_FILE, 'r', encoding='utf-8') as f:
        return {line.strip() for line in f}

def build_article_url(article_data):
    try:
        return f"{BASE_ARTICLE_URL}/{article_data['mainSection']['path']}/{article_data['slug']}-{article_data['id']}"
    except (KeyError, TypeError):
        return None

# --- FUNKCE PRO STATISTIKY (UPRAVENÉ) ---
def load_category_stats():
    if not os.path.exists(STATS_FILE): return {}
    try:
        with open(STATS_FILE, 'r', encoding='utf-8') as f: return json.load(f)
    except json.JSONDecodeError:
        logging.error(f"Soubor '{STATS_FILE}' je poškozen. Vytvářím nový.")
        return {}

def save_category_stats(stats):
    with open(STATS_FILE, 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=4, ensure_ascii=False)

def generate_final_report(stats):
    logging.info("Generuji finální report...")
    if not stats:
        logging.warning("Nebyly nalezeny žádné statistiky k vygenerování reportu.")
        return
        
    sorted_stats = sorted(stats.items(), key=lambda item: item[1]['count'], reverse=True)
    
    with open(REPORT_FILE, 'w', encoding='utf-8') as f:
        f.write("Přehled rubrik a počtu článků na ČT24\n")
        f.write("Seřazeno podle počtu článků\n")
        f.write("=" * 40 + "\n\n")
        total_articles = sum(data['count'] for data in stats.values())
        f.write(f"CELKEM ZPRACOVANÝCH ČLÁNKŮ: {total_articles}\n\n")

        for category_path, data in sorted_stats:
            # Pro hezčí výpis uděláme první písmeno velké
            category_name = category_path.capitalize()
            f.write(f"{category_name}: {data['count']} článků (nalezeno pod tagy: {sorted(data['associated_tags'])})\n")
            
    logging.info(f"Finální report byl uložen do souboru: {REPORT_FILE}")

# --- HLAVNÍ SKRIPT ---
def main():
    logging.info("="*50 + "\nSpouštím skript V9 s přesným počítáním statistik\n" + "="*50)

    state = load_state()
    all_urls = load_existing_urls()
    stats = load_category_stats()

    start_id = 1
    if state.get("current_tag_in_progress"):
        start_id = state["current_tag_in_progress"]
    elif state["completed_tags"]:
        start_id = max(state["completed_tags"]) + 1

    logging.info(f"Budu pokračovat od tagId: {start_id}")

    for tag_id in range(start_id, TAG_ID_RANGE.stop):
        if tag_id in state["completed_tags"]:
            continue
            
        sys.stdout.write(f"\rProhledávám tagId: {tag_id}...")
        sys.stdout.flush()

        page = state["next_page"] if state["current_tag_in_progress"] == tag_id else 1
        
        while True:
            params = {'tagId': tag_id, 'page': page, 'pageSize': PAGE_SIZE}
            try:
                response = requests.get(API_ENDPOINT, params=params, timeout=REQUEST_TIMEOUT)
                response.raise_for_status()
                json_data = response.json()
                articles = json_data.get('data', {}).get('articles', [])

                if not articles:
                    if page == 1: logging.debug(f"TagId {tag_id} je prázdný.")
                    else: logging.info(f"\nTagId {tag_id}: Konec článků.")
                    break

                if page == 1:
                    sys.stdout.write("\r" + " "*50 + "\r")
                    logging.info(f"Nalezeny články pod tagId: {tag_id}. Zpracovávám od stránky {page}...")

                # --- ZÁSADNÍ ZMĚNA LOGIKY POČÍTÁNÍ ---
                for article in articles:
                    # Sestavení URL a uložení (pokud je nová)
                    url = build_article_url(article)
                    if url and url not in all_urls:
                        all_urls.add(url)
                        with open(URL_OUTPUT_FILE, 'a', encoding='utf-8') as f: f.write(url + "\n")

                    # Zjištění SKUTEČNÉ rubriky a aktualizace statistik
                    try:
                        category_path = article['mainSection']['path']
                        # Inicializace statistiky pro novou rubriku
                        if category_path not in stats:
                            stats[category_path] = {"count": 0, "associated_tags": []}
                        
                        # Přičtení článku do správné rubriky
                        stats[category_path]["count"] += 1
                        # Zaznamenání, pod kterým tagId jsme tuto rubriku našli
                        if tag_id not in stats[category_path]["associated_tags"]:
                            stats[category_path]["associated_tags"].append(tag_id)

                    except (KeyError, TypeError):
                        logging.warning(f"Článek s id {article.get('id')} nemá platnou strukturu pro určení rubriky.")

                logging.info(f"TagId {tag_id}, Stránka {page}: Zpracováno {len(articles)} článků.")
                
                # Uložení stavu a statistik po každé stránce
                save_category_stats(stats)
                state["current_tag_in_progress"] = tag_id
                state["next_page"] = page + 1
                save_state(state)
                
                page += 1
                time.sleep(SLEEP_BETWEEN_REQUESTS)

            except requests.exceptions.RequestException as e:
                logging.error(f"\nCHYBA (ID: {tag_id}, str: {page}): {e}. Zkouším znovu za {SLEEP_ON_ERROR}s.")
                time.sleep(SLEEP_ON_ERROR)
            except json.JSONDecodeError:
                logging.error(f"\nCHYBA JSON (ID: {tag_id}, str: {page}). Přeskakuji zbytek rubriky.")
                break
        
        # Aktualizace finálního stavu po dokončení celého tagu
        if page > 1: # Pokud jsme zpracovali alespoň jednu stránku
            if tag_id not in state["completed_tags"]:
                state["completed_tags"].append(tag_id)
        
        state["current_tag_in_progress"] = None
        state["next_page"] = 1
        save_state(state)

    logging.info("\n" + "="*50)
    logging.info("Hotovo! Všechny tagy v rozsahu byly zkontrolovány.")
    generate_final_report(stats)
    logging.info("="*50)


if __name__ == "__main__":
    main()