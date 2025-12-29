"""
Streamlit page for leads management in the Administration tab
Displays collected leads, allows search/filtering, and CSV export
"""
import streamlit as st
import sys
import os
from datetime import datetime
import pandas as pd
import io

# Add Back/app to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "Back", "app"))

from leads_manager import (
    get_leads,
    add_lead,
    delete_lead,
    update_lead,
    export_leads_to_csv,
    search_leads,
    get_leads_count
)


def format_datetime(iso_str: str) -> str:
    """Format ISO datetime string to readable format"""
    try:
        dt = datetime.fromisoformat(iso_str)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except:
        return iso_str


def render_leads_management():
    """Afficher la section de gestion des leads"""
    st.header("Gestion des Contacts")
    
    # Créer des onglets pour différentes sections
    leads_tabs = st.tabs(["Tous les Contacts", "Rechercher"])
    
    # ===== TAB 1: All Leads =====
    with leads_tabs[0]:
        st.subheader("Contacts Collectés")
        
        # Get all leads with spinner
        with st.spinner("Chargement des leads..."):
            leads = get_leads()
        
        if not leads:
            st.info("Aucun lead n'a encore été collecté.")
        else:
            st.write(f"**Total des formulaires de contacts : {len(leads)}**")
            st.divider()
            
            # Create DataFrame for display
            df_data = []
            for lead in leads:
                created_at = format_datetime(lead.get("created_at", ""))
                
                df_data.append({
                    "ID": lead.get("id", ""),
                    "Nom": lead.get("name", ""),
                    "Email": lead.get("email", ""),
                    "Éducation": lead.get("education", "—") or "—",
                    "Programme": lead.get("program_of_interest", "—") or "—",
                    "Message": (lead.get("message", "")[:50] + "...") if lead.get("message") else "—",
                    "Date": created_at
                })
            
            df = pd.DataFrame(df_data)
            
            # Display table
            st.dataframe(
                df,
                width="stretch",
                hide_index=True,
                column_config={
                    "ID": st.column_config.NumberColumn(width="small"),
                    "Nom": st.column_config.TextColumn(width="medium"),
                    "Email": st.column_config.TextColumn(width="medium"),
                    "Éducation": st.column_config.TextColumn(width="medium"),
                    "Programme": st.column_config.TextColumn(width="medium"),
                    "Message": st.column_config.TextColumn(width="large"),
                    "Date": st.column_config.TextColumn(width="medium")
                }
            )
            
            st.divider()
            
            # Actions on leads
            st.subheader("Gestion des Contacts")
            col1, col2 = st.columns(2)
            
            with col1:
                selected_lead_id = st.selectbox(
                    "Sélectionner un lead pour voir/modifier",
                    [f"ID {lead['id']}: {lead['name']} ({lead['email']})" for lead in leads],
                    key="select_lead"
                )
                
                if selected_lead_id:
                    # Extract ID from selection
                    lead_id = int(selected_lead_id.split(":")[0].replace("ID ", ""))
                    selected_lead = next((l for l in leads if l["id"] == lead_id), None)
                    
                    if selected_lead:
                        st.write("**Détails du Lead :**")
                        
                        col_detail1, col_detail2 = st.columns(2)
                        
                        with col_detail1:
                            st.write(f"**Nom :** {selected_lead.get('name', 'N/A')}")
                            st.write(f"**Email :** {selected_lead.get('email', 'N/A')}")
                        
                        with col_detail2:
                            st.write(f"Éducation :** {selected_lead.get('education', 'N/A')}")
                            st.write(f"**Programme :** {selected_lead.get('program_of_interest', 'N/A')}")
                        
                        if selected_lead.get("message"):
                            st.write(f"**Message :**")
                            st.text(selected_lead.get("message", ""))
                        
                        st.write(f"**Collecté le :** {format_datetime(selected_lead.get('created_at', ''))}")
            
            with col2:
                st.write("**Actions Rapides :**")
                
                col_action1, col_action2 = st.columns(2)
                
                with col_action1:
                    if st.button("Supprimer", type="secondary", key="delete_lead"):
                        with st.spinner("Suppression en cours..."):
                            lead_id = int(selected_lead_id.split(":")[0].replace("ID ", ""))
                            if delete_lead(lead_id):
                                st.success("Lead supprimé avec succès")
                                st.rerun()
                            else:
                                st.error("Échec de la suppression")
                
                with col_action2:
                    st.metric("Total Leads", len(leads))
            
            st.divider()
            
            # Statistics
            st.subheader("Statistiques")
            col_stat1, col_stat2, col_stat3 = st.columns(3)
            
            with col_stat1:
                st.metric("Total Leads", len(leads))
            
            with col_stat2:
                unique_emails = len(set(l.get("email", "") for l in leads))
                st.metric("Emails Uniques", unique_emails)
            
            with col_stat3:
                with_program = sum(1 for l in leads if l.get("program_of_interest"))
                st.metric("Avec Programme", with_program)
    
    # ===== TAB 2: Search Leads =====
    with leads_tabs[1]:
        st.subheader("Rechercher des Contacts")
        
        search_query = st.text_input(
            "Rechercher par nom ou email",
            placeholder="Tapez un nom ou une adresse email",
            help="La recherche cherchera des correspondances partielles"
        )
        
        if search_query:
            with st.spinner("Recherche en cours..."):
                results = search_leads(search_query)
            
            if not results:
                st.warning(f"No leads found matching '{search_query}'")
            else:
                st.success(f"Found {len(results)} lead(s)")
                st.divider()
                
                # Create DataFrame for display
                df_data = []
                for lead in results:
                    created_at = format_datetime(lead.get("created_at", ""))
                    
                    df_data.append({
                        "ID": lead.get("id", ""),
                        "Name": lead.get("name", ""),
                        "Email": lead.get("email", ""),
                        "Education": lead.get("education", "—") or "—",
                        "Program": lead.get("program_of_interest", "—") or "—",
                        "Date": created_at
                    })
                
                df = pd.DataFrame(df_data)
                
                st.dataframe(
                    df,
                    width="stretch",
                    hide_index=True
                )
        else:
            st.info("Enter a search term to find leads")
