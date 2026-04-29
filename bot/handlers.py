import os
import logging
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    filters,
)

from db.models import db, Denuncia
from db.protocolo import gerar_protocolo
from db.agrupamento import buscar_denuncias_anteriores, atribuir_grupo
from ai.classifier import classificar
from ai.vereador_mapper import vereador_por_bairro
from bot.exif_extractor import extrair_gps
from bot.media_store import salvar_midia, hash_midia
from bot.audio_transcriber import transcrever
from bot.geocoder import endereco_por_coords
import config

logger = logging.getLogger(__name__)

AGUARDANDO_MIDIA, AGUARDANDO_DESCRICAO, AGUARDANDO_BAIRRO = range(3)

CANAIS_REDIRECIONAMENTO = {
    "156": "📞 Ligue 156 ou acesse o BH APP para registrar pelo canal oficial da Prefeitura.",
    "Procon": "⚖️ Este é um problema de relação de consumo. Registre no Procon: procon.mg.gov.br",
    "Polícia": "🚔 Para segurança pública, acione a Polícia Militar pelo 190 ou Delegacia.",
}


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "🐒 *Macaco Cidadão — BH*\n\n"
        "Envie foto, vídeo, áudio ou texto descrevendo um problema de infraestrutura pública em BH.\n\n"
        "Sua denúncia será verificada e publicada com notificação formal ao vereador responsável.\n\n"
        "_Só registramos problemas de infraestrutura pública municipal._",
        parse_mode="Markdown",
    )
    return AGUARDANDO_MIDIA


