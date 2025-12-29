"""
Système multi-agents pour l'assistant ESILV
Démontre l'utilisation de l'orchestrateur avec les différents agents
"""
import sys
import os
import requests
import json
import re

# Ajouter les chemins nécessaires
sys.path.insert(0, os.path.dirname(__file__))

from orchestrator import OrchestratorAgent
from rag_agent import RAGAgent
from contact_agent import ContactAgent


def main():
    """Fonction principale pour tester le système multi-agents"""
    
    print("=" * 70)
    print("SYSTÈME MULTI-AGENTS ESILV")
    print("=" * 70)
    print()
    
    # Initialiser l'orchestrateur
    print("Initialisation de l'orchestrateur...")
    orchestrator = OrchestratorAgent()
    
    # Créer et enregistrer les agents
    print("Création des agents...")
    
    try:
        rag_agent = RAGAgent()
        orchestrator.register_agent(rag_agent)
    except Exception as e:
        print(f"Impossible d'initialiser le RAG Agent: {e}")
    
    contact_agent = ContactAgent()
    orchestrator.register_agent(contact_agent)
    
    print()
    print(f"Agents enregistrés: {', '.join(orchestrator.list_agents())}")
    print()
    print("=" * 70)
    print("MODE INTERACTIF")
    print("=" * 70)
    print("Tapez vos questions (ou 'quit' pour quitter):")
    print()
    
    # État de la conversation
    conversation_state = {
        "pending_form": None,  # Formulaire en attente
        "agent": None  # Agent en cours
    }
    
    while True:
        try:
            user_input = input("\nVous: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("\nAu revoir!")
                break
            
            print()
            
            # Si un formulaire est en attente, traiter la réponse comme des données de formulaire
            if conversation_state["pending_form"]:
                result = handle_form_input(user_input, conversation_state, contact_agent)
            else:
                result = orchestrator.route(user_input)
            
            if result.get('success'):
                print(f"Assistant ({result.get('agent_used', 'N/A')}): ")
                print(f"{result.get('response', 'Pas de réponse')}")
                
                # Afficher les infos supplémentaires si formulaire de contact
                if result.get('requires_form'):
                    print("\nFormulaire de contact créé:")
                    print(f"   Service: {result.get('service')}")
                    print(f"   Email: {result['form']['service_email']}")
                    # Sauvegarder l'état du formulaire
                    conversation_state["pending_form"] = result["form"]
                    conversation_state["agent"] = "contact"
                elif result.get('form_submitted'):
                    # Réinitialiser l'état après soumission
                    conversation_state["pending_form"] = None
                    conversation_state["agent"] = None
            else:
                print(f"Erreur: {result.get('error', 'Erreur inconnue')}")
        
        except KeyboardInterrupt:
            print("\n\nAu revoir!")
            break
        except Exception as e:
            print(f"\nErreur: {e}")


def handle_form_input(user_input: str, state: dict, contact_agent) -> dict:
    """Traite les entrées utilisateur pour remplir le formulaire avec l'aide du LLM"""
    form = state["pending_form"]
    
    # Utiliser le LLM pour extraire les informations
    form_data = extract_form_data_with_llm(user_input, form["fields"], contact_agent)
    
    if form_data is None:
        return {
            "success": False,
            "agent_used": "Contact Agent",
            "response": "Désolé, je n'ai pas pu analyser vos informations. Pouvez-vous réessayer ?"
        }
    
    # Mettre à jour le formulaire
    for key, value in form_data.items():
        if value:  # Ne pas écraser avec des valeurs vides
            form["fields"][key] = value
    
    # Vérifier si tous les champs requis sont remplis
    required_fields = ["nom", "prenom", "email", "objet", "message"]
    missing = [f for f in required_fields if not form["fields"].get(f)]
    
    if missing:
        # Générer une demande naturelle avec le LLM
        missing_request = generate_missing_fields_request(missing, contact_agent)
        return {
            "success": True,
            "agent_used": "Contact Agent",
            "response": missing_request or f"Il me manque encore : {', '.join(missing)}. Pouvez-vous me les fournir ?"
        }
    
    # Soumettre le formulaire
    submit_data = {**form["fields"], "service": form["service"], "service_email": form["service_email"]}
    result = contact_agent.validate_and_submit_form(submit_data)
    result["form_submitted"] = True
    result["agent_used"] = "Contact Agent"
    
    return result


def extract_form_data_with_llm(user_input: str, current_fields: dict, contact_agent) -> dict:
    """Utilise le LLM pour extraire les données du formulaire depuis le message utilisateur"""
    if not contact_agent.llm:
        # Fallback: parser manuel simple
        return parse_user_input(user_input)
    
    try:
        current_state = "\n".join([f"- {k}: {v or 'Non fourni'}" for k, v in current_fields.items()])
        
        prompt = f"""Tu es un assistant qui extrait des informations d'un formulaire de contact.

Message de l'utilisateur: "{user_input}"

État actuel du formulaire:
{current_state}

Extrais les informations suivantes du message et retourne-les au format JSON strict (uniquement le JSON, rien d'autre):
{{
  "nom": "nom de famille ou null",
  "prenom": "prénom ou null",
  "email": "adresse email ou null",
  "telephone": "numéro de téléphone ou null",
  "objet": "objet/sujet de la demande ou null",
  "message": "message détaillé ou null"
}}

Règles:
- Si une information n'est pas fournie, mets null
- Ne garde que ce qui est NOUVEAU dans le message (ne répète pas ce qui est déjà dans l'état actuel)
- L'email doit contenir un @
- Si l'utilisateur donne "Nom Prénom", le premier mot est le prénom, le reste est le nom
- Si c'est juste un texte sans structure, c'est probablement l'objet ou le message

JSON:"""
        
        response = contact_agent.llm.generate_content(prompt)
        llm_response = response.text.strip()
        
        # Extraire le JSON de la réponse
        import json
        import re
        
        # Chercher le JSON dans la réponse
        json_match = re.search(r'\{[\s\S]*\}', llm_response)
        if json_match:
            form_data = json.loads(json_match.group())
            # Convertir les null en None
            return {k: v if v != "null" and v else None for k, v in form_data.items()}
        
    except Exception as e:
        print(f"Erreur LLM extraction: {e}")
    
    # Fallback: parser manuel
    return parse_user_input(user_input)


def generate_missing_fields_request(missing_fields: list, contact_agent) -> str:
    """Génère une demande naturelle pour les champs manquants avec le LLM"""
    if not contact_agent.llm:
        return None
    
    try:
        prompt = f"""Tu es un assistant pour l'ESILV. L'utilisateur remplit un formulaire de contact mais il manque ces informations:
{', '.join(missing_fields)}

Génère une courte phrase amicale en français (1-2 phrases max) pour demander ces informations manquantes.
Reste naturel.

Réponse:"""
        
        response = contact_agent.llm.generate_content(prompt)
        return response.text.strip()
    except:
        pass
    
    return None


def parse_user_input(text: str) -> dict:
    """Parse l'entrée utilisateur pour extraire les données du formulaire"""
    data = {}
    
    # Séparer par virgules et analyser
    parts = [p.strip() for p in text.split(',')]
    
    # Essayer de détecter les champs
    for part in parts:
        # Email
        if '@' in part and not data.get('email'):
            data['email'] = part.strip()
        # Objet
        elif 'objet' in part.lower() and ':' in part:
            data['objet'] = part.split(':', 1)[1].strip()
        # Message
        elif 'message' in part.lower() and ':' in part:
            data['message'] = part.split(':', 1)[1].strip()
        # Téléphone (commence par + ou contient que des chiffres)
        elif part.replace('+', '').replace(' ', '').replace('.', '').isdigit():
            data['telephone'] = part.strip()
        # Nom et prénom (premier élément sans mot-clé spécial)
        elif not data.get('nom') and not any(k in part.lower() for k in ['objet', 'message', '@']):
            names = part.split()
            if len(names) >= 2:
                data['prenom'] = names[0]
                data['nom'] = ' '.join(names[1:])
            elif len(names) == 1:
                data['nom'] = names[0]
    
    # Si l'objet n'a pas été trouvé mais qu'il y a encore du texte, utiliser comme objet
    if not data.get('objet') and not data.get('message'):
        # Chercher le texte après les infos de base
        remaining = text
        for key in ['email', 'telephone']:
            if key in data:
                remaining = remaining.replace(data[key], '')
        remaining = remaining.strip(', ')
        if remaining and not remaining.startswith(data.get('nom', '')):
            data['objet'] = remaining
    
    return data


if __name__ == "__main__":
    main()
