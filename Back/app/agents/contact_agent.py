"""
Agent de contact pour gérer les demandes de contact avec l'ESILV
"""
import os
import google.generativeai as genai
from typing import Dict, Any
from dotenv import load_dotenv

from base_agent import BaseAgent

load_dotenv()


class ContactAgent(BaseAgent):
    """
    Agent qui gère les demandes de contact avec l'ESILV
    """
    
    # Informations de contact de l'ESILV (à personnaliser selon vos besoins)
    CONTACT_INFO = {
        "adresse": "12 Avenue Léonard de Vinci, 92400 Courbevoie, France",
        "telephone": "+33 1 41 16 70 00",
        "email_general": "contact@esilv.fr",
        "email_admissions": "admissions@esilv.fr",
        "horaires": "Lundi - Vendredi: 9h00 - 18h00",
        "services": {
            "admissions": {
                "email": "admissions@esilv.fr",
                "description": "Pour toutes questions sur les admissions et inscriptions"
            },
            "scolarite": {
                "email": "scolarite@esilv.fr",
                "description": "Pour les questions relatives à la scolarité"
            },
            "international": {
                "email": "international@esilv.fr",
                "description": "Pour les étudiants internationaux"
            },
            "stages": {
                "email": "stages@esilv.fr",
                "description": "Pour les questions sur les stages et l'alternance"
            },
            "entreprises": {
                "email": "entreprises@esilv.fr",
                "description": "Pour les relations entreprises"
            }
        }
    }
    
    def __init__(self):
        super().__init__("Contact Agent")
        
        # Configurer Gemini pour générer des réponses personnalisées
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            genai.configure(api_key=api_key)
            self.llm = genai.GenerativeModel(os.getenv("GEMINI_MODEL", "gemini-2.5-flash"))
        else:
            self.llm = None
        
        print(f"✅ {self.name} initialisé avec succès")
    
    def can_handle(self, query: str, context: Dict[str, Any] = None) -> bool:
        """
        Détermine si cet agent peut traiter la requête
        Gère toutes les demandes de contact
        """
        query_lower = query.lower()
        
        # Mots-clés indiquant une demande de contact
        contact_keywords = [
            'contact', 'contacter', 'joindre', 'appeler', 'téléphone', 'email',
            'mail', 'écrire', 'parler', 'rencontrer', 'rendez-vous', 'rdv',
            'adresse', 'numéro', 'téléphoner', 'envoyer un message',
            'horaires', 'horaire d\'ouverture'
        ]
        
        return any(keyword in query_lower for keyword in contact_keywords)
    
    def _identify_service(self, query: str) -> str:
        """
        Identifie le service concerné par la demande
        
        Args:
            query: La requête utilisateur
            
        Returns:
            Nom du service identifié ou 'general'
        """
        query_lower = query.lower()
        
        # Mots-clés par service
        service_keywords = {
            "admissions": ["admission", "inscri", "candidat", "postuler", "intégrer"],
            "scolarite": ["scolarité", "notes", "bulletin", "cours", "emploi du temps"],
            "international": ["international", "étranger", "visa", "erasmus", "exchange"],
            "stages": ["stage", "alternance", "entreprise", "apprentissage"],
            "entreprises": ["partenariat", "recrut", "collaboration", "taxe d'apprentissage"]
        }
        
        for service, keywords in service_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                return service
        
        return "general"
    
    def _format_contact_response(self, query: str, service: str) -> str:
        """
        Formate une réponse de contact personnalisée
        
        Args:
            query: La requête utilisateur
            service: Le service identifié
            
        Returns:
            Réponse formatée
        """
        response_parts = []
        
        # Introduction
        if service != "general" and service in self.CONTACT_INFO["services"]:
            service_info = self.CONTACT_INFO["services"][service]
            response_parts.append(f"Pour {service_info['description'].lower()}, voici les coordonnées :\n")
            response_parts.append(f"📧 Email: {service_info['email']}\n")
        else:
            response_parts.append("Voici les coordonnées de l'ESILV :\n")
            response_parts.append(f"📧 Email général: {self.CONTACT_INFO['email_general']}\n")
        
        # Informations générales
        response_parts.append(f"📞 Téléphone: {self.CONTACT_INFO['telephone']}\n")
        response_parts.append(f"📍 Adresse: {self.CONTACT_INFO['adresse']}\n")
        response_parts.append(f"🕐 Horaires: {self.CONTACT_INFO['horaires']}\n")
        
        # Autres services disponibles
        if service == "general":
            response_parts.append("\nServices spécialisés :\n")
            for svc_name, svc_info in self.CONTACT_INFO["services"].items():
                response_parts.append(f"• {svc_name.capitalize()}: {svc_info['email']}\n")
        
        return "".join(response_parts)
    
    def process(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Traite la demande de contact
        
        Args:
            query: La requête utilisateur
            context: Contexte additionnel (optionnel)
            
        Returns:
            Informations de contact appropriées
        """
        try:
            # Identifier le service concerné
            service = self._identify_service(query)
            
            # Générer une réponse personnalisée avec Gemini si disponible
            if self.llm:
                try:
                    contact_info_str = self._format_contact_response(query, service)
                    
                    prompt = f"""Tu es un assistant pour l'ESILV. Un utilisateur demande des informations de contact.

Requête utilisateur: {query}

Informations de contact disponibles:
{contact_info_str}

Génère une réponse naturelle, amicale et personnalisée en français qui:
1. Répond directement à la demande de l'utilisateur
2. Fournit les informations de contact pertinentes
3. Reste concise et claire
4. Utilise des emojis appropriés

Réponse:"""
                    
                    response = self.llm.generate_content(prompt)
                    formatted_response = response.text.strip()
                    
                except Exception as e:
                    print(f"⚠️ Erreur Gemini, utilisation du format par défaut: {e}")
                    formatted_response = self._format_contact_response(query, service)
            else:
                formatted_response = self._format_contact_response(query, service)
            
            return {
                "success": True,
                "response": formatted_response,
                "service": service,
                "contact_info": self.CONTACT_INFO["services"].get(service, {})
            }
        
        except Exception as e:
            print(f"❌ Erreur lors du traitement de la demande de contact: {e}")
            return {
                "success": False,
                "error": str(e),
                "response": f"Voici les coordonnées générales de l'ESILV:\n"
                           f"📧 Email: {self.CONTACT_INFO['email_general']}\n"
                           f"📞 Téléphone: {self.CONTACT_INFO['telephone']}\n"
                           f"📍 Adresse: {self.CONTACT_INFO['adresse']}"
            }
    
    def get_description(self) -> str:
        """Retourne une description de l'agent"""
        return f"{self.name}: Fournit les informations de contact de l'ESILV"
