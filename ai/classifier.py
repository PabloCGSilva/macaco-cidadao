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
Registro enviado por cidadão. Verificação em andamento.
#MacacoCidadão #BH #[Bairro]"""


def classificar(descricao: str, bairro: str, tem_midia: bool, coordenadas: str | None) -> dict:
    prompt = CLASSIFICACAO_PROMPT.format(
        descricao=descricao,
        bairro=bairro or "não informado",
        tem_midia="sim" if tem_midia else "não",
        coordenadas=coordenadas or "não disponível",
    )

    response = _client.messages.create(
        model=config.CLAUDE_MODEL,
        max_tokens=1500,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )

    text = response.content[0].text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    return json.loads(text)
