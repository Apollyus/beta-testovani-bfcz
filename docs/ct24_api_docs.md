# Návod: Jak stáhnout kompletní seznam URL článků z ČT24

Tento dokument popisuje spolehlivou metodu pro získání seznamu všech URL článků z webu `ct24.ceskatelevize.cz`. Standardní metody jako analýza `sitemap.xml` nebo přímý scraping vyhledávání selhávají kvůli sofistikované obraně serveru.

Klíčem k úspěchu je využití interního API, které web používá pro dynamické donačítání obsahu v jednotlivých rubrikách.

## 1. Klíčový objev: Interní API endpoint

Web `ct24.ceskatelevize.cz` pro donačítání článků v rubrikách používá následující API endpoint:

```
https://ct24.ceskatelevize.cz/api/articles
```

Tento endpoint vrací data ve formátu JSON a jeho chování se ovládá pomocí parametrů v URL.

### Parametry API

*   `tagId={číslo}`: **Povinný parametr.** Identifikuje konkrétní téma nebo rubriku (např. `1030` může být "Doprava"). Pro získání všech článků je nutné iterovat přes seznam všech existujících `tagId`.
*   `page={číslo}`: **Stránkování.** Určuje, kolikátou stránku výsledků chceme načíst. Začíná se od `1`.
*   `pageSize={číslo}`: **Stránkování.** Určuje počet článků na jedné stránce. Hodnota `24` je bezpečná a ověřená volba.

**Příklad kompletní URL na API:**
Chceme načíst 4. stránku článků z rubriky s ID `1030`, 24 článků na stránku:
`https://ct24.ceskatelevize.cz/api/articles?tagId=1030&page=4&pageSize=24`

## 2. Rekonstrukce finální URL článku

API nevrací přímo hotovou URL článku. Tu je nutné složit z několika částí, které jsou obsaženy v JSON odpovědi pro každý článek.

### Struktura odpovědi (zjednodušeně)

Každý článek v JSON odpovědi vypadá přibližně takto:

```json
{
  "id": 351518,
  "slug": "za-pokuty-kvuli-predjizdeni-letos-kamionaci-dali-skoro-20-milionu",
  "mainSection": {
    "path": "domaci"
  }
  // ... další data
}
```

### Postup složení URL

Finální URL se skládá ze 4 částí v tomto pořadí:

1.  **Základní adresa:** `https://ct24.ceskatelevize.cz/clanek/`
2.  **Cesta rubriky (path):** Získáme z `mainSection.path`. V našem příkladu: `domaci`
3.  **Slug článku (slug):** Získáme z pole `slug`. V našem příkladu: `za-pokuty-kvuli-predjizdeni-letos-kamionaci-dali-skoro-20-milionu`
4.  **ID článku (id):** Získáme z pole `id`. V našem příkladu: `351518`

**Výsledná struktura:** `{základ}/{path}/{slug}-{id}`

**Příklad složené URL:**
`https://ct24.ceskatelevize.cz/clanek/domaci/za-pokuty-kvuli-predjizdeni-letos-kamionaci-dali-skoro-20-milionu-351518`

## 3. Finální skript v Pythonu

Následující skript automatizuje celý proces. Iteruje přes zadaný seznam `tagId`, pro každé ID prochází všechny stránky až do konce a skládá finální URL, které ukládá do textového souboru.

*DISCLAIMER - SKRIPT JSEM NETESTOVAL, JE TO Z AI!*

```python
import requests
import time
import os

# --- KONFIGURACE ---

# Zde je potřeba doplnit seznam ID všech témat, která chcete stáhnout.
# Tento seznam lze získat ručním procházením webu a sledováním URL
# nebo síťové komunikace v jednotlivých rubrikách.
TAG_IDS = [
    1030,  # Příklad: Doprava
    1001,  # Příklad: Domácí
    1002,  # Příklad: Svět
    1006,  # Příklad: Ekonomika
    # ... doplňte další ID
]

API_ENDPOINT = "https://ct24.ceskatelevize.cz/api/articles"
BASE_ARTICLE_URL = "https://ct24.ceskatelevize.cz/clanek"
PAGE_SIZE = 24  # Osvědčený počet článků na stránku
OUTPUT_FILE = "ct24_urls.txt"

# --- HLAVNÍ SKRIPT ---

def build_article_url(article_data):
    """Sestaví finální URL z JSON dat jednoho článku."""
    try:
        article_id = article_data['id']
        slug = article_data['slug']
        path = article_data['mainSection']['path']
        return f"{BASE_ARTICLE_URL}/{path}/{slug}-{article_id}"
    except (KeyError, TypeError):
        # Pokud v datech chybí potřebný klíč, vrátíme None
        return None

def main():
    """Hlavní funkce pro stažení všech URL."""
    print("Spouštím stahování URL článků z ČT24...")
    
    # Používáme `set` pro automatické odstranění případných duplicit
    all_urls = set()

    # Iterujeme přes všechna zadaná ID témat
    for tag_id in TAG_IDS:
        print(f"\n--- Zpracovávám téma s tagId: {tag_id} ---")
        page = 1
        
        # Smyčka pro stránkování v rámci jednoho tématu
        while True:
            params = {
                'tagId': tag_id,
                'page': page,
                'pageSize': PAGE_SIZE
            }
            
            try:
                response = requests.get(API_ENDPOINT, params=params, timeout=20)
                response.raise_for_status()  # Vyvolá chybu pro status kódy 4xx/5xx
                
                data = response.json()
                articles = data.get('articles', [])
                
                # Pokud API vrátí prázdný seznam článků, jsme na konci tohoto tématu
                if not articles:
                    print(f"Stránka {page}: Žádné další články. Konec tématu.")
                    break
                
                print(f"Stránka {page}: Nalezeno {len(articles)} článků.")
                
                # Zpracujeme všechny články na stránce
                for article_data in articles:
                    url = build_article_url(article_data)
                    if url:
                        all_urls.add(url)
                
                page += 1
                time.sleep(1.0)  # Slušná prodleva mezi dotazy

            except requests.exceptions.RequestException as e:
                print(f"CHYBA při stahování stránky {page}: {e}. Zkouším znovu za 10s.")
                time.sleep(10)
            except ValueError: # Chyba při parsování JSONu
                print(f"CHYBA: Neplatná JSON odpověď na stránce {page}. Přeskakuji.")
                break

    # Uložení výsledků do souboru
    print(f"\nCelkem nalezeno {len(all_urls)} unikátních URL.")
    print(f"Ukládám seznam do souboru: {OUTPUT_FILE}")
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        for url in sorted(list(all_urls)):
            f.write(url + "\n")
            
    print("\nHotovo!")

if __name__ == "__main__":
    main()

```

### Jak skript použít

1.  Uložte kód výše jako soubor, například `scraper.py`.
2.  Ujistěte se, že máte nainstalovanou knihovnu `requests`: `pip install requests`
3.  **Doplňte seznam `TAG_IDS`** o všechna ID rubrik, která chcete zpracovat.
4.  Spusťte skript z příkazové řádky: `python scraper.py`
5.  Po dokončení skriptu naleznete všechny unikátní URL v souboru `ct24_urls.txt`.