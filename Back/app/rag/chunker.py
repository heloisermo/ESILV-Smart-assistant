"""
Module pour découper les documents en chunks intelligents
"""
import re
from typing import List, Dict

def smart_chunk_text(
    text: str, 
    chunk_size: int = 1000, 
    overlap: int = 100,
    min_chunk_size: int = 200
) -> List[str]:
    """
    Découpe un texte en chunks de taille fixe avec overlap.
    
    Args:
        text: Le texte à découper
        chunk_size: Taille maximale d'un chunk (en caractères)
        overlap: Nombre de caractères de chevauchement entre chunks
        min_chunk_size: Taille minimale d'un chunk pour être conservé
        
    Returns:
        Liste de chunks de texte
    """
    if not text or len(text.strip()) < min_chunk_size:
        return []
    
    # Nettoyer le texte
    text = re.sub(r'\s+', ' ', text.strip())
    
    chunks = []
    start = 0
    
    while start < len(text):
        # Définir la fin du chunk
        end = start + chunk_size
        
        # Si on est à la fin du texte
        if end >= len(text):
            chunk = text[start:].strip()
            if len(chunk) >= min_chunk_size:
                chunks.append(chunk)
            break
        
        # Chercher une coupure naturelle (phrase complète)
        # On cherche un point suivi d'un espace dans les derniers 100 caractères
        search_start = max(start, end - 100)
        substring = text[search_start:end]
        
        # Chercher les délimiteurs de phrases
        sentence_ends = []
        for match in re.finditer(r'[.!?]\s+', substring):
            sentence_ends.append(search_start + match.end())
        
        if sentence_ends:
            # Prendre la dernière phrase complète
            end = sentence_ends[-1]
        
        chunk = text[start:end].strip()
        
        if len(chunk) >= min_chunk_size:
            chunks.append(chunk)
        
        # Déplacer le curseur avec overlap
        start = end - overlap
    
    return chunks


def chunk_documents(
    documents: Dict[str, str],
    chunk_size: int = 1000,
    overlap: int = 100,
    min_chunk_size: int = 200
) -> tuple[List[str], List[str], List[int]]:
    """
    Découpe une collection de documents en chunks.
    
    Args:
        documents: Dict {url: texte}
        chunk_size: Taille des chunks
        overlap: Chevauchement entre chunks
        min_chunk_size: Taille minimale d'un chunk
        
    Returns:
        Tuple (urls, chunks, doc_indices) où:
        - urls: Liste des URLs répétées pour chaque chunk
        - chunks: Liste des chunks de texte
        - doc_indices: Index du document original pour chaque chunk
    """
    all_urls = []
    all_chunks = []
    all_indices = []
    
    print(f"\nDecoupage des documents en chunks...")
    print(f"   Parametres: chunk_size={chunk_size}, overlap={overlap}")
    
    for doc_idx, (url, text) in enumerate(documents.items()):
        chunks = smart_chunk_text(
            text, 
            chunk_size=chunk_size, 
            overlap=overlap,
            min_chunk_size=min_chunk_size
        )
        
        if chunks:
            print(f"   {url[:60]}... → {len(chunks)} chunks")
            
            for chunk in chunks:
                all_urls.append(url)
                all_chunks.append(chunk)
                all_indices.append(doc_idx)
    
    print(f"\nTotal: {len(all_chunks)} chunks crees a partir de {len(documents)} documents")
    
    return all_urls, all_chunks, all_indices


if __name__ == "__main__":
    # Test
    test_text = """
    Ceci est un premier paragraphe. Il contient plusieurs phrases.
    Et voici une autre phrase pour tester le découpage.
    
    Voici un second paragraphe qui est assez long pour tester le système de chunking.
    Il devrait être découpé en plusieurs morceaux si nécessaire.
    Le système doit respecter les limites de taille tout en gardant des phrases complètes.
    
    Un troisième paragraphe pour bien tester. Avec encore plus de contenu.
    """
    
    chunks = smart_chunk_text(test_text, chunk_size=150, overlap=30)
    
    print(f"Nombre de chunks: {len(chunks)}")
    for i, chunk in enumerate(chunks, 1):
        print(f"\nChunk {i} ({len(chunk)} chars):")
        print(chunk[:100] + "..." if len(chunk) > 100 else chunk)
