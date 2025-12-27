# Interface Streamlit - Chatbot ESILV

Application web interactive pour le chatbot multi-agents ESILV.

## 🚀 Lancement

```bash
cd Front
streamlit run streamlit_app.py
```

L'application sera accessible sur **http://localhost:8501**

## ✨ Fonctionnalités

- 💬 **Chat interactif** avec historique des conversations
- 🎯 **Routage intelligent** vers les agents appropriés (RAG ou Contact)
- 📋 **Gestion des formulaires** de contact avec contexte maintenu
- 🔄 **Réinitialisation** de la conversation et des agents
- 📊 **Statut en temps réel** des agents disponibles
- 🎨 **Interface moderne** et intuitive

## 📦 Installation

Si Streamlit n'est pas installé :

```bash
pip install streamlit
```

Ou installer toutes les dépendances du projet :

```bash
pip install -r ../requirements.txt
```

## 🎮 Utilisation

1. Lancez l'application
2. Posez vos questions dans le chat
3. L'orchestrateur route automatiquement vers le bon agent
4. Pour les demandes de contact, remplissez le formulaire en conversant naturellement
5. Les formulaires sont sauvegardés automatiquement

## 📝 Exemples de questions

- "Qu'est-ce que l'ESILV ?"
- "Quels sont les programmes proposés ?"
- "Je voudrais contacter le service des admissions"
- "Comment s'inscrire ?"
