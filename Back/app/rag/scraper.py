import os
import json
import time
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from datetime import datetime
import shutil

load_dotenv()
START_URL = os.getenv("SCRAPING_URL")

def scrape_page(url):
    """Scrape une page en extrayant le contenu principal"""
    r = requests.get(url, timeout=10)
    soup = BeautifulSoup(r.text, "html.parser")
    
    # Supprimer les éléments non pertinents
    for tag in soup(["script", "style", "noscript", "nav", "header", "footer", "aside", "iframe"]):
        tag.extract()
    
    # Supprimer les menus et éléments de navigation
    for element in soup.find_all(class_=["menu", "nav", "navigation", "sidebar", "footer"]):
        element.extract()
    
    for element in soup.find_all(id=["menu", "nav", "navigation", "sidebar", "footer"]):
        element.extract()
    
    # Essayer de trouver le contenu principal
    main_content = None
    
    # Chercher dans les balises sémantiques HTML5
    for tag in ['main', 'article']:
        main_content = soup.find(tag)
        if main_content:
            break
    
    # Chercher dans les divs avec des classes courantes pour le contenu
    if not main_content:
        for class_name in ['content', 'main-content', 'post-content', 'entry-content', 'article-content']:
            main_content = soup.find(class_=class_name)
            if main_content:
                break
    
    # Si rien trouvé, prendre le body
    if not main_content:
        main_content = soup.find('body')
    
    if main_content:
        text = main_content.get_text(separator=" ", strip=True)
    else:
        text = soup.get_text(separator=" ", strip=True)
    
    # Nettoyer les espaces multiples
    text = ' '.join(text.split())
    
    return text

