"""
Transcribes voice/audio messages via OpenAI Whisper API.
Falls back gracefully when OPENAI_API_KEY is not set.
"""
import io
import logging

import config

logger = logging.getLogger(__name__)


def transcrever(audio_bytes: bytes, extensao: str = "ogg") -> str | None:
    """Returns transcribed text or None on failure / missing API key."""
    if not config.OPENAI_API_KEY:
        logger.warning("OPENAI_API_KEY não configurado — transcrição de áudio desabilitada.")
        return None

    try:
        from openai import OpenAI
        client = OpenAI(api_key=config.OPENAI_API_KEY)

        audio_file = io.BytesIO(audio_bytes)
        audio_file.name = f"audio.{extensao}"

        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            language="pt",
            response_format="text",
        )
        texto = transcript.strip() if isinstance(transcript, str) else str(transcript).strip()
        logger.info("Áudio transcrito (%d chars).", len(texto))
        return texto or None

    except Exception as e:
        logger.error("Falha na transcrição de áudio: %s", e)
        return None
