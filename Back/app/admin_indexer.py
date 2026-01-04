"""
Module for admin indexing operations
Exposes indexing and document management functions for the admin interface
"""
import os
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Any

import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

# Add project root to path for config import
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

try:
    from config import (
        DATA_DIR, FAISS_INDEX_PATH, FAISS_MAPPING_PATH,
        DOCUMENTS_METADATA_PATH, SCRAPED_DATA_PATH, UPLOADS_DIR
    )
    JSON_PATH = str(SCRAPED_DATA_PATH)
    INDEX_PATH = str(FAISS_INDEX_PATH)
    MAPPING_PATH = str(FAISS_MAPPING_PATH)
    DOCUMENTS_METADATA_PATH = str(DOCUMENTS_METADATA_PATH)
    DATA_DIR = str(DATA_DIR)
    UPLOAD_DIR = str(UPLOADS_DIR)
except ImportError:
    # Fallback to defaults if config not available
    DATA_DIR = "data"
    JSON_PATH = os.path.join(DATA_DIR, "scraped_data.json")
    INDEX_PATH = os.path.join(DATA_DIR, "faiss_index.bin")
    MAPPING_PATH = os.path.join(DATA_DIR, "faiss_mapping.json")
    DOCUMENTS_METADATA_PATH = os.path.join(DATA_DIR, "documents_metadata.json")
    UPLOAD_DIR = os.path.join(DATA_DIR, "uploads")

MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"
# Chemin du modèle pré-chargé sur GCP (même que dans rag.py)
GCP_MODEL_CACHE_PATH = '/root/.cache/huggingface/hub/models--sentence-transformers--paraphrase-multilingual-MiniLM-L12-v2/snapshots/86741b4e3f5cb7765a600d3a3d55a0f6a6cb443d'

# Chunking parameters
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 100
MIN_CHUNK_SIZE = 150


def ensure_data_dir():
    """Ensure the data directory exists"""
    os.makedirs(DATA_DIR, exist_ok=True)


def _load_documents_metadata() -> Dict[str, Any]:
    """Load documents metadata from file"""
    ensure_data_dir()
    
    if not os.path.exists(DOCUMENTS_METADATA_PATH):
        return {}
    
    try:
        with open(DOCUMENTS_METADATA_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}


def _save_documents_metadata(metadata: Dict[str, Any]):
    """Save documents metadata to file"""
    ensure_data_dir()
    
    with open(DOCUMENTS_METADATA_PATH, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)


def get_indexed_documents() -> List[Dict[str, Any]]:
    """
    Get list of currently indexed documents with metadata
    
    Returns:
        List of document metadata dictionaries
    """
    metadata = _load_documents_metadata()
    return list(metadata.values())


def get_document_by_id(doc_id: str) -> Dict[str, Any]:
    """Get a specific document by ID"""
    metadata = _load_documents_metadata()
    return metadata.get(doc_id, {})


def add_document_metadata(
    doc_id: str,
    filename: str,
    doc_type: str,
    chunk_count: int,
    file_size: int
) -> Dict[str, Any]:
    """
    Add metadata for a newly indexed document
    
    Args:
        doc_id: Unique document identifier
        filename: Original filename
        doc_type: Document type (pdf, html, txt, etc)
        chunk_count: Number of chunks created from this document
        file_size: File size in bytes
        
    Returns:
        The created metadata dictionary
    """
    metadata = _load_documents_metadata()
    
    doc_metadata = {
        "id": doc_id,
        "filename": filename,
        "type": doc_type,
        "chunk_count": chunk_count,
        "file_size": file_size,
        "indexed_at": datetime.now().isoformat(),
        "status": "indexed"
    }
    
    metadata[doc_id] = doc_metadata
    _save_documents_metadata(metadata)
    
    return doc_metadata


def remove_document_metadata(doc_id: str) -> bool:
    """
    Remove metadata for a document
    
    Args:
        doc_id: Document ID to remove
        
    Returns:
        True if removed, False if not found
    """
    metadata = _load_documents_metadata()
    
    if doc_id in metadata:
        del metadata[doc_id]
        _save_documents_metadata(metadata)
        return True
    
    return False