def scrape_site_recursive(start_url, max_pages=500, important_urls=None):
    """
    Scrape un site web de manière récursive
    
    Args:
        start_url: URL de départ
        max_pages: Nombre maximum de pages à scraper
        important_urls: Liste d'URLs importantes à scraper en priorité
    """
    domain = start_url.split("/")[2]
    visited = set()
    to_visit = [start_url]
    data = {}
    data_file = "data/scraped_data.json"
    
    # Charger les données existantes si le fichier existe
    if os.path.exists(data_file):
        print(f"Chargement des donnees existantes...")
        with open(data_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        visited = set(data.keys())
        print(f"{len(visited)} URLs deja scrapees")
        
        # Si on a déjà des données, scanner quelques pages pour trouver de nouveaux liens
        if len(visited) > 0 and len(visited) < max_pages:
            print(f"Recherche de nouveaux liens...")
            sample_urls = list(visited)[:20]  # Prendre 20 premières URLs
            for url in sample_urls:
                try:
                    r = requests.get(url, timeout=5)
                    soup = BeautifulSoup(r.text, "html.parser")
                    for a in soup.find_all("a", href=True):
                        href = a["href"]
                        if href.startswith("/"):
                            href = f"https://{domain}{href}"
                        elif not href.startswith("http"):
                            continue
                        if domain in href and href not in visited:
                            to_visit.append(href)
                except:
                    pass
            to_visit = list(set(to_visit))  # Dédupliquer
            print(f"{len(to_visit)} nouvelles URLs trouvees a scraper")
    
    # Ajouter les URLs importantes en premier
    if important_urls:
        for url in important_urls:
            if url not in visited:
                to_visit.insert(0, url)
    
    print(f"Debut du scraping (objectif: {max_pages} pages)...\n")
    
    while to_visit and len(visited) < max_pages:
        url = to_visit.pop(0)
        
        if url in visited:
            continue
            
        visited.add(url)
        
        try:
            print(f"  [{len(visited)}/{max_pages}] {url[:70]}...")
            
            # Scraper la page
            r = requests.get(url, timeout=10)
            soup = BeautifulSoup(r.text, "html.parser")
            
            # Extraire le contenu
            data[url] = scrape_page_from_soup(soup)
            
            # Sauvegarder les données tous les 10 pages
            if len(visited) % 10 == 0:
                print(f"   Sauvegarde...")
                with open(data_file, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
            
            # Trouver les nouveaux liens
            for a in soup.find_all("a", href=True):
                href = a["href"]
                
                # Normaliser l'URL
                if href.startswith("/"):
                    href = f"https://{domain}{href}"
                elif not href.startswith("http"):
                    continue
                
                # Ajouter seulement les liens du même domaine
                if domain in href and href not in visited and href not in to_visit:
                    to_visit.append(href)
            
            time.sleep(0.3)
            
        except Exception as e:
            print(f"   Erreur: {e}")
            continue
    
    return data

def scrape_page_from_soup(soup):
    """Extrait le contenu d'une page à partir d'un objet BeautifulSoup"""
    # Supprimer les éléments non pertinents
    for tag in soup(["script", "style", "noscript", "nav", "header", "footer", "aside", "iframe"]):
        tag.extract()
    
    # Supprimer les menus et éléments de navigation
    for element in soup.find_all(class_=["menu", "nav", "navigation", "sidebar", "footer"]):
        element.extract()
    
    for element in soup.find_all(id=["menu", "nav", "navigation", "sidebar", "footer"]):
        element.extract()
    
    # Essayer de trouver le contenu principal
    main_content = None
    
    # Chercher dans les balises sémantiques HTML5
    for tag in ['main', 'article']:
        main_content = soup.find(tag)
        if main_content:
            break
    
    # Chercher dans les divs avec des classes courantes pour le contenu
    if not main_content:
        for class_name in ['content', 'main-content', 'post-content', 'entry-content', 'article-content']:
            main_content = soup.find(class_=class_name)
            if main_content:
                break
    
    # Si rien trouvé, prendre le body
    if not main_content:
        main_content = soup.find('body')
    
    if main_content:
        text = main_content.get_text(separator=" ", strip=True)
    else:
        text = soup.get_text(separator=" ", strip=True)
    
    # Nettoyer les espaces multiples
    text = ' '.join(text.split())
    
    return text

def scrape_site(start_url, limit=5, important_urls=None):
    """
    Scrape un site web (version simple, nombre limité de pages)
    
    Args:
        start_url: URL de départ
        limit: Nombre maximum de pages à scraper
        important_urls: Liste d'URLs importantes à scraper en priorité
    """
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

    links = list(set(links))
    
    # Ajouter les URLs importantes en priorité
    if important_urls:
        for url in important_urls:
            if url not in links:
                links.insert(0, url)
    
    links = links[:limit]
    data = {}

    for i, link in enumerate(links, 1):
        try:
            print(f"  [{i}/{len(links)}] {link[:70]}...")
            data[link] = scrape_page(link)
            time.sleep(1)
        except Exception as e:
            print(f"   Erreur: {e}")
            pass

    return data

def archive_old_files():
    """Archive les anciens fichiers de scraping avec un timestamp"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archive_folder = f"data/archive_{timestamp}"
    
    files_to_archive = [
        "data/scraped_data.json",
        "data/faiss_index.bin",
        "data/faiss_mapping.json"
    ]
    
    existing_files = [f for f in files_to_archive if os.path.exists(f)]
    
    if existing_files:
        os.makedirs(archive_folder, exist_ok=True)
        print(f"Archivage des anciens fichiers dans {archive_folder}...")
        
        for file_path in existing_files:
            if os.path.exists(file_path):
                filename = os.path.basename(file_path)
                shutil.copy2(file_path, os.path.join(archive_folder, filename))
                print(f"  Archive: {filename}")
        
        print(f"Archivage termine.\n")
    else:
        print("Aucun fichier existant a archiver.\n")

def load_urls_from_file(filepath="data/url.txt"):
    """Charge les URLs depuis un fichier texte"""
    if not os.path.exists(filepath):
        print(f"ERREUR: Le fichier {filepath} n'existe pas.")
        return []
    
    with open(filepath, "r", encoding="utf-8") as f:
        urls = [line.strip() for line in f if line.strip() and not line.startswith("#")]
    
    return urls

def scrape_urls_from_list(urls):
    """Scrape une liste d'URLs spécifiques"""
    data = {}
    total = len(urls)
    
    print(f"Scraping de {total} URLs...\n")
    
    for i, url in enumerate(urls, 1):
        try:
            print(f"  [{i}/{total}] {url[:70]}...")
            data[url] = scrape_page(url)
            time.sleep(0.3)
        except Exception as e:
            print(f"   ERREUR: {e}")
            continue
    
    return data

if __name__ == "__main__":
    # Créer le dossier data s'il n'existe pas
    os.makedirs("data", exist_ok=True)
    
    print("=" * 60)
    print("SCRAPING ESILV - Depuis SCRAPING_URL dans .env")
    print("=" * 60 + "\n")
    
    # Archiver les anciens fichiers
    archive_old_files()
    
    # Utiliser SCRAPING_URL depuis le .env
    if not START_URL:
        print("ERREUR: SCRAPING_URL n'est pas défini dans le fichier .env")
        exit(1)
    
    print(f"Scraping depuis: {START_URL}\n")
    
    # Scraper le site de manière récursive
    data = scrape_site_recursive(START_URL, max_pages=500)
    
    print(f"\n{len(data)} pages scrapees avec succes")
    print(f"Sauvegarde dans data/scraped_data.json...")
    
    with open("data/scraped_data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"Termine!")
