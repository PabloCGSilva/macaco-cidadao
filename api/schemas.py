from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    version: str


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
    criado_em: datetime
    aprovada_em: Optional[datetime] = None
    publicada_em: Optional[datetime] = None
    link_post: Optional[str] = None
    email_enviado: bool = False


class DenunciaPath(BaseModel):
    id: int


class AprovarRequest(BaseModel):
    notas: str = ""
    minuta_email: Optional[str] = None
    texto_post: Optional[str] = None


class RejeitarRequest(BaseModel):
    motivo: str = Field(..., min_length=1)


class ScorecardItem(BaseModel):
    vereador: str
    total: int
    cobrou: int
    respondeu_sem_acao: int
    ignorou: int
    pendente: int


class VereadorResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    nome: str
    partido: Optional[str] = None
    email_gabinete: Optional[str] = None
    instagram: Optional[str] = None
    votos_totais_2024: Optional[int] = None
    bairros_base: Optional[str] = None


class VereadorPath(BaseModel):
    id: int