def load_documents(path: str = JSON_PATH) -> Dict[str, str]:
    """
    Load documents from JSON file
    
    Args:
        path: Path to the scraped data JSON file
        
    Returns:
        Dictionary of {url: text}
    """
    if not os.path.exists(path):
        return {}
    
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error loading documents: {e}")
        return {}


def load_uploaded_documents() -> Dict[str, str]:
    """
    Load uploaded documents from the uploads directory
    
    Returns:
        Dictionary of {filename: text}
    """
    from document_manager import extract_text_from_file
    
    documents = {}
    
    # Ensure uploads directory exists
    if not os.path.exists(UPLOAD_DIR):
        return documents
    
    # Load each uploaded file
    for filename in os.listdir(UPLOAD_DIR):
        file_path = os.path.join(UPLOAD_DIR, filename)
        
        if os.path.isfile(file_path):
            try:
                text = extract_text_from_file(file_path)
                if text and len(text.strip()) > 0:
                    documents[filename] = text
            except Exception as e:
                print(f"Error loading {filename}: {e}")
    
    return documents


def load_all_documents() -> Dict[str, str]:
    """
    Load all documents: scraped data + uploaded documents
    
    Returns:
        Dictionary of {source: text}
    """
    all_documents = {}
    
    # Load scraped data
    scraped = load_documents(JSON_PATH)
    all_documents.update(scraped)
    
    # Load uploaded documents
    uploaded = load_uploaded_documents()
    all_documents.update(uploaded)
    
    return all_documents


def smart_chunk_text(
    text: str,
    chunk_size: int = CHUNK_SIZE,
    overlap: int = CHUNK_OVERLAP,
    min_chunk_size: int = MIN_CHUNK_SIZE
) -> List[str]:
    """
    Intelligently chunk text while respecting sentence boundaries
    
    Args:
        text: Text to chunk
        chunk_size: Target chunk size in characters
        overlap: Character overlap between chunks
        min_chunk_size: Minimum chunk size to keep
        
    Returns:
        List of text chunks
    """
    import re
    
    if not text or len(text.strip()) < min_chunk_size:
        return []
    
    # Clean text
    text = re.sub(r'\s+', ' ', text.strip())
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        
        # If at end of text
        if end >= len(text):
            chunk = text[start:].strip()
            if len(chunk) >= min_chunk_size:
                chunks.append(chunk)
            break
        
        # Find natural break point (sentence end)
        search_start = max(start, end - 100)
        substring = text[search_start:end]
        
        # Look for sentence endings
        sentence_ends = []
        for match in re.finditer(r'[.!?]\s+', substring):
            sentence_ends.append(search_start + match.end())
        
        if sentence_ends:
            end = sentence_ends[-1]
        
        chunk = text[start:end].strip()
        
        if len(chunk) >= min_chunk_size:
            chunks.append(chunk)
        
        start = end - overlap
    
    return chunks


def chunk_documents(
    documents: Dict[str, str],
    chunk_size: int = CHUNK_SIZE,
    overlap: int = CHUNK_OVERLAP,
    min_chunk_size: int = MIN_CHUNK_SIZE
) -> Tuple[List[str], List[str], List[int]]:
    """
    Split documents into chunks
    
    Args:
        documents: Dictionary of {url: text}
        chunk_size: Chunk size in characters
        overlap: Overlap between chunks
        min_chunk_size: Minimum chunk size
        
    Returns:
        Tuple of (urls, chunks, doc_indices)
    """
    all_urls = []
    all_chunks = []
    all_indices = []
    
    for doc_idx, (url, text) in enumerate(documents.items()):
        chunks = smart_chunk_text(
            text,
            chunk_size=chunk_size,
            overlap=overlap,
            min_chunk_size=min_chunk_size
        )
        
        if chunks:
            for chunk in chunks:
                all_urls.append(url)
                all_chunks.append(chunk)
                all_indices.append(doc_idx)
    
    return all_urls, all_chunks, all_indices


