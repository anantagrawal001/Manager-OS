"""
MANAGER OS — Provider Name Registry
FILE: core/provider_names.py
CREATED: 2026-05-28 | Claude Sonnet 4.6
UPDATED: 2026-05-31 | Claude Sonnet 4.6
CHANGE: Added OpenRouter, Cerebras, DeepSeek, Together, GitHub Models
        Based on freellmapi + freellm.net research — all free tier, no credit card
DO NOT DELETE ANY CODE — comment out with reason and date
"""

ANTHROPIC   = "anthropic"
GOOGLE      = "google"
OPENAI      = "openai"
GROQ        = "groq"
NVIDIA      = "nvidia"
ELEVENLABS  = "elevenlabs"
HUGGINGFACE = "huggingface"
DEEPSEEK    = "deepseek"
TOGETHER    = "together"
CEREBRAS    = "cerebras"      # NEW: fastest inference, free tier
OPENROUTER  = "openrouter"    # NEW: 100+ models via one key, free tier
GITHUB_MODELS = "github_models"  # NEW: GPT-4.1 free with Copilot
STABILITY   = "stability"
REPLICATE   = "replicate"
PERPLEXITY  = "perplexity"
OLLAMA      = "ollama"

CLOUD_PROVIDERS = [
    ANTHROPIC, GOOGLE, OPENAI, GROQ, NVIDIA,
    ELEVENLABS, HUGGINGFACE, DEEPSEEK, TOGETHER,
    CEREBRAS, OPENROUTER, GITHUB_MODELS,
    STABILITY, REPLICATE, PERPLEXITY,
]
LOCAL_PROVIDERS = [OLLAMA]

# Free tier, no credit card required
FREE_NO_CARD = [GROQ, GOOGLE, HUGGINGFACE, DEEPSEEK, CEREBRAS, OPENROUTER]

# Free tier, phone/account verification required
FREE_WITH_VERIFY = [NVIDIA, TOGETHER]

DISPLAY_NAMES = {
    ANTHROPIC:     "Claude (Anthropic)",
    GOOGLE:        "Gemini (Google)",
    OPENAI:        "GPT (OpenAI)",
    GROQ:          "Groq (Fast free)",
    NVIDIA:        "NVIDIA NIM",
    ELEVENLABS:    "ElevenLabs (TTS)",
    HUGGINGFACE:   "HuggingFace",
    DEEPSEEK:      "DeepSeek",
    TOGETHER:      "Together AI",
    CEREBRAS:      "Cerebras (Ultra-fast)",
    OPENROUTER:    "OpenRouter (100+ models)",
    GITHUB_MODELS: "GitHub Models (GPT-4.1)",
    STABILITY:     "Stability AI",
    REPLICATE:     "Replicate",
    PERPLEXITY:    "Perplexity",
    OLLAMA:        "Ollama (Local)",
}

# Signup URLs for SETUP.bat
SIGNUP_URLS = {
    GROQ:          "https://console.groq.com/keys",
    GOOGLE:        "https://aistudio.google.com/apikey",
    NVIDIA:        "https://build.nvidia.com/",
    ANTHROPIC:     "https://console.anthropic.com/",
    OPENAI:        "https://platform.openai.com/api-keys",
    CEREBRAS:      "https://cloud.cerebras.ai/",
    OPENROUTER:    "https://openrouter.ai/keys",
    DEEPSEEK:      "https://platform.deepseek.com/api_keys",
    ELEVENLABS:    "https://elevenlabs.io/",
    HUGGINGFACE:   "https://huggingface.co/settings/tokens",
}

def display(provider: str) -> str:
    return DISPLAY_NAMES.get(provider, provider)
