from datetime import datetime
from types import SimpleNamespace
from unittest.mock import patch, MagicMock

from notifier.email_sender import enviar_email_formal


def _denuncia(**kw) -> SimpleNamespace:
    defaults = dict(
        protocolo="MC-TEST-001",
        telegram_user_id="1",
        descricao_usuario="Buraco na calçada em frente à escola",
        bairro="Savassi",
        regional="Centro-Sul",
        categoria="buraco_pavimento",
        vereador_nome="Vereador Teste",
        vereador_email="gabinete.teste@cmbh.mg.gov.br",
        secretaria_nome="SUDECAP",
        secretaria_email="sudecap@pbh.gov.br",
        status="aprovada",
        criado_em=datetime(2024, 1, 15, 10, 0),
        latitude=None,
        longitude=None,
        endereco="Rua Paraíba, 200, Savassi",
        minuta_email=None,
        link_post=None,
    )
    defaults.update(kw)
    return SimpleNamespace(**defaults)


def _smtp_mock():
    srv = MagicMock()
    cls = MagicMock()
    cls.return_value.__enter__ = lambda s: srv
    cls.return_value.__exit__ = MagicMock(return_value=False)
    return cls, srv


@patch("notifier.email_sender.smtplib.SMTP")
def test_sucesso_retorna_true(mock_cls):
    _, srv = _smtp_mock()
    mock_cls.return_value.__enter__ = lambda s: srv
    mock_cls.return_value.__exit__ = MagicMock(return_value=False)

    assert enviar_email_formal(_denuncia()) is True
    srv.sendmail.assert_called_once()


@patch("notifier.email_sender.smtplib.SMTP")
def test_falha_smtp_retorna_false(mock_cls):
    mock_cls.side_effect = Exception("Connection refused")
    assert enviar_email_formal(_denuncia()) is False


@patch("notifier.email_sender.smtplib.SMTP")
def test_destinatarios_incluem_vereador_e_secretaria(mock_cls):
    _, srv = _smtp_mock()
    mock_cls.return_value.__enter__ = lambda s: srv
    mock_cls.return_value.__exit__ = MagicMock(return_value=False)

    enviar_email_formal(_denuncia())

    destinatarios = srv.sendmail.call_args[0][1]
    assert "gabinete.teste@cmbh.mg.gov.br" in destinatarios
    assert "sudecap@pbh.gov.br" in destinatarios


@patch("notifier.email_sender.smtplib.SMTP")
def test_destinatarios_incluem_ouvidoria_camara(mock_cls):
    _, srv = _smtp_mock()
    mock_cls.return_value.__enter__ = lambda s: srv
    mock_cls.return_value.__exit__ = MagicMock(return_value=False)

    import config
    enviar_email_formal(_denuncia())

    destinatarios = srv.sendmail.call_args[0][1]
    assert config.OUVIDORIA_CAMARA_EMAIL in destinatarios


@patch("notifier.email_sender.smtplib.SMTP")
def test_usa_minuta_quando_disponivel(mock_cls):
    import email as email_lib

    _, srv = _smtp_mock()
    mock_cls.return_value.__enter__ = lambda s: srv
    mock_cls.return_value.__exit__ = MagicMock(return_value=False)

    minuta = "Corpo personalizado pelo moderador."
    enviar_email_formal(_denuncia(minuta_email=minuta))

    mensagem_raw = srv.sendmail.call_args[0][2]
    msg = email_lib.message_from_string(mensagem_raw)
    body = ""
    for part in msg.walk():
        if part.get_content_type() == "text/plain":
            body = part.get_payload(decode=True).decode("utf-8")
            break
    assert minuta in body


@patch("notifier.email_sender.smtplib.SMTP")
def test_sem_vereador_email_nao_falha(mock_cls):
    _, srv = _smtp_mock()
    mock_cls.return_value.__enter__ = lambda s: srv
    mock_cls.return_value.__exit__ = MagicMock(return_value=False)

    result = enviar_email_formal(_denuncia(vereador_email=None))
    assert result is True
