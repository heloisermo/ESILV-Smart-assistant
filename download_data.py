"""Télécharge les données depuis Google Cloud Storage au démarrage."""
import os
from google.cloud import storage

BUCKET_NAME = "esilv-chatbot-data"

def download_from_gcs(bucket_name, source_blob_name, destination_file_name):
    """Télécharge un fichier depuis GCS."""
    os.makedirs(os.path.dirname(destination_file_name), exist_ok=True)
    
    # Si le fichier existe déjà, pas besoin de le télécharger
    if os.path.exists(destination_file_name):
        print(f"✓ {destination_file_name} existe déjà")
        return
    
    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(source_blob_name)
        blob.download_to_filename(destination_file_name)
        print(f"✓ Téléchargé {source_blob_name} vers {destination_file_name}")
    except Exception as e:
        print(f"✗ Erreur lors du téléchargement de {source_blob_name}: {e}")

def download_directory_from_gcs(bucket_name, source_prefix, destination_dir):
    """Télécharge un dossier complet depuis GCS."""
    if os.path.exists(destination_dir) and os.listdir(destination_dir):
        print(f"✓ {destination_dir} existe déjà")
        return
    
    print(f"Téléchargement du dossier {source_prefix}...")
    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blobs = bucket.list_blobs(prefix=source_prefix)
        
        for blob in blobs:
            if blob.name.endswith('/'):
                continue
            
            # Construire le chemin de destination
            relative_path = blob.name[len(source_prefix):].lstrip('/')
            destination_file = os.path.join(destination_dir, relative_path)
            
            os.makedirs(os.path.dirname(destination_file), exist_ok=True)
            blob.download_to_filename(destination_file)
            print(f"  ✓ {relative_path}")
        
        print(f"✓ Dossier {source_prefix} téléchargé")
    except Exception as e:
        print(f"✗ Erreur lors du téléchargement du dossier {source_prefix}: {e}")

def download_all_data():
    """Télécharge toutes les données nécessaires."""
    print("Téléchargement des données depuis Cloud Storage...")
    
    # Télécharger les fichiers de données
    files_to_download = [
        ("data/faiss_index.bin", "/app/data/faiss_index.bin"),
        ("data/faiss_mapping.json", "/app/data/faiss_mapping.json"),
        ("data/processed_documents.json", "/app/data/processed_documents.json"),
        ("rag/faiss_index.bin", "/app/Back/app/rag/data/faiss_index.bin"),
        ("rag/faiss_mapping.json", "/app/Back/app/rag/data/faiss_mapping.json"),
        ("rag/scraped_data.json", "/app/Back/app/rag/data/scraped_data.json"),
    ]
    
    for source, destination in files_to_download:
        download_from_gcs(BUCKET_NAME, source, destination)
    
    # Télécharger le modèle d'embedding
    model_path = "/root/.cache/huggingface/hub/models--sentence-transformers--paraphrase-multilingual-MiniLM-L12-v2/snapshots/86741b4e3f5cb7765a600d3a3d55a0f6a6cb443d"
    download_directory_from_gcs(BUCKET_NAME, "model/86741b4e3f5cb7765a600d3a3d55a0f6a6cb443d/", model_path)
    
    print("✓ Toutes les données sont prêtes!")

if __name__ == "__main__":
    download_all_data()
