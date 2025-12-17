from helpers.document_retriever import DocumentRetriever
from helpers.rag_chain import SimpleRAGChain
from helpers.database import get_db
from langchain_community.chat_message_histories import ChatMessageHistory
from typing import List, Dict
import os
from sqlalchemy.orm import Session

# Setup retriever dan chain global
current_directory = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
db_path = os.path.join(current_directory, "vector_db")
folder_path = os.path.join(current_directory, "documents")
metadata_path = os.path.join(current_directory, "metadata")

os.makedirs(db_path, exist_ok=True)
os.makedirs(folder_path, exist_ok=True)
os.makedirs(metadata_path, exist_ok=True)

db_session = get_db()

# docs_retriever = DocumentRetriever(db_path=db_path, db_session=db_session)
# docs_retriever.init_or_update_vectorstore(folder_path=folder_path)
# retriever = docs_retriever.get_retriever()

# rag_chain = SimpleRAGChain(retriever=retriever)

def create_rag_chain(db_session: Session) -> SimpleRAGChain:
    """
    Fungsi ini membuat dan menginisialisasi semua yang dibutuhkan
    untuk RAG chain, dan menerima sesi database yang aktif.
    """
    # 1. Inisialisasi retriever di DALAM FUNGSI
    docs_retriever = DocumentRetriever(db_path=db_path, db_session=db_session)
    
    # 2. Lakukan update vector store
    docs_retriever.init_or_update_vectorstore(folder_path=folder_path)
    
    # 3. Dapatkan retriever object
    retriever = docs_retriever.get_retriever()
    
    # 4. Buat RAG chain
    rag_chain = SimpleRAGChain(retriever=retriever)
    
    return rag_chain

def convert_to_chat_history(messages: List[Dict[str, str]]) -> ChatMessageHistory:
    history = ChatMessageHistory()
    for msg in messages:
        if msg["role"] == "user":
            history.add_user_message(msg["message"])
        elif msg["role"] == "assistant":
            history.add_ai_message(msg["message"])
    return history