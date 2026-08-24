import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langchain_core.language_models.chat_models import BaseChatModel

load_dotenv()

from .config import get_llm_config

def get_model(temperature: float = 0.0, use_fallback: bool = False, use_eval: bool = False) -> BaseChatModel:
    config = get_llm_config()
    provider = config["provider"]
    if use_eval:
        model_name = config["eval_model"]
    elif use_fallback:
        model_name = config["fallback_model"]
    else:
        model_name = config["primary_model"]
    
    if provider == "gemini":
        api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        return ChatGoogleGenerativeAI(model=model_name, temperature=temperature, google_api_key=api_key)
    elif provider == "openai":
        return ChatOpenAI(model=model_name, temperature=temperature)
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")
