"""
UltraCore Voice Banking - Australian Accent Optimized
Voice-first banking for accessibility
"""

from openai import OpenAI
import io
import wave
import numpy as np
from typing import Dict, Any, Optional
import speech_recognition as sr
from pathlib import Path

class VoiceBankingAssistant:
    """Voice-activated banking with Australian accent support"""
    
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        
        # Australian-specific voice settings
        self.tts_voice = "alloy"  # Most neutral for Australian accent
        self.language_hints = ["en-AU", "en-GB"]
        
        # Security: Voice biometric placeholder
        self.voice_profiles = {}
        
    async def listen_and_process(self) -> str:
        """Listen to user voice command"""
        
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source)
            print("?? Listening... (Say your command)")
            audio = self.recognizer.listen(source, timeout=5)
        
        # Convert to WAV for OpenAI Whisper
        wav_data = audio.get_wav_data()
        
        # Use Whisper for transcription
        audio_file = io.BytesIO(wav_data)
        audio_file.name = "command.wav"
        
        transcript = self.client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            language="en",
            prompt="Australian banking context: balance, transfer, pay, BPAY, BSB"
        )
        
        return transcript.text
    
    async def speak_response(self, text: str):
        """Convert text to speech with Australian-friendly voice"""
        
        response = self.client.audio.speech.create(
            model="tts-1",
            voice=self.tts_voice,
            input=text,
            speed=0.9  # Slightly slower for clarity
        )
        
        # Play audio (would integrate with audio system)
        audio_data = response.content
        
        # Save for playback
        with open("response.mp3", "wb") as f:
            f.write(audio_data)
        
        return "response.mp3"
    
    async def process_voice_command(self, command: str) -> Dict[str, Any]:
        """Process banking command with Australian context"""
        
        # Enhanced with Australian banking terms
        response = self.client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {
                    "role": "system",
                    "content": """You are an Australian voice banking assistant.
                    Understand Australian banking terms:
                    - BSB numbers (6 digits)
                    - PayID (mobile or email)
                    - BPAY (bill payments)
                    - Super (superannuation)
                    - Centrelink payments
                    
                    Speak clearly and use Australian terminology.
                    Always confirm amounts in Australian dollars."""
                },
                {
                    "role": "user",
                    "content": command
                }
            ],
            functions=[
                {
                    "name": "process_payment",
                    "description": "Process a payment request",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "amount": {"type": "number"},
                            "recipient": {"type": "string"},
                            "method": {"type": "string", "enum": ["payid", "bsb", "bpay"]}
                        }
                    }
                },
                {
                    "name": "check_balance",
                    "description": "Check account balance",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "account": {"type": "string"}
                        }
                    }
                }
            ],
            function_call="auto"
        )
        
        return {
            "command": command,
            "response": response.choices[0].message,
            "requires_confirmation": self.needs_voice_confirmation(command)
        }
    
    def needs_voice_confirmation(self, command: str) -> bool:
        """Check if command needs voice confirmation"""
        high_risk_words = ['transfer', 'send', 'pay', 'withdraw']
        return any(word in command.lower() for word in high_risk_words)
    
    async def voice_authentication(self, audio_sample: bytes) -> bool:
        """Voice biometric authentication (placeholder)"""
        # Would integrate with voice biometric system
        # For now, use Whisper to verify voice clarity
        
        audio_file = io.BytesIO(audio_sample)
        audio_file.name = "auth.wav"
        
        transcript = self.client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            language="en"
        )
        
        # Check if user said their authentication phrase clearly
        auth_phrase = "my voice is my password"
        return auth_phrase in transcript.text.lower()


class AccessibilityAssistant:
    """Enhanced accessibility for elderly and disabled Australians"""
    
    def __init__(self, client: OpenAI):
        self.client = client
        self.simplification_level = "very_simple"
        
    async def simplify_banking_text(self, text: str) -> str:
        """Simplify complex banking text"""
        
        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": """Simplify this banking text for elderly Australians.
                    Use simple words, short sentences, and explain any banking terms.
                    Mention amounts in dollars and cents clearly."""
                },
                {
                    "role": "user",
                    "content": text
                }
            ],
            temperature=0.3
        )
        
        return response.choices[0].message.content
    
    async def create_audio_statement(self, statement_text: str) -> str:
        """Convert bank statement to audio"""
        
        # Simplify first
        simple_text = await self.simplify_banking_text(statement_text)
        
        # Convert to speech
        response = self.client.audio.speech.create(
            model="tts-1",
            voice="nova",  # Clear, warm voice
            input=simple_text,
            speed=0.85  # Slower for elderly users
        )
        
        # Save audio file
        audio_path = "statement_audio.mp3"
        with open(audio_path, "wb") as f:
            f.write(response.content)
        
        return audio_path
