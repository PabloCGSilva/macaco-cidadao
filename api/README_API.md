# Macaco Cidadão — API REST

Base URL: `http://localhost:5000`

Spec completa (auto-gerada): `GET /openapi/openapi.json`  
Swagger UI: `GET /openapi/`  
ReDoc: `GET /openapi/redoc`

---

## Autenticação

Todos os endpoints, exceto `/api/v1/health`, requerem autenticação via sessão de cookie (mesmo login do painel web em `/login`).

---

## Endpoints

### `GET /api/v1/health`

Sem autenticação. Verifica se a API está online.

```json
{ "status": "ok", "version": "1.0.0" }
```

---

### `GET /api/v1/denuncias`

Lista denúncias com paginação.

| Parâmetro | Tipo    | Default | Descrição                                              |
|-----------|---------|---------|--------------------------------------------------------|
| `status`  | string  | —       | Filtro: `aguardando_triagem`, `aprovada`, `rejeitada`, `publicada` |
| `page`    | integer | 1       | Página                                                 |
| `per_page`| integer | 20      | Itens por página (máx. 100)                            |

**Resposta 200:**
```json
{
  "total": 42,
  "page": 1,
  "per_page": 20,
  "items": [{ "id": 1, "protocolo": "MC-240101-0001", "status": "aprovada", ... }]
}
```

---

### `GET /api/v1/denuncias/{id}`

Retorna uma denúncia pelo ID. 404 se não encontrada.

---

### `POST /api/v1/denuncias/{id}/aprovar`

Aprova uma denúncia.

**Body (JSON):**
```json
{
  "notas": "Denúncia válida e relevante.",
  "minuta_email": "Texto personalizado do e-mail formal (opcional)",
  "texto_post": "Texto revisado para publicação (opcional)"
}
```

**Resposta 200:**
```json
{ "ok": true, "protocolo": "MC-240101-0001", "status": "aprovada" }
```

---

### `POST /api/v1/denuncias/{id}/rejeitar`

Rejeita uma denúncia. O campo `motivo` é obrigatório (mín. 1 caractere).

**Body (JSON):**
```json
{ "motivo": "Denúncia duplicada." }
```

**Resposta 200:**
```json
{ "ok": true, "protocolo": "MC-240101-0001", "status": "rejeitada" }
```

---

### `GET /api/v1/scorecard`

Retorna métricas de responsividade por vereador (baseado em denúncias publicadas).

**Resposta 200:**
```json
[
  {
    "vereador": "LUIZA BORGES DULCI",
    "total": 5,
    "cobrou": 3,
    "respondeu_sem_acao": 1,
    "ignorou": 0,
    "pendente": 1
  }
]
```

---

### `GET /api/v1/vereadores`

Lista todos os vereadores em ordem alfabética.

**Resposta 200:**
```json
[
  {
    "id": 1,
    "nome": "LUIZA BORGES DULCI",
    "partido": "PT",
    "email_gabinete": "ver.luizadulci@cmbh.mg.gov.br",
    "instagram": "luizadulci",
    "votos_totais_2024": 12345,
    "bairros_base": "[\"Serra\", \"Funcionários\"]"
  }
]
```

---

### `GET /api/v1/vereadores/{id}/bairros`

Retorna os bairros de base de um vereador.

**Resposta 200:**
```json
{
  "id": 1,
  "nome": "LUIZA BORGES DULCI",
  "bairros": ["Serra", "Funcionários", "Santo Agostinho"]
}
```

---

## Códigos de erro

| Código | Significado                        |
|--------|------------------------------------|
| 401    | Não autenticado                    |
| 404    | Recurso não encontrado             |
| 422    | Validação falhou (corpo inválido)  |
