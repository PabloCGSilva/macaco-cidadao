import json
import anthropic
import config

_client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)

SYSTEM_PROMPT = """Você é o sistema de triagem do Macaco Cidadão, plataforma cívica de accountability urbano de Belo Horizonte.

Sua função é classificar denúncias de cidadãos sobre problemas de infraestrutura e serviços públicos.

Regras de validação:
- VÁLIDA: problema de infraestrutura pública verificável, com foto/vídeo e localização identificável, competência municipal
- INVÁLIDA: conflito privado, sem evidência visual, localização não identificável, identificação negativa de pessoa física

Categorias disponíveis: buraco_pavimento, iluminacao_publica, lixo_entulho, calcada_acessibilidade, obra_irregular, arvore_risco, enchente_drenagem, transporte_onibus, pichacao_vandalismo, outros

Tom dos posts: cobrança dentro do papel constitucional do vereador (cobra o Executivo), nunca acusação direta.
Fórmula correta: "Vereador X, sua base eleitoral no bairro Y registrou esse problema. O que você já cobrou da Prefeitura sobre isso?"

Responda SEMPRE em JSON válido com exatamente os campos especificados."""

CLASSIFICACAO_PROMPT = """Classifique esta denúncia urbana de BH:

Descrição do usuário: {descricao}
Bairro informado: {bairro}
Tem foto/vídeo: {tem_midia}
Coordenadas GPS: {coordenadas}
Denúncias anteriores no mesmo local: {denuncias_anteriores}

Responda em JSON com exatamente estes campos:
{{
  "valida": true/false,
  "motivo_invalidade": "string ou null",
  "categoria": "categoria ou null",
  "bairro_confirmado": "string",
  "regional": "string (Centro-Sul/Leste/Nordeste/Norte/Noroeste/Oeste/Pampulha/Barreiro/Venda Nova)",
  "canal_correto": "null ou '156' ou 'Procon' ou 'Polícia'",
  "texto_post": "string (se válida) ou null",
  "assunto_email": "string (se válida) ou null",
  "corpo_email": "string (se válida) ou null",
  "agrupamento_sugerido": "string descrevendo o problema para busca de duplicatas"
}}

Para o texto_post, use o formato:
📍 [Bairro] | [Categoria em linguagem simples]
[Descrição objetiva do problema em 1-2 frases]
Se houver denúncias anteriores, indique: "⚠️ Reincidência — Nª ocorrência registrada. Protocolos anteriores: MC-XXXX, MC-YYYY."
Registro enviado por cidadão. Verificação em andamento.
#MacacoCidadão #BH #[Bairro]"""


def classificar(
    descricao: str,
    bairro: str,
    tem_midia: bool,
    coordenadas: str | None,
    denuncias_anteriores: list[dict] | None = None,
) -> dict:
    anteriores_str = "nenhuma"
    if denuncias_anteriores:
        itens = [f"{d['protocolo']} ({d['criado_em']})" for d in denuncias_anteriores]
        anteriores_str = f"{len(denuncias_anteriores)} ocorrência(s): " + ", ".join(itens)

    prompt = CLASSIFICACAO_PROMPT.format(
        descricao=descricao,
        bairro=bairro or "não informado",
        tem_midia="sim" if tem_midia else "não",
        coordenadas=coordenadas or "não disponível",
        denuncias_anteriores=anteriores_str,
    )

    response = _client.messages.create(
        model=config.ANTHROPIC_MODEL,
        max_tokens=1500,
        # Cache the static system prompt — saves ~US$0.002 per call after first request
        system=[{"type": "text", "text": SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}}],
        messages=[{"role": "user", "content": prompt}],
    )

    text = response.content[0].text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    return json.loads(text)
