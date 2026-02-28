"""
TTS Engine — Edge TTS (Free Microsoft TTS)

Bilingual text-to-speech engine using edge-tts.
Supports EN (en-US-GuyNeural) and ZH (zh-CN-YunxiNeural).
"""

import logging
import io

try:
    import edge_tts
    EDGE_TTS_AVAILABLE = True
except ImportError:
    edge_tts = None
    EDGE_TTS_AVAILABLE = False

logger = logging.getLogger(__name__)

# Voice configuration
VOICES = {
    "en": "en-US-GuyNeural",
    "zh": "zh-CN-YunxiNeural",
}
RATE = "-10%"
VOLUME = "+0%"


class TTSEngine:
    """Text-to-Speech engine using Microsoft Edge TTS (free)."""

    def get_voice(self, lang: str) -> str:
        """Return the appropriate voice name for the given language code."""
        return VOICES.get(lang, VOICES["en"])

    async def speak(self, text: str, lang: str = "en") -> bytes | None:
        """
        Generate audio bytes (MP3) from text.

        Args:
            text:  The text to convert to speech.
            lang:  Language code — "en" or "zh".

        Returns:
            MP3 audio bytes on success, None on failure.
        """
        if not EDGE_TTS_AVAILABLE:
            logger.error("edge-tts package is not installed. Run: pip install edge-tts")
            return None

        try:
            voice = self.get_voice(lang)
            communicate = edge_tts.Communicate(
                text,
                voice=voice,
                rate=RATE,
                volume=VOLUME,
            )

            buffer = io.BytesIO()
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    buffer.write(chunk["data"])

            audio_bytes = buffer.getvalue()
            if not audio_bytes:
                logger.warning("TTS returned empty audio for text: %s", text[:80])
                return None

            return audio_bytes

        except Exception as e:
            logger.error("TTS speak() failed: %s", e)
            return None

    async def speak_to_file(self, text: str, output_path: str, lang: str = "en") -> bool:
        """
        Generate speech and save directly to an MP3 file.

        Args:
            text:        The text to convert to speech.
            output_path: Destination file path (.mp3).
            lang:        Language code — "en" or "zh".

        Returns:
            True on success, False on failure.
        """
        if not EDGE_TTS_AVAILABLE:
            logger.error("edge-tts package is not installed. Run: pip install edge-tts")
            return False

        try:
            voice = self.get_voice(lang)
            communicate = edge_tts.Communicate(
                text,
                voice=voice,
                rate=RATE,
                volume=VOLUME,
            )
            await communicate.save(output_path)
            return True

        except Exception as e:
            logger.error("TTS speak_to_file() failed: %s", e)
            return False
