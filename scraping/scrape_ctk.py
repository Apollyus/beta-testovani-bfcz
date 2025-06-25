import requests
from bs4 import BeautifulSoup
import sys
import json
import trafilatura
import re
from datetime import datetime

def scrape_ctk_article(url: str) -> dict:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        )
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
    except Exception as e:
        print(f"Chyba při načítání článku: {e}")
        return {}

    # ✅ Pokus o extrakci pomocí Trafilatura
    extracted = trafilatura.extract(response.text, include_comments=False, include_tables=False)
    metadata = trafilatura.extract_metadata(response.text)

    if extracted:
        return {
            "url": url,
            "title": metadata.title if metadata and metadata.title else "Neznámý titulek",
            "date": metadata.date if metadata and metadata.date else "Neznámé datum",
            "content": extracted
        }

    # ❌ Fallback: BeautifulSoup
    print("⚠️ Trafilatura selhala, přecházím na fallback pomocí BeautifulSoup...")

    try:
        soup = BeautifulSoup(response.text, "lxml")
    except:
        soup = BeautifulSoup(response.text, "html.parser")

    title_tag = soup.find("h1", class_="title")
    title = title_tag.text.strip() if title_tag else "Neznámý titulek"

    # Získání data z metadat nebo z <div class="date">
    date_tag = soup.find("meta", {"property": "article:published_time"})
    if date_tag and date_tag.has_attr("content"):
        date = date_tag["content"]
    else:
        date_div = soup.find("div", class_="date")
        date = date_div.get_text(strip=True) if date_div else "Neznámé datum"

    # Obsah článku
    article_div = soup.find("div", class_="article")
    if article_div:
        paragraphs = article_div.find_all("p")
        content = "\n".join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))
    else:
        content = ""

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
        url = input("Zadejte URL článku z ceskenoviny.cz (ČTK): ")

    if not url.startswith("https://www.ceskenoviny.cz"):
        print("CHYBA: URL musí být z domény www.ceskenoviny.cz")
        sys.exit(1)

    print(f"Stahuji článek z: {url}")
    article_data = scrape_ctk_article(url)

    if article_data and article_data.get("content"):
        print("\n" + "="*50)
        print(f"TITULEK: {article_data['title']}")
        print(f"DATUM: {article_data['date']}")
        print("="*50)
        print("\nOBSAH:")
        print(article_data['content'][:500] + "..." if len(article_data['content']) > 500 else article_data['content'])
        print("\n" + "="*50)

        # Uložení do souboru
        safe_title = re.sub(r'[\\/*?:"<>|]', '_', article_data['title'])[:50]
        safe_date = re.sub(r'[^0-9-]', '_', article_data['date']) if article_data['date'] != "Neznámé datum" else datetime.now().strftime('%Y-%m-%d')
        filename = f"ctk_article_{safe_title}_{safe_date}.json"

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(article_data, f, ensure_ascii=False, indent=2)
        print(f"\nData byla uložena do souboru: {filename}")
    else:
        print("Nepodařilo se získat obsah článku.")
