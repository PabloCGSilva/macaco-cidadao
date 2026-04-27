from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Denuncia(db.Model):
    __tablename__ = "denuncias"

    id = db.Column(db.Integer, primary_key=True)
    protocolo = db.Column(db.String(20), unique=True, nullable=False)
    telegram_user_id = db.Column(db.String(50), nullable=False)
    telegram_username = db.Column(db.String(100))
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

    # Mídia
    tipo_midia = db.Column(db.String(20))  # photo, video, audio, text
    arquivo_path = db.Column(db.String(500))
    midia_hash = db.Column(db.String(64))
    descricao_usuario = db.Column(db.Text)

    # Geolocalização
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    endereco = db.Column(db.String(500))
    bairro = db.Column(db.String(100))
    regional = db.Column(db.String(100))

    # Classificação AI
    categoria = db.Column(db.String(50))
    valida = db.Column(db.Boolean)
    motivo_invalidade = db.Column(db.Text)
    vereador_nome = db.Column(db.String(200))
    vereador_email = db.Column(db.String(200))
    vereador_instagram = db.Column(db.String(100))
    vereador_twitter = db.Column(db.String(100))
    secretaria_nome = db.Column(db.String(200))
    secretaria_email = db.Column(db.String(200))
    texto_post_sugerido = db.Column(db.Text)
    minuta_email = db.Column(db.Text)
    denuncia_anterior_protocolo = db.Column(db.String(20))
    # ID da denúncia original do grupo (None = esta é a original)
    grupo_id = db.Column(db.Integer, db.ForeignKey("denuncias.id"), nullable=True)
    grupo_seq = db.Column(db.Integer, default=1)  # posição dentro do grupo (1, 2, 3...)

    # Moderação
    status = db.Column(db.String(30), default="aguardando_triagem")
    # aguardando_triagem | aprovada | rejeitada | publicada
    moderador_notas = db.Column(db.Text)
    aprovada_em = db.Column(db.DateTime)

    # Publicação
    publicada_em = db.Column(db.DateTime)
    link_post = db.Column(db.String(500))
    email_enviado_em = db.Column(db.DateTime)
    email_enviado = db.Column(db.Boolean, default=False)

    # Notificação ao usuário
    telegram_notificado = db.Column(db.Boolean, default=False)

    # Follow-up
    resposta_vereador = db.Column(db.Text)
    resposta_em = db.Column(db.DateTime)
    resolvida_em = db.Column(db.DateTime)
    classificacao_scorecard = db.Column(db.String(30))
    # cobrou_prefeitura | respondeu_sem_acao | ignorou

    followups = db.relationship("FollowUp", backref="denuncia", lazy=True)

    def __repr__(self):
        return f"<Denuncia {self.protocolo}>"


class FollowUp(db.Model):
    __tablename__ = "followups"

    id = db.Column(db.Integer, primary_key=True)
    denuncia_id = db.Column(db.Integer, db.ForeignKey("denuncias.id"), nullable=False)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    tipo = db.Column(db.String(30))  # alerta_3d | cobranca_10d | resposta | resolucao
    texto = db.Column(db.Text)
    publicado = db.Column(db.Boolean, default=False)


class Vereador(db.Model):
    __tablename__ = "vereadores"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(200), nullable=False)
    partido = db.Column(db.String(50))
    email_gabinete = db.Column(db.String(200))
    instagram = db.Column(db.String(100))
    twitter = db.Column(db.String(100))
    bairros_base = db.Column(db.Text)  # JSON list of bairros
    votos_totais_2024 = db.Column(db.Integer)

    def __repr__(self):
        return f"<Vereador {self.nome}>"
