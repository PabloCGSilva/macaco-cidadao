"""
Detects previous complaints at the same location and category (last 90 days).
If GPS coordinates are available, uses a ~200m radius check.
Otherwise falls back to bairro + category match.
"""
import math
from datetime import datetime, timedelta
from .models import Denuncia

JANELA_DIAS = 90
RAIO_METROS = 200


def _distancia_metros(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Haversine distance in metres."""
    R = 6_371_000
    φ1, φ2 = math.radians(lat1), math.radians(lat2)
    Δφ = math.radians(lat2 - lat1)
    Δλ = math.radians(lon2 - lon1)
    a = math.sin(Δφ / 2) ** 2 + math.cos(φ1) * math.cos(φ2) * math.sin(Δλ / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def buscar_denuncias_anteriores(
    bairro: str,
    categoria: str = "",
    latitude: float | None = None,
    longitude: float | None = None,
) -> list[dict]:
    """Returns previous complaints at same location within 90 days.

    When categoria is empty, searches by bairro only (used as pre-filter
    before the AI classifier confirms the category).
    """
    corte = datetime.utcnow() - timedelta(days=JANELA_DIAS)

    q = Denuncia.query.filter(
        Denuncia.bairro.ilike(f"%{bairro}%"),
        Denuncia.status.in_(["aprovada", "publicada"]),
        Denuncia.criado_em >= corte,
    )
    if categoria:
        q = q.filter(Denuncia.categoria == categoria)

    candidatas = q.order_by(Denuncia.criado_em.asc()).all()

    if not candidatas:
        return []

    if latitude and longitude:
        # Filter by GPS proximity when available
        proximas = [
            d for d in candidatas
            if d.latitude
            and d.longitude
            and _distancia_metros(latitude, longitude, d.latitude, d.longitude) <= RAIO_METROS
        ]
        # Fall back to all same-bairro/category if no GPS matches
        resultado = proximas if proximas else candidatas
    else:
        resultado = candidatas

    return [
        {
            "protocolo": d.protocolo,
            "criado_em": d.criado_em.strftime("%d/%m/%Y"),
            "link_post": d.link_post,
            "grupo_id": d.grupo_id or d.id,
        }
        for d in resultado
    ]


def atribuir_grupo(denuncia: Denuncia, anteriores: list[dict]) -> None:
    """Sets grupo_id and grupo_seq on the new complaint in-place."""
    if not anteriores:
        denuncia.grupo_id = None
        denuncia.grupo_seq = 1
        return

    grupo_id = anteriores[0]["grupo_id"]
    seq = len(anteriores) + 1
    denuncia.grupo_id = grupo_id
    denuncia.grupo_seq = seq
