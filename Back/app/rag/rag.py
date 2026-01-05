import os
import json
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
import vertexai
from vertexai.generative_models import GenerativeModel
from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup
import re

load_dotenv()

# Utiliser des chemins absolus pour trouver les fichiers depuis n'importe où
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Chemins pour l'index des PDFs uploadés
PDF_DATA_DIR = os.path.join(PROJECT_ROOT, "data")
PDF_INDEX_PATH = os.path.join(PDF_DATA_DIR, "faiss_index.bin")
PDF_MAPPING_PATH = os.path.join(PDF_DATA_DIR, "faiss_mapping.json")

# Chemins pour l'index des URLs scraped
RAG_DATA_DIR = os.path.join(PROJECT_ROOT, "Back", "app", "rag", "data")
RAG_INDEX_PATH = os.path.join(RAG_DATA_DIR, "faiss_index.bin")
RAG_MAPPING_PATH = os.path.join(RAG_DATA_DIR, "faiss_mapping.json")

MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"
VERTEX_MODEL = os.getenv("VERTEX_MODEL", "gemini-2.0-flash-exp")
VERTEX_PROJECT = os.getenv("VERTEX_PROJECT", "esilv-smart-assistant")
VERTEX_LOCATION = os.getenv("VERTEX_LOCATION", "us-central1")

SYSTEM_PROMPT = os.getenv(
    "SYSTEM_PROMPT", 
    "Tu es un assistant pour l'ecole d'ingenieurs ESILV. "
    "Reponds aux questions en utilisant le contexte fourni. "
    "Reponds toujours en francais et de maniere claire et concise."
)

