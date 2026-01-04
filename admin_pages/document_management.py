"""
Page Streamlit pour la gestion des documents dans l'onglet Administration
Permet de télécharger, visualiser et gérer les documents indexés
"""
import streamlit as st
import sys
import os
from datetime import datetime
import pandas as pd

# Add Back/app to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "Back", "app"))

from admin_indexer import (
    rebuild_index, 
    get_index_stats, 
    get_indexed_documents,
    add_document_to_index
)
from document_manager import (
    save_uploaded_document,
    process_document,
    register_processed_document,
    get_processed_documents,
    delete_document,
    mark_document_as_indexed
)


def format_bytes(bytes_val: int) -> str:
    """Formatte les octets en format lisible"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_val < 1024.0:
            return f"{bytes_val:.2f} {unit}"
        bytes_val /= 1024.0
    return f"{bytes_val:.2f} TB"


def format_datetime(iso_str: str) -> str:
    """Formate une date ISO en format lisible"""
    try:
        dt = datetime.fromisoformat(iso_str)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except:
        return iso_str


def render_document_management():
    """Afficher la section de gestion des documents"""
    st.header("Gestion des Documents")
    
    # Créer des onglets pour différentes sections
    doc_tabs = st.tabs(["Télécharger", "Documents Indexés", "Statut de l'Index"])
    
    # ===== TAB 1: Upload Documents =====
    with doc_tabs[0]:
        st.subheader("Télécharger de Nouveaux Documents")
        st.write("""
        Téléchargez des documents (PDF, HTML ou TXT) pour les indexer et les utiliser dans le système RAG.
        Vous pouvez choisir de les ajouter de manière incrémentale (plus rapide) ou de reconstruire tout l'index.
        """)
        
        uploaded_files = st.file_uploader(
            "Choisir des fichiers",
            type=["pdf", "html", "htm", "txt"],
            accept_multiple_files=True,
            help="Sélectionnez un ou plusieurs documents à télécharger"
        )
        
        if uploaded_files:
            st.write(f"**{len(uploaded_files)} fichier(s) prêt(s) à télécharger**")
            
            # Check if index exists to offer incremental indexing
            with st.spinner("Vérification de l'index..."):
                stats = get_index_stats()
            index_exists = stats["index_exists"] and stats["mapping_exists"]
            
            # Choose indexing method
            if index_exists:
                st.info("**Astuce**: L'indexation incrémentale ajoute seulement les nouveaux documents (plus rapide)")
                indexing_method = st.radio(
                    "Méthode d'indexation:",
                    ["incremental", "rebuild"],
                    format_func=lambda x: "Incrémentale (recommandé)" if x == "incremental" else "Reconstruire tout l'index",
                    horizontal=True
                )
            else:
                st.warning("Aucun index existant. Les documents seront ajoutés et un nouvel index sera créé.")
                indexing_method = "rebuild"
            
            if st.button("Télécharger & Indexer", type="primary"):
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                successful = 0
                failed = 0
                uploaded_docs_info = []
                
                # Step 1: Upload all files first
                for idx, uploaded_file in enumerate(uploaded_files):
                    status_text.text(f"Téléchargement {idx + 1}/{len(uploaded_files)}: {uploaded_file.name}")
                    
                    try:
                        # Read file content
                        file_content = uploaded_file.read()
                        
                        # Save file
                        success, msg, file_path = save_uploaded_document(
                            file_content,
                            uploaded_file.name
                        )
                        
                        if not success:
                            st.error(f"{uploaded_file.name}: {msg}")
                            failed += 1
                            continue
                        
                        # Process document
                        success, msg, doc_info = process_document(
                            file_path,
                            uploaded_file.name
                        )
                        
                        if not success:
                            st.error(f"{uploaded_file.name}: {msg}")
                            failed += 1
                            continue
                        
                        # Register document
                        doc_id = f"doc_{int(datetime.now().timestamp() * 1000)}"
                        register_processed_document(
                            doc_id,
                            uploaded_file.name,
                            doc_info["file_type"],
                            doc_info["file_size"],
                            doc_info["content_length"],
                            file_path
                        )
                        
                        successful += 1
                        uploaded_docs_info.append({
                            "id": doc_id,
                            "filename": uploaded_file.name,
                            "file_path": file_path
                        })
                        st.success(f"{uploaded_file.name} uploaded successfully")
                    
                    except Exception as e:
                        st.error(f"Error uploading {uploaded_file.name}: {str(e)}")
                        failed += 1
                    
                    # Update progress
                    progress_bar.progress((idx + 1) / len(uploaded_files))
                
                st.info(f"Uploaded: {successful} | Failed: {failed}")
                
                # Step 2: Index the uploaded documents
                if successful > 0 and uploaded_docs_info:
                    st.divider()
                    st.subheader("Indexation des documents")
                    
                    # Create containers for progress display
                    progress_bar = st.progress(0.0)
                    progress_container = st.container()
                    
                    if indexing_method == "incremental" and index_exists:
                        # Incremental indexing
                        indexed_successfully = 0
                        index_failed = 0
                        
                        for idx, doc_info in enumerate(uploaded_docs_info):
                            # Update progress for document being processed
                            doc_progress = idx / len(uploaded_docs_info)
                            
                            def progress_callback(progress, step, message):
                                # Calculate overall progress
                                overall_progress = doc_progress + (progress / len(uploaded_docs_info))
                                progress_bar.progress(overall_progress)
                                with progress_container:
                                    st.text(f"{doc_info['filename']} - {step}: {message}")
                            
                            success, message, index_stats = add_document_to_index(
                                doc_info["file_path"],
                                doc_info["filename"],
                                progress_callback
                            )
                            
                            if success:
                                # Mark as indexed
                                mark_document_as_indexed(
                                    doc_info["id"], 
                                    index_stats.get("chunks_added", 0)
                                )
                                indexed_successfully += 1
                            else:
                                index_failed += 1
                                with progress_container:
                                    st.error(f"{doc_info['filename']}: {message}")
                        
                        # Complete progress
                        progress_bar.progress(1.0)
                        
                        if indexed_successfully > 0:
                            st.success(f"{indexed_successfully} document(s) indexé(s) avec succès !")
                            
                            # Recharger l'index RAG automatiquement
                            with st.spinner("Rechargement de l'index RAG..."):
                                try:
                                    # Import ici pour éviter les dépendances circulaires
                                    import streamlit as st_reload
                                    if 'rag_instance' in st_reload.session_state:
                                        if hasattr(st_reload.session_state.rag_instance, 'reload_index'):
                                            if st_reload.session_state.rag_instance.reload_index():
                                                st.success("RAG index rechargé ! Les nouveaux documents sont immédiatement disponibles.")
                                            else:
                                                st.warning("Impossible de recharger l'index RAG. Veuillez redémarrer l'application.")
                                        else:
                                            st.info("Redémarrez l'application pour utiliser les nouveaux documents dans le RAG.")
                                    else:
                                        st.info("Les documents sont indexés. Redémarrez l'application pour les utiliser dans le RAG.")
                                except Exception as e:
                                    st.info("Documents indexés. Redémarrez l'application pour les utiliser dans le RAG.")
                            
                            st.rerun()
                    
                    else:
                        # Rebuild entire index
                        
                        def progress_callback(progress, step, message):
                            progress_bar.progress(progress)
                            with progress_container:
                                st.text(f"{step}: {message}")
                        
                        success, message, index_stats = rebuild_index(progress_callback)
                        
                        if success:
                            progress_bar.progress(1.0)
                            st.success(f"{message}")
                            
                            # Mark all uploaded documents as indexed
                            for doc_info in uploaded_docs_info:
                                mark_document_as_indexed(
                                    doc_info["id"],
                                    0  # Will be updated properly in rebuild
                                )
                            
                            with st.expander("Statistiques de l'index", expanded=False):
                                st.json({
                                    "Documents": index_stats.get("document_count"),
                                    "Chunks Créés": index_stats.get("chunk_count"),
                                    "Dimension des Embeddings": index_stats.get("embedding_dim"),
                                })
                            
                            st.info("Les documents sont maintenant prêts pour les requêtes RAG !")
                            st.rerun()
                        else:
                            st.error(f"{message}")
    
    # ===== TAB 2: Indexed Documents =====
    with doc_tabs[1]:
        st.subheader("Documents Indexés")
        
        # Get processed documents with spinner
        with st.spinner("Chargement des documents..."):
            processed_docs = get_processed_documents()
        
        if not processed_docs:
            st.info("Aucun document n'a encore été téléchargé.")
        else:
            # Create DataFrame for display
            df_data = []
            for doc in processed_docs:
                df_data.append({
                    "Nom du fichier": doc.get("filename", ""),
                    "Type": doc.get("type", "").upper(),
                    "Taille": format_bytes(doc.get("file_size", 0)),
                    "Contenu": f"{doc.get('content_length', 0)} chars",
                    "Chunks": doc.get("chunk_count", "—"),
                    "Indexé": "Oui" if doc.get("indexed") else "Non",
                    "Téléchargé": format_datetime(doc.get("uploaded_at", "")),
                    "ID": doc.get("id", "")
                })
            
            df = pd.DataFrame(df_data)
            
            # Display table
            st.dataframe(
                df.drop("ID", axis=1),
                width="stretch",
                hide_index=True
            )
            
            # Actions on documents
            st.subheader("Gérer les Documents")
            col1, col2 = st.columns(2)
            
            with col1:
                doc_to_delete = st.selectbox(
                    "Sélectionner un document à supprimer",
                    [doc["filename"] for doc in processed_docs],
                    key="delete_doc"
                )
                
                if st.button("Supprimer le Document", type="secondary"):
                    with st.spinner("Suppression en cours..."):
                        doc_id = next(doc["id"] for doc in processed_docs if doc["filename"] == doc_to_delete)
                        if delete_document(doc_id):
                            st.success(f"{doc_to_delete} supprimé avec succès")
                            st.rerun()
                        else:
                            st.error("Échec de la suppression du document")
            
            with col2:
                st.write("**Statistiques :**")
                stats = get_index_stats()
                col_a, col_b, col_c = st.columns(3)
                
                with col_a:
                    st.metric("Total Documents", len(processed_docs))
                
                with col_b:
                    indexed_count = sum(1 for doc in processed_docs if doc.get("indexed"))
                    st.metric("Indexés", indexed_count)
                
                with col_c:
                    if stats.get("chunk_count"):
                        st.metric("Chunks", stats["chunk_count"])
    
    # ===== TAB 3: Index Status & Rebuild =====
    with doc_tabs[2]:
        st.subheader("Statut de l'Index")
        
        # Get current index stats with spinner
        with st.spinner("Vérification de l'index..."):
            stats = get_index_stats()
        
        if stats["index_exists"] and stats["mapping_exists"]:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Documents", stats.get("document_count", "—"))
            
            with col2:
                st.metric("Chunks", stats.get("chunk_count", "—"))
            
            with col3:
                st.metric("Dim. Embedding", stats.get("embedding_dim", "—"))
            
            with col4:
                st.metric("Statut", "Prêt")
            
            st.divider()
            
            # Bouton pour recharger l'index RAG manuellement
            st.subheader("Recharger l'Index RAG")
            st.write("""
            Si vous avez ajouté des documents mais que le chatbot ne les trouve pas, 
            cliquez ici pour forcer le rechargement de l'index dans le système RAG.
            """)
            
            if st.button("Recharger l'Index RAG Maintenant", type="primary", key="reload_rag_btn"):
                with st.spinner("Rechargement de l'index RAG..."):
                    try:
                        import streamlit as st_reload
                        if 'rag_instance' in st_reload.session_state:
                            if hasattr(st_reload.session_state.rag_instance, 'reload_index'):
                                if st_reload.session_state.rag_instance.reload_index():
                                    st.success("Index RAG rechargé avec succès ! Les nouveaux documents sont maintenant disponibles.")
                                else:
                                    st.error("Échec du rechargement. Redémarrez l'application.")
                            else:
                                st.warning("La fonction reload_index n'est pas disponible. Redémarrez l'application.")
                        else:
                            st.warning("Instance RAG non trouvée. Redémarrez l'application pour utiliser les nouveaux documents.")
                    except Exception as e:
                        st.error(f"Erreur : {str(e)}")
                        st.info("Solution : Redémarrez l'application Streamlit.")
            
            st.divider()
        else:
            st.warning("Aucun index n'existe encore. Téléchargez des documents et reconstruisez l'index.")
        
        # Rebuild index section
        st.subheader("Reconstruire l'Index")
        st.write("""
        Cliquez sur le bouton ci-dessous pour reconstruire l'index FAISS avec tous les documents téléchargés.
        Ce processus va :
        1. Charger tous les documents téléchargés
        2. Les diviser en chunks
        3. Générer les embeddings
        4. Construire l'index FAISS
        
        Cela peut prendre quelques minutes selon le nombre de documents.
        """)
        
        # Check if there are documents to index
        processed_docs = get_processed_documents()
        non_indexed = [doc for doc in processed_docs if not doc.get("indexed")]
        
        if not processed_docs:
            st.info("Aucun document disponible à indexer. Veuillez d'abord télécharger des documents.")
        else:
            if st.button("Reconstruire l'Index", type="primary", key="rebuild_btn"):
                st.subheader("Reconstruction en cours")
                
                # Create progress bar and container
                progress_bar = st.progress(0.0)
                progress_container = st.container()
                
                def progress_callback(progress, step, message):
                    progress_bar.progress(progress)
                    with progress_container:
                        st.text(f"{step}: {message}")
                
                success, message, index_stats = rebuild_index(progress_callback)
                
                if success:
                    progress_bar.progress(1.0)
                    st.success(f"{message}")
                    
                    # Update document metadata to mark as indexed
                    for doc in non_indexed:
                        chunk_count = index_stats.get("chunk_count", 0)
                        mark_document_as_indexed(doc["id"], chunk_count)
                    
                    # Display new stats
                    with st.expander("Statistiques de l'index", expanded=True):
                        st.json({
                            "Documents": index_stats.get("document_count"),
                            "Chunks Created": index_stats.get("chunk_count"),
                            "Embedding Dimension": index_stats.get("embedding_dim"),
                            "Indexed At": index_stats.get("indexed_at")
                        })
                    
                    st.info("Documents are now ready for RAG queries!")
                    st.rerun()
                else:
                    st.error(f"{message}")
            
            # Show summary
            st.divider()
            st.write("**Documents Status:**")
            
            indexed_count = sum(1 for doc in processed_docs if doc.get("indexed"))
            non_indexed_count = len(processed_docs) - indexed_count
            
            col1, col2 = st.columns(2)
            with col1:
                st.success(f"Indexed: {indexed_count}")
            
            with col2:
                st.warning(f"Pending: {non_indexed_count}")
