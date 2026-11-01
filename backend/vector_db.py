"""ChromaDB 벡터 저장소 (Google Gemini 임베딩)."""
import os
from typing import List

from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_google_genai import GoogleGenerativeAIEmbeddings

load_dotenv()


class VectorDB:
    def __init__(self, collection_name: str = "company_docs"):
        api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model=os.getenv("EMBEDDING_MODEL", "models/text-embedding-004"),
            google_api_key=api_key,
        )
        # persist_directory 지정 시 서버 재시작 후에도 자동 로드된다.
        self.store = Chroma(
            collection_name=collection_name,
            embedding_function=self.embeddings,
            persist_directory=os.getenv("CHROMA_PERSIST_DIR", "./chroma_db"),
        )

    def add_documents(self, chunks: List[Document]) -> int:
        """같은 파일 재업로드 시 중복 적재를 막기 위해 기존 청크를 먼저 삭제(upsert)."""
        if not chunks:
            return 0
        source = chunks[0].metadata["source"]
        self.store.delete(where={"source": source})
        ids = [f'{c.metadata["source"]}::{c.metadata["chunk"]}' for c in chunks]
        self.store.add_documents(chunks, ids=ids)
        return len(chunks)

    def search(self, query: str, k: int = 4) -> List[Document]:
        """코사인 유사도 기반 Top-k 검색."""
        return self.store.similarity_search(query, k=k)
