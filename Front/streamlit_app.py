"""
Interface Streamlit épurée et moderne pour le chatbot ESILV
Design: Minimalisme lumineux Scandinave - Très lisible, textes gros, espaces généreux
"""
import sys
import os
import streamlit as st
import json
from datetime import datetime

# Ajouter le chemin des agents
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'Back', 'app', 'agents'))

from orchestrator import OrchestratorAgent
from rag_agent import RAGAgent
from contact_agent import ContactAgent

# Configuration de la page
st.set_page_config(
    page_title="ESILV Assistant",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items={
        'Get Help': 'https://www.esilv.fr',
        'Report a bug': None,
        'About': 'Assistant IA ESILV'
    }
)

# CSS complètement refait - Design épuré et lumineux
st.markdown("""
<style>
    * {
        margin: 0;
        padding: 0;
        box-sizing: border-box;
    }
    
    html, body, [data-testid="stAppViewContainer"] {
        background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Helvetica Neue', sans-serif;
        color: #2c3e50;
    }
    
    [data-testid="stHeader"] {
        background: transparent;
        border: none;
    }
    
    /* Conteneur principal */
    [data-testid="stMain"] {
        background: transparent;
        padding: 0 !important;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #ffffff 0%, #f8f9fa 100%);
        border-right: 1px solid #e8eaed;
    }
    
    /* Header principal avec logo */
    .header-container {
        background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
        border-bottom: 1px solid #e8eaed;
        padding: 3rem 3rem 2rem 3rem;
        margin-bottom: 2rem;
    }
    
    .logo-section {
        display: flex;
        align-items: center;
        gap: 2rem;
    }
    
    .logo-box {
        width: 180px;
        height: 120px;
        border-radius: 12px;
        background: white;
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 1.5rem;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
        flex-shrink: 0;
    }
    
    .logo-box img {
        width: 100%;
        height: 100%;
        object-fit: contain;
    }
    
    .title-section h1 {
        font-size: 2.2rem;
        font-weight: 700;
        color: #2c3e50;
        margin: 0;
        letter-spacing: -0.5px;
    }
    
    .title-section p {
        font-size: 1rem;
        color: #7f8c8d;
        margin: 0.5rem 0 0 0;
        font-weight: 400;
    }
    
    /* Chat container */
    .chat-container {
        max-width: 1000px;
        margin: 0 auto;
        padding: 0 3rem 2rem 3rem;
        height: calc(100vh - 350px);
        overflow-y: auto;
        scroll-behavior: smooth;
    }
    
    .chat-container::-webkit-scrollbar {
        width: 8px;
    }
    
    .chat-container::-webkit-scrollbar-track {
        background: transparent;
    }
    
    .chat-container::-webkit-scrollbar-thumb {
        background: #ddd;
        border-radius: 4px;
    }
    
    .chat-container::-webkit-scrollbar-thumb:hover {
        background: #ccc;
    }
    
    /* Messages du chat */
    .chat-message {
        margin-bottom: 2rem;
        animation: slideIn 0.3s ease-out;
    }
    
    @keyframes slideIn {
        from {
            opacity: 0;
            transform: translateY(15px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    .message-wrapper {
        display: flex;
        gap: 1.5rem;
        align-items: flex-start;
    }
    
    .message-avatar {
        width: 48px;
        height: 48px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.5rem;
        flex-shrink: 0;
    }
    
    .user-avatar {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
    }
    
    .assistant-avatar {
        background: #f0f2f5;
        color: #667eea;
    }
    
    .message-content {
        flex: 1;
        background: #ffffff;
        border: 1px solid #e8eaed;
        border-radius: 14px;
        padding: 1.5rem;
        word-wrap: break-word;
        overflow-x: auto;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
    }
    
    .user-message .message-content {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border: none;
        color: white;
    }
    
    .message-content p {
        margin: 0.75rem 0;
        line-height: 1.8;
        font-size: 1.05rem;
    }
    
    .message-content p:first-child {
        margin-top: 0;
    }
    
    .message-content p:last-child {
        margin-bottom: 0;
    }
    
    .assistant-name {
        font-weight: 600;
        font-size: 0.95rem;
        color: #667eea;
        display: block;
        margin-bottom: 0.5rem;
    }
    
    .user-message .assistant-name {
        color: rgba(255, 255, 255, 0.8);
    }
    
    .message-time {
        font-size: 0.85rem;
        color: #a0a8b0;
        margin-top: 0.75rem;
        display: block;
    }
    
    .user-message .message-time {
        color: rgba(255, 255, 255, 0.6);
    }
    
    /* Form info */
    .form-info {
        background: linear-gradient(135deg, #f5f7fa 0%, #ffffff 100%);
        border: 2px solid #667eea;
        border-radius: 12px;
        padding: 1.5rem;
        margin-top: 1rem;
        color: #2c3e50;
    }
    
    .form-info strong {
        display: block;
        margin-bottom: 1rem;
        font-size: 1.1rem;
        color: #667eea;
    }
    
    .form-info-item {
        font-size: 1rem;
        margin: 0.75rem 0;
        color: #2c3e50;
    }
    
    /* Input chat */
    .input-container {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        background: linear-gradient(180deg, transparent 0%, #ffffff 80%);
        padding: 2rem 3rem;
        max-width: 100%;
        border-top: 1px solid #e8eaed;
    }
    
    .input-wrapper {
        max-width: 1000px;
        margin: 0 auto;
    }
    
    [data-testid="stChatInputContainer"] {
        background: transparent;
    }
    
    .stChatInputContainer input {
        background: #ffffff !important;
        border: 2px solid #e8eaed !important;
        color: #2c3e50 !important;
        border-radius: 12px !important;
        padding: 1.2rem !important;
        font-family: inherit !important;
        font-size: 1.05rem !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.03) !important;
    }
    
    .stChatInputContainer input:focus {
        border-color: #667eea !important;
        box-shadow: 0 0 0 4px rgba(102, 126, 234, 0.1) !important;
        background: #ffffff !important;
    }
    
    .stChatInputContainer input::placeholder {
        color: #a0a8b0 !important;
    }
    
    /* Sidebar content */
    .sidebar-content {
        padding: 2rem 1.5rem;
    }
    
    .sidebar-title {
        font-size: 1.3rem;
        font-weight: 600;
        color: #2c3e50;
        margin-bottom: 1rem;
        margin-top: 1.5rem;
    }
    
    .sidebar-title:first-child {
        margin-top: 0;
    }
    
    /* Sidebar buttons */
    [data-testid="stSidebar"] button {
        background: #ffffff !important;
        border: 2px solid #667eea !important;
        color: #667eea !important;
        padding: 0.875rem 1.25rem !important;
        border-radius: 10px !important;
        font-size: 1rem !important;
        font-weight: 500 !important;
        cursor: pointer !important;
        transition: all 0.3s ease !important;
        width: 100% !important;
        margin-bottom: 0.75rem !important;
    }
    
    [data-testid="stSidebar"] button:hover {
        background: #667eea !important;
        color: #ffffff !important;
    }
    
    /* Divider */
    .sidebar-divider {
        height: 1px;
        background: #e8eaed;
        margin: 1.5rem 0;
    }
    
    /* Status badge */
    .status-badge {
        display: inline-block;
        background: #f0f2f5;
        border: 2px solid #22c55e;
        color: #22c55e;
        padding: 0.75rem 1.25rem;
        border-radius: 20px;
        font-size: 0.95rem;
        font-weight: 500;
    }
    
    /* Text elements */
    [data-testid="stSidebar"] h2 {
        font-size: 1.3rem !important;
        color: #2c3e50 !important;
        margin-bottom: 1rem !important;
    }
    
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] li {
        font-size: 1rem !important;
        color: #2c3e50 !important;
        line-height: 1.6 !important;
    }
    
    [data-testid="stSidebar"] .caption {
        font-size: 1rem !important;
        color: #7f8c8d !important;
        margin: 0.5rem 0 !important;
    }
    
    /* Expander */
    [data-testid="stSidebar"] [data-testid="stExpander"] {
        background: #f8f9fa;
        border: 1px solid #e8eaed;
    }
    
    [data-testid="stSidebar"] [data-testid="stExpander"] button {
        border: none !important;
        background: transparent !important;
        color: #2c3e50 !important;
        font-size: 1rem !important;
        font-weight: 600 !important;
    }
    
    /* Code blocks */
    .stCodeBlock {
        background: #f8f9fa !important;
        border: 1px solid #e8eaed !important;
        border-radius: 10px !important;
        font-size: 0.95rem !important;
    }
    
    /* Success/Warning messages */
    .stSuccess, .stWarning, .stInfo {
        border-radius: 10px !important;
        padding: 1rem 1.25rem !important;
        font-size: 1rem !important;
    }
    
    .stSuccess {
        background-color: #f0fdf4 !important;
        border: 2px solid #22c55e !important;
        color: #166534 !important;
    }
    
    .stWarning {
        background-color: #fffbeb !important;
        border: 2px solid #f59e0b !important;
        color: #92400e !important;
    }
    
    .stInfo {
        background-color: #eff6ff !important;
        border: 2px solid #3b82f6 !important;
        color: #1e40af !important;
    }
    
    /* Tabs */
    [data-testid="stTabs"] {
        font-size: 1.05rem;
    }
    
    [data-testid="stTabs"] button {
        font-size: 1rem !important;
        font-weight: 500 !important;
        padding: 1rem !important;
    }
    
    /* Divider global */
    [data-testid="stHorizontalBlock"] hr {
        border: none;
        height: 1px;
        background: #e8eaed;
        margin: 1.5rem 0;
    }
    
    /* Custom scrollbar global */
    ::-webkit-scrollbar {
        width: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: transparent;
    }
    
    ::-webkit-scrollbar-thumb {
        background: #ddd;
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: #bbb;
    }
</style>
""", unsafe_allow_html=True)


