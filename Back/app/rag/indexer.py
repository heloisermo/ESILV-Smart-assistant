import json
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from .chunker import chunk_documents
from datetime import datetime
import shutil
import os

JSON_PATH = "data/scraped_data.json"
INDEX_PATH = "data/faiss_index.bin"
MAPPING_PATH = "data/faiss_mapping.json"

# Utiliser un modèle multilingue cohérent
MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"
# Chemin du modèle pré-chargé sur GCP
GCP_MODEL_CACHE_PATH = '/root/.cache/huggingface/hub/models--sentence-transformers--paraphrase-multilingual-MiniLM-L12-v2/snapshots/86741b4e3f5cb7765a600d3a3d55a0f6a6cb443d'

# Paramètres de chunking
CHUNK_SIZE = 1000  # Taille d'un chunk en caractères (800-1500 recommandé)
CHUNK_OVERLAP = 100  # Chevauchement entre chunks
MIN_CHUNK_SIZE = 150  # Taille minimale d'un chunk

def load_scraped_data(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def make_embeddings(texts, batch_size=64):
    """Génère les embeddings par batch pour économiser la mémoire"""
    # Charger le modèle : GCP cache si disponible, sinon HuggingFace
    if os.path.exists(GCP_MODEL_CACHE_PATH):
        print("Indexer: Chargement du modèle depuis le cache GCP")
        model = SentenceTransformer(GCP_MODEL_CACHE_PATH)
    else:
        print(f"Indexer: Chargement du modèle {MODEL_NAME} depuis HuggingFace")
        model = SentenceTransformer(MODEL_NAME)
    
    all_embeddings = []
    
    print(f"Génération des embeddings pour {len(texts)} textes...")
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i+batch_size]
        print(f"  Batch {i//batch_size + 1}/{(len(texts)-1)//batch_size + 1}")
        embeddings = model.encode(
            batch, 
            convert_to_numpy=True, 
            normalize_embeddings=True, 
            show_progress_bar=False
        )
        all_embeddings.append(embeddings)
    
    return np.vstack(all_embeddings)

def build_faiss_index(embeddings):
    dim = embeddings.shape[1]
    # IndexFlatIP pour cosine similarity avec embeddings normalisés
    index = faiss.IndexFlatIP(dim)
    index.add(embeddings)
    return index

def archive_old_index():
    """Archive l'ancien index FAISS avec un timestamp"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archive_folder = f"data/archive_{timestamp}"
    
    files_to_archive = [
        INDEX_PATH,
        MAPPING_PATH
    ]
    
    existing_files = [f for f in files_to_archive if os.path.exists(f)]
    
    if existing_files:
        os.makedirs(archive_folder, exist_ok=True)
        print(f"Archivage de l'ancien index dans {archive_folder}...")
        
        for file_path in existing_files:
            if os.path.exists(file_path):
                filename = os.path.basename(file_path)
                shutil.copy2(file_path, os.path.join(archive_folder, filename))
                print(f"  Archive: {filename}")
        
        print(f"Archivage termine.\n")
    else:
        print("Aucun index existant a archiver.\n")

if __name__ == "__main__":
    print("=" * 60)
    print("INDEXATION FAISS")
    print("=" * 60 + "\n")
    
    # Archiver l'ancien index
    archive_old_index()
    data = load_scraped_data(JSON_PATH)

    # Découper les documents en chunks
    urls, chunks, doc_indices = chunk_documents(
        data, 
        chunk_size=CHUNK_SIZE,
        overlap=CHUNK_OVERLAP,
        min_chunk_size=MIN_CHUNK_SIZE
    )
    
    # Afficher des stats pour débugger
    print(f"\nStatistiques:")
    print(f"   Documents originaux : {len(data)}")
    print(f"   Chunks créés : {len(chunks)}")
    print(f"   Ratio chunks/doc : {len(chunks)/len(data):.1f}")
    print(f"\n   Exemple de chunk :")
    print(f"   {chunks[0][:200]}...")

    embeds = make_embeddings(chunks)
    index = build_faiss_index(embeds)

    faiss.write_index(index, INDEX_PATH)

    with open(MAPPING_PATH, "w", encoding="utf-8") as f:
        json.dump({
            "urls": urls, 
            "texts": chunks,
            "doc_indices": doc_indices  # Pour retrouver le document d'origine
        }, f, ensure_ascii=False, indent=2)

    print(f"\nIndex FAISS cree: {embeds.shape[0]} chunks, dimension {embeds.shape[1]}")
    print(f"   Fichiers: {INDEX_PATH} et {MAPPING_PATH}")
    print(f"Termine!")