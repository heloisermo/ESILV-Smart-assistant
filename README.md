# ESILV Smart Assistant

Assistant intelligent pour l'ESILV utilisant le scraping web, la recherche vectorielle (RAG) et Google Vertex AI.

## 🚀 Installation et Configuration (Première fois)

### Prérequis

- Python 3.9 ou supérieur
- Un compte Google Cloud Platform (GCP) avec Vertex AI activé
- Les credentials GCP (fichier JSON de service account)

### 1. Cloner le projet

```bash
git clone <url-du-repo>
cd ESILV-Smart-assistant
```

### 2. Installer les dépendances

```bash
pip install -r requirements.txt
```

### 3. Configuration de Google Vertex AI

#### a) Créer un projet GCP et activer Vertex AI

1. Aller sur [Google Cloud Console](https://console.cloud.google.com/)
2. Créer un nouveau projet ou sélectionner un projet existant
3. Activer l'API Vertex AI :
   - Aller dans "APIs & Services" > "Enable APIs and Services"
   - Rechercher "Vertex AI API" et l'activer

#### b) Créer un service account et télécharger les credentials

1. Aller dans "IAM & Admin" > "Service Accounts"
2. Cliquer sur "Create Service Account"
3. Donner un nom (ex: `esilv-smart-assistant`)
4. Attribuer les rôles :
   - `Vertex AI User`
   - `Storage Object Viewer` (si besoin)
5. Créer une clé JSON :
   - Cliquer sur le service account créé
   - Onglet "Keys" > "Add Key" > "Create new key"
   - Choisir le format JSON
   - Le fichier JSON sera téléchargé automatiquement
6. Placer le fichier JSON dans `Back/app/` (ex: `Back/app/esilv-smart-assistant-xxxxx.json`)

### 4. Configuration de l'environnement (.env)

Créer un fichier `.env` à la racine du projet avec le contenu suivant :

```env
# Configuration du scraping
SCRAPING_URL=https://www.esilv.fr/

# Configuration de la base de données vectorielle
CHROMA_DB_PATH=./data/chroma_db

# Configuration du RAG
CHUNK_SIZE=1000
CHUNK_OVERLAP=200

SYSTEM_PROMPT="Tu es un assistant pour l'ecole d'ingenieurs ESILV. Reponds aux questions en utilisant le contexte fourni. Si l'information n'est pas presente dans le contexte mais que tu penses qu'elle pourrait se trouver sur le site ESILV, suggere a l'utilisateur de consulter directement le site web https://www.esilv.fr ou indique-lui les pages pertinentes a visiter. Reponds toujours en francais et de maniere claire et concise."

# Vertex AI Configuration (SDK)
GOOGLE_APPLICATION_CREDENTIALS=C:\chemin\absolu\vers\votre\fichier.json
VERTEX_MODEL=gemini-2.0-flash-exp
VERTEX_PROJECT=votre-project-id-gcp
VERTEX_LOCATION=us-central1

# Admin Panel Authentication
ADMIN_PASSWORD=admin2025
```

**⚠️ Important :** 
- Remplacer `GOOGLE_APPLICATION_CREDENTIALS` par le chemin ABSOLU vers votre fichier JSON de credentials
- Remplacer `VERTEX_PROJECT` par votre Project ID GCP
- Le fichier `.env` est ignoré par git pour la sécurité

### 5. Scraper le site (première fois)

Cette étape va récupérer tout le contenu du site ESILV :

```bash
python Back/app/rag/scraper.py
```

Cette commande va :
- Scraper jusqu'à 500 pages du site ESILV
- Sauvegarder les données dans `data/scraped_data.json`
- Prendre environ 5-10 minutes selon la vitesse de connexion
- Créer une sauvegarde dans `data/archive_YYYYMMDD_HHMMSS/`

**Note :** Les données scrapées sont sauvegardées localement et ne sont pas versionnées dans git.

### 6. Indexer les données (première fois)

Cette étape va créer l'index de recherche vectorielle :

```bash
python Back/app/admin_indexer.py
```

Cette commande va :
- Charger les données de `data/scraped_data.json`
- Découper le contenu en chunks optimisés
- Créer les embeddings vectoriels avec le modèle `paraphrase-multilingual-MiniLM-L12-v2`
- Générer l'index FAISS dans `data/faiss_index.bin`
- Sauvegarder le mapping dans `data/faiss_mapping.json`
- Prendre environ 2-5 minutes selon la quantité de données

### 7. Lancer l'application

#### Interface utilisateur (Streamlit)

```bash
cd Front
streamlit run streamlit_app.py
```

L'application sera accessible sur `http://localhost:8501`

## 📁 Structure du projet

```
ESILV-Smart-assistant/
├── .env                          # Configuration (à créer - ignoré par git)
├── config.py                     # Gestion centralisée des chemins
├── requirements.txt              # Dépendances Python
├── README.md
│
├── data/                         # Données générées (ignoré par git)
│   ├── scraped_data.json        # Données scrapées
│   ├── faiss_index.bin          # Index vectoriel FAISS
│   ├── faiss_mapping.json       # Mapping des chunks
│   ├── processed_documents.json # Métadonnées des documents
│   ├── archive_*/               # Sauvegardes automatiques
│   ├── leads/                   # Données des leads
│   └── uploads/                 # Documents uploadés
│
├── Back/
│   └── app/
│       ├── esilv-smart-assistant-xxxxx.json  # Credentials GCP (à placer - ignoré par git)
│       ├── admin_indexer.py                  # Module d'indexation
│       ├── document_manager.py               # Gestion des documents
│       ├── leads_manager.py                  # Gestion des leads
│       │
│       ├── agents/                           # Agents conversationnels
│       │   ├── orchestrator.py              # Orchestrateur principal
│       │   ├── rag_agent.py                 # Agent RAG
│       │   ├── contact_agent.py             # Agent de contact
│       │   └── base_agent.py                # Classe de base
│       │
│       └── rag/                             # Système RAG
│           ├── scraper.py                   # Script de scraping
│           ├── indexer.py                   # Script d'indexation
│           ├── chunker.py                   # Découpage de texte
│           └── rag.py                       # Recherche vectorielle
│
├── Front/
│   ├── streamlit_app.py         # Interface utilisateur
│   ├── DEPLOYMENT.md            # Guide de déploiement
│   └── assets/                  # Ressources visuelles
│
└── admin_pages/                 # Pages d'administration
    ├── auth.py                  # Authentification admin
    ├── document_management.py   # Gestion des documents
    └── leads_management.py      # Gestion des leads
```

## 🔄 Mise à jour des données

### Re-scraper le site

Pour mettre à jour les données du site ESILV :

```bash
python Back/app/rag/scraper.py
```

### Re-indexer après scraping

Après avoir re-scrapé, il faut re-indexer :

```bash
python Back/app/admin_indexer.py
```

### Via l'interface admin

L'application Streamlit inclut une interface d'administration accessible depuis le menu latéral qui permet de :
- Re-scraper et re-indexer directement
- Gérer les documents uploadés
- Consulter les leads/contacts

## 🧪 Tests

Pour tester le système RAG :

```bash
python Back/app/rag/main.py
```

## ⚙️ Configuration avancée

### Modèles Vertex AI disponibles

Dans le fichier `.env`, vous pouvez changer le modèle utilisé :
- `gemini-2.0-flash-exp` (par défaut, le plus rapide)
- `gemini-1.5-pro`
- `gemini-1.5-flash`

### Paramètres de chunking

Dans le fichier `.env` :
- `CHUNK_SIZE` : Taille des chunks de texte (défaut: 1000)
- `CHUNK_OVERLAP` : Chevauchement entre chunks (défaut: 200)

### Modèle d'embeddings

Le modèle `paraphrase-multilingual-MiniLM-L12-v2` est utilisé par défaut pour les embeddings.
Modifiable dans `Back/app/admin_indexer.py` (variable `MODEL_NAME`).

## 🔒 Sécurité

**Fichiers sensibles ignorés par git :**
- `.env` : Variables d'environnement et mots de passe
- `Back/app/*.json` : Credentials GCP
- `data/` : Toutes les données générées
- `__pycache__/` : Fichiers Python compilés

**⚠️ Ne JAMAIS commiter :**
- Les credentials GCP (fichiers .json)
- Le fichier .env
- Les données scrapées ou indexées

## 🐛 Résolution des problèmes

### Erreur : "GOOGLE_APPLICATION_CREDENTIALS not found"

Vérifier que :
1. Le chemin dans `.env` est correct et ABSOLU
2. Le fichier JSON existe bien à cet emplacement
3. Les permissions de lecture sont correctes

### Erreur lors du scraping

Vérifier :
1. La connexion internet
2. L'URL dans `.env` est accessible
3. Le site cible n'a pas changé sa structure

### Erreur lors de l'indexation

Vérifier :
1. Le fichier `data/scraped_data.json` existe
2. Il contient des données valides
3. Suffisamment d'espace disque disponible

## 📝 Licence

[À compléter selon votre licence]
