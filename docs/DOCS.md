Tento dokument popisuje organizaci a účel jednotlivých součástí projektu pro scraping a zpracování článků z českých zpravodajských webů.

## Přehled struktury

```
beta-testovani-bfcz/
├── .env                    # Konfigurační soubor s API klíči
├── ct24_api_docs.md       # Dokumentace API ČT24
├── processed_data/        # Zpracované články s embeddingy
├── scraping/             # Skripty pro stahování článků
├── scrapnute_clanky/     # Původní nestahované články
├── test/                 # Testovací a experimentální skripty
└── utils/               # Pomocné nástroje
```

## Jednotlivé složky a soubory

### 📁 scraping
**Účel:** Hlavní skripty pro stahování článků z různých zdrojů

- `scrape_ct24.py` - Scraper pro články z ČT24
- `scrape_ctk.py` - Scraper pro články z ČeskéNoviny.cz (ČTK)
- `scrape_demagog.py` - Scraper pro fact-checking články z Demagog.cz
- `scrape_irozhlas.py` - Scraper pro články z iROZHLAS.cz
- `scrape_manipulatori.py` - Scraper pro články z Manipulátoři.cz
- `scrape_refresher.py` - Scraper pro články z Refresher.cz

**Všechny scrapery používají:**
- Knihovnu `trafilatura` pro primární extrakci obsahu
- BeautifulSoup jako fallback metodu
- Realistické User-Agent hlavičky pro obcházení blokování
- Jednotný formát výstupu (JSON s url, title, date, content)

### 📁 scrapnute_clanky
**Účel:** Úložiště původních stažených článků v JSON formátu

Obsahuje články z různých zdrojů:
- `ct24_article_*.json` - Články z ČT24
- `ctk_article_*.json` - Články z ČeskéNoviny.cz
- `demagog_article_*.json` - Články z Demagog.cz
- `irozhlas_article_*.json` - Články z iROZHLAS.cz
- `refresher_article_*.json` - Články z Refresher.cz

**Struktura článku:**
```json
{
  "url": "https://...",
  "title": "Název článku",
  "date": "2025-06-23",
  "content": "Celý text článku..."
}
```

### 📁 processed_data
**Účel:** Zpracované články rozčleněné na chunky s vygenerovanými embeddingy

Například [`refresher_article_5 dovedností, které budou zaměstnavatelé nejvíce v_2025-06-18_processed_20250623-170552.json`](processed_data/refresher_article_5 dovedností, které budou zaměstnavatelé nejvíce v_2025-06-18_processed_20250623-170552.json) obsahuje:

```json
[
  {
    "chunk": "Text části článku...",
    "embedding": [0.123, -0.456, ...], // 1536-rozměrný vektor
    "metadata": {
      "title": "Název článku",
      "url": "https://...",
      "date": "2025-06-18",
      "source": "refresher",
      "chunk_index": 0,
      "chunk_length": 497
    }
  }
]
```

### 📁 test
**Účel:** Experimentální a testovací skripty

- `test_od_gemini.py` - Experimentální scraper pro ČT24 založený na vyhledávání
- `test_pipeline.py` - Testovací pipeline pro zpracování článků
- `get_ct24_sitemap.py` - Pokus o získání článků přes sitemap

### 📄 ct24_api_docs.md
**Účel:** Detailní dokumentace pro použití interního API ČT24

Obsahuje:
- Objev interního API endpointu `https://ct24.ceskatelevize.cz/api/articles`
- Popis parametrů (`tagId`, `page`, `pageSize`)
- Návod na rekonstrukci finálních URL článků
- Kompletní Python skript pro automatické stahování

### 📄 .env
**Účel:** Konfigurační soubor s citlivými daty (API klíče, tokeny)

Není viditelný v ukázkách kódu z bezpečnostních důvodů.

## Workflow projektu

1. **Stahování článků** - Použití scraperů ze složky scraping
2. **Ukládání surových dat** - Články se ukládají do scrapnute_clanky
3. **Zpracování** - Články se rozdělují na chunky a generují se embeddingy
4. **Finální data** - Zpracované články s embeddingy v processed_data

## Technické detaily

### Scraping strategie
- **Primární:** Trafilatura (rychlá, spolehlivá extrakce)
- **Fallback:** BeautifulSoup (když trafilatura selže)
- **Anti-blocking:** Realistické User-Agent hlavičky

### Formáty dat
- **Surové články:** JSON s metadaty a plným textem
- **Zpracované články:** JSON pole chunků s embeddingy
- **Embeddingy:** 1536-rozměrné vektory (pravděpodobně OpenAI)

### Podporované zdroje
1. **ČT24** - Hlavní zpravodajství České televize
2. **ČTK/ČeskéNoviny.cz** - Oficiální tisková agentura
3. **iROZHLAS.cz** - Zpravodajství Českého rozhlasu
4. **Demagog.cz** - Fact-checking platform
5. **Manipulátoři.cz** - Analýza dezinformací
6. **Refresher.cz** - Lifestyle a tech články