"""
pbh_obras.py — Integração com o Portal de Dados Abertos PBH (CKAN).

Fonte: https://dados.pbh.gov.br/dataset/obras-publicas_2
Atualização: mensal (PBH publica novo CSV todo início de mês)
Cache local: 24h (evita requisições excessivas)
"""
import csv
import io
import json
import logging
import os
import time
import urllib.request
from datetime import datetime

logger = logging.getLogger(__name__)

CKAN_PACKAGE_ID = "obras-publicas_2"
CKAN_API = "https://dados.pbh.gov.br/api/3/action/package_show?id=" + CKAN_PACKAGE_ID
CACHE_DIR = os.path.join(os.path.dirname(__file__), "cache")
CACHE_FILE = os.path.join(CACHE_DIR, "pbh_obras.json")
CACHE_TTL_HORAS = 24

# Mapeamento categoria Macaco Cidadão → temáticas PBH
CATEGORIA_TEMATICA = {
    "buraco_pavimento":      ["Infraestrutura", "Manutenção", "Mobilidade"],
    "iluminacao_publica":    ["Infraestrutura", "Manutenção"],
    "lixo_entulho":          ["Manutenção", "Urbanização"],
    "calcada_acessibilidade":["Infraestrutura", "Mobilidade", "Urbanização"],
    "obra_irregular":        ["Urbanização", "Habitação"],
    "arvore_risco":          ["Manutenção", "Outros"],
    "enchente_drenagem":     ["Infraestrutura", "Manutenção"],
    "transporte_onibus":     ["Mobilidade", "Infraestrutura"],
    "pichacao_vandalismo":   ["Manutenção", "Cultura"],
    "outros":                ["Infraestrutura", "Manutenção"],
}


def _cache_valido() -> bool:
    if not os.path.exists(CACHE_FILE):
        return False
    idade_horas = (time.time() - os.path.getmtime(CACHE_FILE)) / 3600
    return idade_horas < CACHE_TTL_HORAS


def _url_csv_mais_recente() -> str:
    req = urllib.request.Request(CKAN_API, headers={"User-Agent": "macaco-cidadao/1.0"})
    with urllib.request.urlopen(req, timeout=15) as r:
        data = json.loads(r.read())

    recursos_csv = [
        res for res in data["result"]["resources"]
        if res.get("format", "").upper() == "CSV"
    ]
    # Sort by name descending (format: YYYYMMDD_obras_publicas)
    recursos_csv.sort(key=lambda r: r["name"], reverse=True)
    return recursos_csv[0]["url"]


def _baixar_e_parsear(url: str) -> list[dict]:
    req = urllib.request.Request(url, headers={"User-Agent": "macaco-cidadao/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        raw = r.read().decode("utf-8-sig", errors="replace")

    reader = csv.DictReader(io.StringIO(raw), delimiter=";")
    obras = []
    for row in reader:
        obras.append(
            {
                "id": row.get("ID_AREA_EMPREENDIMENTO", ""),
                "numero_po": row.get("NUMERO_PO", ""),
                "nome": row.get("NOME_PO", "").title(),
                "regional": row.get("REGIONAL", ""),
                "tematica": row.get("TEMATICA", ""),
                "status": row.get("STATUS", ""),
                "empresa": row.get("EMPRESA_RESPONSAVEL", ""),
                "grupo": row.get("GRUPO", ""),
            }
        )
    return obras


def _carregar_obras() -> list[dict]:
    """Returns cached or freshly fetched obras list."""
    if _cache_valido():
        with open(CACHE_FILE, encoding="utf-8") as f:
            return json.load(f)

    try:
        url = _url_csv_mais_recente()
        logger.info("Baixando obras PBH de %s", url)
        obras = _baixar_e_parsear(url)
        os.makedirs(CACHE_DIR, exist_ok=True)
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(obras, f, ensure_ascii=False)
        return obras
    except Exception as e:
        logger.error("Falha ao carregar obras PBH: %s", e)
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, encoding="utf-8") as f:
                return json.load(f)
        return []


def buscar_por_regional(regional: str, categoria: str | None = None) -> list[dict]:
    """Returns obras in the given regional, optionally filtered by categoria."""
    obras = _carregar_obras()
    tematicas_alvo = CATEGORIA_TEMATICA.get(categoria or "outros", [])

    resultado = [
        o for o in obras
        if o["regional"].strip().lower() == regional.strip().lower()
        and (not tematicas_alvo or o["tematica"] in tematicas_alvo)
    ]
    return resultado[:20]  # cap to avoid overwhelming the panel


def resumo_regional(regional: str, categoria: str | None = None) -> dict:
    """Returns a summary dict for the panel template."""
    obras = buscar_por_regional(regional, categoria)
    return {
        "total": len(obras),
        "obras": obras,
        "fonte": "Portal de Dados Abertos PBH — dados.pbh.gov.br",
        "atualizado_em": (
            datetime.fromtimestamp(os.path.getmtime(CACHE_FILE)).strftime("%d/%m/%Y %H:%M")
            if os.path.exists(CACHE_FILE)
            else "—"
        ),
    }
