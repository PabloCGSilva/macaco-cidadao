import json
import os
from db.models import Vereador, db

TSE_DATA_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "vereadores_bh_tse2024.json")


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


def _is_person_name(nome: str) -> bool:
    """TSE candidate names are ALL CAPS; party/legend entries have mixed case."""
    return bool(nome) and nome == nome.upper() and len(nome.split()) >= 2


def seed_vereadores_tse(app):
    """Seeds vereadores from TSE 2024 data (vereadores_bh_tse2024.json)."""
    if not os.path.exists(TSE_DATA_FILE):
        return

    with open(TSE_DATA_FILE, encoding="utf-8") as f:
        candidatos = json.load(f)

    with app.app_context():
        if Vereador.query.count() > 0:
            return
        for c in candidatos:
            nome = c.get("nome", "").strip()
            if not _is_person_name(nome):
                continue
            db.session.add(Vereador(
                nome=nome,
                partido=c.get("partido") or "",
                email_gabinete=c.get("email_gabinete"),
                instagram=c.get("instagram"),
                twitter=None,
                bairros_base=json.dumps(c.get("bairros_base", [])),
                votos_totais_2024=c.get("votos_total", 0),
            ))
        db.session.commit()


# Backward-compat alias (panel/app.py and any external callers)
seed_vereadores_exemplo = seed_vereadores_tse
