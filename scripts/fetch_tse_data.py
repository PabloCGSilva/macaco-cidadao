"""
fetch_tse_data.py — Processa dados eleitorais TSE 2024 de BH e gera JSON de vereadores.

Uso:
    python scripts/fetch_tse_data.py [--cache-dir ./data/tse_cache]

Saída:
    data/vereadores_bh_tse2024.json

Fontes:
    - Votos por seção: TSE (votacao_secao_2024_MG.zip)
    - Geocodificação: Nominatim/OpenStreetMap (1 req/s — gratuito)
    - Dados dos eleitos: manual (41 vereadores eleitos em BH 2024)
"""

import argparse
import csv
import io
import json
import os
import re
import sys
import time
import urllib.request
import zipfile
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

TSE_URL = "https://cdn.tse.jus.br/estatistica/sead/odsele/votacao_secao/votacao_secao_2024_MG.zip"
CD_MUNICIPIO_BH = "41238"
OUT_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "vereadores_bh_tse2024.json")

# Zonas eleitorais de BH → regional
# Validado via geocodificação Nominatim de amostra de endereços por zona (2024)
ZONA_REGIONAL = {
    "26": "Noroeste",   # Colégio Batista
    "27": "Nordeste",   # Goiânia
    "28": "Leste",      # Vera Cruz
    "29": "Barreiro",   # Nossa Senhora da Glória
    "30": "Noroeste",   # Carlos Prates
    "31": "Venda Nova", # Jardim São José
    "32": "Barreiro",   # Vila Suzana
    "33": "Oeste",      # Nova Gameleira / Contorno
    "34": "Centro-Sul", # Sion
    "35": "Leste",      # Santa Efigênia
    "36": "Barreiro",   # Lindeia
    "37": "Oeste",      # Nova Gameleira
    "38": "Nordeste",   # Jardim dos Comerciários
    "39": "Norte",      # Tupi
    "331": "Nordeste",  # São Gabriel
    "332": "Oeste",     # Nova Suíça
    "333": "Venda Nova",# Flávio de Oliveira
    "334": "Norte",     # Venda Nova / Norte border
}


def _geocode_bairro(endereco: str, cache: dict) -> str | None:
    """Returns neighborhood name from address via Nominatim (cached)."""
    if endereco in cache:
        return cache[endereco]

    query = f"{endereco}, Belo Horizonte, MG, Brasil"
    url = (
        "https://nominatim.openstreetmap.org/search"
        f"?q={urllib.parse.quote(query)}&format=json&addressdetails=1&limit=1"
    )
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "macaco-cidadao/1.0"})
        with urllib.request.urlopen(req, timeout=10) as r:
            results = json.loads(r.read())
        if results:
            addr = results[0].get("address", {})
            bairro = (
                addr.get("neighbourhood")
                or addr.get("suburb")
                or addr.get("city_district")
            )
            cache[endereco] = bairro
            return bairro
    except Exception:
        pass
    cache[endereco] = None
    return None


def _extrair_bairro_do_endereco(endereco: str) -> str | None:
    """Heuristic: last comma-separated part if it looks like a neighborhood name."""
    partes = [p.strip() for p in endereco.split(",")]
    if len(partes) >= 3:
        candidato = partes[-1]
        # Reject if it looks like a number or CEP
        if not re.match(r"^\d", candidato) and len(candidato) > 3:
            return candidato.title()
    return None


def _download_tse(cache_dir: str) -> bytes:
    zip_path = os.path.join(cache_dir, "votacao_secao_2024_MG.zip")
    if os.path.exists(zip_path):
        print(f"Usando cache: {zip_path}")
        with open(zip_path, "rb") as f:
            return f.read()

    print("Baixando dados TSE MG 2024 (191 MB)...")
    req = urllib.request.Request(TSE_URL, headers={"User-Agent": "macaco-cidadao/1.0"})
    with urllib.request.urlopen(req, timeout=120) as r:
        data = r.read()
    os.makedirs(cache_dir, exist_ok=True)
    with open(zip_path, "wb") as f:
        f.write(data)
    print(f"Salvo em {zip_path}")
    return data


