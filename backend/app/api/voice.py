"""
Voice Interface API Endpoints
Text-to-speech and speech-to-text for UnifiedAi
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any

from app.core.voice_interface import voice_interface

router = APIRouter(prefix="/api/voice", tags=["Voice Interface"])


class SynthesizeRequest(BaseModel):
    text: str
    voice_id: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None


@router.get("/voices")
async def list_voices() -> Dict[str, Any]:
    """List available TTS voices"""
    try:
        voices = await voice_interface.list_voices()
        return {
            "voices": [
                {
                    "voice_id": v.voice_id,
                    "name": v.name,
                    "provider": v.provider,
                    "language": v.language
                }
                for v in voices
            ],
            "default_voice_id": voice_interface.default_voice_id,
            "count": len(voices)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/synthesize")
async def synthesize_speech(request: SynthesizeRequest) -> Dict[str, Any]:
    """Convert text to speech"""
    try:
        result = await voice_interface.synthesize_speech(
            text=request.text,
            voice_id=request.voice_id,
            settings=request.settings
        )
        
        return {
            "success": result.success,
            "audio_base64": result.audio_base64,
            "audio_format": result.audio_format,
            "duration_estimate": result.duration_estimate,
            "voice_used": result.voice_used,
            "error": result.error
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/set-default-voice")
async def set_default_voice(voice_id: str) -> Dict[str, Any]:
    """Set the default voice for TTS"""
    try:
        voice_interface.set_default_voice(voice_id)
        return {
            "status": "updated",
            "default_voice_id": voice_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/browser-tts-script")
async def get_browser_tts_script():
    """Get JavaScript for browser-based TTS fallback"""
    try:
        script = voice_interface.get_browser_tts_script()
        return PlainTextResponse(
            content=script,
            media_type="application/javascript"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/browser-stt-script")
async def get_browser_stt_script():
    """Get JavaScript for browser-based speech recognition"""
    try:
        script = voice_interface.get_browser_stt_script()
        return PlainTextResponse(
            content=script,
            media_type="application/javascript"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/voice/{voice_id}")
async def get_voice_info(voice_id: str) -> Dict[str, Any]:
    """Get information about a specific voice"""
    try:
        voice = await voice_interface.get_voice_info(voice_id)
        if not voice:
            raise HTTPException(status_code=404, detail="Voice not found")
        
        return {
            "voice_id": voice.voice_id,
            "name": voice.name,
            "provider": voice.provider,
            "language": voice.language,
            "settings": voice.settings
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

