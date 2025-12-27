"""
Classe de base pour tous les agents
"""
from abc import ABC, abstractmethod
from typing import Dict, Any


class BaseAgent(ABC):
    """Classe de base pour tous les agents du système"""
    
    def __init__(self, name: str):
        self.name = name
    
    @abstractmethod
    def can_handle(self, query: str, context: Dict[str, Any] = None) -> bool:
        """
        Détermine si cet agent peut traiter la requête
        
        Args:
            query: La requête utilisateur
            context: Contexte additionnel (optionnel)
            
        Returns:
            True si l'agent peut traiter la requête, False sinon
        """
        pass
    
    @abstractmethod
    def process(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Traite la requête utilisateur
        
        Args:
            query: La requête utilisateur
            context: Contexte additionnel (optionnel)
            
        Returns:
            Réponse de l'agent sous forme de dictionnaire
        """
        pass
    
    def get_description(self) -> str:
        """Retourne une description de l'agent"""
        return f"Agent: {self.name}"