def make_embeddings(texts: List[str], batch_size: int = 64) -> np.ndarray:
    """
    Generate embeddings for texts using sentence-transformers
    
    Args:
        texts: List of texts to embed
        batch_size: Batch size for processing
        
    Returns:
        NumPy array of embeddings
    """
    # Charger le modèle : GCP cache si disponible, sinon HuggingFace
    if os.path.exists(GCP_MODEL_CACHE_PATH):
        print("Admin: Chargement du modèle depuis le cache GCP")
        model = SentenceTransformer(GCP_MODEL_CACHE_PATH)
    else:
        print(f"Admin: Chargement du modèle {MODEL_NAME} depuis HuggingFace")
        model = SentenceTransformer(MODEL_NAME)
    
    all_embeddings = []
    
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i+batch_size]
        embeddings = model.encode(
            batch,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False
        )
        all_embeddings.append(embeddings)
    
    return np.vstack(all_embeddings)


def build_faiss_index(embeddings: np.ndarray) -> faiss.Index:
    """
    Build a FAISS index from embeddings
    
    Args:
        embeddings: NumPy array of embeddings
        
    Returns:
        FAISS index
    """
    dim = embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)  # Inner product for cosine similarity
    index.add(embeddings)
    return index


def archive_old_index():
    """Archive the current index with a timestamp"""
    ensure_data_dir()
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archive_folder = os.path.join(DATA_DIR, f"archive_{timestamp}")
    
    files_to_archive = [INDEX_PATH, MAPPING_PATH]
    existing_files = [f for f in files_to_archive if os.path.exists(f)]
    
    if existing_files:
        os.makedirs(archive_folder, exist_ok=True)
        
        for file_path in existing_files:
            if os.path.exists(file_path):
                filename = os.path.basename(file_path)
                shutil.copy2(file_path, os.path.join(archive_folder, filename))
        
        return archive_folder
    
    return None


