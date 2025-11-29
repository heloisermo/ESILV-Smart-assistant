# ESILV Smart Assistant

Assistant intelligent pour l'ESILV utilisant le scraping web et la recherche vectorielle (RAG).

## Installation et première utilisation

### 1. Installer les dépendances

```bash
pip install -r requirements.txt
```

### 2. Configuration de l'environnement

Créer un fichier `.env` dans le dossier `Back/app/rag/` avec l'URL à scraper :

```env
SCRAPING_URL=https://www.esilv.fr/
```

### 3. Scraper le site (première fois)

```bash
cd Back/app/rag
python scraper.py
```

Cette commande va :
- Scraper jusqu'à 100 pages du site
- Sauvegarder les données dans `data/scraped_data.json`
- Prendre environ 2-3 minutes

### 4. Indexer les données (première fois)

```bash
python indexer.py
```

Cette commande va :
- Créer les embeddings vectoriels
- Générer l'index FAISS dans `data/faiss_index.bin`
- Sauvegarder le mapping dans `data/faiss_mapping.json`

## Structure des fichiers

```
ESILV-Smart-assistant/
├── Back/
│   └── app/
│       └── rag/
│           ├── data/              # Dossier des données générées (ignoré par git)
│           │   ├── scraped_data.json
│           │   ├── faiss_index.bin
│           │   └── faiss_mapping.json
│           ├── scraper.py         # Script de scraping
│           ├── indexer.py         # Script d'indexation
│           └── .env               # Configuration (à créer)
└── requirements.txt
```

## Tests

Pour tester le système complet :

```bash
python test_simple.py
```

## Configuration

- **SCRAPING_URL** : URL de base à scraper (dans `.env`)
- **limit** : Nombre maximum de pages à scraper (modifiable dans `scraper.py`)
- **Modèle d'embeddings** : `all-MiniLM-L6-v2` (configurable dans `indexer.py`)
