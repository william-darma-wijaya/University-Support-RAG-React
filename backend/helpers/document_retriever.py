from sqlalchemy import create_engine, select, String
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from model.models import ProcessedFile
import glob
import os
import json

class DocumentRetriever:
    def __init__(self, db_path, db_session: Session, model_name="LazarusNLP/all-indo-e5-small-v4", k=3):
        self.embeddings = HuggingFaceEmbeddings(model_name=model_name)
        self.k = k
        self.db_path = db_path
        self.db_session = db_session
        self.vector_store = None
        self.retriever = None
    
    def _load_docs_by_type(self, file_path):
        ext = os.path.splitext(file_path)[1].lower()

        if ext == ".txt":
            return self._load_txt_docs(file_path)
        elif ext in [".docx", "doc"]:
            return self._load_word_docs(file_path)
        else:
            raise ValueError(f"Unsupported file type {ext}")
        
    def _load_txt_docs(self, file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()
        return [Document(page_content=text, metadata={"source": os.path.basename(file_path)})]
    
    def _load_word_docs(self, file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()
        return [Document(page_content=text, metadata={"source": os.path.basename(file_path)})]
        
    def load_docs_from_folder(self, folder_path):
        supported_ext = [".txt", ".docx", ".doc"]
        docs = []

        for ext in supported_ext:
            file_paths = glob.glob(os.path.join(folder_path, f"*{ext}"))
            for file in file_paths:
                try:
                    docs += self._load_docs_by_type(file)
                except Exception as e:
                    print(f"GAGAL LOAD FILE {file}: {e}")

        return docs
    
    def _split_docs(self, docs: list[Document]):
        text_splitter = RecursiveCharacterTextSplitter(chunk_size = 500, chunk_overlap=100, length_function=len, is_separator_regex=False)
        all_chunks = []
        for doc in docs:
            chunks = text_splitter.split_text(doc.page_content)
            total = len(chunks)
            for i, chunk in enumerate(chunks):
                new_doc = Document(
                    page_content=chunk,
                    metadata = {
                        **doc.metadata,
                        "chunk_number": i,
                        "total_chunks": total
                    }
                )
                all_chunks.append(new_doc)

        return all_chunks

    def _is_file_processed(self, filename: str) -> bool:
        """
        Mengecek apakah sebuah file sudah ada di database.
        """
        query = select(ProcessedFile).where(ProcessedFile.filename == filename)
        result = self.db_session.execute(query).first()
        return result is not None

    def _add_processed_file(self, filename: str):
        """
        Menambahkan nama file baru ke database.
        """
        new_file = ProcessedFile(filename=filename)
        self.db_session.add(new_file)
        self.db_session.commit()
    
    def init_or_update_vectorstore(self, folder_path):
        documents = self.load_docs_from_folder(folder_path=folder_path)

        new_chunks = []

        for doc in documents:
            source = doc.metadata["source"]
            if self._is_file_processed(source):
                print(f"File {source} sudah pernah diproses, dilewatkan...")
                continue
            print(f"Memproses file baru: {source}")
            chunks = self._split_docs([doc])
            new_chunks.extend(chunks)
            self._add_processed_file(source)
        
        added = 0
        if os.path.exists(os.path.join(self.db_path, "index.faiss")):
            print("Load vectorstore dari lokal...")
            self.vector_store = FAISS.load_local(self.db_path, self.embeddings, allow_dangerous_deserialization=True)
            added = len(new_chunks)
            if (new_chunks):
                print(f"Menambahkan {added} chunks baru ke vectorstore...")
                self.vector_store.add_documents(new_chunks)
        else:
            print("Membuat vectorstore baru...")
            self.vector_store = FAISS.from_documents(documents=new_chunks, embedding=self.embeddings)
            added = len(new_chunks)
            self.vector_store.save_local(self.db_path)

        self.retriever = self.vector_store.as_retriever(
            search_type="similarity",
            search_kwargs={"k": self.k}
        )

        print(f"Vectorstore siap. {added} chunks baru ditambahkan.")

    def get_retriever(self):
        return self.retriever

        

        

