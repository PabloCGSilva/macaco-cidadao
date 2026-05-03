"""
Integration test: full complaint lifecycle — create → approve → publish (mocked email).
"""
from datetime import datetime
from unittest.mock import patch, MagicMock

import pytest

from db.models import db, Denuncia
from db.protocolo import gerar_protocolo


def test_fluxo_denuncia_completo(flask_app):
    """Complaint goes from aguardando_triagem → aprovada → email dispatched."""
    with flask_app.app_context():
        protocolo = gerar_protocolo()
        d = Denuncia(
            protocolo=protocolo,
            telegram_user_id="999",
            tipo_midia="photo",
            descricao_usuario="Buraco grave na calçada próximo à escola",
            bairro="Floresta",
            regional="Leste",
            categoria="buraco_pavimento",
            vereador_nome="Vereador Floresta",
            vereador_email="gabinete.floresta@cmbh.mg.gov.br",
            secretaria_nome="SUDECAP",
            secretaria_email="sudecap@pbh.gov.br",
            texto_post_sugerido="📍 Floresta | Buraco no Pavimento\nBuraco profundo na calçada.",
            minuta_email="Prezado Vereador,\n\nRegistramos denúncia...",
            status="aguardando_triagem",
            valida=True,
            criado_em=datetime.utcnow(),
        )
        db.session.add(d)
        db.session.commit()

        created = Denuncia.query.filter_by(protocolo=protocolo).first()
        assert created is not None
        assert created.status == "aguardando_triagem"

        # Moderator approves
        created.status = "aprovada"
        created.aprovada_em = datetime.utcnow()
        db.session.commit()

        approved = Denuncia.query.filter_by(protocolo=protocolo).first()
        assert approved.status == "aprovada"

        # Publish: send formal email (SMTP mocked)
        srv = MagicMock()
        with patch("notifier.email_sender.smtplib.SMTP") as mock_cls:
            mock_cls.return_value.__enter__ = lambda s: srv
            mock_cls.return_value.__exit__ = MagicMock(return_value=False)
            from notifier.email_sender import enviar_email_formal
            ok = enviar_email_formal(approved)

        assert ok is True
        srv.sendmail.assert_called_once()

        # Verify email recipients include vereador
        dest = srv.sendmail.call_args[0][1]
        assert "gabinete.floresta@cmbh.mg.gov.br" in dest


def test_protocolo_unico(flask_app):
    """gerar_protocolo generates a non-empty string with expected prefix."""
    with flask_app.app_context():
        p = gerar_protocolo()
        assert p.startswith("MC-")
        assert len(p) > 6


def test_grouping_seq_default(flask_app):
    """New Denuncia has grupo_seq=1 by default."""
    with flask_app.app_context():
        d = Denuncia(
            protocolo=gerar_protocolo(),
            telegram_user_id="1",
            bairro="Centro",
            status="aguardando_triagem",
            valida=True,
            criado_em=datetime.utcnow(),
        )
        db.session.add(d)
        db.session.commit()
        assert d.grupo_seq == 1
        assert d.grupo_id is None
