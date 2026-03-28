from pathlib import Path

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
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
        self.vector_store = Chroma(
            collection_name="assistant_kb",
            embedding_function=self.embedding,
            persist_directory=settings.vector_store_dir,
        )

    def ingest_from_disk(self) -> int:
        docs_path = Path(settings.docs_dir)
        docs = []
        for file in docs_path.glob("*.txt"):
            content = file.read_text(encoding="utf-8")
            docs.extend(self._to_chunks(content, str(file)))
        if docs:
            self.vector_store.add_documents(docs)
        return len(docs)

    def ingest_text(self, content: str, source: str) -> int:
        docs = self._to_chunks(content, source)
        if docs:
            self.vector_store.add_documents(docs)
        return len(docs)

    def retrieve(self, query: str, top_k: int = 4) -> list[Document]:
        return self.vector_store.similarity_search(query, k=top_k)

    def _to_chunks(self, content: str, source: str) -> list[Document]:
        splits = self.splitter.split_text(content)
        return [Document(page_content=chunk, metadata={"source": source}) for chunk in splits]
