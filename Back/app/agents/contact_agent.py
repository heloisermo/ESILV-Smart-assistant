"""
Agent de contact pour gérer les demandes de contact avec l'ESILV
"""
import os
import json
import requests
from typing import Dict, Any
from datetime import datetime
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
        
        # Configurer Vertex AI pour générer des réponses personnalisées
        self.api_key = os.getenv("VERTEX_API_KEY")
        if self.api_key:
            model = os.getenv("VERTEX_MODEL", "gemini-2.0-flash-exp")
            self.api_endpoint = f"https://aiplatform.googleapis.com/v1/publishers/google/models/{model}:generateContent"
        else:
            self.api_endpoint = None
        
        print(f"✅ {self.name} initialisé avec succès")
    
    def can_handle(self, query: str, context: Dict[str, Any] = None) -> bool:
        """
        Détermine si cet agent peut traiter la requête
        Gère les demandes de contact actives (formulaire)
        """
        query_lower = query.lower()
        
        # Mots-clés indiquant une VOLONTÉ DE CONTACTER (pas juste avoir les coordonnées)
        contact_action_keywords = [
            'contacter', 'joindre', 'écrire', 'parler à', 'parler avec',
            'rencontrer', 'rendez-vous', 'rdv', 'envoyer un message',
            'je veux contacter', 'je voudrais contacter', 'j\'aimerais contacter',
            'envoyer un email', 'envoyer un mail', 'prendre contact'
        ]
        
        return any(keyword in query_lower for keyword in contact_action_keywords)
    
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
        Traite la demande de contact en créant un formulaire
        
        Args:
            query: La requête utilisateur
            context: Contexte additionnel (optionnel)
            
        Returns:
            Formulaire de contact à remplir
        """
        try:
            # Identifier le service concerné
            service = self._identify_service(query)
            service_info = self.CONTACT_INFO["services"].get(service, {
                "email": self.CONTACT_INFO["email_general"],
                "description": "Service général"
            })
            
            # Créer un formulaire de contact
            contact_form = {
                "service": service,
                "service_email": service_info["email"],
                "service_description": service_info["description"],
                "fields": {
                    "nom": None,
                    "prenom": None,
                    "email": None,
                    "telephone": None,
                    "objet": None,
                    "message": None
                },
                "status": "pending"
            }
            
            # Générer une réponse pour demander les informations
            response_text = self._generate_form_request(query, service, service_info)
            
            return {
                "success": True,
                "response": response_text,
                "requires_form": True,
                "form": contact_form,
                "service": service,
                "next_action": "collect_user_info"
            }
        
        except Exception as e:
            print(f"❌ Erreur lors du traitement de la demande de contact: {e}")
            return {
                "success": False,
                "error": str(e),
                "response": "Désolé, je n'ai pas pu créer le formulaire de contact. "
                           f"Vous pouvez contacter directement: {self.CONTACT_INFO['email_general']}"
            }
    
    def _generate_form_request(self, query: str, service: str, service_info: Dict) -> str:
        """
        Génère une demande de remplissage de formulaire
        """
        if self.api_endpoint:
            try:
                prompt = f"""Tu es un assistant pour l'ESILV. Un utilisateur veut contacter le service {service}.

Requête: {query}
Service concerné: {service_info['description']}
Email du service: {service_info['email']}

Génère une réponse courte et amicale en français qui:
1. Confirme que tu vas l'aider à contacter le service
2. Demande les informations suivantes de manière naturelle:
   - Nom et prénom
   - Email
   - Téléphone (optionnel)
   - Objet de la demande
   - Message détaillé
3. Reste concise (3-4 phrases maximum)
4. Utilise des emojis appropriés

Réponse:"""
                
                url = f"{self.api_endpoint}?key={self.api_key}"
                payload = {
                    "contents": [{"role": "user", "parts": [{"text": prompt}]}]
                }
                response = requests.post(url, headers={"Content-Type": "application/json"}, json=payload, timeout=15)
                response.raise_for_status()
                
                result = response.json()
                if "candidates" in result and len(result["candidates"]) > 0:
                    return result["candidates"][0]["content"]["parts"][0]["text"].strip()
            except Exception as e:
                print(f"⚠️ Erreur Vertex AI: {e}")
        
        # Réponse par défaut
        return (
            f"📝 Parfait ! Je vais vous aider à contacter {service_info['description'].lower()}.\n\n"
            f"Pour que je puisse transmettre votre demande au service concerné ({service_info['email']}), "
            f"j'ai besoin des informations suivantes :\n\n"
            f"• Nom et prénom\n"
            f"• Email\n"
            f"• Téléphone (optionnel)\n"
            f"• Objet de votre demande\n"
            f"• Votre message détaillé\n\n"
            f"Pouvez-vous me fournir ces informations ?"
        )
    
    def validate_and_submit_form(self, form_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Valide et soumet le formulaire de contact
        
        Args:
            form_data: Données du formulaire remplies
            
        Returns:
            Résultat de la soumission
        """
        required_fields = ["nom", "prenom", "email", "objet", "message"]
        missing_fields = [field for field in required_fields if not form_data.get(field)]
        
        if missing_fields:
            return {
                "success": False,
                "error": f"Champs manquants: {', '.join(missing_fields)}",
                "missing_fields": missing_fields
            }
        
        # Sauvegarder le formulaire dans un fichier
        self._save_form_to_file(form_data)
        
        return {
            "success": True,
            "response": f"✅ Votre demande a été transmise au service {form_data.get('service', 'concerné')}!\n"
                      f"Vous recevrez une réponse à l'adresse: {form_data.get('email')}\n\n"
                      f"📧 Email de contact: {form_data.get('service_email', 'contact@esilv.fr')}\n\n"
                      f"📄 Le formulaire a été sauvegardé dans: contact_forms.json",
            "form_data": form_data
        }
    
    def _save_form_to_file(self, form_data: Dict[str, Any]):
        """Sauvegarde le formulaire dans un fichier JSON"""
        import json
        from datetime import datetime
        
        # Ajouter un timestamp
        form_with_timestamp = {
            "timestamp": datetime.now().isoformat(),
            "status": "pending",
            **form_data
        }
        
        # Charger les formulaires existants
        forms_file = "contact_forms.json"
        try:
            if os.path.exists(forms_file):
                with open(forms_file, "r", encoding="utf-8") as f:
                    forms = json.load(f)
            else:
                forms = []
        except:
            forms = []
        
        # Ajouter le nouveau formulaire
        forms.append(form_with_timestamp)
        
        # Sauvegarder
        with open(forms_file, "w", encoding="utf-8") as f:
            json.dump(forms, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Formulaire sauvegardé dans {forms_file}")
    
    def get_description(self) -> str:
        """Retourne une description de l'agent"""
        return f"{self.name}: Crée des formulaires de contact pour l'ESILV"