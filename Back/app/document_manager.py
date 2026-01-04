"""
Module de gestion des documents uploadés
Gère le traitement, le stockage et le suivi des métadonnées des documents
"""
import os
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# Add project root to path for config import
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

try:
    from config import UPLOADS_DIR, PROCESSED_DOCUMENTS_PATH
    UPLOAD_DIR = str(UPLOADS_DIR)
    PROCESSED_DOCUMENTS_FILE = str(PROCESSED_DOCUMENTS_PATH)
except ImportError:
    # Fallback to defaults if config not available
    UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "uploads")
    PROCESSED_DOCUMENTS_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "data", "processed_documents.json")

try:
    import PyPDF2
except ImportError:
    PyPDF2 = None


def ensure_upload_dir():
    """Crée le répertoire uploads s'il n'existe pas"""
    os.makedirs(UPLOAD_DIR, exist_ok=True)


def _get_file_type(filename: str) -> str:
    """Extrait le type de fichier depuis le nom du fichier"""
    ext = os.path.splitext(filename)[1].lower()
    
    if ext == ".pdf":
        return "pdf"
    elif ext in [".html", ".htm"]:
        return "html"
    elif ext == ".txt":
        return "txt"
    else:
        return "other"


def _get_file_size(file_path: str) -> int:
    """Retourne la taille du fichier en octets"""
    try:
        return os.path.getsize(file_path)
    except OSError:
        return 0


def _load_processed_documents() -> Dict[str, Any]:
    """Charge les métadonnées des documents traités"""
    if not os.path.exists(PROCESSED_DOCUMENTS_FILE):
        return {}
    
    try:
        with open(PROCESSED_DOCUMENTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}


def _save_processed_documents(documents: Dict[str, Any]):
    """Sauvegarde les métadonnées des documents traités"""
    os.makedirs(os.path.dirname(PROCESSED_DOCUMENTS_FILE), exist_ok=True)
    
    with open(PROCESSED_DOCUMENTS_FILE, "w", encoding="utf-8") as f:
        json.dump(documents, f, ensure_ascii=False, indent=2)


def extract_pdf_text(file_path: str) -> Tuple[str, int]:
    """
    Extract text from PDF file
    
    Args:
        file_path: Path to PDF file
        
    Returns:
        Tuple of (text content, page count)
    """
    if PyPDF2 is None:
        raise Exception("PyPDF2 is not installed. Please install it: pip install PyPDF2")
    
    try:
        text_parts = []
        page_count = 0
        
        with open(file_path, "rb") as f:
            pdf_reader = PyPDF2.PdfReader(f)
            page_count = len(pdf_reader.pages)
            
            for page in pdf_reader.pages:
                text = page.extract_text()
                if text:
                    text_parts.append(text)
        
        return "\n".join(text_parts), page_count
    except Exception as e:
        raise Exception(f"Error extracting PDF text: {str(e)}")


def extract_html_text(file_path: str) -> str:
    """
    Extract text from HTML file
    
    Args:
        file_path: Path to HTML file
        
    Returns:
        Text content
    """
    try:
        from bs4 import BeautifulSoup
        
        with open(file_path, "r", encoding="utf-8") as f:
            soup = BeautifulSoup(f, "html.parser")
            
            # Remove script and style elements
            for tag in soup(["script", "style"]):
                tag.extract()
            
            # Get text
            text = soup.get_text()
            
            # Clean up whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = " ".join(chunk for chunk in chunks if chunk)
            
            return text
    except Exception as e:
        raise Exception(f"Error extracting HTML text: {str(e)}")


