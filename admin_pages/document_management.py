"""
Streamlit page for document management in the Administration tab
Allows uploading, viewing, and managing indexed documents
"""
import streamlit as st
import sys
import os
from datetime import datetime
import pandas as pd

# Add Back/app to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "Back", "app"))

from admin_indexer import rebuild_index, get_index_stats, get_indexed_documents
from document_manager import (
    save_uploaded_document,
    process_document,
    register_processed_document,
    get_processed_documents,
    delete_document,
    mark_document_as_indexed
)
from admin_indexer import chunk_documents, load_documents


def format_bytes(bytes_val: int) -> str:
    """Format bytes to human-readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_val < 1024.0:
            return f"{bytes_val:.2f} {unit}"
        bytes_val /= 1024.0
    return f"{bytes_val:.2f} TB"


def format_datetime(iso_str: str) -> str:
    """Format ISO datetime string to readable format"""
    try:
        dt = datetime.fromisoformat(iso_str)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except:
        return iso_str


def render_document_management():
    """Render the document management section"""
    st.header("📄 Document Management")
    
    # Create tabs for different sections
    doc_tabs = st.tabs(["Upload Documents", "Indexed Documents", "Index Status"])
    
    # ===== TAB 1: Upload Documents =====
    with doc_tabs[0]:
        st.subheader("Upload New Documents")
        st.write("""
        Upload documents (PDF, HTML, or TXT) to be indexed and used by the RAG system.
        After uploading, you'll need to rebuild the index to make them available.
        """)
        
        uploaded_files = st.file_uploader(
            "Choose files to upload",
            type=["pdf", "html", "htm", "txt"],
            accept_multiple_files=True,
            help="Select one or more documents to upload"
        )
        
        if uploaded_files:
            st.write(f"**{len(uploaded_files)} file(s) ready to upload**")
            
            if st.button("📤 Upload Files", type="primary"):
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                successful = 0
                failed = 0
                
                for idx, uploaded_file in enumerate(uploaded_files):
                    status_text.text(f"Processing {idx + 1}/{len(uploaded_files)}: {uploaded_file.name}")
                    
                    try:
                        # Read file content
                        file_content = uploaded_file.read()
                        
                        # Save file
                        success, msg, file_path = save_uploaded_document(
                            file_content,
                            uploaded_file.name
                        )
                        
                        if not success:
                            st.error(f"❌ {uploaded_file.name}: {msg}")
                            failed += 1
                            continue
                        
                        # Process document
                        success, msg, doc_info = process_document(
                            file_path,
                            uploaded_file.name
                        )
                        
                        if not success:
                            st.error(f"❌ {uploaded_file.name}: {msg}")
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
                        st.success(f"✅ {uploaded_file.name} uploaded successfully")
                    
                    except Exception as e:
                        st.error(f"❌ Error uploading {uploaded_file.name}: {str(e)}")
                        failed += 1
                    
                    # Update progress
                    progress_bar.progress((idx + 1) / len(uploaded_files))
                
                st.info(f"✅ Uploaded: {successful} | ❌ Failed: {failed}")
    
    # ===== TAB 2: Indexed Documents =====
    with doc_tabs[1]:
        st.subheader("Indexed Documents")
        
        # Get processed documents
        processed_docs = get_processed_documents()
        
        if not processed_docs:
            st.info("No documents have been uploaded yet.")
        else:
            # Create DataFrame for display
            df_data = []
            for doc in processed_docs:
                df_data.append({
                    "Filename": doc.get("filename", ""),
                    "Type": doc.get("type", "").upper(),
                    "Size": format_bytes(doc.get("file_size", 0)),
                    "Content": f"{doc.get('content_length', 0)} chars",
                    "Chunks": doc.get("chunk_count", "—"),
                    "Indexed": "✅ Yes" if doc.get("indexed") else "❌ No",
                    "Uploaded": format_datetime(doc.get("uploaded_at", "")),
                    "ID": doc.get("id", "")
                })
            
            df = pd.DataFrame(df_data)
            
            # Display table
            st.dataframe(
                df.drop("ID", axis=1),
                use_container_width=True,
                hide_index=True
            )
            
            # Actions on documents
            st.subheader("Manage Documents")
            col1, col2 = st.columns(2)
            
            with col1:
                doc_to_delete = st.selectbox(
                    "Select document to delete",
                    [doc["filename"] for doc in processed_docs],
                    key="delete_doc"
                )
                
                if st.button("🗑️ Delete Selected Document", type="secondary"):
                    doc_id = next(doc["id"] for doc in processed_docs if doc["filename"] == doc_to_delete)
                    if delete_document(doc_id):
                        st.success(f"✅ {doc_to_delete} deleted successfully")
                        st.rerun()
                    else:
                        st.error("Failed to delete document")
            
            with col2:
                st.write("**Statistics:**")
                stats = get_index_stats()
                col_a, col_b, col_c = st.columns(3)
                
                with col_a:
                    st.metric("Total Documents", len(processed_docs))
                
                with col_b:
                    indexed_count = sum(1 for doc in processed_docs if doc.get("indexed"))
                    st.metric("Indexed", indexed_count)
                
                with col_c:
                    if stats.get("chunk_count"):
                        st.metric("Chunks", stats["chunk_count"])
    
    # ===== TAB 3: Index Status & Rebuild =====
    with doc_tabs[2]:
        st.subheader("Index Status")
        
        # Get current index stats
        stats = get_index_stats()
        
        if stats["index_exists"] and stats["mapping_exists"]:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Documents", stats.get("document_count", "—"))
            
            with col2:
                st.metric("Chunks", stats.get("chunk_count", "—"))
            
            with col3:
                st.metric("Embedding Dim", stats.get("embedding_dim", "—"))
            
            with col4:
                st.metric("Status", "✅ Ready")
            
            st.divider()
        else:
            st.warning("No index exists yet. Upload documents and rebuild the index.")
        
        # Rebuild index section
        st.subheader("Rebuild Index")
        st.write("""
        Click the button below to rebuild the FAISS index with all uploaded documents.
        This process will:
        1. Load all uploaded documents
        2. Split them into chunks
        3. Generate embeddings
        4. Build the FAISS index
        
        This may take a few minutes depending on the number of documents.
        """)
        
        # Check if there are documents to index
        processed_docs = get_processed_documents()
        non_indexed = [doc for doc in processed_docs if not doc.get("indexed")]
        
        if not processed_docs:
            st.info("No documents available to index. Please upload documents first.")
        else:
            if st.button("🔄 Rebuild Index", type="primary", key="rebuild_btn"):
                with st.spinner("Rebuilding index... This may take a few minutes."):
                    progress_placeholder = st.empty()
                    status_placeholder = st.empty()
                    
                    def progress_callback(message):
                        status_placeholder.info(f"📋 {message}")
                    
                    success, message, index_stats = rebuild_index(progress_callback)
                    
                    if success:
                        st.success(f"✅ {message}")
                        
                        # Update document metadata to mark as indexed
                        for doc in non_indexed:
                            chunk_count = index_stats.get("chunk_count", 0)
                            mark_document_as_indexed(doc["id"], chunk_count)
                        
                        # Display new stats
                        st.json({
                            "Documents": index_stats.get("document_count"),
                            "Chunks Created": index_stats.get("chunk_count"),
                            "Embedding Dimension": index_stats.get("embedding_dim"),
                            "Indexed At": index_stats.get("indexed_at")
                        })
                        
                        st.info("✅ Documents are now ready for RAG queries!")
                        st.rerun()
                    else:
                        st.error(f"❌ {message}")
            
            # Show summary
            st.divider()
            st.write("**Documents Status:**")
            
            indexed_count = sum(1 for doc in processed_docs if doc.get("indexed"))
            non_indexed_count = len(processed_docs) - indexed_count
            
            col1, col2 = st.columns(2)
            with col1:
                st.success(f"✅ Indexed: {indexed_count}")
            
            with col2:
                st.warning(f"⏳ Pending: {non_indexed_count}")
