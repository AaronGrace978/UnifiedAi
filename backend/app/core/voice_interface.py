"""
Voice Interface
Text-to-speech and speech-to-text integration for UnifiedAi.

Supports ElevenLabs API and local TTS alternatives.
"""

import asyncio
import base64
import os
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False
    httpx = None


@dataclass
class VoiceConfig:
    """Configuration for a voice"""
    voice_id: str
    name: str
    provider: str  # "elevenlabs", "local", "browser"
    language: str = "en"
    settings: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SpeechResult:
    """Result of text-to-speech synthesis"""
    text: str
    audio_base64: Optional[str]
    audio_format: str
    duration_estimate: float
    voice_used: str
    success: bool
    error: Optional[str] = None


class VoiceInterface:
    """
    Voice interface for UnifiedAi.
    
    Provides:
    - Text-to-speech with ElevenLabs or local alternatives
    - Speech-to-text (browser-based)
    - Voice configuration management
    """
    
    def __init__(self, elevenlabs_api_key: str = None):
        self.api_key = elevenlabs_api_key or os.environ.get("ELEVENLABS_API_KEY")
        self.client = httpx.AsyncClient(timeout=60.0) if HTTPX_AVAILABLE else None
        
        # Default voice (from user preferences)
        self.default_voice_id = "FOfJ2PMgU6HOGbNYnzto"
        
        # Available voices cache
        self.voices: Dict[str, VoiceConfig] = {}
        
        # ElevenLabs settings
        self.elevenlabs_url = "https://api.elevenlabs.io/v1"
        
        # Voice settings
        self.default_settings = {
            "stability": 0.5,
            "similarity_boost": 0.75,
            "style": 0.0,
            "use_speaker_boost": True
        }
    
    async def list_voices(self) -> List[VoiceConfig]:
        """Get available voices from ElevenLabs"""
        if not self.api_key or not self.client:
            # Return placeholder voices for browser TTS
            return [
                VoiceConfig(
                    voice_id="browser_default",
                    name="Browser Default",
                    provider="browser",
                    language="en"
                )
            ]
        
        try:
            response = await self.client.get(
                f"{self.elevenlabs_url}/voices",
                headers={"xi-api-key": self.api_key}
            )
            response.raise_for_status()
            data = response.json()
            
            voices = []
            for voice in data.get("voices", []):
                config = VoiceConfig(
                    voice_id=voice["voice_id"],
                    name=voice["name"],
                    provider="elevenlabs",
                    language=voice.get("labels", {}).get("language", "en"),
                    settings=voice.get("settings", self.default_settings)
                )
                voices.append(config)
                self.voices[voice["voice_id"]] = config
            
            return voices
        except Exception as e:
            print(f"Error fetching voices: {e}")
            return []
    
    async def synthesize_speech(
        self,
        text: str,
        voice_id: str = None,
        settings: Dict[str, Any] = None
    ) -> SpeechResult:
        """
        Convert text to speech using ElevenLabs.
        
        Args:
            text: Text to synthesize
            voice_id: Voice ID to use (defaults to user preference)
            settings: Voice settings override
            
        Returns:
            SpeechResult with audio data
        """
        voice_id = voice_id or self.default_voice_id
        settings = settings or self.default_settings
        
        if not self.api_key or not self.client:
            # Return instruction for browser-based TTS
            return SpeechResult(
                text=text,
                audio_base64=None,
                audio_format="browser",
                duration_estimate=len(text) / 15,  # Rough estimate: 15 chars/sec
                voice_used="browser",
                success=True,
                error="No ElevenLabs API key - use browser TTS"
            )
        
        try:
            response = await self.client.post(
                f"{self.elevenlabs_url}/text-to-speech/{voice_id}",
                headers={
                    "xi-api-key": self.api_key,
                    "Content-Type": "application/json"
                },
                json={
                    "text": text,
                    "model_id": "eleven_monolingual_v1",
                    "voice_settings": {
                        "stability": settings.get("stability", 0.5),
                        "similarity_boost": settings.get("similarity_boost", 0.75)
                    }
                }
            )
            response.raise_for_status()
            
            # Audio comes as raw bytes
            audio_bytes = response.content
            audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
            
            # Estimate duration (rough: ~150 words/min, avg 5 chars/word)
            duration_estimate = len(text) / 12.5  # chars per second
            
            return SpeechResult(
                text=text,
                audio_base64=audio_base64,
                audio_format="mp3",
                duration_estimate=duration_estimate,
                voice_used=voice_id,
                success=True
            )
        except Exception as e:
            return SpeechResult(
                text=text,
                audio_base64=None,
                audio_format="none",
                duration_estimate=0,
                voice_used=voice_id,
                success=False,
                error=str(e)
            )
    
    async def synthesize_stream(
        self,
        text: str,
        voice_id: str = None
    ):
        """
        Stream text-to-speech audio chunks.
        
        Yields audio chunks for real-time playback.
        """
        voice_id = voice_id or self.default_voice_id
        
        if not self.api_key or not self.client:
            return
        
        try:
            async with self.client.stream(
                "POST",
                f"{self.elevenlabs_url}/text-to-speech/{voice_id}/stream",
                headers={
                    "xi-api-key": self.api_key,
                    "Content-Type": "application/json"
                },
                json={
                    "text": text,
                    "model_id": "eleven_monolingual_v1",
                    "voice_settings": self.default_settings
                }
            ) as response:
                async for chunk in response.aiter_bytes():
                    yield chunk
        except Exception as e:
            print(f"Streaming error: {e}")
    
    def set_default_voice(self, voice_id: str):
        """Set the default voice for synthesis"""
        self.default_voice_id = voice_id
    
    def get_browser_tts_script(self) -> str:
        """
        Get JavaScript for browser-based TTS fallback.
        
        Returns JavaScript code that can be used in the frontend
        for speech synthesis without an API key.
        """
        return """
// Browser TTS fallback for UnifiedAi
class BrowserTTS {
    constructor() {
        this.synth = window.speechSynthesis;
        this.voices = [];
        this.loadVoices();
    }
    
    loadVoices() {
        this.voices = this.synth.getVoices();
        if (this.voices.length === 0) {
            // Chrome loads voices async
            this.synth.onvoiceschanged = () => {
                this.voices = this.synth.getVoices();
            };
        }
    }
    
    speak(text, voiceName = null, rate = 1.0, pitch = 1.0) {
        // Cancel any ongoing speech
        this.synth.cancel();
        
        const utterance = new SpeechSynthesisUtterance(text);
        
        // Find requested voice or use default
        if (voiceName && this.voices.length > 0) {
            const voice = this.voices.find(v => v.name.includes(voiceName));
            if (voice) utterance.voice = voice;
        }
        
        utterance.rate = rate;
        utterance.pitch = pitch;
        
        return new Promise((resolve, reject) => {
            utterance.onend = () => resolve();
            utterance.onerror = (e) => reject(e);
            this.synth.speak(utterance);
        });
    }
    
    stop() {
        this.synth.cancel();
    }
    
    getVoices() {
        return this.voices.map(v => ({
            name: v.name,
            lang: v.lang,
            local: v.localService
        }));
    }
}

// Initialize
window.unifiedTTS = new BrowserTTS();
"""
    
    def get_browser_stt_script(self) -> str:
        """
        Get JavaScript for browser-based speech recognition.
        
        Returns JavaScript code for speech-to-text in the frontend.
        """
        return """
// Browser STT for UnifiedAi
class BrowserSTT {
    constructor() {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SpeechRecognition) {
            console.warn('Speech recognition not supported');
            return;
        }
        
        this.recognition = new SpeechRecognition();
        this.recognition.continuous = false;
        this.recognition.interimResults = true;
        this.recognition.lang = 'en-US';
        
        this.isListening = false;
        this.onResult = null;
        this.onEnd = null;
        
        this.recognition.onresult = (event) => {
            const results = Array.from(event.results);
            const transcript = results.map(r => r[0].transcript).join('');
            const isFinal = results.some(r => r.isFinal);
            
            if (this.onResult) {
                this.onResult(transcript, isFinal);
            }
        };
        
        this.recognition.onend = () => {
            this.isListening = false;
            if (this.onEnd) this.onEnd();
        };
    }
    
    start(onResult, onEnd) {
        if (!this.recognition) return false;
        
        this.onResult = onResult;
        this.onEnd = onEnd;
        this.isListening = true;
        this.recognition.start();
        return true;
    }
    
    stop() {
        if (this.recognition && this.isListening) {
            this.recognition.stop();
        }
    }
    
    setLanguage(lang) {
        if (this.recognition) {
            this.recognition.lang = lang;
        }
    }
}

// Initialize
window.unifiedSTT = new BrowserSTT();
"""
    
    async def get_voice_info(self, voice_id: str) -> Optional[VoiceConfig]:
        """Get information about a specific voice"""
        if voice_id in self.voices:
            return self.voices[voice_id]
        
        # Try to fetch from API
        if self.api_key and self.client:
            try:
                response = await self.client.get(
                    f"{self.elevenlabs_url}/voices/{voice_id}",
                    headers={"xi-api-key": self.api_key}
                )
                response.raise_for_status()
                data = response.json()
                
                config = VoiceConfig(
                    voice_id=data["voice_id"],
                    name=data["name"],
                    provider="elevenlabs",
                    language=data.get("labels", {}).get("language", "en"),
                    settings=data.get("settings", self.default_settings)
                )
                self.voices[voice_id] = config
                return config
            except Exception:
                pass
        
        return None


# Global instance
voice_interface = VoiceInterface()

