import requests
from bs4 import BeautifulSoup
from datetime import date, timedelta
import time
import os

# Adresa, na kterou budeme posílat požadavky
SEARCH_URL = "https://ct24.ceskatelevize.cz/hledat"
# Soubor pro ukládání URL
URL_FILE = "ct24_urls.txt"

# Vytvoříme si Session objekt
session = requests.Session()
# Nastavíme se tak, abychom vypadali jako reálný prohlížeč
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
})

# Funkce pro získání odkazů z jedné stránky výsledků
def get_links_from_page(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    links = []
    # Tato třída se zdá být správná pro odkazy na články
    for link_tag in soup.find_all('a', class_='stretched-link'):
        if link_tag.has_attr('href'):
            # Uložíme plnou URL
            full_url = "https://ct24.ceskatelevize.cz" + link_tag['href']
            links.append(full_url)
    # Zjistíme, jestli je na stránce tlačítko "Následující"
    next_button = soup.find('a', class_='page-link', string='Následující')
    has_next_page = next_button is not None
    return links, has_next_page

# ---- Hlavní logika skriptu ----

# Nejprve navštívíme stránku, abychom dostali cookies
print("Inicializuji session...")
session.get(SEARCH_URL)
time.sleep(1)

# Nastavíme rozsah dat
start_date = date(2005, 5, 2)
end_date = date.today()
current_date = start_date

# Hlavní smyčka pro procházení dní
while current_date <= end_date:
    date_str = current_date.strftime("%d.%m.%Y")
    print(f"Zpracovávám datum: {date_str}")
    
    page_num = 1
    while True:
        params = {'q': '', 'from': date_str, 'to': date_str, 'page': page_num}
        
        try:
            response = session.get(SEARCH_URL, params=params, timeout=10)
            if not response.ok:
                print(f"  Chyba {response.status_code} na stránce {page_num}. Přeskakuji.")
                break

            links, has_next_page = get_links_from_page(response.text)
            
            if not links and page_num == 1:
                print("  Žádné články tento den.")
                break # Přejdeme na další den

            # Uložíme nalezené linky do souboru
            with open(URL_FILE, 'a') as f:
                for link in links:
                    f.write(link + "\n")
            
            print(f"  Stránka {page_num}: nalezeno {len(links)} odkazů.")

            if not has_next_page:
                print("  Konec stránkování pro tento den.")
                break # Konec vnitřní smyčky, jdeme na další den
            
            page_num += 1
            time.sleep(1.5) # Důležitá prodleva!

        except requests.RequestException as e:
            print(f"  Nastala chyba při stahování: {e}. Zkusím to znovu za 10s.")
            time.sleep(10)
            continue

    # Posun na další den
    current_date += timedelta(days=1)

print("Hotovo! Všechny nalezené URL jsou v souboru ct24_urls.txt")