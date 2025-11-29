"""
Script principal pour indexer les documents d'un site web
"""
import logging
from scraper import WebScraper
from indexer import DocumentIndexer

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Pipeline complet de scraping et indexation"""
    
    logger.info("=== Démarrage du système d'indexation ===")
    
    # 1. Scraper le site web
    logger.info("\n--- Étape 1: Scraping du site web ---")
    scraper = WebScraper()
    
    # Vous pouvez ajuster ces paramètres selon vos besoins
    scraped_docs = scraper.scrape_recursive(
        max_pages=20,    # Nombre maximum de pages à scraper
        max_depth=2      # Profondeur maximale de navigation
    )
    
    if not scraped_docs:
        logger.error("Aucun document scrapé. Vérifiez l'URL dans .env")
        return
    
    logger.info(f"✓ {len(scraped_docs)} documents scrapés avec succès")
    
    # 2. Indexer les documents
    logger.info("\n--- Étape 2: Indexation des documents ---")
    indexer = DocumentIndexer()
    vectorstore = indexer.index_from_scraped_data(scraped_docs)
    
    if vectorstore:
        logger.info("✓ Indexation terminée avec succès")
    else:
        logger.error("✗ Échec de l'indexation")
        return
    
    # 3. Test de recherche
    logger.info("\n--- Étape 3: Test de recherche ---")
    test_query = "Quelle est l'information principale ?"
    results = indexer.search(test_query, k=3)
    
    logger.info(f"Résultats pour la requête: '{test_query}'")
    for i, doc in enumerate(results, 1):
        logger.info(f"\n{i}. {doc.metadata.get('title', 'Sans titre')}")
        logger.info(f"   Source: {doc.metadata.get('source', 'Inconnue')}")
        logger.info(f"   Aperçu: {doc.page_content[:150]}...")
    
    logger.info("\n=== Indexation terminée ===")
    logger.info(f"Base de données sauvegardée dans: {indexer.persist_directory}")


if __name__ == "__main__":
    main()
