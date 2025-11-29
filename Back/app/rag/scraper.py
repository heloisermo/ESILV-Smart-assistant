import os
import json
import time
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()
START_URL = os.getenv("SCRAPING_URL")

def scrape_page(url):
    r = requests.get(url, timeout=10)
    soup = BeautifulSoup(r.text, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.extract()
    return soup.get_text(separator=" ", strip=True)

def scrape_site(start_url, limit=5):
    r = requests.get(start_url)
    soup = BeautifulSoup(r.text, "html.parser")

    domain = start_url.split("/")[2]
    links = []

    for a in soup.find_all("a", href=True):
        href = a["href"]
        if href.startswith("/") or domain in href:
            if href.startswith("/"):
                href = f"https://{domain}{href}"
            links.append(href)

    links = list(set(links))[:limit]
    data = {}

    for link in links:
        try:
            data[link] = scrape_page(link)
            time.sleep(1)
        except:
            pass

    return data

if __name__ == "__main__":
    # Créer le dossier data s'il n'existe pas
    os.makedirs("data", exist_ok=True)
    
    print(f"Scraping de {START_URL}")
    print(f"Cela peut prendre plusieurs minutes...\n")
    
    # Scraper tout le site (limite augmentée)
    data = scrape_site(START_URL, limit=100)
    
    print(f"\n{len(data)} pages scrapées")
    print(f"Sauvegarde dans data/scraped_data.json...")
    
    with open("data/scraped_data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"Terminé!")
