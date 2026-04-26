import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime

import config

logger = logging.getLogger(__name__)


def enviar_email_formal(denuncia) -> bool:
    """Sends the formal accountability email and returns True on success."""
    destinatarios = []

    if denuncia.vereador_email:
        destinatarios.append(denuncia.vereador_email)
    if denuncia.secretaria_email:
        destinatarios.append(denuncia.secretaria_email)
    destinatarios.append(config.OUVIDORIA_CAMARA_EMAIL)

    assunto = (
        f"[{denuncia.protocolo}] Denúncia pública — {denuncia.categoria.replace('_', ' ').title()} "
        f"— {denuncia.bairro}"
    )

    corpo = denuncia.minuta_email or _corpo_padrao(denuncia)

    try:
        msg = MIMEMultipart()
        msg["From"] = config.EMAIL_FROM
        msg["To"] = destinatarios[0]
        msg["CC"] = ", ".join(destinatarios[1:])
        msg["Subject"] = assunto
        msg.attach(MIMEText(corpo, "plain", "utf-8"))

        with smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT) as server:
            server.starttls()
            server.login(config.SMTP_USER, config.SMTP_PASSWORD)
            server.sendmail(config.EMAIL_FROM, destinatarios, msg.as_string())

        logger.info("Email enviado para %s — protocolo %s", destinatarios, denuncia.protocolo)
        return True

    except Exception as e:
        logger.error("Falha ao enviar email %s: %s", denuncia.protocolo, e)
        return False


def _corpo_padrao(denuncia) -> str:
    data = denuncia.criado_em.strftime("%d/%m/%Y às %H:%M")
    coords = ""
    if denuncia.latitude and denuncia.longitude:
        coords = f"\nCoordenadas GPS: {denuncia.latitude:.6f}, {denuncia.longitude:.6f}"

    return f"""Prezado(a) {denuncia.vereador_nome or 'Senhor(a) Vereador(a)'},

Número de protocolo: {denuncia.protocolo}
Data e hora da submissão: {data}
Categoria: {denuncia.categoria.replace('_', ' ').title() if denuncia.categoria else 'N/A'}
Endereço: {denuncia.endereco or denuncia.bairro}{coords}

Descrição objetiva:
{denuncia.descricao_usuario}

Esta denúncia foi recebida por cidadão residente ou frequentador do bairro {denuncia.bairro}, \
que integra a base eleitoral que contribuiu para sua eleição.

PERGUNTA CENTRAL:
O que V.Sa. já cobrou ou pretende cobrar da Prefeitura de Belo Horizonte sobre este problema?

Solicitamos resposta em até 10 (dez) dias úteis, conforme art. 5º, XXXIII da Constituição Federal \
e Lei nº 12.527/2011 (Lei de Acesso à Informação).

Informamos que esta denúncia já foi publicada nas redes sociais do Macaco Cidadão com o número \
de protocolo acima. O silêncio ou inação serão documentados no Scorecard Mensal de Responsividade \
publicado todo primeiro dia do mês.

Atenciosamente,

Macaco Cidadão — Plataforma de Accountability Urbano
instagram.com/macacocidadao_bh
protocolo@macacocidadao.com.br
"""
