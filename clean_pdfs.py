import json

# Charger le fichier
with open("data/scraped_data.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# Compter avant
count_before = len(data)

# Supprimer les PDFs (toutes les clés contenant "download/")
data_cleaned = {url: text for url, text in data.items() if "download/" not in url}

# Compter après
count_after = len(data_cleaned)

print(f"Avant: {count_before} documents")
print(f"Après: {count_after} documents")
print(f"PDFs supprimés: {count_before - count_after}")

# Sauvegarder le fichier nettoyé
with open("data/scraped_data.json", "w", encoding="utf-8") as f:
    json.dump(data_cleaned, f, ensure_ascii=False, indent=2)

print("✅ Fichier nettoyé avec succès !")
