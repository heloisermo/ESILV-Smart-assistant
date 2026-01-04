# Utiliser une image Python officielle
FROM python:3.11-slim

# Définir le répertoire de travail
WORKDIR /app

# Copier les fichiers de requirements depuis la racine
COPY requirements.txt .

# Installer les dépendances
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code de l'application
COPY Back/ /app/Back/
COPY Front/ /app/Front/
COPY admin_pages/ /app/admin_pages/
COPY config.py /app/
COPY data/ /app/data/

# Définir le répertoire de travail pour l'app
WORKDIR /app/Front

# Exposer le port
EXPOSE 8501

# Variable d'environnement pour Streamlit
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

# Commande pour lancer l'application
CMD ["streamlit", "run", "streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
