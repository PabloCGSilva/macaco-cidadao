"""
WhatsApp notifier via wa.me deep links.

No paid API required. The moderator clicks the generated link and WhatsApp
Web opens with a pre-filled message ready to send — one click.
"""
import json
import os
import urllib.parse


def _carregar_gabinetes() -> dict:
    path = os.path.join(os.path.dirname(__file__), "..", "data", "gabinetes_pbh.json")
    try:
        with open(path, encoding="utf-8") as f:
            return {g["slug"]: g for g in json.load(f)}
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _formatar_mensagem(denuncia, vereador=None, para_secretaria: bool = False) -> str:
    criado = getattr(denuncia, "criado_em", None)
    data = criado.strftime("%d/%m/%Y") if criado else "—"
    categoria = (getattr(denuncia, "categoria", "") or "problema urbano").replace("_", " ")
    bairro = getattr(denuncia, "bairro", "") or "BH"
    descricao = (getattr(denuncia, "descricao_usuario", "") or "")[:200]
    protocolo = getattr(denuncia, "protocolo", "")
    url_midia = getattr(denuncia, "link_post", "") or ""

    if para_secretaria:
        intro = "Boa tarde! Registramos uma demanda de cidadão via Macaco Cidadão:"
    else:
        nome = (vereador.nome if vereador else None) or getattr(denuncia, "vereador_nome", "") or "Vereador"
        intro = f"Boa tarde, gabinete do(a) {nome}!"

    partes = [
        intro,
        "",
        f"📍 *{categoria.upper()}* — {bairro}, BH",
        f"🗓 {data}",
        "",
        descricao,
        "",
        f"Protocolo Macaco Cidadão: {protocolo}",
    ]
    if url_midia:
        partes.append(f"📸 Publicação: {url_midia}")
    partes.append("")
    partes.append("Cobrado por cidadão via @macacocidadao")
    return "\n".join(partes)


def gerar_link_whatsapp(denuncia, vereador=None, secretaria=None) -> dict:
    """
    Returns {'vereador': url_or_none, 'secretaria': url_or_none}.

    Uses wa.me deep link — no paid API required.
    Moderator clicks; WhatsApp Web opens with the message pre-filled.
    """
    gabinetes = _carregar_gabinetes()
    resultado = {"vereador": None, "secretaria": None}

    # -- Link para o vereador -----------------------------------------------
    numero_ver = None
    if vereador is not None:
        numero_ver = getattr(vereador, "whatsapp_gabinete", None)
    if not numero_ver:
        numero_ver = getattr(denuncia, "vereador_whatsapp", None)

    if numero_ver:
        msg = _formatar_mensagem(denuncia, vereador=vereador, para_secretaria=False)
        resultado["vereador"] = (
            "https://wa.me/" + numero_ver + "?text=" + urllib.parse.quote(msg)
        )

    # -- Link para a secretaria ---------------------------------------------
    slug = getattr(denuncia, "secretaria_slug", None)
    if slug is None and isinstance(secretaria, dict):
        slug = secretaria.get("slug")

    if slug and slug in gabinetes:
        numero_sec = gabinetes[slug].get("whatsapp")
        if numero_sec:
            msg = _formatar_mensagem(denuncia, para_secretaria=True)
            resultado["secretaria"] = (
                "https://wa.me/" + numero_sec + "?text=" + urllib.parse.quote(msg)
            )

    return resultado
