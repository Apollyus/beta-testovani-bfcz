# Toto je projekt na testování pro projekt Bezfejku.cz
Pro vylepšení přesnosti projektu chci získat lepší data a dostat lepší informace. No a abych to mohl implementovat tak to potřebuju někde zkoušet - tady. Hlavní logika projektu je v jiném GH repository. 

## Co tady je?
- Scrapovací skripty pro několik zdrojů ze kterých bude nová verze aplikace vycházet.
- Testovací skripty pro dosažení scrapovaní
- Skripty pro převod textu na embeddings
- Trochu těch DOCS

## Co je potřeba pro zprovoznění?
- Python (já zde používám 3.12.3)
- Nainstalovaný requirements.txt
- API klíče (OpenAI, QDrant)
- Zbytek věcí v .env.example

## Jaké weby jak?
- ČT24 - pouziti jejich neverejne api na ziskani a poskladani vsech odkazu na scraping
- iRozhlas - jejich archiv vsech clanku (od roku 2000 po soucasnost, mely by tam byt vsechny clanky) [https://www.irozhlas.cz/zpravy-archiv/2000-10-02]