# Utiliser une image Python officielle
FROM python:3.11-slim

# Définir le répertoire de travail
WORKDIR /app

# Copier les fichiers de requirements
COPY requirements.txt .

# Installer les dépendances
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code de l'application (SANS les données)
COPY Back/ /app/Back/
COPY Front/ /app/Front/
COPY admin_pages/ /app/admin_pages/
COPY config.py /app/
COPY download_data.py /app/

# Créer les dossiers pour les données
RUN mkdir -p /app/data /app/Back/app/rag/data

# Définir le répertoire de travail
WORKDIR /app/Front

# Exposer le port
EXPOSE 8501

# Variables d'environnement pour Streamlit
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
ENV PYTHONUNBUFFERED=1

# Télécharger les données au démarrage puis lancer l'app
CMD ["sh", "-c", "python /app/download_data.py && streamlit run streamlit_app.py --server.port=8501 --server.address=0.0.0.0"]
