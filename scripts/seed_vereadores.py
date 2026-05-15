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
        added = updated = skipped = 0
        for v in data:
            nome = v.get("nome", "").strip()
            if not nome or nome != nome.upper() or len(nome.split()) < 2:
                skipped += 1
                continue
            votos = v.get("votos_total") or v.get("votos_totais_2024") or 0
            existing = Vereador.query.filter_by(nome=nome).first()
            if existing:
                existing.partido = v.get("partido") or existing.partido
                existing.email_gabinete = v.get("email_gabinete") or existing.email_gabinete
                existing.instagram = v.get("instagram") or existing.instagram
                existing.bairros_base = json.dumps(v.get("bairros_base", [])) or existing.bairros_base
                existing.votos_totais_2024 = votos or existing.votos_totais_2024
                updated += 1
            else:
                db.session.add(Vereador(
                    nome=nome,
                    partido=v.get("partido"),
                    email_gabinete=v.get("email_gabinete"),
                    instagram=v.get("instagram"),
                    twitter=v.get("twitter"),
                    bairros_base=json.dumps(v.get("bairros_base", [])),
                    votos_totais_2024=votos,
                ))
                added += 1
        db.session.commit()
        print(f"Seed concluído: {added} adicionados, {updated} atualizados, {skipped} ignorados.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/seed_vereadores.py <json_file>")
        sys.exit(1)
    seed(sys.argv[1])
