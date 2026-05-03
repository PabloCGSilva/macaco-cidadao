import json
from unittest.mock import patch, MagicMock

from ai.classifier import classificar

_VALID = {
    "valida": True,
    "motivo_invalidade": None,
    "categoria": "buraco_pavimento",
    "bairro_confirmado": "Savassi",
    "regional": "Centro-Sul",
    "canal_correto": None,
    "texto_post": "📍 Savassi | Buraco no Pavimento\nBuraco profundo na calçada.",
    "assunto_email": "Buraco na calçada — Savassi",
    "corpo_email": "Prezado Vereador...",
    "agrupamento_sugerido": "buraco calçada savassi",
}

_INVALID = {
    "valida": False,
    "motivo_invalidade": "Conflito entre particulares, fora do escopo municipal.",
    "categoria": None,
    "bairro_confirmado": "Savassi",
    "regional": "Centro-Sul",
    "canal_correto": "Polícia",
    "texto_post": None,
    "assunto_email": None,
    "corpo_email": None,
    "agrupamento_sugerido": None,
}


def _resp(payload: dict) -> MagicMock:
    r = MagicMock()
    r.content = [MagicMock(text=json.dumps(payload))]
    return r


@patch("ai.classifier._client")
def test_classificar_retorna_valida(mock_client):
    mock_client.messages.create.return_value = _resp(_VALID)
    r = classificar("Buraco na calçada", "Savassi", True, None)
    assert r["valida"] is True
    assert r["categoria"] == "buraco_pavimento"
    assert r["regional"] == "Centro-Sul"


@patch("ai.classifier._client")
def test_classificar_retorna_invalida(mock_client):
    mock_client.messages.create.return_value = _resp(_INVALID)
    r = classificar("Briga com vizinho", "Savassi", False, None)
    assert r["valida"] is False
    assert r["canal_correto"] == "Polícia"


@patch("ai.classifier._client")
def test_classificar_strips_markdown_fences(mock_client):
    wrapped = MagicMock()
    wrapped.content = [MagicMock(text=f"```json\n{json.dumps(_VALID)}\n```")]
    mock_client.messages.create.return_value = wrapped
    r = classificar("Buraco", "Savassi", True, None)
    assert r["valida"] is True


@patch("ai.classifier._client")
def test_classificar_sem_midia(mock_client):
    mock_client.messages.create.return_value = _resp(_VALID)
    classificar("Buraco na calçada", "Savassi", False, None)
    prompt = mock_client.messages.create.call_args.kwargs["messages"][0]["content"]
    assert "não" in prompt


@patch("ai.classifier._client")
def test_classificar_inclui_denuncias_anteriores(mock_client):
    mock_client.messages.create.return_value = _resp(_VALID)
    anteriores = [{"protocolo": "MC-2024-001", "criado_em": "2024-01-10"}]
    classificar("Buraco", "Savassi", True, None, anteriores)
    prompt = mock_client.messages.create.call_args.kwargs["messages"][0]["content"]
    assert "MC-2024-001" in prompt


@patch("ai.classifier._client")
def test_classificar_com_coordenadas(mock_client):
    mock_client.messages.create.return_value = _resp(_VALID)
    classificar("Buraco", "Savassi", True, "-19.932, -43.938")
    prompt = mock_client.messages.create.call_args.kwargs["messages"][0]["content"]
    assert "-19.932" in prompt
