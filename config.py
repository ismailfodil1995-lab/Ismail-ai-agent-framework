import os
from dotenv import load_dotenv

# تحميل متغيرات البيئة تلقائياً من .env
load_dotenv()

# ==========================================
# AI Agent V2 Configuration
# ==========================================

# Agent Profile
AGENT_NAME = os.getenv("AGENT_NAME", "Ismail Smart Agent")
CREATOR_NAME = os.getenv("CREATOR_NAME", "Ismail")

# LLM Providers & Selection (Ollama / OpenAI / Claude / Gemini)
# Provider Options: "ollama", "openai", "claude", "gemini"
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama").lower().strip()

# Default Model Selection:
# Examples:
#   Ollama:   "qwen2.5:3b", "llama3.1:8b", "mistral"
#   OpenAI:   "gpt-4o", "gpt-4o-mini", "o1-mini"
#   Claude:   "claude-3-5-sonnet-20241022", "claude-3-haiku-20240307"
#   Gemini:   "gemini/gemini-1.5-flash", "gemini/gemini-1.5-pro"
MODEL_NAME = os.getenv("MODEL_NAME", "qwen2.5:3b" if LLM_PROVIDER == "ollama" else "gpt-4o-mini")

# Remote API Keys (Loaded from .env / System Environment)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Ollama Endpoint
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434/api/generate")

# Generation Hyperparameters
TEMPERATURE = float(os.getenv("TEMPERATURE", "0.2"))
TIMEOUT = int(os.getenv("TIMEOUT", "120"))

# Memory
MEMORY_DB_FILE = "memory.db"  # SQLite — يدعم Multi-tenancy عبر session_id

# Conversation
MAX_CONVERSATION_MESSAGES = 30

# Debug
DEBUG = True

# Security & Guardrails (Human-in-the-Loop)
GUARDRAILS_MODE = "auto"  # "ask": prompt user in CLI/Bot, "auto": permit with security audit, "strict": block
CRITICAL_TOOLS = [
    "run_system_code",
    "write_system_file",
    "n8n_orchestrator",
    "send_email_report"
]

# Self-Healing & Reflection
ENABLE_SELF_HEALING = True
MAX_REFLECTION_ATTEMPTS = 2