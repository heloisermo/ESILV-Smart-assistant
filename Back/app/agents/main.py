"""
Système multi-agents pour l'assistant ESILV
Démontre l'utilisation de l'orchestrateur avec les différents agents
"""
import sys
import os

# Ajouter les chemins nécessaires
sys.path.insert(0, os.path.dirname(__file__))

from orchestrator import OrchestratorAgent
from rag_agent import RAGAgent
from contact_agent import ContactAgent


def main():
    """Fonction principale pour tester le système multi-agents"""
    
    print("=" * 70)
    print("🤖 SYSTÈME MULTI-AGENTS ESILV")
    print("=" * 70)
    print()
    
    # Initialiser l'orchestrateur
    print("📋 Initialisation de l'orchestrateur...")
    orchestrator = OrchestratorAgent()
    
    # Créer et enregistrer les agents
    print("🔧 Création des agents...")
    
    try:
        rag_agent = RAGAgent()
        orchestrator.register_agent(rag_agent)
    except Exception as e:
        print(f"⚠️ Impossible d'initialiser le RAG Agent: {e}")
    
    contact_agent = ContactAgent()
    orchestrator.register_agent(contact_agent)
    
    print()
    print(f"✅ Agents enregistrés: {', '.join(orchestrator.list_agents())}")
    print()
    print("=" * 70)
    print()
    
    # Exemples de requêtes
    test_queries = [
        "Qu'est-ce que l'ESILV ?",
        "Comment contacter le service des admissions ?",
        "Quels sont les programmes proposés ?",
        "Je voudrais joindre quelqu'un pour parler des stages",
        "Quelle est l'adresse de l'école ?",
        "Comment s'inscrire à l'ESILV ?"
    ]
    
    print("🧪 Tests avec des exemples de requêtes:")
    print()
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{'─' * 70}")
        print(f"Query {i}: {query}")
        print('─' * 70)
        
        result = orchestrator.route(query)
        
        print(f"\n📊 Résultat:")
        print(f"   Agent utilisé: {result.get('agent_used', 'N/A')}")
        print(f"   Intention: {result.get('intent', 'N/A')}")
        print(f"   Succès: {result.get('success', False)}")
        
        if result.get('success'):
            print(f"\n💬 Réponse:")
            print(f"   {result.get('response', 'Pas de réponse')[:200]}...")
        else:
            print(f"\n❌ Erreur: {result.get('error', 'Erreur inconnue')}")
        
        print()
    
    # Mode interactif
    print("\n" + "=" * 70)
    print("💬 MODE INTERACTIF")
    print("=" * 70)
    print("Tapez vos questions (ou 'quit' pour quitter):")
    print()
    
    while True:
        try:
            user_input = input("\n🙋 Vous: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("\n👋 Au revoir!")
                break
            
            print()
            result = orchestrator.route(user_input)
            
            if result.get('success'):
                print(f"🤖 Assistant ({result.get('agent_used', 'N/A')}): ")
                print(f"{result.get('response', 'Pas de réponse')}")
            else:
                print(f"❌ Erreur: {result.get('error', 'Erreur inconnue')}")
        
        except KeyboardInterrupt:
            print("\n\n👋 Au revoir!")
            break
        except Exception as e:
            print(f"\n❌ Erreur: {e}")


if __name__ == "__main__":
    main()
