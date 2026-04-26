"""Entry point: runs the Telegram bot (blocking)."""
import logging
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from telegram.ext import Application
from bot.handlers import build_conversation_handler
from panel.app import app as flask_app
from db.models import db

logging.basicConfig(
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
    level=logging.INFO,
)

import config

def main():
    with flask_app.app_context():
        db.create_all()
        from ai.vereador_mapper import seed_vereadores_exemplo
        seed_vereadores_exemplo(flask_app)

    application = Application.builder().token(config.TELEGRAM_BOT_TOKEN).build()
    application.add_handler(build_conversation_handler(flask_app))

    logging.getLogger(__name__).info("Bot iniciado. Aguardando mensagens...")
    application.run_polling(allowed_updates=["message"])


if __name__ == "__main__":
    main()