def init_session_state():
    """Initialise l'état de la session"""
    if 'initialized' not in st.session_state:
        st.session_state.initialized = False
        st.session_state.orchestrator = None
        st.session_state.contact_agent = None
        st.session_state.messages = []
        st.session_state.pending_form = None
        st.session_state.agent_status = None
        st.session_state.admin_authenticated = False


def initialize_agents():
    """Initialise l'orchestrateur et les agents"""
    if not st.session_state.initialized:
        with st.spinner("⏳ Initialisation des agents..."):
            try:
                orchestrator = OrchestratorAgent()
                
                # Créer et enregistrer les agents
                try:
                    rag_agent = RAGAgent()
                    orchestrator.register_agent(rag_agent)
                except Exception as e:
                    st.warning(f"⚠️ RAG Agent non disponible: {e}")
                
                contact_agent = ContactAgent()
                orchestrator.register_agent(contact_agent)
                
                st.session_state.orchestrator = orchestrator
                st.session_state.contact_agent = contact_agent
                st.session_state.initialized = True
                st.session_state.agent_status = f"✅ Agents disponibles: {', '.join(orchestrator.list_agents())}"
                
            except Exception as e:
                st.error(f"❌ Erreur d'initialisation: {e}")
                return False
    
    return True


def extract_form_data_with_llm(user_input, current_fields, contact_agent):
    """Utilise le LLM pour extraire les données du formulaire"""
    import requests
    import re
    
    if not contact_agent.api_endpoint:
        return None
    
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
- Ne garde que ce qui est NOUVEAU dans le message
- L'email doit contenir un @
- Si l'utilisateur donne "Nom Prénom", le premier mot est le prénom, le reste est le nom
- Si c'est juste un texte sans structure, c'est probablement l'objet ou le message

