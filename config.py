"""
Configuration et gestion des chemins pour ESILV Smart Assistant
Centralise la configuration des chemins pour éviter les conflits
entre les modules Assistant (interface utilisateur) et Administration
"""
import os
from pathlib import Path

# Get project root
PROJECT_ROOT = Path(__file__).parent.absolute()

# Back-end paths
BACK_DIR = PROJECT_ROOT / "Back"
APP_DIR = BACK_DIR / "app"
RAG_DIR = APP_DIR / "rag"
AGENTS_DIR = APP_DIR / "agents"
ADMIN_PAGES_DIR = PROJECT_ROOT / "admin_pages"

# Data directories
DATA_DIR = PROJECT_ROOT / "data"
LEADS_DATA_DIR = DATA_DIR / "leads"
UPLOADS_DIR = DATA_DIR / "uploads"
ARCHIVE_DIR = DATA_DIR / "archive"

# Index files
FAISS_INDEX_PATH = DATA_DIR / "faiss_index.bin"
FAISS_MAPPING_PATH = DATA_DIR / "faiss_mapping.json"
DOCUMENTS_METADATA_PATH = DATA_DIR / "documents_metadata.json"
LEADS_FILE_PATH = LEADS_DATA_DIR / "leads.json"
PROCESSED_DOCUMENTS_PATH = DATA_DIR / "processed_documents.json"

# Scraped data
SCRAPED_DATA_PATH = DATA_DIR / "scraped_data.json"

# Environment
ENV_FILE = PROJECT_ROOT / ".env"


def ensure_directories():
    """Crée tous les répertoires nécessaires s'ils n'existent pas"""
    directories = [
        DATA_DIR,
        LEADS_DATA_DIR,
        UPLOADS_DIR,
        ARCHIVE_DIR,
        RAG_DIR,
        AGENTS_DIR,
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)


def get_backend_paths():
    """Retourne un dictionnaire de tous les chemins backend"""
    return {
        "app_dir": str(APP_DIR),
        "rag_dir": str(RAG_DIR),
        "agents_dir": str(AGENTS_DIR),
        "data_dir": str(DATA_DIR),
    }


def get_admin_paths():
    """Retourne un dictionnaire de tous les chemins liés à l'administration"""
    return {
        "leads_dir": str(LEADS_DATA_DIR),
        "leads_file": str(LEADS_FILE_PATH),
        "uploads_dir": str(UPLOADS_DIR),
        "documents_metadata": str(DOCUMENTS_METADATA_PATH),
        "processed_documents": str(PROCESSED_DOCUMENTS_PATH),
        "index_file": str(FAISS_INDEX_PATH),
        "mapping_file": str(FAISS_MAPPING_PATH),
    }
