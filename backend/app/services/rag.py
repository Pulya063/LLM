import json
from dataclasses import dataclass
from pathlib import Path

from app.config import settings


@dataclass
class RetrievedDocument:
    page_content: str
    metadata: dict


class DeterministicEmbeddings:
    size = 128

    def embed(self, text: str) -> list[float]:
        vector = [0.0] * self.size
        for i, b in enumerate(text.encode("utf-8")):
            vector[i % self.size] += (b % 31) / 31
        norm = sum(abs(v) for v in vector) or 1.0
        return [v / norm for v in vector]


class RagService:
    def __init__(self) -> None:
        self.embedding = DeterministicEmbeddings()
        self.chunk_size = 600
        self.chunk_overlap = 100
        self.index_dir = Path(settings.vector_store_dir)
        self.index_dir.mkdir(parents=True, exist_ok=True)
        self.index_file = self.index_dir / "index.json"
        self.records = self._load_records()

    def ingest_from_disk(self) -> int:
        docs_path = Path(settings.docs_dir)
        chunks = []
        for file in docs_path.glob("*.txt"):
            content = file.read_text(encoding="utf-8")
            chunks.extend(self._to_chunks(content, str(file)))
        self._upsert(chunks)
        return len(chunks)

    def ingest_text(self, content: str, source: str) -> int:
        chunks = self._to_chunks(content, source)
        self._upsert(chunks)
        return len(chunks)

    def retrieve(self, query: str, top_k: int = 4) -> list[RetrievedDocument]:
        if not self.records:
            return []
        query_vec = self.embedding.embed(query)
        scored = []
        for record in self.records:
            score = self._cosine(query_vec, record["embedding"])
            scored.append((score, record))
        scored.sort(key=lambda item: item[0], reverse=True)
        best = scored[:top_k]
        return [RetrievedDocument(page_content=item[1]["content"], metadata={"source": item[1]["source"]}) for item in best]

    def _to_chunks(self, content: str, source: str) -> list[RetrievedDocument]:
        text = content.strip()
        if not text:
            return []
        chunks = []
        start = 0
        while start < len(text):
            end = min(start + self.chunk_size, len(text))
            chunks.append(RetrievedDocument(page_content=text[start:end], metadata={"source": source}))
            if end == len(text):
                break
            start = max(0, end - self.chunk_overlap)
        return chunks

    def _upsert(self, chunks: list[RetrievedDocument]) -> None:
        if not chunks:
            return
        for chunk in chunks:
            self.records.append(
                {
                    "source": chunk.metadata.get("source", "unknown"),
                    "content": chunk.page_content,
                    "embedding": self.embedding.embed(chunk.page_content),
                }
            )
        self.index_file.write_text(json.dumps(self.records, ensure_ascii=False), encoding="utf-8")

    def _load_records(self) -> list[dict]:
        if not self.index_file.exists():
            return []
        return json.loads(self.index_file.read_text(encoding="utf-8"))

    def _cosine(self, a: list[float], b: list[float]) -> float:
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = sum(x * x for x in a) ** 0.5
        norm_b = sum(y * y for y in b) ** 0.5
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)
