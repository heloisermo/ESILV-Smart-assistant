import json
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

JSON_PATH = "data/scraped_data.json"
INDEX_PATH = "data/faiss_index.bin"
MAPPING_PATH = "data/faiss_mapping.json"

def load_scraped_data(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def make_embeddings(texts):
    model = SentenceTransformer("all-MiniLM-L6-v2")
    embeddings = model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
    return embeddings

def build_faiss_index(embeddings):
    dim = embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)  # cosine similarity (works with normalized embeddings)
    index.add(embeddings)
    return index

if __name__ == "__main__":
    data = load_scraped_data(JSON_PATH)

    urls = list(data.keys())
    texts = list(data.values())

    embeds = make_embeddings(texts)
    index = build_faiss_index(embeds)

    faiss.write_index(index, INDEX_PATH)

    with open(MAPPING_PATH, "w", encoding="utf-8") as f:
        json.dump({"urls": urls, "texts": texts}, f, ensure_ascii=False, indent=2)

    print("FAISS index + mapping saved.")
