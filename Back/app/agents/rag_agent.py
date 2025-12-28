"""
Agent RAG pour répondre aux questions sur l'ESILV
"""
import sys
import os
from typing import Dict, Any
from dotenv import load_dotenv

# Charger les variables d'environnement depuis la racine du projet
env_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', '.env')
load_dotenv(env_path)

# Ajouter le chemin du module rag
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'rag'))

from .base_agent import BaseAgent


class RAGAgent(BaseAgent):
    """
    Agent qui utilise le système RAG pour répondre aux questions sur l'ESILV
    """
    
    def __init__(self):
        super().__init__("RAG Agent")
        self.rag_system = None
        self._initialize_rag()
    
    def _initialize_rag(self):
        """Initialise le système RAG"""
        try:
            # Définir le répertoire du module rag
            rag_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'rag'))
            
            # Sauvegarder le répertoire actuel
            original_dir = os.getcwd()
            
            # Charger le .env depuis la racine AVANT de changer de dossier
            env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '.env'))
            load_dotenv(env_path)
            
            # Vérifier que Vertex AI est configuré
            project_id = os.getenv("VERTEX_PROJECT")
            if not project_id:
                print(f"VERTEX_PROJECT non trouvé. Chemin .env: {env_path}")
                self.rag_system = None
                return
            
            # Changer vers le dossier rag pour charger les fichiers FAISS
            os.chdir(rag_dir)
            
            from rag import FaissRAGGemini
            self.rag_system = FaissRAGGemini()
            
            # Revenir au répertoire original
            os.chdir(original_dir)
            
            print(f"{self.name} initialisé avec succès")
        except Exception as e:
            print(f"Erreur lors de l'initialisation du RAG: {e}")
            import traceback
            traceback.print_exc()
            self.rag_system = None
            # Revenir au répertoire original même en cas d'erreur
            try:
                os.chdir(original_dir)
            except:
                pass
    
    def can_handle(self, query: str, context: Dict[str, Any] = None) -> bool:
        """
        Détermine si cet agent peut traiter la requête
        """
        if not self.rag_system:
            return False
        
        query_lower = query.lower()
        
        # Mots-clés de contact à éviter
        contact_keywords = [
            'contacter', 'joindre', 'appeler', 'téléphone', 'email',
            'mail', 'écrire', 'parler', 'rencontrer', 'rendez-vous'
        ]
        
        is_contact_request = any(keyword in query_lower for keyword in contact_keywords)
        
        return not is_contact_request
    
    def process(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Traite la requête en utilisant le système RAG
        
        Args:
            query: La requête utilisateur
            context: Contexte additionnel (optionnel)
            
        Returns:
            Réponse de l'agent avec le contexte RAG
        """
        if not self.rag_system:
            return {
                "success": False,
                "error": "Le système RAG n'est pas disponible",
                "response": "Désolé, le système de réponse n'est pas disponible actuellement."
            }
        
        try:
            # Récupérer le nombre de chunks à rechercher depuis le contexte
            k = context.get('k', 5) if context else 5
            
            # Utiliser la méthode answer() du système RAG
            response, chunks = self.rag_system.answer(query, k=k)
            
            return {
                "success": True,
                "response": response,
                "chunks": chunks,
                "num_chunks": len(chunks)
            }
        
        except Exception as e:
            print(f"❌ Erreur lors du traitement RAG: {e}")
            return {
                "success": False,
                "error": str(e),
                "response": "Désolé, une erreur s'est produite lors de la recherche d'informations."
            }
    
    def get_description(self) -> str:
        """Retourne une description de l'agent"""
        return f"{self.name}: Répond aux questions sur l'ESILV en utilisant le système RAG"
