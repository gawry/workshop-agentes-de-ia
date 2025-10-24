"""
Configuration management for RAG evaluation demo.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
PYTHON_DIR = Path(__file__).parent
DATASETS_DIR = PROJECT_ROOT / "datasets"
CHROMA_DB_PATH = PYTHON_DIR / "chroma_db"

# API Keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
LANGCHAIN_API_KEY = os.getenv("LANGCHAIN_API_KEY")

# LangSmith configuration
LANGCHAIN_PROJECT = os.getenv("LANGCHAIN_PROJECT", "rag-evaluation-demo")
LANGCHAIN_TRACING_V2 = os.getenv("LANGCHAIN_TRACING_V2", "true").lower() == "true"

# Model configuration
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")

# Dataset paths
GOLDEN_SET_CSV = DATASETS_DIR / "golden-set.csv"
RELATORIO_FINANCEIRO = DATASETS_DIR / "relatorio-financeiro.txt"
RELATORIO_ADMINISTRACAO = DATASETS_DIR / "Relatorio-da-administracao.txt"

# RAG configuration
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
TOP_K_RETRIEVAL = 5

# Evaluation configuration
EVALUATION_METRICS = {
    "faithfulness_threshold": 0.7,
    "hallucination_threshold": 0.5,
    "relevancy_threshold": 0.7
}

def validate_config():
    """Validate that required configuration is present."""
    errors = []
    
    if not OPENAI_API_KEY and not OPENROUTER_API_KEY:
        errors.append("Either OPENAI_API_KEY or OPENROUTER_API_KEY must be set")
    
    if not LANGCHAIN_API_KEY:
        errors.append("LANGCHAIN_API_KEY must be set for tracing and evaluation")
    
    if not GOLDEN_SET_CSV.exists():
        errors.append(f"Golden set CSV not found at {GOLDEN_SET_CSV}")
    
    if not RELATORIO_FINANCEIRO.exists():
        errors.append(f"Financial report not found at {RELATORIO_FINANCEIRO}")
    
    if not RELATORIO_ADMINISTRACAO.exists():
        errors.append(f"Administration report not found at {RELATORIO_ADMINISTRACAO}")
    
    if errors:
        raise ValueError("Configuration validation failed:\n" + "\n".join(f"- {error}" for error in errors))
    
    return True

def get_llm_config():
    """Get LLM configuration based on available API keys."""
    if OPENAI_API_KEY:
        return {
            "provider": "openai",
            "api_key": OPENAI_API_KEY,
            "model": OPENAI_MODEL
        }
    elif OPENROUTER_API_KEY:
        return {
            "provider": "openrouter",
            "api_key": OPENROUTER_API_KEY,
            "model": OPENAI_MODEL
        }
    else:
        raise ValueError("No valid API key found")

if __name__ == "__main__":
    try:
        validate_config()
        print("✅ Configuration is valid")
        print(f"📁 Chroma DB path: {CHROMA_DB_PATH}")
        print(f"📊 Golden set: {GOLDEN_SET_CSV}")
        print(f"🤖 LLM config: {get_llm_config()}")
    except ValueError as e:
        print(f"❌ {e}")
