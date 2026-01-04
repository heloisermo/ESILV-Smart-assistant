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

def download_all_data():
    """Télécharge toutes les données nécessaires."""
    print("Téléchargement des données depuis Cloud Storage...")
    
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
    
    print("✓ Toutes les données sont prêtes!")

if __name__ == "__main__":
    download_all_data()
