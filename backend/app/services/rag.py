from pathlib import Path

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

from app.config import settings


class DeterministicEmbeddings:
    size = 128

    def _embed(self, text: str) -> list[float]:
        vector = [0.0] * self.size
        for i, b in enumerate(text.encode("utf-8")):
            vector[i % self.size] += (b % 31) / 31
        norm = sum(abs(v) for v in vector) or 1.0
        return [v / norm for v in vector]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._embed(t) for t in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._embed(text)


class RagService:
    def __init__(self) -> None:
        self.embedding = DeterministicEmbeddings()
        self.splitter = RecursiveCharacterTextSplitter(chunk_size=600, chunk_overlap=100)
        self.index_dir = Path(settings.vector_store_dir)
        self.index_dir.mkdir(parents=True, exist_ok=True)
        self.vector_store = self._load_store()

    def ingest_from_disk(self) -> int:
        docs_path = Path(settings.docs_dir)
        docs = []
        for file in docs_path.glob("*.txt"):
            content = file.read_text(encoding="utf-8")
            docs.extend(self._to_chunks(content, str(file)))
        self._upsert(docs)
        return len(docs)

    def ingest_text(self, content: str, source: str) -> int:
        docs = self._to_chunks(content, source)
        self._upsert(docs)
        return len(docs)

    def retrieve(self, query: str, top_k: int = 4) -> list[Document]:
        if self.vector_store is None:
            self.vector_store = self._load_store()
        if self.vector_store is None:
            return []
        return self.vector_store.similarity_search(query, k=top_k)

    def _to_chunks(self, content: str, source: str) -> list[Document]:
        splits = self.splitter.split_text(content)
        return [Document(page_content=chunk, metadata={"source": source}) for chunk in splits]

    def _upsert(self, docs: list[Document]) -> None:
        if not docs:
            return
        if self.vector_store is None:
            self.vector_store = FAISS.from_documents(docs, self.embedding)
        else:
            self.vector_store.add_documents(docs)
        self.vector_store.save_local(str(self.index_dir))

    def _load_store(self) -> FAISS | None:
        faiss_file = self.index_dir / "index.faiss"
        pkl_file = self.index_dir / "index.pkl"
        if faiss_file.exists() and pkl_file.exists():
            return FAISS.load_local(str(self.index_dir), self.embedding, allow_dangerous_deserialization=True)
        return None
