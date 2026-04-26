import logging
import httpx
import config

logger = logging.getLogger(__name__)

TELEGRAM_API = "https://api.telegram.org/bot{token}/sendMessage"


def notificar_usuario(telegram_user_id: str, protocolo: str, link_post: str) -> bool:
    """Sends a Telegram message back to the citizen when their complaint is published."""
    texto = (
        f"✅ *Sua denúncia foi publicada!*\n\n"
        f"Protocolo: `{protocolo}`\n\n"
        f"Notificamos o vereador responsável e a secretaria municipal por e-mail formal.\n\n"
        f"Acompanhe o post: {link_post}\n\n"
        f"_Macaco Cidadão — Accountability Urbano BH_"
    )

    url = TELEGRAM_API.format(token=config.TELEGRAM_BOT_TOKEN)
    payload = {
        "chat_id": telegram_user_id,
        "text": texto,
        "parse_mode": "Markdown",
    }

    try:
        resp = httpx.post(url, json=payload, timeout=10)
        resp.raise_for_status()
        return True
    except Exception as e:
        logger.error("Falha ao notificar usuário %s: %s", telegram_user_id, e)
        return False
