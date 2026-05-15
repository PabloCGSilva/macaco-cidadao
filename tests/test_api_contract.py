"""
API contract tests for the Macaco Cidadão REST API.
Tests use an isolated OpenAPI app with in-memory SQLite.
"""
import json
import pytest

from flask_openapi3 import OpenAPI, Info
from db.models import db, Denuncia, Vereador
from panel.api_routes import api_bp


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def api_app():
    info = Info(title="Test API", version="1.0.0")
    app = OpenAPI(__name__, info=info)
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.secret_key = "test-secret"
    db.init_app(app)
    app.register_api(api_bp)
    with app.app_context():
        db.create_all()
        yield app


@pytest.fixture
def client(api_app):
    return api_app.test_client()


@pytest.fixture
def authed_client(client):
    with client.session_transaction() as sess:
        sess["logado"] = True
    return client


@pytest.fixture
def sample_denuncia(api_app):
    with api_app.app_context():
        d = Denuncia(
            protocolo="MC-TEST-001",
            telegram_user_id="42",
            descricao_usuario="Buraco na rua",
            bairro="Savassi",
            regional="Centro-Sul",
            categoria="buraco_pavimento",
            vereador_nome="Vereador Teste",
            status="aguardando_triagem",
        )
        db.session.add(d)
        db.session.commit()
        yield d.id
        db.session.delete(db.session.get(Denuncia, d.id))
        db.session.commit()


@pytest.fixture
def sample_vereador(api_app):
    with api_app.app_context():
        v = Vereador(
            nome="VEREADOR TESTE SILVA",
            partido="PT",
            email_gabinete="ver.teste@cmbh.mg.gov.br",
            bairros_base=json.dumps(["Savassi", "Serra"]),
        )
        db.session.add(v)
        db.session.commit()
        yield v.id
        db.session.delete(db.session.get(Vereador, v.id))
        db.session.commit()


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

def test_health_returns_ok(client):
    r = client.get("/api/v1/health")
    assert r.status_code == 200
    data = r.get_json()
    assert data["status"] == "ok"
    assert "version" in data


# ---------------------------------------------------------------------------
# Auth guard
# ---------------------------------------------------------------------------

def test_denuncias_unauthenticated_returns_401(client):
    r = client.get("/api/v1/denuncias")
    assert r.status_code == 401
    assert "error" in r.get_json()


def test_vereadores_unauthenticated_returns_401(client):
    r = client.get("/api/v1/vereadores")
    assert r.status_code == 401


def test_scorecard_unauthenticated_returns_401(client):
    r = client.get("/api/v1/scorecard")
    assert r.status_code == 401


# ---------------------------------------------------------------------------
# Denúncias list
# ---------------------------------------------------------------------------

def test_denuncias_authenticated_returns_list(authed_client):
    r = authed_client.get("/api/v1/denuncias")
    assert r.status_code == 200
    data = r.get_json()
    assert "items" in data
    assert "total" in data
    assert "page" in data
    assert "per_page" in data


def test_denuncias_filter_by_status(authed_client, sample_denuncia):
    r = authed_client.get("/api/v1/denuncias?status=aguardando_triagem")
    assert r.status_code == 200
    data = r.get_json()
    assert data["total"] >= 1
    for item in data["items"]:
        assert item["status"] == "aguardando_triagem"


def test_denuncias_filter_invalid_status_returns_empty(authed_client):
    r = authed_client.get("/api/v1/denuncias?status=status_inexistente")
    assert r.status_code == 200
    assert r.get_json()["total"] == 0


# ---------------------------------------------------------------------------
# Denúncia single
# ---------------------------------------------------------------------------

def test_get_denuncia_returns_denuncia(authed_client, sample_denuncia):
    r = authed_client.get(f"/api/v1/denuncias/{sample_denuncia}")
    assert r.status_code == 200
    data = r.get_json()
    assert data["protocolo"] == "MC-TEST-001"
    assert data["bairro"] == "Savassi"


def test_get_denuncia_not_found(authed_client):
    r = authed_client.get("/api/v1/denuncias/999999")
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# Aprovar
# ---------------------------------------------------------------------------

def test_aprovar_denuncia(authed_client, sample_denuncia):
    r = authed_client.post(
        f"/api/v1/denuncias/{sample_denuncia}/aprovar",
        json={"notas": "Denúncia válida"},
    )
    assert r.status_code == 200
    data = r.get_json()
    assert data["ok"] is True
    assert data["status"] == "aprovada"


def test_aprovar_denuncia_not_found(authed_client):
    r = authed_client.post("/api/v1/denuncias/999999/aprovar", json={"notas": ""})
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# Rejeitar
# ---------------------------------------------------------------------------

def test_rejeitar_denuncia(authed_client, sample_denuncia):
    r = authed_client.post(
        f"/api/v1/denuncias/{sample_denuncia}/rejeitar",
        json={"motivo": "Fora do escopo"},
    )
    assert r.status_code == 200
    data = r.get_json()
    assert data["ok"] is True
    assert data["status"] == "rejeitada"


def test_rejeitar_requires_motivo(authed_client, sample_denuncia):
    r = authed_client.post(
        f"/api/v1/denuncias/{sample_denuncia}/rejeitar",
        json={"motivo": ""},
    )
    assert r.status_code == 422


# ---------------------------------------------------------------------------
# Scorecard
# ---------------------------------------------------------------------------

def test_scorecard_returns_list(authed_client):
    r = authed_client.get("/api/v1/scorecard")
    assert r.status_code == 200
    assert isinstance(r.get_json(), list)


# ---------------------------------------------------------------------------
# Vereadores
# ---------------------------------------------------------------------------

def test_vereadores_returns_list(authed_client, sample_vereador):
    r = authed_client.get("/api/v1/vereadores")
    assert r.status_code == 200
    data = r.get_json()
    assert isinstance(data, list)
    assert len(data) >= 1


def test_vereador_bairros(authed_client, sample_vereador):
    r = authed_client.get(f"/api/v1/vereadores/{sample_vereador}/bairros")
    assert r.status_code == 200
    data = r.get_json()
    assert "bairros" in data
    assert "Savassi" in data["bairros"]


def test_vereador_bairros_not_found(authed_client):
    r = authed_client.get("/api/v1/vereadores/999999/bairros")
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# OpenAPI spec
# ---------------------------------------------------------------------------

def test_openapi_spec_accessible(client):
    r = client.get("/openapi/openapi.json")
    assert r.status_code == 200
    spec = r.get_json()
    assert spec["openapi"].startswith("3.")
    assert "paths" in spec