def rebuild_index(
    progress_callback=None
) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Rebuild the FAISS index from scraped documents and uploaded documents
    
    Args:
        progress_callback: Optional callback function for progress updates.
                         Called with (progress: float, step: str, message: str)
                         progress is between 0.0 and 1.0
        
    Returns:
        Tuple of (success: bool, message: str, stats: dict)
    """
    try:
        ensure_data_dir()
        
        if progress_callback:
            progress_callback(0.0, "Chargement", "Chargement des documents...")
        
        # Load all documents (scraped + uploaded)
        documents = load_all_documents()
        if not documents:
            return False, "No documents found to index", {}
        
        # Archive old index
        if progress_callback:
            progress_callback(0.15, "Archivage", "Archivage de l'ancien index...")
        archive_old_index()
        
        # Chunk documents
        if progress_callback:
            progress_callback(0.25, "Découpage", f"Découpage de {len(documents)} documents...")
        
        urls, chunks, doc_indices = chunk_documents(documents)
        
        if not chunks:
            return False, "No chunks created from documents", {}
        
        # Generate embeddings
        if progress_callback:
            progress_callback(0.45, "Embeddings", f"Génération des embeddings pour {len(chunks)} chunks...")
        
        embeddings = make_embeddings(chunks)
        
        # Build index
        if progress_callback:
            progress_callback(0.75, "Construction", "Construction de l'index FAISS...")
        
        index = build_faiss_index(embeddings)
        
        # Save index and mapping
        if progress_callback:
            progress_callback(0.90, "Sauvegarde", "Sauvegarde des fichiers d'index...")
        
        faiss.write_index(index, INDEX_PATH)
        
        mapping_data = {
            "urls": urls,
            "texts": chunks,
            "doc_indices": doc_indices
        }
        
        with open(MAPPING_PATH, "w", encoding="utf-8") as f:
            json.dump(mapping_data, f, ensure_ascii=False, indent=2)
        
        # Prepare stats
        stats = {
            "document_count": len(documents),
            "chunk_count": len(chunks),
            "embedding_dim": embeddings.shape[1],
            "indexed_at": datetime.now().isoformat()
        }
        
        if progress_callback:
            progress_callback(1.0, "Terminé", "Index reconstruit avec succès !")
        
        return True, f"Index rebuilt successfully with {len(chunks)} chunks from {len(documents)} documents", stats
    
    except Exception as e:
        return False, f"Error rebuilding index: {str(e)}", {}


def add_document_to_index(
    document_path: str,
    document_name: str,
    progress_callback=None
) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Add a single document to the existing FAISS index incrementally (without rebuilding everything)
    
    Args:
        document_path: Path to the document file
        document_name: Name/identifier for the document
        progress_callback: Optional callback function for progress updates.
                         Called with (progress: float, step: str, message: str)
                         progress is between 0.0 and 1.0
        
    Returns:
        Tuple of (success: bool, message: str, stats: dict)
    """
    try:
        ensure_data_dir()
        
        # Check if index exists
        if not os.path.exists(INDEX_PATH) or not os.path.exists(MAPPING_PATH):
            return False, "Index does not exist. Please rebuild the index first.", {}
        
        if progress_callback:
            progress_callback(0.0, "Chargement", "Chargement de l'index existant...")
        
        # Load existing index and mapping
        index = faiss.read_index(INDEX_PATH)
        with open(MAPPING_PATH, "r", encoding="utf-8") as f:
            mapping_data = json.load(f)
        
        urls = mapping_data.get("urls", [])
        chunks = mapping_data.get("texts", [])
        doc_indices = mapping_data.get("doc_indices", [])
        
        # Get the next document index
        max_doc_idx = max(doc_indices) if doc_indices else -1
        new_doc_idx = max_doc_idx + 1
        
        if progress_callback:
            progress_callback(0.15, "Extraction", "Extraction du texte du document...")
        
        # Extract text from the new document
        from document_manager import extract_text_from_file
        text = extract_text_from_file(document_path)
        
        if not text or len(text.strip()) < MIN_CHUNK_SIZE:
            return False, "Document is empty or too short to index", {}
        
        if progress_callback:
            progress_callback(0.30, "Découpage", "Découpage du document...")
        
        # Chunk the new document
        new_chunks = smart_chunk_text(text)
        
        if not new_chunks:
            return False, "No chunks created from document", {}
        
        if progress_callback:
            progress_callback(0.50, "Embeddings", f"Génération des embeddings pour {len(new_chunks)} chunks...")
        
        # Generate embeddings for new chunks
        new_embeddings = make_embeddings(new_chunks)
        
        if progress_callback:
            progress_callback(0.75, "Ajout", "Ajout à l'index...")
        
        # Add new embeddings to the existing index
        index.add(new_embeddings)
        
        # Update mapping data
        for chunk in new_chunks:
            urls.append(document_name)
            chunks.append(chunk)
            doc_indices.append(new_doc_idx)
        
        if progress_callback:
            progress_callback(0.90, "Sauvegarde", "Sauvegarde de l'index mis à jour...")
        
        # Save updated index
        faiss.write_index(index, INDEX_PATH)
        
        # Save updated mapping
        updated_mapping = {
            "urls": urls,
            "texts": chunks,
            "doc_indices": doc_indices
        }
        
        with open(MAPPING_PATH, "w", encoding="utf-8") as f:
            json.dump(updated_mapping, f, ensure_ascii=False, indent=2)
        
        if progress_callback:
            progress_callback(1.0, "Terminé", "Document ajouté avec succès !")
        
        # Prepare stats
        stats = {
            "chunks_added": len(new_chunks),
            "total_chunks": len(chunks),
            "document_name": document_name,
            "added_at": datetime.now().isoformat()
        }
        
        return True, f"Document added successfully with {len(new_chunks)} chunks", stats
    
    except Exception as e:
        return False, f"Error adding document to index: {str(e)}", {}


def get_index_stats() -> Dict[str, Any]:
    """
    Get statistics about the current index
    
    Returns:
        Dictionary with index statistics
    """
    stats = {
        "index_exists": os.path.exists(INDEX_PATH),
        "mapping_exists": os.path.exists(MAPPING_PATH),
        "document_count": 0,
        "chunk_count": 0,
        "embedding_dim": 0,
    }
    
    try:
        if stats["mapping_exists"]:
            with open(MAPPING_PATH, "r", encoding="utf-8") as f:
                mapping = json.load(f)
            
            stats["chunk_count"] = len(mapping.get("texts", []))
            
            # Count unique documents
            doc_indices = mapping.get("doc_indices", [])
            if doc_indices:
                stats["document_count"] = len(set(doc_indices))
        
        if stats["index_exists"]:
            index = faiss.read_index(INDEX_PATH)
            stats["embedding_dim"] = index.d
    
    except Exception as e:
        stats["error"] = str(e)
    
    return stats
