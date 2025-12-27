"""
Test simple pour déboguer l'agent RAG
"""
import sys
import os

# Charger les variables d'environnement
from dotenv import load_dotenv
env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '.env'))
load_dotenv(env_path)

print(f"VERTEX_API_KEY: {os.getenv('VERTEX_API_KEY')[:20]}...")
print(f"VERTEX_MODEL: {os.getenv('VERTEX_MODEL')}")

# Tester l'import du RAG
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'rag'))

rag_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'rag'))
print(f"\nRAG directory: {rag_dir}")
print(f"Current directory: {os.getcwd()}")

original_dir = os.getcwd()
os.chdir(rag_dir)

try:
    from rag import FaissRAGGemini
    print("\n✅ Import réussi")
    
    rag = FaissRAGGemini()
    print("✅ Initialisation réussie")
    
    # Tester une requête
    response, chunks = rag.answer("Qu'est-ce que l'ESILV ?", k=3)
    print(f"\n✅ Réponse: {response[:100]}...")
    
except Exception as e:
    print(f"\n❌ Erreur: {e}")
    import traceback
    traceback.print_exc()
finally:
    os.chdir(original_dir)
