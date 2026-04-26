import json
import os
from db.models import Vereador, db

DATA_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "vereadores_bh.json")


def vereador_por_bairro(bairro: str) -> Vereador | None:
    """Returns the vereador with most votes in the given bairro (DB lookup)."""
    vereadores = Vereador.query.all()
    melhor = None
    melhor_votos = 0

    for v in vereadores:
        if not v.bairros_base:
            continue
        try:
            bairros = json.loads(v.bairros_base)
        except (json.JSONDecodeError, TypeError):
            continue
        bairro_norm = bairro.lower().strip()
        if any(bairro_norm in b.lower() for b in bairros):
            if (v.votos_totais_2024 or 0) > melhor_votos:
                melhor = v
                melhor_votos = v.votos_totais_2024 or 0

    return melhor


def seed_vereadores_exemplo(app):
    """Seeds placeholder data — replace with real TSE 2024 data."""
    exemplos = [
        {
            "nome": "Vereador Exemplo Norte",
            "partido": "PARTIDO",
            "email_gabinete": "gabinete.norte@cmbh.mg.gov.br",
            "instagram": "@vereador_norte",
            "twitter": "@vereador_norte",
            "bairros_base": ["Tupi", "Floramar", "Jardim Leblon", "Céu Azul"],
            "votos_totais_2024": 4500,
        },
        {
            "nome": "Vereador Exemplo Centro",
            "partido": "PARTIDO",
            "email_gabinete": "gabinete.centro@cmbh.mg.gov.br",
            "instagram": "@vereador_centro",
            "twitter": "@vereador_centro",
            "bairros_base": ["Centro", "Funcionários", "Savassi", "Lourdes"],
            "votos_totais_2024": 6200,
        },
    ]

    with app.app_context():
        if Vereador.query.count() == 0:
            for v in exemplos:
                vereador = Vereador(
                    nome=v["nome"],
                    partido=v["partido"],
                    email_gabinete=v["email_gabinete"],
                    instagram=v["instagram"],
                    twitter=v["twitter"],
                    bairros_base=json.dumps(v["bairros_base"]),
                    votos_totais_2024=v["votos_totais_2024"],
                )
                db.session.add(vereador)
            db.session.commit()
