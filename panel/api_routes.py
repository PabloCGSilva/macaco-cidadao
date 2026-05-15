import json
from datetime import datetime

from flask import session, jsonify, request
from flask_openapi3 import APIBlueprint, Tag

from db.models import db, Denuncia, Vereador
from api.schemas import (
    AprovarRequest,
    DenunciaListQuery,
    DenunciaPath,
    DenunciaResponse,
    HealthResponse,
    RejeitarRequest,
    ScorecardItem,
    VereadorPath,
    VereadorResponse,
)

_health_tag = Tag(name="health", description="Health check")
_denuncias_tag = Tag(name="denuncias", description="Gestão de denúncias")
_scorecard_tag = Tag(name="scorecard", description="Scorecard de vereadores")
_vereadores_tag = Tag(name="vereadores", description="Dados dos vereadores")

api_bp = APIBlueprint("api_v1", __name__, url_prefix="/api/v1")

_EXEMPT_PATHS = {"/api/v1/health"}


@api_bp.before_request
def _require_login():
    if request.path in _EXEMPT_PATHS:
        return
    if not session.get("logado"):
        return jsonify({"error": "Unauthorized", "code": 401}), 401


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

@api_bp.get("/health", tags=[_health_tag], responses={"200": HealthResponse})
def health():
    return jsonify({"status": "ok", "version": "1.0.0"})


# ---------------------------------------------------------------------------
# Denúncias
# ---------------------------------------------------------------------------

@api_bp.get("/denuncias", tags=[_denuncias_tag])
def list_denuncias(query: DenunciaListQuery):
    q = Denuncia.query
    if query.status:
        q = q.filter_by(status=query.status)
    q = q.order_by(Denuncia.criado_em.desc())
    total = q.count()
    items = q.offset((query.page - 1) * query.per_page).limit(query.per_page).all()
    return jsonify({
        "total": total,
        "page": query.page,
        "per_page": query.per_page,
        "items": [DenunciaResponse.model_validate(d).model_dump(mode="json") for d in items],
    })


@api_bp.get("/denuncias/<int:id>", tags=[_denuncias_tag])
def get_denuncia(path: DenunciaPath):
    d = db.session.get(Denuncia, path.id)
    if d is None:
        return jsonify({"error": "Not found"}), 404
    return jsonify(DenunciaResponse.model_validate(d).model_dump(mode="json"))


@api_bp.post("/denuncias/<int:id>/aprovar", tags=[_denuncias_tag])
def aprovar_denuncia(path: DenunciaPath, body: AprovarRequest):
    d = db.session.get(Denuncia, path.id)
    if d is None:
        return jsonify({"error": "Not found"}), 404
    d.status = "aprovada"
    d.aprovada_em = datetime.utcnow()
    d.moderador_notas = body.notas
    if body.minuta_email:
        d.minuta_email = body.minuta_email
    if body.texto_post:
        d.texto_post_sugerido = body.texto_post
    db.session.commit()
    return jsonify({"ok": True, "protocolo": d.protocolo, "status": d.status})


@api_bp.post("/denuncias/<int:id>/rejeitar", tags=[_denuncias_tag])
def rejeitar_denuncia(path: DenunciaPath, body: RejeitarRequest):
    d = db.session.get(Denuncia, path.id)
    if d is None:
        return jsonify({"error": "Not found"}), 404
    d.status = "rejeitada"
    d.moderador_notas = body.motivo
    db.session.commit()
    return jsonify({"ok": True, "protocolo": d.protocolo, "status": d.status})


# ---------------------------------------------------------------------------
# Scorecard
# ---------------------------------------------------------------------------

@api_bp.get("/scorecard", tags=[_scorecard_tag])
def scorecard():
    publicadas = Denuncia.query.filter_by(status="publicada").all()
    stats: dict[str, dict] = {}
    for d in publicadas:
        nome = d.vereador_nome or "Não identificado"
        if nome not in stats:
            stats[nome] = {
                "vereador": nome,
                "total": 0,
                "cobrou": 0,
                "respondeu_sem_acao": 0,
                "ignorou": 0,
                "pendente": 0,
            }
        stats[nome]["total"] += 1
        sc = d.classificacao_scorecard
        if sc == "cobrou_prefeitura":
            stats[nome]["cobrou"] += 1
        elif sc == "respondeu_sem_acao":
            stats[nome]["respondeu_sem_acao"] += 1
        elif sc == "ignorou":
            stats[nome]["ignorou"] += 1
        else:
            stats[nome]["pendente"] += 1

    items = [ScorecardItem(**v).model_dump() for v in stats.values()]
    return jsonify(items)


# ---------------------------------------------------------------------------
# Vereadores
# ---------------------------------------------------------------------------

@api_bp.get("/vereadores", tags=[_vereadores_tag])
def list_vereadores():
    vereadores = Vereador.query.order_by(Vereador.nome).all()
    return jsonify([VereadorResponse.model_validate(v).model_dump() for v in vereadores])


@api_bp.get("/vereadores/<int:id>/bairros", tags=[_vereadores_tag])
def vereador_bairros(path: VereadorPath):
    v = db.session.get(Vereador, path.id)
    if v is None:
        return jsonify({"error": "Not found"}), 404
    try:
        bairros = json.loads(v.bairros_base or "[]")
    except (json.JSONDecodeError, TypeError):
        bairros = []
    return jsonify({"id": v.id, "nome": v.nome, "bairros": bairros})
