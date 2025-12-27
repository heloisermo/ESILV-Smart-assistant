# Déploiement sur Google Cloud Platform (GCP)

Ce guide vous explique comment déployer l'application Streamlit sur GCP avec **Cloud Run**.

## 📋 Prérequis

1. **Compte GCP** avec facturation activée
2. **Google Cloud SDK** installé ([Installation](https://cloud.google.com/sdk/docs/install))
3. **Docker** installé (optionnel, pour tester localement)

## 🚀 Déploiement sur Cloud Run

### 1. Configuration initiale

```bash
# Se connecter à GCP
gcloud auth login

# Définir votre projet
gcloud config set project VOTRE_PROJECT_ID

# Activer les APIs nécessaires
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
```

### 2. Créer un fichier .env pour la production

Créez un fichier `.env.production` avec vos variables :

```env
VERTEX_API_KEY=votre_clé
VERTEX_MODEL=gemini-2.0-flash-exp
VERTEX_PROJECT=votre-projet-gcp
VERTEX_LOCATION=us-central1
```

### 3. Déployer avec Cloud Build

```bash
# Depuis le dossier racine du projet
cd C:\Users\ASUS\Desktop\A5\ESILV-Smart-assistant

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
  --set-env-vars VERTEX_API_KEY=votre_clé,VERTEX_MODEL=gemini-2.0-flash-exp
```

### 4. Variables d'environnement (alternative)

Vous pouvez aussi créer un fichier `env.yaml` :

```yaml
VERTEX_API_KEY: "votre_clé"
VERTEX_MODEL: "gemini-2.0-flash-exp"
VERTEX_PROJECT: "votre-projet-gcp"
VERTEX_LOCATION: "us-central1"
```

Et déployer avec :

```bash
gcloud run deploy esilv-chatbot \
  --source ./Front \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --env-vars-file env.yaml
```

## 🧪 Test en local avec Docker

```bash
# Construire l'image
cd Front
docker build -t esilv-chatbot .

# Lancer le conteneur
docker run -p 8501:8501 --env-file ../.env esilv-chatbot

# Accéder à http://localhost:8501
```

## 🔒 Sécurité

### Utiliser Secret Manager (recommandé)

1. **Créer un secret** :
```bash
echo -n "votre_clé_api" | gcloud secrets create vertex-api-key --data-file=-
```

2. **Donner accès à Cloud Run** :
```bash
gcloud secrets add-iam-policy-binding vertex-api-key \
  --member=serviceAccount:PROJECT_NUMBER-compute@developer.gserviceaccount.com \
  --role=roles/secretmanager.secretAccessor
```

3. **Déployer avec le secret** :
```bash
gcloud run deploy esilv-chatbot \
  --source ./Front \
  --platform managed \
  --region us-central1 \
  --set-secrets VERTEX_API_KEY=vertex-api-key:latest
```

## 📊 Configuration Streamlit pour la production

Le fichier `.streamlit/config.toml` est déjà optimisé pour la production.

## 💰 Estimation des coûts

Cloud Run facture selon l'utilisation :
- **Gratuit** : 2 millions de requêtes/mois
- **CPU** : ~$0.00002400 par vCPU-seconde
- **Mémoire** : ~$0.00000250 par GiB-seconde
- **Requêtes** : $0.40 par million de requêtes

**Estimation** : ~10-50€/mois pour un usage modéré

## 🔄 Mise à jour

```bash
# Redéployer avec la nouvelle version
gcloud run deploy esilv-chatbot \
  --source ./Front \
  --platform managed \
  --region us-central1
```

## 🐛 Logs et Debug

```bash
# Voir les logs
gcloud run logs read esilv-chatbot --region us-central1

# Voir les logs en temps réel
gcloud run logs tail esilv-chatbot --region us-central1
```

## 🌐 Domaine personnalisé

1. Aller dans Cloud Run console
2. Sélectionner votre service
3. Cliquer sur "Manage custom domains"
4. Suivre les instructions pour mapper votre domaine

## 📱 Alternative : App Engine

Si vous préférez App Engine, créez un `app.yaml` :

```yaml
runtime: python311
entrypoint: streamlit run streamlit_app.py --server.port=$PORT

env_variables:
  VERTEX_API_KEY: "votre_clé"
  VERTEX_MODEL: "gemini-2.0-flash-exp"

automatic_scaling:
  min_instances: 0
  max_instances: 10
```

Déploiement :
```bash
gcloud app deploy
```

## ✅ Checklist de déploiement

- [ ] Variables d'environnement configurées
- [ ] Secrets créés dans Secret Manager
- [ ] APIs activées (Cloud Run, Cloud Build)
- [ ] Facturation activée
- [ ] Fichiers .env non commités (dans .gitignore)
- [ ] Test en local réussi
- [ ] Déploiement Cloud Run effectué
- [ ] URL testée et fonctionnelle

## 🔗 Ressources

- [Documentation Cloud Run](https://cloud.google.com/run/docs)
- [Streamlit sur Cloud Run](https://docs.streamlit.io/knowledge-base/tutorials/deploy/docker)
- [Secret Manager](https://cloud.google.com/secret-manager/docs)