async def receber_midia(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    msg = update.message
    context.user_data.clear()

    if msg.photo:
        foto = msg.photo[-1]
        file = await foto.get_file()
        arquivo_bytes = bytes(await file.download_as_bytearray())
        context.user_data["tipo_midia"] = "photo"
        context.user_data["arquivo_bytes"] = arquivo_bytes
        context.user_data["midia_hash"] = hash_midia(arquivo_bytes)
        coords = extrair_gps(arquivo_bytes)
        if coords:
            context.user_data["latitude"] = coords[0]
            context.user_data["longitude"] = coords[1]
    elif msg.video:
        file = await msg.video.get_file()
        arquivo_bytes = bytes(await file.download_as_bytearray())
        context.user_data["tipo_midia"] = "video"
        context.user_data["arquivo_bytes"] = arquivo_bytes
        context.user_data["midia_hash"] = hash_midia(arquivo_bytes)
    elif msg.voice or msg.audio:
        media = msg.voice or msg.audio
        file = await media.get_file()
        arquivo_bytes = bytes(await file.download_as_bytearray())
        context.user_data["tipo_midia"] = "audio"
        context.user_data["arquivo_bytes"] = arquivo_bytes
        context.user_data["midia_hash"] = hash_midia(arquivo_bytes)
        # Transcribe immediately — if successful, skip the description step
        await msg.reply_text("🎙️ Transcrevendo áudio...")
        transcricao = transcrever(arquivo_bytes)
        if transcricao:
            context.user_data["descricao"] = transcricao
            context.user_data["transcricao_audio"] = transcricao
            await msg.reply_text(
                f"✅ Transcrição: _{transcricao}_\n\n📍 Em qual bairro fica o problema?",
                parse_mode="Markdown",
            )
            return AGUARDANDO_BAIRRO
        else:
            await msg.reply_text(
                "✅ Áudio recebido.\n\nDescreva o problema em uma frase (ex: buraco na calçada):"
            )
            return AGUARDANDO_DESCRICAO
    elif msg.text and not msg.text.startswith("/"):
        context.user_data["tipo_midia"] = "text"
        context.user_data["descricao"] = msg.text

    if context.user_data.get("tipo_midia") == "text":
        await msg.reply_text("📍 Em qual bairro fica o problema?")
        return AGUARDANDO_BAIRRO

    await msg.reply_text(
        "✅ Mídia recebida.\n\nDescreva o problema em uma frase (ex: buraco na calçada, lâmpada queimada):"
    )
    return AGUARDANDO_DESCRICAO


async def receber_descricao(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["descricao"] = update.message.text
    await update.message.reply_text("📍 Em qual bairro fica o problema?")
    return AGUARDANDO_BAIRRO


async def receber_bairro(update: Update, context: ContextTypes.DEFAULT_TYPE, flask_app) -> int:
    bairro = update.message.text.strip()
    context.user_data["bairro"] = bairro

    await update.message.reply_text("⏳ Analisando sua denúncia...")

    descricao = context.user_data.get("descricao", "")
    tem_midia = context.user_data.get("tipo_midia") in ("photo", "video", "audio")
    coords = None
    if "latitude" in context.user_data:
        coords = f"{context.user_data['latitude']}, {context.user_data['longitude']}"

    try:
        # Look up previous complaints before classifying so AI can flag recurrence
        with flask_app.app_context():
            anteriores = buscar_denuncias_anteriores(
                bairro=bairro,
                categoria="",  # unknown yet — pass bairro-only pre-filter
                latitude=context.user_data.get("latitude"),
                longitude=context.user_data.get("longitude"),
            )
        resultado = classificar(descricao, bairro, tem_midia, coords, anteriores)
    except Exception as e:
        logger.error("Erro na classificação: %s", e)
        await update.message.reply_text(
            "⚠️ Erro interno na triagem. Tente novamente em alguns minutos."
        )
        return ConversationHandler.END

    if not resultado.get("valida"):
        canal = resultado.get("canal_correto")
        motivo = resultado.get("motivo_invalidade", "Fora do escopo de infraestrutura pública municipal.")
        msg_redirect = CANAIS_REDIRECIONAMENTO.get(canal, "")
        await update.message.reply_text(
            f"ℹ️ Sua denúncia não pôde ser registrada aqui.\n\n"
            f"*Motivo:* {motivo}\n\n"
            f"{msg_redirect}",
            parse_mode="Markdown",
        )
        return ConversationHandler.END

    with flask_app.app_context():
        protocolo = gerar_protocolo()

        # Refined grouping using confirmed category from classifier
        categoria_confirmada = resultado.get("categoria", "")
        anteriores_confirmados = buscar_denuncias_anteriores(
            bairro=resultado.get("bairro_confirmado", bairro),
            categoria=categoria_confirmada,
            latitude=context.user_data.get("latitude"),
            longitude=context.user_data.get("longitude"),
        )

        vereador = vereador_por_bairro(resultado.get("bairro_confirmado", bairro))
        secretaria_nome, secretaria_email = config.SECRETARIAS_POR_CATEGORIA.get(
            resultado.get("categoria", "outros"), ("Ouvidoria PBH", "ouvidoria@pbh.gov.br")
        )

        tipo_midia = context.user_data.get("tipo_midia")
        arquivo_path = None
        if tipo_midia in ("photo", "video", "audio") and context.user_data.get("arquivo_bytes"):
            arquivo_path = salvar_midia(context.user_data["arquivo_bytes"], tipo_midia, protocolo)

        endereco = None
        if context.user_data.get("latitude") and context.user_data.get("longitude"):
            endereco = endereco_por_coords(
                context.user_data["latitude"], context.user_data["longitude"]
            )

        denuncia = Denuncia(
            protocolo=protocolo,
            telegram_user_id=str(update.effective_user.id),
            telegram_username=update.effective_user.username,
            tipo_midia=tipo_midia,
            arquivo_path=arquivo_path,
            midia_hash=context.user_data.get("midia_hash"),
            transcricao_audio=context.user_data.get("transcricao_audio"),
            descricao_usuario=descricao,
            latitude=context.user_data.get("latitude"),
            longitude=context.user_data.get("longitude"),
            endereco=endereco,
            bairro=resultado.get("bairro_confirmado", bairro),
            regional=resultado.get("regional"),
            categoria=resultado.get("categoria"),
            valida=True,
            vereador_nome=vereador.nome if vereador else "A identificar",
            vereador_email=vereador.email_gabinete if vereador else None,
            vereador_instagram=vereador.instagram if vereador else None,
            vereador_twitter=vereador.twitter if vereador else None,
            secretaria_nome=secretaria_nome,
            secretaria_email=secretaria_email,
            texto_post_sugerido=resultado.get("texto_post"),
            minuta_email=resultado.get("corpo_email"),
            status="aguardando_triagem",
        )
        atribuir_grupo(denuncia, anteriores_confirmados)
        db.session.add(denuncia)
        db.session.commit()

    await update.message.reply_text(
        f"✅ *Denúncia registrada!*\n\n"
        f"Protocolo: `{protocolo}`\n"
        f"Categoria: {resultado.get('categoria', '').replace('_', ' ').title()}\n"
        f"Bairro: {resultado.get('bairro_confirmado', bairro)}\n\n"
        f"Sua denúncia será revisada e, se aprovada, publicada com notificação formal.\n"
        f"Você receberá uma mensagem com o link quando isso acontecer.",
        parse_mode="Markdown",
    )
    return ConversationHandler.END


async def cmd_cancelar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Cancelado. Use /start para nova denúncia.")
    return ConversationHandler.END


def build_conversation_handler(flask_app):
    from functools import partial

    bairro_handler = partial(receber_bairro, flask_app=flask_app)

    return ConversationHandler(
        entry_points=[CommandHandler("start", cmd_start)],
        states={
            AGUARDANDO_MIDIA: [
                MessageHandler(filters.PHOTO | filters.VIDEO | filters.VOICE | filters.AUDIO, receber_midia),
                MessageHandler(filters.TEXT & ~filters.COMMAND, receber_midia),
            ],
            AGUARDANDO_DESCRICAO: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receber_descricao),
            ],
            AGUARDANDO_BAIRRO: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, bairro_handler),
            ],
        },
        fallbacks=[CommandHandler("cancelar", cmd_cancelar)],
        allow_reentry=True,
    )