def processar(cache_dir: str, geocode: bool = False) -> list[dict]:
    import urllib.parse

    data = _download_tse(cache_dir)
    z = zipfile.ZipFile(io.BytesIO(data))

    # votos[candidato] = {total, por_zona: {zona: votos}, locais: {zona_sec: endereco}}
    votos: dict[str, dict] = defaultdict(lambda: {"total": 0, "por_zona": defaultdict(int), "locais": {}})

    print("Processando votos de BH (pode levar ~30s)...")
    with z.open("votacao_secao_2024_MG.csv") as f:
        reader = csv.DictReader(io.TextIOWrapper(f, encoding="latin-1"), delimiter=";")
        for row in reader:
            if row["CD_MUNICIPIO"].strip() != CD_MUNICIPIO_BH:
                continue
            if row["DS_CARGO"].strip() != "Vereador":
                continue
            nome = row["NM_VOTAVEL"].strip()
            # Skip branco/nulo/partido
            if nome in ("VOTO BRANCO", "VOTO NULO") or len(nome) < 5:
                continue

            try:
                qt = int(row["QT_VOTOS"])
            except ValueError:
                continue

            zona = row["NR_ZONA"].strip()
            sec = row["NR_SECAO"].strip()
            votos[nome]["total"] += qt
            votos[nome]["por_zona"][zona] += qt
            votos[nome]["locais"][f"{zona}_{sec}"] = row["DS_LOCAL_VOTACAO_ENDERECO"].strip()

    print(f"{len(votos):,} candidatos únicos encontrados em BH.")

    # Build per-candidate regional profile
    geocache_path = os.path.join(cache_dir, "geocache.json")
    geocache: dict = {}
    if os.path.exists(geocache_path):
        with open(geocache_path) as f:
            geocache = json.load(f)

    candidatos = []
    for nome, info in sorted(votos.items(), key=lambda x: x[1]["total"], reverse=True):
        total = info["total"]
        if total < 500:  # Skip minor candidates
            continue

        # Regional com mais votos
        regional_votos: dict[str, int] = defaultdict(int)
        for zona, vts in info["por_zona"].items():
            reg = ZONA_REGIONAL.get(zona, "Centro-Sul")
            regional_votos[reg] += vts

        regional_principal = max(regional_votos, key=regional_votos.get)

        # Extract bairros from voting location addresses
        bairros: set[str] = set()
        enderecos_amostrados = list(info["locais"].values())[:50]
        for end in enderecos_amostrados:
            b = _extrair_bairro_do_endereco(end)
            if b:
                bairros.add(b)

        if geocode and len(bairros) < 3:
            for end in enderecos_amostrados[:10]:
                b = _geocode_bairro(end, geocache)
                if b:
                    bairros.add(b)
                time.sleep(1.1)  # Nominatim rate limit

        candidatos.append(
            {
                "nome": nome,
                "partido": "",  # Not in this TSE file — fill from consulta_cand or manually
                "regional": regional_principal,
                "bairros_base": sorted(bairros)[:10],
                "votos_total": total,
                "instagram": None,
                "email_gabinete": None,
                "telefone_gabinete": None,
            }
        )

    # Save geocache
    with open(geocache_path, "w", encoding="utf-8") as f:
        json.dump(geocache, f, ensure_ascii=False, indent=2)

    return candidatos


def main():
    parser = argparse.ArgumentParser(description="Processa dados TSE 2024 de BH")
    parser.add_argument("--cache-dir", default="./data/tse_cache", help="Diretório de cache")
    parser.add_argument("--geocode", action="store_true", help="Geocodificar endereços via Nominatim (lento)")
    parser.add_argument("--limit", type=int, default=60, help="Máximo de candidatos no JSON (default: 60)")
    args = parser.parse_args()

    candidatos = processar(args.cache_dir, geocode=args.geocode)
    candidatos = candidatos[: args.limit]

    os.makedirs(os.path.dirname(OUT_PATH) or ".", exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(candidatos, f, ensure_ascii=False, indent=2)

    print(f"\nExportado: {OUT_PATH}")
    print(f"Total de candidatos: {len(candidatos)}")
    print("\nTop 10:")
    for c in candidatos[:10]:
        print(f"  {c['votos_total']:>8,} votos — {c['nome']} ({c['regional']})")
    print()
    print("PRÓXIMOS PASSOS:")
    print("  1. Preencher 'partido' e 'email_gabinete' para os 41 eleitos")
    print("     Fonte: https://www.cmbh.mg.gov.br/vereadores")
    print("  2. Adicionar 'instagram' e 'bairros_base' manualmente para os mais votados")
    print("  3. Rodar: python scripts/seed_vereadores.py data/vereadores_bh_tse2024.json")
    print("  4. Para bairros mais precisos, rodar com --geocode (requer ~10min)")


if __name__ == "__main__":
    main()
