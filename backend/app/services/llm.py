import hashlib
import json

from cachetools import TTLCache
from openai import OpenAI

from app.config import settings


class LlmService:
    def __init__(self) -> None:
        self.cache = TTLCache(maxsize=256, ttl=settings.cache_ttl_seconds)
        self.client = OpenAI(api_key=settings.openai_api_key) if settings.openai_api_key else None

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
            result = self.client.chat.completions.create(
                model=settings.model_name,
                temperature=0.2,
                messages=[{"role": "user", "content": prompt}],
            )
            answer = result.choices[0].message.content or ""
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
            stream = self.client.chat.completions.create(
                model=settings.model_name,
                temperature=0.2,
                messages=[{"role": "user", "content": prompt}],
                stream=True,
            )
            for chunk in stream:
                delta = chunk.choices[0].delta.content if chunk.choices else None
                if delta:
                    yield delta
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
