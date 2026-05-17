"""
Tenta extrair números de WhatsApp das bios de Instagram dos vereadores eleitos.

Estratégia: HTTP simples (sem JS rendering).
Instagram bloqueia a maioria das requisições sem sessão autenticada, portanto
o resultado esperado é baixo — mas o script identifica quais vereadores precisam
de preenchimento manual.

Saída: data/whatsapp_encontrados.json
"""
import json
import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import httpx
except ImportError:
    import urllib.request as _ur
    httpx = None

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
JSON_VEREADORES = os.path.join(DATA_DIR, "vereadores_bh_tse2024.json")
JSON_SAIDA = os.path.join(DATA_DIR, "whatsapp_encontrados.json")

# Padrões de WhatsApp em bios/páginas
_PATTERNS = [
    r"wa\.me/(\d{10,15})",
    r"api\.whatsapp\.com/send\?phone=(\d{10,15})",
    r"whatsapp\.com/send\?phone=(\d{10,15})",
    r"(?:\+55|55)\s*\(?(\d{2})\)?\s*9?\d{4}[-\s]?\d{4}",
    r"\(31\)\s*9?\d{4}[-\s]?\d{4}",
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "pt-BR,pt;q=0.9",
}


def _get(url: str) -> str:
    """Fetch page content; returns empty string on failure."""
    try:
        if httpx:
            resp = httpx.get(url, headers=HEADERS, timeout=10, follow_redirects=True)
            return resp.text if resp.status_code == 200 else ""
        else:
            req = _ur.Request(url, headers=HEADERS)
            with _ur.urlopen(req, timeout=10) as r:
                return r.read().decode("utf-8", errors="ignore")
    except Exception:
        return ""


def _extrair_numero(html: str) -> str | None:
    """Extract first WhatsApp number found in HTML."""
    for pattern in _PATTERNS:
        m = re.search(pattern, html)
        if m:
            raw = re.sub(r"\D", "", m.group(0))
            # Normalizar para DDI+DDD+numero (11-13 dígitos com DDI 55)
            if raw.startswith("55") and len(raw) >= 12:
                return raw
            if len(raw) == 11:  # DDD + 9 dígitos
                return "55" + raw
            if len(raw) == 10:  # DDD + 8 dígitos (fixo)
                return "55" + raw
    return None


def buscar(vereadores: list) -> dict:
    encontrados = {}
    nao_encontrados = []

    for v in vereadores:
        if not v.get("eleito"):
            continue
        if v.get("whatsapp_gabinete"):
            encontrados[v["nome"]] = v["whatsapp_gabinete"]
            continue

        instagram = v.get("instagram")
        numero = None

        if instagram:
            url = f"https://www.instagram.com/{instagram}/"
            html = _get(url)
            numero = _extrair_numero(html)
            time.sleep(1)  # respeitar rate limit

        if numero:
            encontrados[v["nome"]] = numero
            print(f"  OK {v['nome']}: {numero}")
        else:
            nao_encontrados.append(v["nome"])
            print(f"  -- {v['nome']}: nao encontrado")

    return {"encontrados": encontrados, "nao_encontrados": nao_encontrados}


def main():
    with open(JSON_VEREADORES, encoding="utf-8") as f:
        vereadores = json.load(f)

    eleitos = [v for v in vereadores if v.get("eleito")]
    print(f"Buscando WhatsApp para {len(eleitos)} vereadores eleitos...\n")

    resultado = buscar(eleitos)

    with open(JSON_SAIDA, "w", encoding="utf-8") as f:
        json.dump(resultado, f, ensure_ascii=False, indent=2)

    total = len(eleitos)
    achou = len(resultado["encontrados"])
    faltam = len(resultado["nao_encontrados"])

    print(f"\n{'='*50}")
    print("Resultado:")
    print(f"  Encontrados automaticamente : {achou}/{total}")
    print(f"  Precisam preenchimento manual: {faltam}/{total}")
    print("\nVereadores sem WhatsApp identificado:")
    for nome in resultado["nao_encontrados"]:
        print(f"  - {nome}")
    print(f"\nSalvo em: {JSON_SAIDA}")


if __name__ == "__main__":
    main()
