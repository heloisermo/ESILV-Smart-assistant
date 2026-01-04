# ESILV Smart Assistant

🤖 Assistant intelligent pour l'ESILV utilisant le scraping web, la recherche vectorielle (RAG) et Google Vertex AI.

**🌐 Site du projet :** [https://esilv-chatbot-970477989170.us-central1.run.app/](https://esilv-chatbot-970477989170.us-central1.run.app/)

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)](https://streamlit.io/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

## 📖 Table des matières

- [Fonctionnalités](#-fonctionnalités)
- [Installation et Configuration](#-installation-et-configuration-première-fois)
- [Créer l'index initial](#-créer-lindex-initial-scraping--indexation)
- [Lancer l'application](#-lancer-lapplication)
- [Structure du projet](#-structure-du-projet)
- [Mise à jour des données](#-mise-à-jour-des-données)
- [Déploiement sur GCP](#-déploiement-sur-google-cloud-platform)
- [Tests](#-tests)
- [Configuration avancée](#️-configuration-avancée)
- [Résolution des problèmes](#-résolution-des-problèmes)
- [Contribution](#-contribution)

## ✨ Fonctionnalités

- 🔍 **Scraping web intelligent** : Extraction automatique du contenu du site ESILV
- 🧠 **Recherche vectorielle (RAG)** : Recherche sémantique avec FAISS et embeddings multilingues
- 🤖 **Multi-agents** : Orchestration intelligente entre agent RAG et agent de contact
- 💬 **Interface conversationnelle** : Chat intuitif avec Streamlit
- 📝 **Gestion des leads** : Collecte et export des demandes de contact
- 📄 **Upload de documents** : Indexation de PDF, DOCX, TXT
- 🔐 **Interface admin** : Gestion complète des données et réindexation
- ☁️ **Déploiement GCP** : Prêt pour Cloud Run avec streaming optimisé

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

### 5. Créer l'index initial (scraping + indexation)

Pour initialiser la base de connaissances du chatbot, vous devez d'abord scraper le site web puis indexer les données. Il existe deux méthodes :

#### Méthode 1 : Pipeline complet automatique (Recommandé pour débuter)

```bash
python Back/app/rag/main.py
```

Cette commande va automatiquement :
1. Scraper le site ESILV (20 pages par défaut)
2. Indexer les documents scrapés
3. Effectuer un test de recherche

Vous pouvez ajuster les paramètres dans le fichier `Back/app/rag/main.py` :
- `max_pages` : nombre de pages à scraper
- `max_depth` : profondeur de navigation

#### Méthode 2 : Étapes manuelles (Pour plus de contrôle)

**a) Scraper le site web**

```bash
python Back/app/rag/scraper.py
```

Cette commande va :
- Scraper jusqu'à 500 pages du site ESILV
- Extraire le contenu principal de chaque page
- Sauvegarder les données dans `data/scraped_data.json`
- Créer une sauvegarde dans `data/archive_YYYYMMDD_HHMMSS/`
- Prendre environ 5-10 minutes selon la vitesse de connexion

**b) Indexer les données scrapées**

```bash
python Back/app/rag/indexer.py
```

Cette commande va :
- Charger les données de `data/scraped_data.json`
- Découper le contenu en chunks optimisés (1000 caractères avec 100 de chevauchement)
- Créer les embeddings vectoriels avec le modèle `paraphrase-multilingual-MiniLM-L12-v2`
- Générer l'index FAISS dans `data/faiss_index.bin`
- Sauvegarder le mapping dans `data/faiss_mapping.json`
- Prendre environ 2-5 minutes selon la quantité de données

**Note importante :** 
- Les scripts dans `Back/app/rag/` sont utilisés pour l'indexation **initiale** à partir du scraping web
- Le module `admin_indexer.py` est utilisé par l'interface Streamlit pour la **réindexation** et la gestion des documents uploadés
- Les données générées sont sauvegardées localement et ne sont pas versionnées dans git

### 6. Lancer l'application

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
│       ├── admin_indexer.py                  # Indexation pour l'interface admin (réindexation)
│       ├── document_manager.py               # Gestion des documents uploadés
│       ├── leads_manager.py                  # Gestion des leads
│       │
│       ├── agents/                           # Agents conversationnels
│       │   ├── orchestrator.py              # Orchestrateur principal
│       │   ├── rag_agent.py                 # Agent RAG
│       │   ├── contact_agent.py             # Agent de contact
│       │   └── base_agent.py                # Classe de base
│       │
│       └── rag/                             # Système RAG (indexation initiale)
│           ├── main.py                      # Pipeline complet scraping + indexation
│           ├── scraper.py                   # Script de scraping web
│           ├── indexer.py                   # Script d'indexation initiale
│           ├── chunker.py                   # Découpage de texte
│           └── rag.py                       # Recherche vectorielle (utilisé par le chatbot)
│
├── Front/
│   ├── streamlit_app.py         # Interface utilisateur
│   ├── Dockerfile               # Configuration Docker pour déploiement
│   └── assets/                  # Ressources visuelles
│
└── admin_pages/                 # Pages d'administration
    ├── auth.py                  # Authentification admin
    ├── document_management.py   # Gestion des documents
    └── leads_management.py      # Gestion des leads
```

## 🔄 Mise à jour des données

### Re-scraper et re-indexer

Pour mettre à jour les données du site ESILV, vous pouvez :

#### Via le pipeline complet
```bash
python Back/app/rag/main.py
```

#### Via les étapes manuelles
```bash
# 1. Re-scraper le site
python Back/app/rag/scraper.py

# 2. Re-indexer les données
python Back/app/rag/indexer.py
```

#### Via l'interface admin

L'application Streamlit inclut une interface d'administration accessible depuis le menu latéral qui permet de :
- Re-scraper et re-indexer directement depuis l'interface
- Gérer les documents uploadés (PDF, DOCX, TXT)
- Consulter et exporter les leads/contacts

**Note :** L'interface admin utilise `admin_indexer.py` pour gérer l'indexation.

## 🚀 Déploiement sur Google Cloud Platform

### Prérequis pour le déploiement

1. **Compte GCP** avec facturation activée
2. **Google Cloud SDK** installé ([Installation](https://cloud.google.com/sdk/docs/install))
3. **Docker** installé (optionnel, pour tester localement)

### Configuration initiale GCP

```bash
# Se connecter à GCP
gcloud auth login

# Définir votre projet
gcloud config set project VOTRE_PROJECT_ID

# Activer les APIs nécessaires
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable artifactregistry.googleapis.com
```

### Déploiement sur Cloud Run

#### Option 1 : Déploiement avec variables d'environnement

```bash
# Depuis le dossier racine du projet
cd ESILV-Smart-assistant

# Construire et déployer
gcloud run deploy esilv-chatbot \
  --source ./Front \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --port 8501 \
  --memory 2Gi \
  --cpu 2 \
  --timeout 300 \
  --set-env-vars VERTEX_MODEL=gemini-2.0-flash-exp,VERTEX_PROJECT=votre-projet-gcp,VERTEX_LOCATION=us-central1
```

#### Option 2 : Déploiement avec fichier env.yaml

Créez un fichier `env.yaml` à la racine :

```yaml
VERTEX_MODEL: "gemini-2.0-flash-exp"
VERTEX_PROJECT: "votre-projet-gcp"
VERTEX_LOCATION: "us-central1"
ADMIN_PASSWORD: "votre-mot-de-passe-admin"
```

Puis déployez :

```bash
gcloud run deploy esilv-chatbot \
  --source ./Front \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --env-vars-file env.yaml
```

#### Option 3 : Utilisation de Secret Manager (Recommandé pour la production)

```bash
# 1. Créer les secrets
echo -n "votre-mot-de-passe-admin" | gcloud secrets create admin-password --data-file=-

# 2. Donner accès à Cloud Run
PROJECT_NUMBER=$(gcloud projects describe VOTRE_PROJECT_ID --format="value(projectNumber)")
gcloud secrets add-iam-policy-binding admin-password \
  --member=serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com \
  --role=roles/secretmanager.secretAccessor

# 3. Déployer avec les secrets
gcloud run deploy esilv-chatbot \
  --source ./Front \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars VERTEX_MODEL=gemini-2.0-flash-exp,VERTEX_PROJECT=votre-projet-gcp \
  --set-secrets ADMIN_PASSWORD=admin-password:latest
```

### Test local avec Docker

```bash
# Construire l'image
cd Front
docker build -t esilv-chatbot .

# Lancer le conteneur
docker run -p 8501:8501 --env-file ../.env esilv-chatbot

# Accéder à http://localhost:8501
```

### Mise à jour du déploiement

```bash
# Redéployer avec la nouvelle version
gcloud run deploy esilv-chatbot \
  --source ./Front \
  --platform managed \
  --region us-central1
```

### Logs et monitoring

```bash
# Voir les logs
gcloud run logs read esilv-chatbot --region us-central1

# Voir les logs en temps réel
gcloud run logs tail esilv-chatbot --region us-central1

# Voir les builds en cours
gcloud builds list --filter="status=WORKING" --limit=5
```

### Configuration d'un domaine personnalisé

1. Aller dans la console Cloud Run
2. Sélectionner votre service `esilv-chatbot`
3. Cliquer sur "Manage custom domains"
4. Suivre les instructions pour mapper votre domaine

### Estimation des coûts Cloud Run

Cloud Run facture selon l'utilisation :
- **Gratuit** : 2 millions de requêtes/mois
- **CPU** : ~$0.00002400 par vCPU-seconde
- **Mémoire** : ~$0.00000250 par GiB-seconde
- **Requêtes** : $0.40 par million de requêtes

**Estimation** : ~10-50€/mois pour un usage modéré (quelques centaines d'utilisateurs)

### Checklist de déploiement

- [ ] Variables d'environnement configurées
- [ ] Secrets créés dans Secret Manager (pour production)
- [ ] APIs activées (Cloud Run, Cloud Build, Artifact Registry)
- [ ] Facturation activée sur le projet GCP
- [ ] Fichiers .env et credentials non commités (vérifier .gitignore)
- [ ] Test en local réussi
- [ ] Déploiement Cloud Run effectué
- [ ] URL testée et fonctionnelle
- [ ] Logs vérifiés (pas d'erreurs au démarrage)

## 🧪 Tests

Pour tester le système RAG complet (scraping + indexation + recherche) :

```bash
python Back/app/rag/main.py
```

Cette commande effectue un test complet du pipeline et affiche des résultats de recherche.

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

## 🤝 Contribution

Les contributions sont les bienvenues ! Consultez le fichier [CONTRIBUTING.md](CONTRIBUTING.md) pour les guidelines.

### Comment contribuer
1. Fork le projet
2. Créer une branche (`git checkout -b feature/AmazingFeature`)
3. Commit les changements (`git commit -m 'Ajoute une fonctionnalité incroyable'`)
4. Push vers la branche (`git push origin feature/AmazingFeature`)
5. Ouvrir une Pull Request

## 📄 Licence

Ce projet est sous licence MIT. Voir le fichier [LICENSE](LICENSE) pour plus de détails.

## 👥 Auteurs

- **Équipe ESILV Smart Assistant** - Développement initial

## 🙏 Remerciements

- ESILV pour le contenu du site web
- Google Cloud Platform pour Vertex AI
- La communauté open source pour les bibliothèques utilisées

## 📞 Support

Pour toute question ou problème :
- Ouvrir une [issue](../../issues) sur GitHub
- Consulter la documentation
- Contacter l'équipe de développement

---

**Fait avec ❤️ pour l'ESILV**