def extract_text_file(file_path: str) -> str:
    """
    Extract text from plain text file
    
    Args:
        file_path: Path to text file
        
    Returns:
        Text content
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        raise Exception(f"Error reading text file: {str(e)}")


def save_uploaded_document(
    file_content: bytes,
    filename: str,
    file_type: Optional[str] = None
) -> Tuple[bool, str, str]:
    """
    Save an uploaded document to the upload directory
    
    Args:
        file_content: File content as bytes
        filename: Original filename
        file_type: File type (pdf, html, txt). If None, detected from filename
        
    Returns:
        Tuple of (success: bool, message: str, file_path: str)
    """
    ensure_upload_dir()
    
    try:
        # Detect file type if not provided
        if not file_type:
            file_type = _get_file_type(filename)
        
        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_")
        safe_filename = "".join(c for c in filename if c.isalnum() or c in "._- ")
        unique_filename = timestamp + safe_filename
        
        file_path = os.path.join(UPLOAD_DIR, unique_filename)
        
        # Save file
        with open(file_path, "wb") as f:
            f.write(file_content)
        
        return True, f"File saved successfully", file_path
    
    except Exception as e:
        return False, f"Error saving file: {str(e)}", ""


def process_document(
    file_path: str,
    filename: str,
    file_type: Optional[str] = None
) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Process an uploaded document and extract content
    
    Args:
        file_path: Path to the file
        filename: Original filename
        file_type: File type (pdf, html, txt). If None, detected from filename
        
    Returns:
        Tuple of (success: bool, message: str, document_info: dict)
    """
    try:
        if not file_type:
            file_type = _get_file_type(filename)
        
        # Extract content based on file type
        if file_type == "pdf":
            content, page_count = extract_pdf_text(file_path)
            additional_info = {"pages": page_count}
        elif file_type == "html":
            content = extract_html_text(file_path)
            additional_info = {}
        elif file_type == "txt":
            content = extract_text_file(file_path)
            additional_info = {}
        else:
            return False, f"Unsupported file type: {file_type}", {}
        
        file_size = _get_file_size(file_path)
        
        doc_info = {
            "filename": filename,
            "file_type": file_type,
            "file_size": file_size,
            "content": content,
            "content_length": len(content),
            "uploaded_at": datetime.now().isoformat(),
            **additional_info
        }
        
        return True, "Document processed successfully", doc_info
    
    except Exception as e:
        return False, f"Error processing document: {str(e)}", {}


def register_processed_document(
    doc_id: str,
    original_filename: str,
    file_type: str,
    file_size: int,
    content_length: int,
    saved_path: str
) -> Dict[str, Any]:
    """
    Register a processed document in metadata
    
    Args:
        doc_id: Unique document ID
        original_filename: Original filename
        file_type: Document type (pdf, html, txt)
        file_size: File size in bytes
        content_length: Length of extracted content
        saved_path: Path where file is saved
        
    Returns:
        The registered document metadata
    """
    documents = _load_processed_documents()
    
    doc_metadata = {
        "id": doc_id,
        "filename": original_filename,
        "type": file_type,
        "file_size": file_size,
        "content_length": content_length,
        "saved_path": saved_path,
        "uploaded_at": datetime.now().isoformat(),
        "indexed": False
    }
    
    documents[doc_id] = doc_metadata
    _save_processed_documents(documents)
    
    return doc_metadata


def get_processed_documents() -> List[Dict[str, Any]]:
    """Get all processed documents metadata"""
    documents = _load_processed_documents()
    return list(documents.values())


def mark_document_as_indexed(doc_id: str, chunk_count: int) -> bool:
    """
    Mark a document as indexed
    
    Args:
        doc_id: Document ID
        chunk_count: Number of chunks created
        
    Returns:
        True if successful
    """
    documents = _load_processed_documents()
    
    if doc_id in documents:
        documents[doc_id]["indexed"] = True
        documents[doc_id]["chunk_count"] = chunk_count
        documents[doc_id]["indexed_at"] = datetime.now().isoformat()
        _save_processed_documents(documents)
        return True
    
    return False


def delete_document(doc_id: str) -> bool:
    """
    Delete a document and its metadata
    
    Args:
        doc_id: Document ID
        
    Returns:
        True if successful
    """
    documents = _load_processed_documents()
    
    if doc_id in documents:
        doc_info = documents[doc_id]
        
        # Delete file if it exists
        if os.path.exists(doc_info.get("saved_path", "")):
            try:
                os.remove(doc_info["saved_path"])
            except OSError:
                pass
        
        # Delete metadata
        del documents[doc_id]
        _save_processed_documents(documents)
        return True
    
    return False


def search_documents(query: str) -> List[Dict[str, Any]]:
    """
    Search documents by filename
    
    Args:
        query: Search query
        
    Returns:
        List of matching documents
    """
    documents = _load_processed_documents()
    query_lower = query.lower()
    
    results = []
    for doc in documents.values():
        if query_lower in doc.get("filename", "").lower():
            results.append(doc)
    
    return results


def extract_text_from_file(file_path: str) -> str:
    """
    Extract text from any supported file type (PDF, HTML, TXT)
    
    Args:
        file_path: Path to the file
        
    Returns:
        Extracted text content
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    file_type = _get_file_type(os.path.basename(file_path))
    
    try:
        if file_type == "pdf":
            text, _ = extract_pdf_text(file_path)
            return text
        elif file_type == "html":
            return extract_html_text(file_path)
        elif file_type == "txt":
            return extract_text_file(file_path)
        else:
            # Try text file as fallback
            return extract_text_file(file_path)
    except Exception as e:
        print(f"Error extracting text from {file_path}: {e}")
        return ""
