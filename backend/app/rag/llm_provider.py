import os
import re
import json
import logging
from typing import List, Dict, Any, Optional
import httpx
from backend.app.config import settings

logger = logging.getLogger("neuralsearch.llm")

class BaseLLMProvider:
    def generate(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: int = 1500
    ) -> str:
        raise NotImplementedError

class MockLLMProvider(BaseLLMProvider):
    """
    Intelligent heuristic offline generator for hermetic testing and zero-cost operation.
    Synthesizes retrieved passages, preserves exact citations, and flags unavailable knowledge.
    """
    def generate(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: int = 1500
    ) -> str:
        # Check if the prompt contains context sections
        if "CONTEXT PASSAGES:" not in prompt:
            return "Based on the provided research context, no supporting passages were found."

        context_part = prompt.split("CONTEXT PASSAGES:")[1]
        if "USER QUESTION:" in context_part:
            context_text, question = context_part.split("USER QUESTION:", 1)
        else:
            context_text = context_part
            question = ""

        # Extract passages: [Passage 1 | Doc: filename.pdf | Page: 2] ...
        passages = re.findall(
            r"\[Passage (\d+) \| Doc: ([^\|]+) \| Page: (\d+)\]\n(.*?)(?=\n\[Passage|\n*$)",
            context_text,
            re.DOTALL
        )

        if not passages:
            return "I do not have sufficient information in the provided documents to answer this question. (No relevant context found in uploaded research papers)"

        q_lower = question.lower()
        key_words = [w for w in re.findall(r"\b\w{3,}\b", q_lower) if w not in {"what", "when", "where", "which", "how", "does", "explain", "describe", "compare", "paper", "documents"}]

        # Find best matching sentences across passages
        extracted_points = []
        citations_used = []

        for p_idx, doc_name, page_num, text in passages:
            clean_text = text.strip()
            sentences = re.split(r"(?<=[.!?])\s+", clean_text)
            matched_sentences = []
            
            for s in sentences:
                s_clean = s.strip()
                if not s_clean or len(s_clean) < 15:
                    continue
                match_count = sum(1 for kw in key_words if kw in s_clean.lower())
                if match_count > 0 or len(passages) <= 2:
                    matched_sentences.append((match_count, s_clean))

            if matched_sentences:
                matched_sentences.sort(key=lambda x: x[0], reverse=True)
                top_sent = matched_sentences[0][1]
                cite = f"[{doc_name.strip()}, p.{page_num.strip()}]"
                extracted_points.append(f"- {top_sent} {cite}")
                citations_used.append(cite)

        if not extracted_points:
            # Fallback to first passage excerpt
            p_idx, doc_name, page_num, text = passages[0]
            first_sent = text.strip().split(".")[0] + "."
            cite = f"[{doc_name.strip()}, p.{page_num.strip()}]"
            extracted_points.append(f"- {first_sent} {cite}")

        answer_intro = "Based on the retrieved research context from the uploaded documents:\n\n"
        answer_body = "\n".join(extracted_points)
        answer_conclusion = f"\n\nThese findings are supported by primary source citations from {', '.join(set(citations_used))}."
        
        return answer_intro + answer_body + answer_conclusion

class OpenAILLMProvider(BaseLLMProvider):
    """OpenAI API connector (supports GPT-4o, GPT-4o-mini)."""
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.model = model or settings.OPENAI_MODEL

    def generate(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: int = 1500
    ) -> str:
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY is not configured.")

        from openai import OpenAI
        client = OpenAI(api_key=self.api_key)
        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})

        response = client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        return response.choices[0].message.content or ""

class GeminiLLMProvider(BaseLLMProvider):
    """Google Gemini API connector using standard HTTP API."""
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model = model or settings.GEMINI_MODEL

    def generate(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: int = 1500
    ) -> str:
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is not configured.")

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        
        contents = []
        if system_instruction:
            contents.append({"role": "user", "parts": [{"text": f"SYSTEM INSTRUCTION: {system_instruction}"}]})
            contents.append({"role": "model", "parts": [{"text": "Understood. I will strictly follow this instruction."}]})
        contents.append({"role": "user", "parts": [{"text": prompt}]})

        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens
            }
        }
        with httpx.Client(timeout=30.0) as client:
            resp = client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            candidates = data.get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                if parts:
                    return parts[0].get("text", "")
            return ""

class AnthropicLLMProvider(BaseLLMProvider):
    """Anthropic Claude API connector."""
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or settings.ANTHROPIC_API_KEY
        self.model = model or settings.ANTHROPIC_MODEL

    def generate(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: int = 1500
    ) -> str:
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY is not configured.")

        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        payload = {
            "model": self.model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [{"role": "user", "content": prompt}]
        }
        if system_instruction:
            payload["system"] = system_instruction

        with httpx.Client(timeout=35.0) as client:
            resp = client.post("https://api.anthropic.com/v1/messages", headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            content_blocks = data.get("content", [])
            if content_blocks:
                return content_blocks[0].get("text", "")
            return ""

class OllamaLLMProvider(BaseLLMProvider):
    """Local Ollama LLM provider connector."""
    def __init__(self, base_url: Optional[str] = None, model: Optional[str] = None):
        self.base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self.model = model or settings.OLLAMA_MODEL

    def generate(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: int = 1500
    ) -> str:
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "system": system_instruction or "",
            "stream": False,
            "options": {"temperature": temperature, "num_predict": max_tokens}
        }
        with httpx.Client(timeout=60.0) as client:
            resp = client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data.get("response", "")

def get_llm_provider(provider_name: Optional[str] = None, model_name: Optional[str] = None) -> BaseLLMProvider:
    """Factory to retrieve configured LLM provider."""
    name = (provider_name or settings.DEFAULT_LLM_PROVIDER).lower()
    
    if name == "openai":
        return OpenAILLMProvider(model=model_name)
    elif name == "gemini":
        return GeminiLLMProvider(model=model_name)
    elif name == "anthropic":
        return AnthropicLLMProvider(model=model_name)
    elif name == "ollama":
        return OllamaLLMProvider(model=model_name)
    else:
        return MockLLMProvider()
