# 🐒 Macaco Cidadão

Plataforma cívica de **accountability urbano** para Belo Horizonte.

Cidadãos enviam denúncias de infraestrutura via Telegram. A IA classifica, identifica o vereador responsável pelo bairro, e publica nas redes sociais com **notificação formal simultânea ao gabinete** — criando lastro documental para o Scorecard Mensal de Responsividade.

> "Não é página de reclamação — é sistema de accountability com dados."

---

## Como funciona

```text
Cidadão envia foto/vídeo/texto no Telegram
    ↓
Bot gera protocolo e extrai GPS do EXIF
    ↓
Claude Haiku classifica: categoria, bairro, regional, vereador
    ↓
Se inválida → cidadão recebe redirecionamento (156, Procon, Polícia)
    ↓
Se válida → entra no painel de moderação
    ↓
Moderador revisa texto do post + minuta do e-mail
    ↓
Aprovação → publicação manual no Instagram/X
             + e-mail formal ao gabinete + secretaria + ouvidoria da Câmara
             + notificação ao cidadão com link do post
    ↓
Scheduler verifica follow-ups: 3 dias / 10 dias úteis sem resposta
    ↓
Scorecard mensal: ✅ Cobrou / ⚠️ Respondeu / ❌ Ignorou
```

---

## Por que o vereador e não a Prefeitura?

Vereador tem mandato para toda a cidade, mas foi eleito com votos de territórios específicos. O mapeamento é eleitoral (dados TSE 2024), não administrativo.

A linguagem correta:

> "Vereador X, sua base eleitoral no bairro Y registrou esse problema. O que você já cobrou da Prefeitura sobre isso?"

Juridicamente precisa (respeita o papel constitucional), politicamente difícil de ignorar.

---

## Stack

| Componente | Tecnologia |
| --- | --- |
| Bot de recebimento | [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) 21.6 |
| Extração GPS | Pillow + exifread |
| Classificação + post + e-mail | Claude Haiku (`claude-haiku-4-5-20251001`) via Anthropic SDK |
| Painel de moderação | Flask 3 + Flask-SQLAlchemy |
| Banco de dados | SQLite (MVP) → PostgreSQL (produção) |
| Follow-up scheduler | APScheduler 3.10 |
| Notificação ao cidadão | Telegram Bot API (HTTP direto via httpx) |
| Envio de e-mail formal | SMTP (Gmail App Password ou SendGrid) |
| Storage de mídia | Disco local (`uploads/`) → Cloudflare R2 (produção) |

---

## Estrutura do projeto

```text
macaco-cidadao/
├── bot/
│   ├── handlers.py          # Fluxo de conversa Telegram (3 estados)
│   ├── exif_extractor.py    # Extrai GPS do EXIF da foto
│   └── media_store.py       # Salva mídia em disco com hash SHA-256
├── ai/
│   ├── classifier.py        # Claude Haiku: classifica + gera post + minuta e-mail
│   └── vereador_mapper.py   # Lookup vereador por bairro (via DB)
├── db/
│   ├── models.py            # Denuncia, FollowUp, Vereador
│   ├── protocolo.py         # Gerador MC-2026-XXXXX
│   └── agrupamento.py       # Detecção de reincidências (GPS 200m / bairro+categoria)
├── notifier/
│   ├── email_sender.py      # E-mail formal SMTP com LAI
│   ├── telegram_notifier.py # Notifica cidadão quando publicado
│   └── scheduler.py         # APScheduler: alertas 3d / 10 dias úteis
├── panel/
│   ├── app.py               # Flask: login, triagem, aprovar, publicar, scorecard
│   ├── templates/           # login, painel, detalhe, followups, scorecard
│   └── static/css/style.css # UI dark theme
├── data/
│   ├── pbh_obras.py                 # Integração Portal Dados Abertos PBH (cache 24h)
│   ├── vereadores_bh_exemplo.json   # 10 vereadores de exemplo
│   └── vereadores_bh_tse2024.json   # Gerado por fetch_tse_data.py (dados reais TSE)
├── scripts/
│   ├── fetch_tse_data.py    # Baixa e processa dados eleitorais TSE 2024
│   └── seed_vereadores.py   # Importa JSON de vereadores para o DB
├── config.py
├── requirements.txt
├── run_bot.py               # Inicia o bot Telegram
├── run_panel.py             # Inicia o painel Flask
└── setup.bat                # Setup com um clique (Windows)
```

---

## Instalação e execução

### Pré-requisitos

