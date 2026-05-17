import json
from datetime import datetime, timedelta

from flask import session, jsonify, request
from flask_openapi3 import APIBlueprint, Tag

from db.models import db, Denuncia, FollowUp, Vereador
from api.schemas import (
    AprovarRequest,
    DenunciaListQuery,
    DenunciaPath,
    DenunciaPublicaResponse,
    DenunciaResponse,
    HealthResponse,
    RegistrarAcaoRequest,
    RejeitarRequest,
    ScorecardItem,
    ScorecardVereadorPath,
    VereadorPath,
    VereadorResponse,
)

_health_tag = Tag(name="health", description="Health check")
_denuncias_tag = Tag(name="denuncias", description="Gestão de denúncias")
_scorecard_tag = Tag(name="scorecard", description="Scorecard de vereadores")
_vereadores_tag = Tag(name="vereadores", description="Dados dos vereadores")

api_bp = APIBlueprint("api_v1", __name__, url_prefix="/api/v1")

# Endpoints acessíveis sem autenticação
_EXEMPT_PATHS = {"/api/v1/health", "/api/v1/scorecard"}
_EXEMPT_PREFIXES = ("/api/v1/scorecard/",)


@api_bp.before_request
def _require_login():
    if request.path in _EXEMPT_PATHS:
        return
    for prefix in _EXEMPT_PREFIXES:
        if request.path.startswith(prefix):
            return
    if not session.get("logado"):
        return jsonify({"error": "Unauthorized", "code": 401}), 401


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

@api_bp.get("/health", tags=[_health_tag], responses={"200": HealthResponse})
def health():
    from sqlalchemy import text
    try:
        db.session.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False
    return jsonify({"status": "ok", "version": "1.0.0", "db_ok": db_ok})


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


@api_bp.post("/denuncias/<int:id>/registrar_acao", tags=[_denuncias_tag])
def registrar_acao(path: DenunciaPath, body: RegistrarAcaoRequest):
    """Registra que o moderador usou uma ação de pressão direta (WA/Instagram)."""
    d = db.session.get(Denuncia, path.id)
    if d is None:
        return jsonify({"error": "Not found"}), 404
    if d.status not in ("aprovada", "publicada"):
        return jsonify({"error": "Ação disponível apenas para denúncias aprovadas ou publicadas"}), 422

    tipo_acao = f"acao_{body.acao}"
    fu = FollowUp(
        denuncia_id=d.id,
        tipo=tipo_acao,
        texto=f"Moderador usou ação: {body.acao} em {datetime.utcnow().strftime('%d/%m/%Y %H:%M')}",
        publicado=True,
    )
    db.session.add(fu)

    if body.acao == "whatsapp_vereador":
        d.whatsapp_enviado = True
    elif body.acao == "instagram":
        d.instagram_marcado = True

    db.session.commit()
    return jsonify({"ok": True, "acao": body.acao, "registrado_em": fu.criado_em.isoformat()})


# ---------------------------------------------------------------------------
# Scorecard — público (sem autenticação)
# ---------------------------------------------------------------------------

@api_bp.get("/scorecard", tags=[_scorecard_tag])
def scorecard():
    from sqlalchemy import func
    publicadas = Denuncia.query.filter_by(status="publicada").all()
    agora = datetime.utcnow()
    trinta_dias_atras = agora - timedelta(days=30)

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
                "_tempos_resolucao": [],
                "denuncias_sem_resposta_30d": 0,
                "ultima_denuncia_data": None,
            }
        s = stats[nome]
        s["total"] += 1
        sc = d.classificacao_scorecard
        if sc == "cobrou_prefeitura":
            s["cobrou"] += 1
        elif sc == "respondeu_sem_acao":
            s["respondeu_sem_acao"] += 1
        elif sc == "ignorou":
            s["ignorou"] += 1
        else:
            s["pendente"] += 1

        # Tempo de resolução
        if d.resolvida_em and d.publicada_em:
            delta = (d.resolvida_em - d.publicada_em).days
            s["_tempos_resolucao"].append(delta)

        # Sem resposta nos últimos 30 dias
        if d.publicada_em and d.publicada_em >= trinta_dias_atras and not d.classificacao_scorecard:
            s["denuncias_sem_resposta_30d"] += 1

        # Última denúncia
        if d.publicada_em:
            if s["ultima_denuncia_data"] is None or d.publicada_em > s["ultima_denuncia_data"]:
                s["ultima_denuncia_data"] = d.publicada_em

    items = []
    for s in stats.values():
        tempos = s.pop("_tempos_resolucao")
        s["tempo_medio_resolucao_dias"] = round(sum(tempos) / len(tempos), 1) if tempos else None
        items.append(ScorecardItem(**s).model_dump(mode="json"))
    return jsonify(items)


@api_bp.get("/scorecard/<int:vereador_id>/denuncias", tags=[_scorecard_tag])
def scorecard_vereador_denuncias(path: ScorecardVereadorPath):
    """Lista pública das denúncias publicadas de um vereador — sem dados pessoais."""
    vereador = db.session.get(Vereador, path.vereador_id)
    if vereador is None:
        return jsonify({"error": "Not found"}), 404

    denuncias = (
        Denuncia.query
        .filter_by(status="publicada", vereador_nome=vereador.nome)
        .order_by(Denuncia.publicada_em.desc())
        .all()
    )
    return jsonify({
        "vereador": vereador.nome,
        "total": len(denuncias),
        "denuncias": [DenunciaPublicaResponse.model_validate(d).model_dump(mode="json") for d in denuncias],
    })


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
