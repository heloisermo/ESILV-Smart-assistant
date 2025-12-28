"""
Authentication module for the admin panel
Handles password verification and session management
"""
import os
import streamlit as st
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get admin password from .env
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin2025")


def check_password() -> bool:
    """
    Check if the user has entered the correct password.
    
    Returns:
        True if password is correct, False otherwise
    """
    # Initialize session state for authentication
    if "admin_authenticated" not in st.session_state:
        st.session_state.admin_authenticated = False
    
    # If already authenticated, return True
    if st.session_state.admin_authenticated:
        return True
    
    # Show password input
    st.markdown("""
    <div style='text-align: center; padding: 3rem 0;'>
        <h2>🔐 Panneau d'Administration</h2>
        <p style='color: #666; margin-top: 1rem;'>
            Cette zone est restreinte. Veuillez entrer le mot de passe administrateur pour continuer.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        password_input = st.text_input(
            "Mot de passe",
            type="password",
            key="admin_password_input",
            placeholder="Entrez le mot de passe admin"
        )
        
        col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 1])
        
        with col_btn2:
            if st.button("🔓 Connexion", width="stretch", type="primary"):
                with st.spinner("🔄 Vérification en cours..."):
                    if password_input == ADMIN_PASSWORD:
                        st.session_state.admin_authenticated = True
                        st.success("✅ Authentification réussie ! Redirection...")
                        st.rerun()
                    else:
                        st.error("❌ Mot de passe incorrect. Accès refusé.")
    
    return False


def logout():
    """Déconnecter l'utilisateur administrateur"""
    with st.spinner("🔄 Déconnexion en cours..."):
        st.session_state.admin_authenticated = False


def is_authenticated() -> bool:
    """
    Vérifier si l'utilisateur est actuellement authentifié
    
    Returns:
        True si authentifié, False sinon
    """
    return st.session_state.get("admin_authenticated", False)