- Python 3.10+
- Token de bot Telegram (via [@BotFather](https://t.me/BotFather))
- API key da Anthropic (console.anthropic.com)
- Conta de e-mail com SMTP habilitado (Gmail: App Password)

### Setup (Windows)

```bat
git clone https://github.com/PabloCGSilva/macaco-cidadao.git
cd macaco-cidadao
setup.bat
```

O script cria o virtualenv, instala dependências e gera o `.env`.

### Setup (Linux/macOS)

```bash
git clone https://github.com/PabloCGSilva/macaco-cidadao.git
cd macaco-cidadao
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

### Configurar o `.env`

```env
TELEGRAM_BOT_TOKEN=seu_token_aqui
ANTHROPIC_API_KEY=sua_chave_aqui
SMTP_USER=seu_email@gmail.com
SMTP_PASSWORD=sua_app_password
PANEL_USERNAME=moderador
PANEL_PASSWORD=senha_segura
```

### Importar vereadores

```bash
# Exemplo com os dados de demonstração incluídos
python scripts/seed_vereadores.py data/vereadores_bh_exemplo.json

# Com dados reais do TSE 2024
python scripts/seed_vereadores.py data/vereadores_bh_tse2024.json
```

### Rodar

```bash
# Terminal 1 — painel de moderação
python run_panel.py
# Acesse: http://localhost:5000

# Terminal 2 — bot Telegram
python run_bot.py
```

---

## Painel de moderação

| Seção | Função |
| --- | --- |
| **Denúncias › Triagem** | Revisar classificação da IA, editar texto do post e minuta do e-mail |
| **Denúncias › Aprovadas** | Publicar manualmente no Instagram/X e confirmar o link |
| **Denúncias › Publicadas** | Registrar resposta do vereador, classificar no scorecard |
| **Follow-ups** | Alertas gerados automaticamente: 3 dias e 10 dias úteis sem resposta |
| **Scorecard** | Ranking de responsividade por vereador |

Ao confirmar a publicação, o sistema dispara **simultaneamente**:

1. E-mail formal ao gabinete + secretaria competente + ouvidoria da Câmara
2. Mensagem de retorno ao cidadão via Telegram com o link do post

---

## E-mail formal

Todo e-mail enviado inclui:

- Número de protocolo interno (`MC-2026-XXXXX`)
- Coordenadas GPS quando disponíveis
- Pergunta central: *"O que V.Sa. já cobrou ou pretende cobrar da Prefeitura sobre este problema?"*
- Prazo de resposta: **10 dias úteis**
- Fundamentação: art. 5º, XXXIII da CF + Lei 12.527/2011 (LAI)
- Informação de que a denúncia já foi publicada nas redes sociais

---

## Scorecard mensal

Publicado todo primeiro dia do mês. Cada vereador tagado é classificado em:

| Categoria | Critério |
| --- | --- |
| ✅ Cobrou a Prefeitura | Registro público de cobrança documentada |
| ⚠️ Respondeu sem ação | Acusou recebimento mas sem ação verificável |
| ❌ Ignorou | Sem resposta dentro de 10 dias úteis |

Lastro documental: não é percepção, são protocolos rastreáveis.

---

## Proteção jurídica

- Disclaimer em todo post: *"Registro enviado por cidadão. Verificação em andamento."*
- Moderação humana obrigatória antes de qualquer publicação
- Foco exclusivo em infraestrutura e serviços públicos municipais
- Linguagem de cobrança dentro do papel constitucional do vereador (nunca acusação direta)
- Log completo com timestamp e hash SHA-256 da mídia original
- Comprovante de cada e-mail enviado armazenado no banco

---

## Dataset de Vereadores (TSE 2024)

O script `scripts/fetch_tse_data.py` processa os dados eleitorais oficiais do TSE 2024 para BH e gera `data/vereadores_bh_tse2024.json` com os candidatos reais, total de votos e regional de maior votação.

```bash
# Baixa 191 MB do TSE, processa e gera JSON com top 70 candidatos
python scripts/fetch_tse_data.py --cache-dir ./data/tse_cache

# Com geocodificação Nominatim (mais preciso, ~10 min)
python scripts/fetch_tse_data.py --cache-dir ./data/tse_cache --geocode

# Importar no banco
python scripts/seed_vereadores.py data/vereadores_bh_tse2024.json
```

**Próximos passos manuais:** preencher `email_gabinete`, `instagram` e `bairros_base` para os 41 eleitos. Fonte: [cmbh.mg.gov.br/vereadores](https://www.cmbh.mg.gov.br/vereadores)

---

## Integração com Obras PBH

O módulo `data/pbh_obras.py` consome o [Portal de Dados Abertos da PBH](https://dados.pbh.gov.br/dataset/obras-publicas_2) via API CKAN e retorna obras públicas da regional da denúncia.

No painel de moderação, a tela de detalhe de cada denúncia exibe automaticamente os contratos e obras SUDECAP relacionados à mesma regional e categoria — permitindo ao moderador incluir no post: *"Existe contrato de manutenção desta regional — o problema persiste."*

O cache é renovado a cada 24h sem necessidade de configuração adicional.

---

## Agrupamento de Denúncias

Denúncias do mesmo local (raio de 200m por GPS, ou mesmo bairro + categoria) são automaticamente agrupadas dentro de uma janela de 90 dias. O sistema:

- Passa as denúncias anteriores ao Claude Haiku antes de gerar o texto do post
- O Claude indica reincidência no texto: *"⚠️ 2ª ocorrência registrada. Protocolo anterior: MC-XXXX"*
- O painel exibe a sequência dentro do grupo na tela de detalhe

---

## Roadmap

- [ ] Preencher `email_gabinete` e `instagram` dos 41 vereadores eleitos no JSON TSE
- [ ] Publicação automática no Instagram via API
- [ ] Storage de mídia no Cloudflare R2
- [ ] Scorecard público como página estática (geração mensal automática)
- [ ] Replicação para outras cidades (configuração por município)
- [ ] Transcrição de áudio via OpenAI Whisper

---

## Contexto

Projeto inspirado no comentário viral de Samuel Rosa ("PACATO cidadão") e no modelo do canal do Otário. Referências de posicionamento: Banksy, Don Pixote.

BH tem 41 vereadores, 9 regionais e 1 fiscal para cada 7.000 moradores. A fiscalização opera exclusivamente por demanda — sem denúncia, sem ação.

---

## Licença

MIT
