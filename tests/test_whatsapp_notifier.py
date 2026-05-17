"""Tests for WhatsApp notifier and Instagram caption generator."""
from datetime import datetime
from types import SimpleNamespace

import pytest

from notifier.whatsapp_notifier import gerar_link_whatsapp
from notifier.instagram_tagger import gerar_caption_instagram


def _denuncia(**kwargs):
    defaults = {
        "protocolo": "MC-2026-00001",
        "criado_em": datetime(2026, 5, 17, 10, 0),
        "categoria": "buraco_pavimento",
        "bairro": "Savassi",
        "descricao_usuario": "Buraco enorme na Rua Pernambuco",
        "link_post": None,
        "vereador_nome": "JOÃO DA SILVA",
        "vereador_instagram": "joaodasilva_bh",
        "vereador_whatsapp": None,
        "secretaria_slug": None,
    }
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def _vereador(**kwargs):
    defaults = {
        "nome": "JOÃO DA SILVA",
        "instagram": "joaodasilva_bh",
        "whatsapp_gabinete": None,
    }
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


class TestGerarLinkWhatsapp:
    def test_gerar_link_whatsapp_com_numero_valido(self):
        d = _denuncia()
        v = _vereador(whatsapp_gabinete="5531991230001")
        links = gerar_link_whatsapp(d, vereador=v)
        assert links["vereador"] is not None
        assert links["vereador"].startswith("https://wa.me/5531991230001?text=")
        # URL deve conter o protocolo codificado
        assert "MC-2026-00001" in links["vereador"] or "MC-2026-00001" in links["vereador"].replace("%2D", "-")

    def test_gerar_link_whatsapp_sem_numero_retorna_none(self):
        d = _denuncia()
        v = _vereador(whatsapp_gabinete=None)
        links = gerar_link_whatsapp(d, vereador=v)
        assert links["vereador"] is None
        assert links["secretaria"] is None

    def test_gerar_link_whatsapp_secretaria_com_numero(self, tmp_path, monkeypatch):
        # Monkeypatch para usar um gabinetes_pbh.json temporário com número preenchido
        import json
        gabinetes = [{"slug": "smobi", "nome": "SMOBI", "whatsapp": "5531322770001", "instagram": "pbhoficial"}]
        p = tmp_path / "gabinetes_pbh.json"
        p.write_text(json.dumps(gabinetes), encoding="utf-8")

        import notifier.whatsapp_notifier as wn
        monkeypatch.setattr(wn, "_carregar_gabinetes", lambda: {g["slug"]: g for g in gabinetes})

        d = _denuncia(secretaria_slug="smobi")
        v = _vereador()
        links = gerar_link_whatsapp(d, vereador=v)
        assert links["secretaria"] is not None
        assert links["secretaria"].startswith("https://wa.me/5531322770001?text=")

    def test_gerar_link_mensagem_contem_bairro_e_categoria(self):
        import urllib.parse
        v = _vereador(whatsapp_gabinete="5531991230001")
        d = _denuncia(bairro="Lourdes", categoria="lixo_entulho")
        links = gerar_link_whatsapp(d, vereador=v)
        msg_decoded = urllib.parse.unquote(links["vereador"].split("?text=")[1])
        assert "Lourdes" in msg_decoded
        assert "LIXO ENTULHO" in msg_decoded


class TestGerarCaptionInstagram:
    def test_caption_instagram_inclui_arroba_vereador(self):
        d = _denuncia()
        v = _vereador(instagram="joaodasilva_bh")
        caption = gerar_caption_instagram(d, vereador=v)
        assert "@joaodasilva_bh" in caption

    def test_caption_instagram_sem_instagram_omite_arroba(self):
        d = _denuncia(vereador_instagram=None)
        v = _vereador(instagram=None)
        caption = gerar_caption_instagram(d, vereador=v)
        # Deve usar o nome em vez do @handle
        assert "@None" not in caption
        assert "JOÃO DA SILVA" in caption

    def test_caption_contem_hashtags(self):
        d = _denuncia(bairro="Savassi", categoria="buraco_pavimento")
        caption = gerar_caption_instagram(d)
        assert "#MacaCoCidadão" in caption
        assert "#BH" in caption
        assert "#Savassi" in caption
        assert "#buracopavimento" in caption

    def test_caption_secretaria_com_instagram(self):
        d = _denuncia()
        v = _vereador()
        secretaria = {"slug": "smobi", "nome": "SMOBI", "instagram": "pbhoficial"}
        caption = gerar_caption_instagram(d, vereador=v, secretaria=secretaria)
        assert "@pbhoficial" in caption
