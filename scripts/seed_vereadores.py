"""
Seed real TSE 2024 vereador data.
Usage: python scripts/seed_vereadores.py data/vereadores_tse_2024.json
"""
import sys
import os
import json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from panel.app import app
from db.models import db, Vereador


def seed(json_path: str):
    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)

    with app.app_context():
        db.create_all()
        added = 0
        for v in data:
            existing = Vereador.query.filter_by(nome=v["nome"]).first()
            if existing:
                continue
            vereador = Vereador(
                nome=v["nome"],
                partido=v.get("partido"),
                email_gabinete=v.get("email_gabinete"),
                instagram=v.get("instagram"),
                twitter=v.get("twitter"),
                bairros_base=json.dumps(v.get("bairros_base", [])),
                votos_totais_2024=v.get("votos_totais_2024", 0),
            )
            db.session.add(vereador)
            added += 1
        db.session.commit()
        print(f"{added} vereadores adicionados.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/seed_vereadores.py <json_file>")
        sys.exit(1)
    seed(sys.argv[1])
