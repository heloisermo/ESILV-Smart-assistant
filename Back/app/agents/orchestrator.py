"""
Agent orchestrateur qui route les requêtes vers les agents appropriés
"""
import os
import re
import vertexai
from vertexai.generative_models import GenerativeModel
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

try:
    from .base_agent import BaseAgent
except ImportError:
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
        
        # Configurer Vertex AI
        project_id = os.getenv("VERTEX_PROJECT", "esilv-smart-assistant")
        location = os.getenv("VERTEX_LOCATION", "us-central1")
        
        try:
            vertexai.init(project=project_id, location=location)
            model_name = os.getenv("VERTEX_MODEL", "gemini-2.0-flash-exp")
            self.llm = GenerativeModel(model_name)
        except Exception as e:
            print(f"Erreur initialisation Vertex AI: {e}")
            self.llm = None
    
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
        
        # Utiliser Gemini pour une analyse plus fine si disponible
        if self.llm and not (has_contact or has_info):
            try:
                prompt = f"""Analyse cette requête et détermine l'intention principale.
Réponds UNIQUEMENT par un seul mot: 'information', 'contact', ou 'other'

Requête: {query}

Intention:"""
                response = self.llm.generate_content(prompt)
                intent = response.text.strip().lower()
                
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
        print(f"\nIntention détectée: {intent}")
        
        # Trouver le premier agent capable de traiter la requête
        for agent in self.agents:
            if agent.can_handle(query, context):
                print(f"Routage vers: {agent.name}")
                try:
                    result = agent.process(query, context)
                    result["agent_used"] = agent.name
                    result["intent"] = intent
                    return result
                except Exception as e:
                    print(f"Erreur lors du traitement par {agent.name}: {e}")
                    continue
        
        # Aucun agent spécialisé n'a pu traiter - utiliser le LLM générique comme fallback
        print("Aucun agent spécialisé disponible - utilisation du LLM générique")
        try:
            if self.llm:
                prompt = f"""Tu es un assistant virtuel de l'ESILV (École Supérieure d'Ingénieurs Léonard de Vinci).
Réponds de manière professionnelle et courtoise à cette question, même si tu n'as pas toutes les informations.
Si tu ne peux pas répondre précisément, oriente vers le site web de l'ESILV ou propose de contacter l'école.

Question: {query}

Réponse:"""
                response = self.llm.generate_content(prompt)
                return {
                    "success": True,
                    "agent_used": "llm_fallback",
                    "intent": intent,
                    "response": response.text,
                    "chunks": []
                }
        except Exception as e:
            print(f"Erreur LLM fallback: {e}")
        
        # Si même le LLM échoue, message professionnel
        return {
            "success": True,
            "agent_used": "fallback",
            "intent": intent,
            "response": "Je vous remercie pour votre question. Pour obtenir une réponse précise, je vous invite à consulter le site www.esilv.fr ou à contacter directement notre équipe d'admission.",
            "chunks": []
        }
    
    def route_stream(self, query: str, context: Dict[str, Any] = None):
        """
        Route la requête vers l'agent approprié en mode streaming
        
        Args:
            query: La requête utilisateur
            context: Contexte additionnel (optionnel)
            
        Yields:
            Chunks de la réponse de l'agent sélectionné
        """
        if not self.agents:
            yield {
                "success": False,
                "error": "Aucun agent disponible",
                "agent": "orchestrator"
            }
            return
        
        # Analyser l'intention
        intent = self._analyze_intent(query)
        print(f"\nIntention détectée: {intent}")
        
        # Trouver le premier agent capable de traiter la requête
        for agent in self.agents:
            if agent.can_handle(query, context):
                print(f"Routage vers: {agent.name}")
                try:
                    # Vérifier si l'agent supporte le streaming
                    if hasattr(agent, 'process_stream'):
                        for chunk in agent.process_stream(query, context):
                            chunk["agent_used"] = agent.name
                            chunk["intent"] = intent
                            yield chunk
                        return
                    else:
                        # Fallback sur process normal si pas de streaming
                        result = agent.process(query, context)
                        result["agent_used"] = agent.name
                        result["intent"] = intent
                        yield result
                        return
                except Exception as e:
                    print(f"Erreur lors du traitement par {agent.name}: {e}")
                    continue
        
        # Aucun agent spécialisé n'a pu traiter - utiliser le LLM générique comme fallback
        print("Aucun agent spécialisé disponible - utilisation du LLM générique")
        try:
            if self.llm:
                prompt = f"""Tu es un assistant virtuel de l'ESILV (École Supérieure d'Ingénieurs Léonard de Vinci).
Réponds de manière professionnelle et courtoise à cette question, même si tu n'as pas toutes les informations.
Si tu ne peux pas répondre précisément, oriente vers le site web de l'ESILV ou propose de contacter l'école.

Question: {query}

Réponse:"""
                response = self.llm.generate_content(prompt)
                yield {
                    "success": True,
                    "agent_used": "llm_fallback",
                    "intent": intent,
                    "response": response.text,
                    "chunks": []
                }
                return
        except Exception as e:
            print(f"Erreur LLM fallback: {e}")
        
        # Si même le LLM échoue, message professionnel
        yield {
            "success": True,
            "agent_used": "fallback",
            "intent": intent,
            "response": "Je vous remercie pour votre question. Pour obtenir une réponse précise, je vous invite à consulter le site www.esilv.fr ou à contacter directement notre équipe d'admission.",
            "chunks": []
        }
    
    def list_agents(self) -> List[str]:
        """Retourne la liste des agents enregistrés"""
        return [agent.name for agent in self.agents]