JSON:"""
        
        url = f"{contact_agent.api_endpoint}?key={contact_agent.api_key}"
        payload = {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.1, "maxOutputTokens": 512}
        }
        response = requests.post(url, headers={"Content-Type": "application/json"}, json=payload, timeout=15)
        response.raise_for_status()
        
        result = response.json()
        if "candidates" in result and len(result["candidates"]) > 0:
            llm_response = result["candidates"][0]["content"]["parts"][0]["text"].strip()
            
            json_match = re.search(r'\{[\s\S]*\}', llm_response)
            if json_match:
                form_data = json.loads(json_match.group())
                return {k: v if v != "null" and v else None for k, v in form_data.items()}
    except Exception as e:
        st.warning(f"⚠️ Erreur extraction: {e}")
    
    return None


def handle_form_input(user_input):
    """Traite les entrées pour remplir le formulaire"""
    form = st.session_state.pending_form
    contact_agent = st.session_state.contact_agent
    
    # Extraire les données avec le LLM
    form_data = extract_form_data_with_llm(user_input, form["fields"], contact_agent)
    
    if form_data:
        # Mettre à jour le formulaire
        for key, value in form_data.items():
            if value:
                form["fields"][key] = value
    
    # Vérifier les champs manquants
    required_fields = ["nom", "prenom", "email", "objet", "message"]
    missing = [f for f in required_fields if not form["fields"].get(f)]
    
    if missing:
        return {
            "success": True,
            "agent_used": "Contact Agent",
            "response": f"📝 Merci ! Il me manque encore : {', '.join(missing)}.\n\nPouvez-vous me les fournir ?",
            "stream": False
        }
    
    # Soumettre le formulaire
    submit_data = {**form["fields"], "service": form["service"], "service_email": form["service_email"]}
    result = contact_agent.validate_and_submit_form(submit_data)
    result["form_submitted"] = True
    result["agent_used"] = "Contact Agent"
    result["stream"] = False
    
    return result


def handle_rag_response(query):
    """Gère la réponse RAG avec streaming"""
    from rag_agent import RAGAgent
    
    try:
        # Obtenir l'agent RAG
        for agent in st.session_state.orchestrator.agents:
            if isinstance(agent, RAGAgent) and agent.rag_system:
                # Utiliser le mode streaming
                generator = agent.rag_system.answer(query, k=5, stream=True)
                
                # Créer un placeholder pour la réponse
                response_placeholder = st.empty()
                full_response = ""
                docs = []
                
                # Streamer la réponse
                for chunk in generator:
                    if isinstance(chunk, dict) and "docs" in chunk:
                        # Dernier chunk avec les métadonnées
                        docs = chunk["docs"]
                        full_response = chunk["full_response"]
                    else:
                        # Chunk de texte
                        full_response += chunk
                        response_placeholder.markdown(full_response + "▌")
                
                # Afficher la réponse finale
                response_placeholder.markdown(full_response)
                
                return {
                    "success": True,
                    "response": full_response,
                    "chunks": docs,
                    "agent_used": "RAG Agent",
                    "streamed": True
                }
    except Exception as e:
        st.error(f"Erreur: {e}")
    
    return {"success": False, "error": "RAG non disponible"}


def display_chat_message(message):
    """Affiche un message du chat avec nouveau design"""
    role = message["role"]
    content = message["content"]
    timestamp = message.get("timestamp", "")
    
    if role == "user":
        st.markdown(f"""
        <div class="chat-message user-message">
            <div class="message-wrapper">
                <div class="message-avatar user-avatar">👤</div>
                <div style="flex: 1;">
                    <div class="message-content">
                        <p>{content}</p>
                        <span class="message-time">{timestamp}</span>
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        agent = message.get("agent", "Assistant")
        agent_emoji = "🤖" if agent == "RAG Agent" else "📞" if agent == "Contact Agent" else "✨"
        
        st.markdown(f"""
        <div class="chat-message assistant-message">
            <div class="message-wrapper">
                <div class="message-avatar assistant-avatar">{agent_emoji}</div>
                <div style="flex: 1;">
                    <div class="message-content">
                        <span class="assistant-name">{agent}</span>
                        <p>{content}</p>
                        <span class="message-time">{timestamp}</span>
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Afficher les infos de formulaire si présent
        if message.get("form_info"):
            st.markdown(f"""
            <div class="form-info">
                <strong>📋 Formulaire de contact créé</strong>
                <div class="form-info-item"><strong>Service :</strong> {message['form_info']['service']}</div>
                <div class="form-info-item"><strong>Email :</strong> {message['form_info']['email']}</div>
            </div>
            """, unsafe_allow_html=True)


def main():
    """Application principale"""
    init_session_state()
    
    # Header avec logo
    logo_path = os.path.join(os.path.dirname(__file__), "assets", "esilv_logo.png")
    
    if os.path.exists(logo_path):
        import base64
        with open(logo_path, "rb") as f:
            logo_b64 = base64.b64encode(f.read()).decode()
        logo_html = f'<img src="data:image/png;base64,{logo_b64}" alt="ESILV Logo">'
    else:
        logo_html = '🎓'
    
    st.markdown(f"""
    <div class="header-container">
        <div class="logo-section">
            <div class="logo-box">{logo_html}</div>
            <div class="title-section">
                <h1>ESILV Assistant</h1>
                <p>Votre assistant IA pour les questions sur ESILV</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar avec options
    with st.sidebar:
        st.markdown('<div class="sidebar-content">', unsafe_allow_html=True)
        
        st.markdown('<div class="sidebar-title">⚙️ Outils</div>', unsafe_allow_html=True)
        
        col_reset1, col_reset2 = st.columns(2)
        with col_reset1:
            if st.button("🔄 Réinitialiser", use_container_width=True):
                st.session_state.messages = []
                st.session_state.pending_form = None
                st.rerun()
        
        with col_reset2:
            if st.button("🔧 Réinit. agents", use_container_width=True):
                st.session_state.initialized = False
                st.rerun()
        
        st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)
        
        st.markdown('<div class="sidebar-title">📊 État</div>', unsafe_allow_html=True)
        if st.session_state.agent_status:
            st.markdown(f'<div class="status-badge">{st.session_state.agent_status}</div>', unsafe_allow_html=True)
        else:
            st.info("🔄 Initialisation en cours...")
        
        if st.session_state.pending_form:
            st.warning("📝 Formulaire en cours de remplissage")
            with st.expander("Voir les champs"):
                for key, value in st.session_state.pending_form["fields"].items():
                    status = "✅" if value else "❌"
                    st.text(f"{status} {key.capitalize()}: {value or 'Non fourni'}")
        
        st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)
        
        st.markdown('<div class="sidebar-title">💡 Exemples de questions</div>', unsafe_allow_html=True)
        examples = [
            "Qu'est-ce que l'ESILV ?",
            "Quels sont les programmes ?",
            "Comment s'inscrire ?",
            "Contacter les admissions",
            "Quels sont les frais ?",
            "Où est ESILV situé ?"
        ]
        for example in examples:
            st.caption(f"• {example}")
        
        st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)
        
        st.markdown('<div class="sidebar-title">🔐 Admin</div>', unsafe_allow_html=True)
        if st.button("Accès à l'interface admin", use_container_width=True):
            st.info("Interface admin en développement")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Initialiser les agents
    if not initialize_agents():
        st.error("Impossible d'initialiser les agents")
        return
    
    # Conteneur chat
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    
    for message in st.session_state.messages:
        display_chat_message(message)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Input utilisateur (fixé en bas)
    st.markdown('<div class="input-container">', unsafe_allow_html=True)
    st.markdown('<div class="input-wrapper">', unsafe_allow_html=True)
    user_input = st.chat_input("Posez votre question...", key="user_input")
    st.markdown('</div></div>', unsafe_allow_html=True)
    
    if user_input:
        # Ajouter le message utilisateur
        st.session_state.messages.append({
            "role": "user",
            "content": user_input,
            "timestamp": datetime.now().strftime("%H:%M")
        })
        
        # Traiter la réponse
        if st.session_state.pending_form:
            result = handle_form_input(user_input)
            
            if result.get("success"):
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": result.get("response", "Pas de réponse"),
                    "agent": result.get("agent_used", "Assistant"),
                    "timestamp": datetime.now().strftime("%H:%M")
                })
                
                if result.get("form_submitted"):
                    st.session_state.pending_form = None
                    st.balloons()
            else:
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": f"❌ Erreur: {result.get('error', 'Erreur inconnue')}",
                    "agent": "Système",
                    "timestamp": datetime.now().strftime("%H:%M")
                })
            
            st.rerun()
        else:
            # Déterminer quel agent va traiter
            result = st.session_state.orchestrator.route(user_input)
            
            if result.get("agent_used") == "RAG Agent" and result.get("success"):
                # Streaming pour RAG
                rag_result = handle_rag_response(user_input)
                
                if rag_result.get("success"):
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": rag_result.get("response"),
                        "agent": "RAG Agent",
                        "timestamp": datetime.now().strftime("%H:%M")
                    })
                else:
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": result.get("response", "Pas de réponse"),
                        "agent": result.get("agent_used", "Assistant"),
                        "timestamp": datetime.now().strftime("%H:%M")
                    })
            else:
                # Pas de streaming pour les autres agents
                if result.get("success"):
                    assistant_message = {
                        "role": "assistant",
                        "content": result.get("response", "Pas de réponse"),
                        "agent": result.get("agent_used", "Assistant"),
                        "timestamp": datetime.now().strftime("%H:%M")
                    }
                    
                    # Gérer les formulaires
                    if result.get("requires_form"):
                        st.session_state.pending_form = result["form"]
                        assistant_message["form_info"] = {
                            "service": result.get("service"),
                            "email": result["form"]["service_email"]
                        }
                    elif result.get("form_submitted"):
                        st.session_state.pending_form = None
                        st.balloons()
                    
                    st.session_state.messages.append(assistant_message)
                else:
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": f"❌ Erreur: {result.get('error', 'Erreur inconnue')}",
                        "agent": "Système",
                        "timestamp": datetime.now().strftime("%H:%M")
                    })
            
            st.rerun()


if __name__ == "__main__":
    main()