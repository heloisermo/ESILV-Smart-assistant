import os
import json
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup
import re

load_dotenv()

INDEX_PATH = "data/faiss_index.bin"
MAPPING_PATH = "data/faiss_mapping.json"

MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"
VERTEX_MODEL = os.getenv("VERTEX_MODEL", "gemini-2.0-flash-exp")
VERTEX_API_KEY = os.getenv("VERTEX_API_KEY")
VERTEX_API_ENDPOINT = f"https://aiplatform.googleapis.com/v1/publishers/google/models/{VERTEX_MODEL}:generateContent"

SYSTEM_PROMPT = os.getenv(
    "SYSTEM_PROMPT", 
    "Tu es un assistant pour l'ecole d'ingenieurs ESILV. "
    "Reponds aux questions en utilisant le contexte fourni. "
    "Reponds toujours en francais et de maniere claire et concise."
)

class FaissRAGGemini:
    def __init__(self):
        if not VERTEX_API_KEY:
            raise ValueError("VERTEX_API_KEY manquante dans .env")
        
        self.api_key = VERTEX_API_KEY
        self.api_endpoint = VERTEX_API_ENDPOINT
        
        self.index = faiss.read_index(INDEX_PATH)
        with open(MAPPING_PATH, "r", encoding="utf-8") as f:
            mapping = json.load(f)
        self.urls = mapping["urls"]
        self.texts = mapping["texts"]
        # Charger les indices de documents (optionnel, pour info)
        self.doc_indices = mapping.get("doc_indices", None)
        
        self.model = SentenceTransformer(MODEL_NAME)
        
        print(f"Index charge : {len(self.texts)} chunks")
        print(f"Modele Vertex AI : {VERTEX_MODEL}")

    def retrieve(self, query, k=5):
        q_emb = self.model.encode(
            [query],
            convert_to_numpy=True,
            normalize_embeddings=True
        )
        q_emb = np.ascontiguousarray(q_emb, dtype="float32")

        assert q_emb.shape[1] == self.index.d, \
            f"Dimension mismatch: query={q_emb.shape[1]}, index={self.index.d}"

        scores, ids = self.index.search(q_emb, k)

        results = []
        print(f"\nRecherche: '{query}'")
        print(f"Top {k} chunks pertinents:")

        for rank, (i, score) in enumerate(zip(ids[0], scores[0]), 1):
            if i == -1:
                continue
            text_preview = self.texts[i][:100].replace('\n', ' ')
            print(f"  {rank}. Score: {score:.4f} | {text_preview}...")
            print(f"     Source: {self.urls[i][:80]}")
            results.append({
                "url": self.urls[i],
                "text": self.texts[i],
                "score": float(score),
                "chunk_id": int(i),
            })

        return results

    def _scrape_page(self, url):
        """Scrape une page web et retourne son contenu"""
        try:
            r = requests.get(url, timeout=10)
            soup = BeautifulSoup(r.text, "html.parser")
            
            # Supprimer les éléments non pertinents
            for tag in soup(["script", "style", "noscript", "nav", "header", "footer", "aside", "iframe"]):
                tag.extract()
            
            # Chercher le contenu principal
            main_content = None
            for tag in ['main', 'article']:
                main_content = soup.find(tag)
                if main_content:
                    break
            
            if not main_content:
                main_content = soup.find('body')
            
            if main_content:
                text = main_content.get_text(separator=" ", strip=True)
            else:
                text = soup.get_text(separator=" ", strip=True)
            
            # Nettoyer les espaces multiples
            text = ' '.join(text.split())
            # Limiter à 5000 caractères pour ne pas surcharger le contexte
            return text[:5000]
        except Exception as e:
            print(f"Erreur lors du scraping de {url}: {e}")
            return None

    def _search_on_esilv_site(self, question):
        """Tente de trouver des pages pertinentes sur le site ESILV"""
        try:
            # Utiliser Google pour rechercher sur le site ESILV
            search_query = f"site:esilv.fr {question}"
            # Note: Google limite les requêtes automatiques, c'est une solution simplifiée
            # Pour une vraie implémentation, utilisez l'API Google Search ou un autre moteur
            
            # Fallback: essayer des URLs communes basées sur les mots-clés
            keywords_to_url = {
                "admission": "https://www.esilv.fr/admissions/",
                "tarif": "https://www.esilv.fr/admissions/tarifs-et-financement/",
                "prix": "https://www.esilv.fr/admissions/tarifs-et-financement/",
                "cout": "https://www.esilv.fr/admissions/tarifs-et-financement/",
                "formation": "https://www.esilv.fr/formations/",
                "majeure": "https://www.esilv.fr/formations/cycle-ingenieur/majeures/",
                "parcours": "https://www.esilv.fr/formations/cycle-ingenieur/parcours/",
                "bachelor": "https://www.esilv.fr/formations/bachelor-informatique-cybersecurite/",
                "entreprise": "https://www.esilv.fr/entreprises-debouches/",
                "emploi": "https://www.esilv.fr/entreprises-debouches/enquete-premier-emploi-ingenieur/",
                "salaire": "https://www.esilv.fr/combien-gagne-un-ingenieur-les-salaires-en-sortie-decole-dingenieurs-a-lesilv/",
            }
            
            question_lower = question.lower()
            for keyword, url in keywords_to_url.items():
                if keyword in question_lower:
                    return url
            
            # Par défaut, retourner la page d'accueil
            return "https://www.esilv.fr/"
        except Exception as e:
            print(f"Erreur lors de la recherche: {e}")
            return None


    def _generate(self, system_prompt: str, user_prompt: str) -> str:
        """Génère une réponse avec Vertex AI via API REST"""
        try:
            # Combiner system prompt et user prompt
            full_prompt = f"{system_prompt}\n\n{user_prompt}"
            
            # Préparer la requête
            url = f"{self.api_endpoint}?key={self.api_key}"
            headers = {"Content-Type": "application/json"}
            payload = {
                "contents": [{
                    "role": "user",
                    "parts": [{"text": full_prompt}]
                }],
                "generationConfig": {
                    "temperature": 0.7,
                    "maxOutputTokens": 1024,
                }
            }
            
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            if "candidates" in result and len(result["candidates"]) > 0:
                text = result["candidates"][0]["content"]["parts"][0]["text"]
                return text.strip()
            else:
                print(f"Réponse inattendue de l'API: {result}")
                return None
            
        except Exception as e:
            print(f"Erreur Vertex AI: {e}")
            print(f"Type d'erreur: {type(e).__name__}")
            import traceback
            traceback.print_exc()
            return None

    def answer(self, question: str, k: int = 5, fallback_mode: bool = True, enable_web_search: bool = True):
        """Répond à une question en utilisant le RAG et le scraping en temps réel si nécessaire"""
        docs = self.retrieve(question, k=k)
        
        # Vérifier si les résultats sont pertinents (score > 0.3)
        has_relevant_docs = any(d['score'] > 0.3 for d in docs)
        
        # Les chunks sont déjà de taille raisonnable, pas besoin de tronquer autant
        # On combine les k meilleurs chunks pour le contexte
        context_parts = []
        for i, d in enumerate(docs, 1):
            context_parts.append(f"[Extrait {i}]\n{d['text']}")
        
        context = "\n\n---\n\n".join(context_parts)
        
        # Si les docs ne sont pas pertinents et que le web search est activé, chercher sur le site
        additional_context = ""
        if not has_relevant_docs and enable_web_search:
            print("\nLes resultats du RAG ne sont pas assez pertinents. Recherche sur le site ESILV...")
            url = self._search_on_esilv_site(question)
            if url:
                print(f"Scraping de {url}...")
                scraped_content = self._scrape_page(url)
                if scraped_content:
                    additional_context = f"\n\n[Contenu scrape depuis {url}]\n{scraped_content}"
                    print("Contenu supplementaire recupere avec succes.\n")
        
        user_prompt = (
            f"Contexte (extraits pertinents):{context}{additional_context}\n\n"
            f"Question: {question}\n\n"
            "Reponds de facon claire et concise en te basant sur les extraits fournis. "
            "Si l'information n'est pas dans les extraits, dis-le clairement."
        )
        
        ans = self._generate(SYSTEM_PROMPT, user_prompt)
        
        # Mode fallback si Vertex AI est indisponible
        if ans is None and fallback_mode:
            print("\nVertex AI est indisponible. Voici un resume basique des documents trouves:")
            ans = self._fallback_answer(docs, question)
        
        return ans, docs
    
    def _fallback_answer(self, docs, question):
        """Réponse de secours sans LLM"""
        if not docs:
            return "Aucun chunk pertinent trouvé."
        
        # Les chunks sont déjà de bonne taille
        snippets = []
        for i, doc in enumerate(docs[:3], 1):
            text = doc['text']
            snippets.append(f"{i}. {text}")
        
        return (
            f"Voici les extraits les plus pertinents trouves pour votre question:\n\n" +
            "\n\n".join(snippets) +
            "\n\nReponse generee sans IA (Vertex AI indisponible). "
            "Consultez les sources ci-dessous pour plus de details."
        )


