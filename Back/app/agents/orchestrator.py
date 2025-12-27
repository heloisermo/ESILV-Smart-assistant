"""
Agent orchestrateur qui route les requêtes vers les agents appropriés
"""
import os
import re
import requests
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

from base_agent import BaseAgent

load_dotenv()


class OrchestratorAgent:
    """
    Agent orchestrateur qui analyse les requêtes et les route vers l'agent approprié
    """
    
    def __init__(self, agents: Optional[List[BaseAgent]] = None):
        """
        Initialise l'orchestrateur avec une liste d'agents
        
        Args:
            agents: Liste des agents disponibles
        """
        self.agents = agents or []
        
        # Configurer Vertex AI pour l'analyse d'intention
        self.api_key = os.getenv("VERTEX_API_KEY")
        if self.api_key:
            model = os.getenv("VERTEX_MODEL", "gemini-2.0-flash-exp")
            self.api_endpoint = f"https://aiplatform.googleapis.com/v1/publishers/google/models/{model}:generateContent"
        else:
            self.api_endpoint = None
    
    def register_agent(self, agent: BaseAgent):
        """Enregistre un nouvel agent"""
        self.agents.append(agent)
        print(f"Agent enregistré: {agent.name}")
    
    def _analyze_intent(self, query: str) -> str:
        """
        Analyse l'intention de la requête utilisateur
        
        Args:
            query: La requête utilisateur
            
        Returns:
            Type d'intention détecté: 'information', 'contact', 'other'
        """
        query_lower = query.lower()
        
        # Mots-clés pour détecter une demande de contact
        contact_keywords = [
            'contact', 'contacter', 'joindre', 'appeler', 'téléphone', 'email',
            'mail', 'écrire', 'parler', 'rencontrer', 'rendez-vous', 'rdv',
            'adresse', 'numéro', 'téléphoner', 'envoyer un message'
        ]
        
        # Mots-clés pour détecter une demande d'information
        info_keywords = [
            'qu\'est-ce', 'c\'est quoi', 'comment', 'pourquoi', 'quand', 'où',
            'qui', 'quel', 'quelle', 'info', 'information', 'renseignement',
            'savoir', 'connaître', 'expliquer', 'présenter', 'décrire',
            'programme', 'cours', 'formation', 'admission', 'étudier'
        ]
        
        # Détection basée sur les mots-clés
        has_contact = any(keyword in query_lower for keyword in contact_keywords)
        has_info = any(keyword in query_lower for keyword in info_keywords)
        
        # Utiliser Vertex AI pour une analyse plus fine si disponible
        if self.api_endpoint and not (has_contact or has_info):
            try:
                prompt = f"""Analyse cette requête et détermine l'intention principale.
Réponds UNIQUEMENT par un seul mot: 'information', 'contact', ou 'other'

Requête: {query}

Intention:"""
                
                url = f"{self.api_endpoint}?key={self.api_key}"
                payload = {
                    "contents": [{"role": "user", "parts": [{"text": prompt}]}]
                }
                response = requests.post(url, headers={"Content-Type": "application/json"}, json=payload, timeout=10)
                response.raise_for_status()
                
                result = response.json()
                if "candidates" in result and len(result["candidates"]) > 0:
                    intent = result["candidates"][0]["content"]["parts"][0]["text"].strip().lower()
                    if intent in ['information', 'contact', 'other']:
                        return intent
            except Exception as e:
                print(f"Erreur lors de l'analyse d'intention avec LLM: {e}")
        
        # Logique de décision basée sur les mots-clés
        if has_contact:
            return 'contact'
        elif has_info:
            return 'information'
        else:
            # Par défaut, considérer comme une demande d'information
            return 'information'
    
    def route(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Route la requête vers l'agent approprié
        
        Args:
            query: La requête utilisateur
            context: Contexte additionnel (optionnel)
            
        Returns:
            Réponse de l'agent sélectionné
        """
        if not self.agents:
            return {
                "success": False,
                "error": "Aucun agent disponible",
                "agent": "orchestrator"
            }
        
        # Analyser l'intention
        intent = self._analyze_intent(query)
        print(f"\n🎯 Intention détectée: {intent}")
        
        # Trouver le premier agent capable de traiter la requête
        for agent in self.agents:
            if agent.can_handle(query, context):
                print(f"✅ Routage vers: {agent.name}")
                try:
                    result = agent.process(query, context)
                    result["agent_used"] = agent.name
                    result["intent"] = intent
                    return result
                except Exception as e:
                    print(f"❌ Erreur lors du traitement par {agent.name}: {e}")
                    continue
        
        # Aucun agent n'a pu traiter la requête
        return {
            "success": False,
            "error": "Aucun agent n'a pu traiter cette requête",
            "agent_used": "none",
            "intent": intent,
            "response": "Désolé, je ne peux pas traiter cette demande pour le moment."
        }
    
    def list_agents(self) -> List[str]:
        """Retourne la liste des agents enregistrés"""
        return [agent.name for agent in self.agents]
