"""
Instagram caption generator with correct @mentions for vereador and secretaria.
"""


def gerar_caption_instagram(denuncia, vereador=None, secretaria=None) -> str:
    """
    Returns a ready-to-paste Instagram caption.

    Parameters
    ----------
    denuncia : Denuncia ORM object or any object with the expected attributes.
    vereador : Vereador ORM object (optional — falls back to denuncia fields).
    secretaria : dict from gabinetes_pbh.json (optional).
    """
    categoria = (getattr(denuncia, "categoria", "") or "problema urbano").replace("_", " ").upper()
    bairro = getattr(denuncia, "bairro", "") or "BH"
    descricao = (getattr(denuncia, "descricao_usuario", "") or "")[:300]
    protocolo = getattr(denuncia, "protocolo", "")

    # Instagram handle do vereador
    if vereador is not None:
        ver_ig = getattr(vereador, "instagram", None)
    else:
        ver_ig = getattr(denuncia, "vereador_instagram", None)
    ver_mention = f"@{ver_ig}" if ver_ig else (getattr(denuncia, "vereador_nome", "") or "Vereador responsável")

    # Instagram handle da secretaria
    sec_ig = None
    if isinstance(secretaria, dict):
        sec_ig = secretaria.get("instagram")
    elif secretaria is not None:
        sec_ig = getattr(secretaria, "instagram", None)
    sec_mention = f"@{sec_ig}" if sec_ig else None

    # Hashtags — remove spaces, hyphens, apostrophes
    bairro_tag = bairro.replace(" ", "").replace("-", "").replace("'", "")
    cat_tag = (getattr(denuncia, "categoria", "") or "urbano").replace("_", "").lower()

    linhas = [
        f"🚨 {categoria} em {bairro}, BH",
        "",
        descricao,
        "",
        f"Vereador responsável pela regional: {ver_mention}",
    ]
    if sec_mention:
        linhas.append(f"Secretaria responsável: {sec_mention}")
    linhas.extend([
        "Prefeitura: @pbhoficial",
        "",
        f"Protocolo: {protocolo}",
        f"#MacaCoCidadão #BH #{bairro_tag} #{cat_tag}",
    ])

    return "\n".join(linhas)
