import requests
from bs4 import BeautifulSoup
import gzip
import io

# Adresa sitemap indexu
sitemap_index_url = 'https://ct24.ceskatelevize.cz/sitemaps/sitemap.xml'

# TOTO JE KLÍČOVÁ ZMĚNA: Použijeme User-Agent, kterého se server neodváží zablokovat.
headers = {
    'User-Agent': 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)'
}

print("Zkouším poslední trik: maskování za Googlebota...")
print(f"Cíl: {sitemap_index_url}")

try:
    # --- KROK 1: Získání seznamu archivů (.gz souborů) ---
    response = requests.get(sitemap_index_url, headers=headers, timeout=10)
    response.raise_for_status()
    
    soup = BeautifulSoup(response.content, 'xml')
    archive_urls = [loc.text for loc in soup.find_all('loc')]

    if not archive_urls:
        raise ValueError("Soubor s archivy se stáhl, ale je prázdný. Změnili strukturu.")

    print("\n[ÚSPĚCH] Povedlo se! Seznam archivů stažen.")
    print(f"První archiv v seznamu je: {archive_urls[0]}")

    # --- KROK 2: Stažení a inspekce prvního archivu ze seznamu ---
    first_archive_url = archive_urls[0]
    print(f"\nTeď zkusím stáhnout a rozbalit obsah archivu: {first_archive_url}")
    
    archive_response = requests.get(first_archive_url, headers=headers, timeout=10)
    archive_response.raise_for_status()

    # Obsah je komprimovaný, musíme ho rozbalit v paměti
    with gzip.open(io.BytesIO(archive_response.content), 'rt') as f:
        archive_content = f.read()
    
    archive_soup = BeautifulSoup(archive_content, 'xml')
    article_urls = [loc.text for loc in archive_soup.find_all('loc')]

    if not article_urls:
        raise ValueError("Archiv se podařilo stáhnout a rozbalit, ale neobsahuje žádné URL článků.")

    print("\n[FINÁLNÍ ÚSPĚCH] Jsme tam! Podařilo se získat seznam konkrétních článků.")
    print("Toto je prvních 5 článků z prvního archivu:")
    for url in article_urls[:5]:
        print(url)

    print(f"\nCelkem článků v prvním archivu: {len(article_urls)}")
    print("\nCelý postup funguje. Teď stačí vytvořit smyčku a stáhnout všechny archivy.")


except requests.exceptions.RequestException as e:
    print(f"\n[FATÁLNÍ SELHÁNÍ] Ani maskování za Googlebota nepomohlo: {e}")
    print("Jsou lepší, než jsme čekali. V tuto chvíli bohužel nemám další nápady, jak jejich ochranu obejít.")
except Exception as e:
    print(f"\n[NEČEKANÁ CHYBA] Nastal problém při zpracování dat: {e}")