import os

def get_llm_config() -> dict:
    return {
        "provider": os.getenv("LLM_PROVIDER", "gemini"),
        "primary_model": os.getenv("LLM_PRIMARY_MODEL", "gemini-3.5-flash"),
        "fallback_model": os.getenv("LLM_FALLBACK_MODEL", "gemini-3.1-flash-lite"),
        "eval_model": os.getenv("LLM_EVAL_MODEL", "gemini-3.1-flash-lite"),
    }
