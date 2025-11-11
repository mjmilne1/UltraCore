"""
UltraCore OpenAI Configuration
"""
import os
from dataclasses import dataclass
from typing import Optional

@dataclass
class OpenAISettings:
    api_key: str = os.getenv("OPENAI_API_KEY", "")
    model: str = "gpt-4-turbo-preview"
    temperature: float = 0.3
    max_tokens: int = 2000

settings = OpenAISettings()
