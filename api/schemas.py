from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    version: str
    db_ok: bool


class DenunciaListQuery(BaseModel):
    status: Optional[str] = None
    page: int = Field(1, ge=1)
    per_page: int = Field(20, ge=1, le=100)


class DenunciaResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    protocolo: str
    status: str
    bairro: Optional[str] = None
    regional: Optional[str] = None
    categoria: Optional[str] = None
    descricao_usuario: Optional[str] = None
    vereador_nome: Optional[str] = None
    vereador_email: Optional[str] = None
    secretaria_nome: Optional[str] = None
    secretaria_slug: Optional[str] = None
    criado_em: datetime
    aprovada_em: Optional[datetime] = None
    publicada_em: Optional[datetime] = None
    link_post: Optional[str] = None
    email_enviado: bool = False
    whatsapp_enviado: bool = False
    instagram_marcado: bool = False


class DenunciaPublicaResponse(BaseModel):
    """Versão pública de denúncia — sem dados pessoais do cidadão."""
    model_config = {"from_attributes": True}

    id: int
    protocolo: str
    bairro: Optional[str] = None
    regional: Optional[str] = None
    categoria: Optional[str] = None
    descricao_usuario: Optional[str] = None
    publicada_em: Optional[datetime] = None
    link_post: Optional[str] = None
    classificacao_scorecard: Optional[str] = None


class DenunciaPath(BaseModel):
    id: int


class AprovarRequest(BaseModel):
    notas: str = ""
    minuta_email: Optional[str] = None
    texto_post: Optional[str] = None


class RejeitarRequest(BaseModel):
    motivo: str = Field(..., min_length=1)


class RegistrarAcaoRequest(BaseModel):
    acao: str = Field(..., pattern="^(whatsapp_vereador|whatsapp_secretaria|instagram)$")


class ScorecardItem(BaseModel):
    vereador: str
    total: int
    cobrou: int
    respondeu_sem_acao: int
    ignorou: int
    pendente: int
    tempo_medio_resolucao_dias: Optional[float] = None
    denuncias_sem_resposta_30d: int = 0
    ultima_denuncia_data: Optional[datetime] = None


class ScorecardVereadorPath(BaseModel):
    vereador_id: int


class VereadorResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    nome: str
    partido: Optional[str] = None
    email_gabinete: Optional[str] = None
    instagram: Optional[str] = None
    whatsapp_gabinete: Optional[str] = None
    votos_totais_2024: Optional[int] = None
    bairros_base: Optional[str] = None


class VereadorPath(BaseModel):
    id: int