if __name__ == "__main__":
    try:
        rag = FaissRAGGemini()
    except ValueError as e:
        print(e)
        print("\nPour configurer Vertex AI:")
        print("1. Va sur Google Cloud Console")
        print("2. Active l'API Vertex AI")
        print("3. Cree des credentials (service account key JSON)")
        print("4. Ajoute le chemin dans ton .env: VERTEX_API_KEY=chemin/vers/credentials.json")
        exit(1)
    
    print("\n" + "="*60)
    print("Chatbot RAG avec Vertex AI pret !")
    print("="*60 + "\n")
    
    while True:
        q = input("\nQuestion (ou 'q' pour quitter) > ")
        if q.lower() in ['q', 'quit', 'exit']:
            print("Au revoir !")
            break
        
        if not q.strip():
            continue
            
        try:
            ans, docs = rag.answer(q, k=5)
            
            if ans:
                print("\n" + "="*60)
                print("REPONSE")
                print("="*60)
                print(ans)
            
            print("\n" + "="*60)
            print("SOURCES")
            print("="*60)
            for i, d in enumerate(docs, 1):
                print(f"{i}. {d['url']}")
                print(f"   Score: {d['score']:.4f}")
                
        except KeyboardInterrupt:
            print("\n\nInterruption - Au revoir !")
            break
        except Exception as e:
            print(f"Erreur inattendue: {e}")
            import traceback
            traceback.print_exc()