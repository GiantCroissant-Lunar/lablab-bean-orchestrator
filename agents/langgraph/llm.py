import os
from typing import List, Dict, Any


def call_llm(messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
    """
    Minimal, pluggable LLM caller.
    - If GLM env vars are set (GLM_API_KEY/GLM_BASE_URL/GLM_MODEL), call an OpenAI-compatible endpoint.
    - Otherwise, no-op stub that returns a placeholder.
    This keeps costs zero until you configure GLM.
    """
    api_key = os.getenv("GLM_API_KEY")
    base_url = os.getenv("GLM_BASE_URL")
    model = os.getenv("GLM_MODEL", "glm-4")

    if not api_key or not base_url:
        return {"role": "assistant", "content": "[stub] No LLM configured. Provide GLM_API_KEY and GLM_BASE_URL to enable."}

    try:
        # Lazy import to avoid hard dependency if you don't use it
        from openai import OpenAI

        client = OpenAI(api_key=api_key, base_url=base_url)
        resp = client.chat.completions.create(model=model, messages=messages, **kwargs)
        choice = resp.choices[0].message
        return {"role": choice.role, "content": choice.content}
    except Exception as e:
        return {"role": "assistant", "content": f"[error calling LLM] {e}"}

