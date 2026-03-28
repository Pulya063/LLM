import hashlib
import json
from cachetools import TTLCache
from langchain_openai import ChatOpenAI

from app.config import settings


class LlmService:
    def __init__(self) -> None:
        self.cache = TTLCache(maxsize=256, ttl=settings.cache_ttl_seconds)
        self.client = None
        if settings.openai_api_key:
            self.client = ChatOpenAI(model=settings.model_name, api_key=settings.openai_api_key, temperature=0.2)

    def generate(self, question: str, context_blocks: list[str]) -> dict:
        cache_key = self._cache_key(question, context_blocks)
        if cache_key in self.cache:
            return {"answer": self.cache[cache_key], "cache": True}
        if self.client:
            context = "\n\n".join(context_blocks)
            prompt = (
                "You are a production support AI assistant. Use context when relevant. "
                "If context is insufficient, clearly state assumptions.\n"
                f"Context:\n{context}\n\nQuestion:\n{question}"
            )
            answer = self.client.invoke(prompt).content
        else:
            answer = self._deterministic_answer(question, context_blocks)
        self.cache[cache_key] = answer
        return {"answer": answer, "cache": False}

    def stream_tokens(self, question: str, context_blocks: list[str]):
        if self.client:
            context = "\n\n".join(context_blocks)
            prompt = (
                "You are a production support AI assistant. Use context when relevant. "
                "If context is insufficient, clearly state assumptions.\n"
                f"Context:\n{context}\n\nQuestion:\n{question}"
            )
            for chunk in self.client.stream(prompt):
                token = chunk.content or ""
                if token:
                    yield token
            return
        answer = self._deterministic_answer(question, context_blocks)
        for token in answer.split(" "):
            yield token + " "

    def _cache_key(self, question: str, context_blocks: list[str]) -> str:
        payload = json.dumps({"q": question, "c": context_blocks}, sort_keys=True)
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def _deterministic_answer(self, question: str, context_blocks: list[str]) -> str:
        if not context_blocks:
            return f"No indexed context found for: {question}. Try ingesting documents first."
        top = context_blocks[0][:300]
        return f"Based on retrieved context: {top}"
