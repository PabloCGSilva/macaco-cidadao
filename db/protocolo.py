from datetime import datetime
from .models import db, Denuncia


def gerar_protocolo() -> str:
    ano = datetime.utcnow().year
    ultimo = (
        db.session.query(Denuncia)
        .filter(Denuncia.protocolo.like(f"MC-{ano}-%"))
        .order_by(Denuncia.id.desc())
        .first()
    )
    if ultimo:
        seq = int(ultimo.protocolo.split("-")[-1]) + 1
    else:
        seq = 1
    return f"MC-{ano}-{seq:05d}"