class FaissRAGGemini:
    def __init__(self):
        try:
            # Configurer Vertex AI
            vertexai.init(project=VERTEX_PROJECT, location=VERTEX_LOCATION)
            self.llm = GenerativeModel(VERTEX_MODEL)
        except Exception as e:
            raise ValueError(f"Erreur initialisation Vertex AI: {e}")
        
        # Charger l'index des PDFs uploadés
        self.pdf_index = None
        self.pdf_urls = []
        self.pdf_texts = []
        
        if os.path.exists(PDF_INDEX_PATH) and os.path.exists(PDF_MAPPING_PATH):
            self.pdf_index = faiss.read_index(PDF_INDEX_PATH)
            with open(PDF_MAPPING_PATH, "r", encoding="utf-8") as f:
                mapping = json.load(f)
            self.pdf_urls = mapping["urls"]
            self.pdf_texts = mapping["texts"]
            print(f"Index PDFs charge : {len(self.pdf_texts)} chunks")
        else:
            print(f"Index PDFs non trouve")
        
        # Charger l'index des URLs scraped
        self.rag_index = None
        self.rag_urls = []
        self.rag_texts = []
        
        if os.path.exists(RAG_INDEX_PATH) and os.path.exists(RAG_MAPPING_PATH):
            self.rag_index = faiss.read_index(RAG_INDEX_PATH)
            with open(RAG_MAPPING_PATH, "r", encoding="utf-8") as f:
                mapping = json.load(f)
            self.rag_urls = mapping["urls"]
            self.rag_texts = mapping["texts"]
            print(f"Index URLs scraped charge : {len(self.rag_texts)} chunks")
        else:
            print(f"Index URLs scraped non trouve")
        
        # NE PAS charger le modèle au démarrage (lazy loading)
        self.model = None
        self.gcp_cache_path = '/root/.cache/huggingface/hub/models--sentence-transformers--paraphrase-multilingual-MiniLM-L12-v2/snapshots/86741b4e3f5cb7765a600d3a3d55a0f6a6cb443d'
        
        print(f"Modele Vertex AI : {VERTEX_MODEL}")
        print("Modele d'embedding sera charge a la premiere utilisation")

    def reload_index(self):
        """
        Recharge l'index FAISS et le mapping depuis le disque.
        Utile après l'ajout de nouveaux documents sans redémarrer l'application.
        """
        try:
            if not os.path.exists(PDF_INDEX_PATH):
                print(f"Index PDF FAISS non trouvé: {PDF_INDEX_PATH}")
                self.pdf_index = None
                self.pdf_urls = []
                self.pdf_texts = []
                return False
            
            if not os.path.exists(PDF_MAPPING_PATH):
                print(f"Mapping PDF FAISS non trouvé: {PDF_MAPPING_PATH}")
                self.pdf_index = None
                self.pdf_urls = []
                self.pdf_texts = []
                return False
            
            # Recharger l'index PDF et le mapping
            self.pdf_index = faiss.read_index(PDF_INDEX_PATH)
            with open(PDF_MAPPING_PATH, "r", encoding="utf-8") as f:
                mapping = json.load(f)
            self.pdf_urls = mapping["urls"]
            self.pdf_texts = mapping["texts"]
            
            print(f"Index PDFs rechargé : {len(self.pdf_texts)} chunks")
            return True
        except Exception as e:
            print(f"Erreur lors du rechargement de l'index: {e}")
            return False

    def _ensure_model_loaded(self):
        """Charge le modèle à la demande (lazy loading)"""
        if self.model is not None:
            return  # Déjà chargé
        
        print("Chargement du modèle d'embedding...")
        if os.path.exists(self.gcp_cache_path):
            print("Utilisation du cache GCP")
            self.model = SentenceTransformer(self.gcp_cache_path)
        else:
            print(f"Téléchargement depuis HuggingFace: {MODEL_NAME}")
            self.model = SentenceTransformer(MODEL_NAME)
        print("Modèle chargé avec succès")

    def retrieve(self, query, k=5):
        # Charger le modèle si nécessaire
        self._ensure_model_loaded()
        
    def retrieve(self, query, k=5):
        """Recherche dans les DEUX index (PDFs + URLs) et retourne les k meilleurs résultats combinés"""
        self._ensure_model_loaded()
        
        q_emb = self.model.encode(
            [query],
            convert_to_numpy=True,
            normalize_embeddings=True
        )
        q_emb = np.ascontiguousarray(q_emb, dtype="float32")

        results = []
        
        # Chercher dans l'index des URLs scraped ET PDFs avec le même k
        if self.rag_index is not None:
            scores, ids = self.rag_index.search(q_emb, k)
            for i, score in zip(ids[0], scores[0]):
                if i != -1 and i < len(self.rag_texts):
                    results.append({
                        "url": self.rag_urls[i],
                        "text": self.rag_texts[i],
                        "score": float(score),
                        "chunk_id": int(i),
                        "source": "URL"
                    })
        
        # Chercher dans l'index des PDFs
        if self.pdf_index is not None:
            scores, ids = self.pdf_index.search(q_emb, k)
            for i, score in zip(ids[0], scores[0]):
                if i != -1 and i < len(self.pdf_texts):
                    results.append({
                        "url": self.pdf_urls[i],
                        "text": self.pdf_texts[i],
                        "score": float(score),
                        "chunk_id": int(i),
                        "source": "PDF"
                    })
        
        # Trier par score (croissant car distance L2) et garder les k meilleurs
        # Pas de bonus - URLs et PDFs sont traités à égalité
        results.sort(key=lambda x: x['score'])
        results = results[:k]
        
        print(f"\nRecherche: '{query}'")
        print(f"Top {k} chunks pertinents:")
        for rank, r in enumerate(results, 1):
            text_preview = r['text'][:100].replace('\n', ' ')
            print(f"  {rank}. Score: {r['score']:.4f} [{r['source']}] | {text_preview}...")
            print(f"     Source: {r['url'][:80]}")

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
        """Génère une réponse avec Google Gemini"""
        try:
            # Gemini n'a pas de system prompt séparé, on le combine avec le user prompt
            full_prompt = f"{system_prompt}\n\n{user_prompt}"
            
            response = self.llm.generate_content(
                full_prompt
            )
            
            return response.text.strip()
            
        except Exception as e:
            print(f"Erreur Gemini: {e}")
            print(f"Type d'erreur: {type(e).__name__}")
            import traceback
            traceback.print_exc()
            return None
    
    def _generate_stream(self, system_prompt: str, user_prompt: str):
        """Génère une réponse en streaming avec Google Gemini"""
        try:
            # Gemini n'a pas de system prompt séparé, on le combine avec le user prompt
            full_prompt = f"{system_prompt}\n\n{user_prompt}"
            
            response = self.llm.generate_content(
                full_prompt,
                stream=True
            )
            
            # Yield chaque chunk de la réponse
            for chunk in response:
                if chunk.text:
                    yield chunk.text
            
        except Exception as e:
            print(f"Erreur Gemini streaming: {e}")
            print(f"Type d'erreur: {type(e).__name__}")
            import traceback
            traceback.print_exc()
            yield None

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
        
        # Mode fallback si Gemini est indisponible
        if ans is None and fallback_mode:
            print("\nGemini est indisponible. Voici un resume basique des documents trouves:")
            ans = self._fallback_answer(docs, question)
        
        return ans, docs
    
    def answer_stream(self, question: str, k: int = 5, fallback_mode: bool = True, enable_web_search: bool = True):
        """Répond à une question en streaming en utilisant le RAG et le scraping en temps réel si nécessaire"""
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
        
        # Streaming de la réponse
        for chunk in self._generate_stream(SYSTEM_PROMPT, user_prompt):
            if chunk is None and fallback_mode:
                print("\nGemini est indisponible. Voici un resume basique des documents trouves:")
                yield self._fallback_answer(docs, question)
                break
            elif chunk is not None:
                yield chunk
        
        # Retourner les docs à la fin (via un tuple spécial)
        yield ("__DOCS__", docs)
    
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
            "\n\nReponse generee sans IA (Gemini indisponible). "
            "Consultez les sources ci-dessous pour plus de details."
        )


if __name__ == "__main__":
    try:
        rag = FaissRAGGemini()
    except ValueError as e:
        print(e)
        print("\nPour obtenir une cle API Vertex AI:")
        print("1. Va sur https://console.cloud.google.com/")
        print("2. Active l'API Vertex AI")
        print("3. Cree une cle de service")
        print("4. Ajoute les variables dans ton .env")
        exit(1)
    
    print("\n" + "="*60)
    print("Chatbot RAG avec Google Vertex AI pret !")
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