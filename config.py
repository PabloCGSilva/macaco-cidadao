import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.environ["SMTP_USER"]
SMTP_PASSWORD = os.environ["SMTP_PASSWORD"]
EMAIL_FROM = os.getenv("EMAIL_FROM", SMTP_USER)

FLASK_SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "dev-secret-key")
PANEL_USERNAME = os.getenv("PANEL_USERNAME", "moderador")
PANEL_PASSWORD = os.getenv("PANEL_PASSWORD", "senha123")

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///macaco_cidadao.db")

ANTHROPIC_MODEL = "claude-haiku-4-5-20251001"

CATEGORIAS = [
    "buraco_pavimento",
    "iluminacao_publica",
    "lixo_entulho",
    "calcada_acessibilidade",
    "obra_irregular",
    "arvore_risco",
    "enchente_drenagem",
    "transporte_onibus",
    "pichacao_vandalismo",
    "outros",
]

SECRETARIAS_POR_CATEGORIA = {
    "buraco_pavimento": ("SUDECAP", "sudecap@pbh.gov.br"),
    "iluminacao_publica": ("CEMIG / SLU", "ouvidoria@pbh.gov.br"),
    "lixo_entulho": ("SLU", "slu@pbh.gov.br"),
    "calcada_acessibilidade": ("SUDECAP", "sudecap@pbh.gov.br"),
    "obra_irregular": ("SMARU", "smaru@pbh.gov.br"),
    "arvore_risco": ("SMMA", "smma@pbh.gov.br"),
    "enchente_drenagem": ("SUDECAP", "sudecap@pbh.gov.br"),
    "transporte_onibus": ("BHTRANS", "bhtrans@pbh.gov.br"),
    "pichacao_vandalismo": ("SMPU", "smpu@pbh.gov.br"),
    "outros": ("Ouvidoria PBH", "ouvidoria@pbh.gov.br"),
}

OUVIDORIA_CAMARA_EMAIL = "ouvidoria@cmbh.mg.gov.br"

FOLLOW_UP_DIAS_ALERTA = 3
FOLLOW_UP_DIAS_COBRANCA = 10
