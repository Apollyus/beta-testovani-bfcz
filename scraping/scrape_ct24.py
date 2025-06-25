import requests
from bs4 import BeautifulSoup
import sys
import json
import trafilatura
import re
from datetime import datetime

def scrape_ct24_article(url: str) -> dict:
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; FakeNewsScraper/1.0; +https://bezfejku.cz)"
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
    except Exception as e:
        print(f"Chyba při načítání článku: {e}")
        return {}

    # ✅ Nejprve se pokusíme použít trafilatura
    extracted = trafilatura.extract(response.text, include_comments=False, include_tables=False)
    metadata = trafilatura.extract_metadata(response.text)

    if extracted:
        return {
            "url": url,
            "title": metadata.title if metadata and metadata.title else "Neznámý titulek",
            "date": metadata.date if metadata and metadata.date else "Neznámé datum",
            "content": extracted
        }

    # ❌ Pokud trafilatura selže, použijeme fallback přes BeautifulSoup
    print("⚠️ Trafilatura selhala, přecházím na fallback pomocí BeautifulSoup...")

    try:
        soup = BeautifulSoup(response.text, "lxml")
    except:
        soup = BeautifulSoup(response.text, "html.parser")

    title_tag = soup.find("h1")
    title = title_tag.text.strip() if title_tag else "Neznámý titulek"

    date_tag = soup.find("time")
    date = date_tag["datetime"] if date_tag and "datetime" in date_tag.attrs else "Neznámé datum"

    paragraphs = soup.select("div.article__body > p")
    content = "\n".join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))

    return {
        "url": url,
        "title": title,
        "date": date,
        "content": content
    }

if __name__ == "__main__":
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        url = input("Zadejte URL článku ČT24: ")

    if not url.startswith("https://ct24.ceskatelevize.cz"):
        print("CHYBA: URL musí být z domény ct24.ceskatelevize.cz")
        sys.exit(1)

    print(f"Stahuji článek z: {url}")
    article_data = scrape_ct24_article(url)

    if article_data and article_data.get("content"):
        print("\n" + "="*50)
        print(f"TITULEK: {article_data['title']}")
        print(f"DATUM: {article_data['date']}")
        print("="*50)
        print("\nOBSAH:")
        print(article_data['content'][:500] + "..." if len(article_data['content']) > 500 else article_data['content'])
        print("\n" + "="*50)

        # Better date handling for filename
        date_str = article_data['date']
        if date_str and date_str != "Neznámé datum":
            # Try to extract a date format that works as a filename
            # Remove any characters that aren't allowed in filenames
            safe_date = re.sub(r'[^0-9-]', '_', date_str)
            if len(safe_date) > 5:  # Ensure we have something meaningful
                filename = f"ct24_article_{article_data['title']}_{safe_date}.json"
            else:
                filename = f"ct24_article_{article_data['title']}_{datetime.now().strftime('%Y-%m-%d')}.json"
        else:
            filename = f"ct24_article_{article_data['title']}_{datetime.now().strftime('%Y-%m-%d')}.json"
            
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(article_data, f, ensure_ascii=False, indent=2)
        print(f"\nData byla uložena do souboru: {filename}")
    else:
        print("Nepodařilo se získat obsah článku.")