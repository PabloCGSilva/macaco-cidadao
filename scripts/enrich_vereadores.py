#!/usr/bin/env python3
"""
enrich_vereadores.py
Cruza o TSE JSON com dados raspados do site CMBH (maio/2026).
Adiciona: partido, email_gabinete, instagram, telefone_gabinete, eleito, fonte.
Complementa bairros_base com padrão regional quando vazio.
"""

import json
import os
import shutil
import unicodedata

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TSE_FILE = os.path.join(BASE_DIR, "data", "vereadores_bh_tse2024.json")
BACKUP_FILE = os.path.join(BASE_DIR, "data", "vereadores_bh_tse2024.backup.json")

# Bairros representativos por regional (fonte: instrução do usuário)
REGIONAL_BAIRROS = {
    "Barreiro": ["Barreiro", "Lindéia", "Flávio Marques Lisboa", "Milionários"],
    "Centro-Sul": ["Serra", "Funcionários", "Santo Agostinho", "Lourdes", "Barro Preto"],
    "Leste": ["Santa Efigênia", "Sagrada Família", "Santa Inês", "Horto"],
    "Nordeste": ["Floresta", "Santa Tereza", "Taquaril", "Ribeiro de Abreu"],
    "Noroeste": ["Lagoinha", "Carlos Prates", "Caiçara", "Padre Eustáquio"],
    "Norte": ["Floramar", "São Bernardo", "Primeiro de Maio", "Tupi"],
    "Oeste": ["Gameleira", "Nova Gameleira", "Prado", "Gutierrez", "Buritis"],
    "Pampulha": ["Pampulha", "Castelo", "Itapoã", "São Luís", "Ouro Preto"],
    "Venda Nova": ["Venda Nova", "Mantiqueira", "Jardim Leblon", "Candelária"],
}

# (tse_nome_uppercase, partido, email_gabinete, instagram_handle, telefone)
# Fonte: cmbh.mg.gov.br/vereadores, scrape realizado em 14/05/2026
CMBH_ENRICHMENTS = [
    ("PHABLO GOMES ALMEIDA",                   "PL",            "ver.pabloalmeida@cmbh.mg.gov.br",          "pabloalmeidabh",              "(31) 3555-1178"),
    ("MARLI APARECIDA DE ARO FERREIRA",        "PP",            "ver.professoramarli@cmbh.mg.gov.br",       "professora.marli",            "(31) 3555-1176"),
    ("IZABELLA LOURENÇA AMORIM ROMUALDO",      "PSOL",          "ver.izalourenca@cmbh.mg.gov.br",           "izalourenca",                 "(31) 3555-1205"),
    ("FERNANDA ELISA PEREIRA ALTOÉ",           "NOVO",          "ver.fernandapereira@cmbh.mg.gov.br",       "fernandapereiraaltoe",        "(31) 3555-1159"),
    ("MARCELA DE LACERDA TRÓPIA",              "NOVO",          "ver.marcelatropia@cmbh.mg.gov.br",         "marcelatropia",               "(31) 3555-1168"),
    ("PEDRO FARAH ROUSSEFF",                   "PT",            "ver.pedrorousseff@cmbh.mg.gov.br",         "pedrorousseff",               "(31) 3555-1182"),
    ("FLAVIA FERREIRA BORJA PINTO",            "PODE",          "ver.flaviaborja@cmbh.mg.gov.br",           "flaviaborjaoficial",          "(31) 3555-1184"),
    ("WILI DOS SANTOS",                        "PL",            "ver.vile@cmbh.mg.gov.br",                  "vilebr",                      "(31) 3555-1418"),
    ("UNER AUGUSTO DE CARVALHO ALVARENGA",     "PL",            "ver.uneraugusto@cmbh.mg.gov.br",           "uneraugusto",                 "(31) 3555-1188"),
    ("IRLAN CHAVES DE OLIVEIRA MELO",          "PL",            "ver.irlanmelo@cmbh.mg.gov.br",             "irlan.melo",                  "(31) 3555-1153"),
    ("WAGNER MARIANO JUNIOR",                  "AVANTE",        "ver.juninholoshermanos@cmbh.mg.gov.br",    "juninholoshermanos",          "(31) 3555-1151"),
    ("WAGNER DE JESUS FERREIRA",               "REDE",          "ver.wagnerferreira@cmbh.mg.gov.br",        "euwagnerferreira",            "(31) 3472-9077"),
    ("BRUNO ABREU GOMES",                      "PT",            "ver.brunopedralva@cmbh.mg.gov.br",         "brunopedralvabh",             "(31) 3472-9193"),
    ("LUCAS DO CARMO NAVARRO",                 "MDB",           "ver.lucasganem@cmbh.mg.gov.br",            "lucasganem.mg",               "(31) 3555-1157"),
    ("OSVALDO LOPES DE OLIVEIRA JUNIOR",       "PODE",          "ver.osvaldolopes@cmbh.mg.gov.br",          "osvaldolopescba",             "(31) 3555-1352"),
    ("ELIZETE LOIDE GONÇALVES TAVARES",        "MDB",           "ver.loidegoncalves@cmbh.mg.gov.br",        "loidegoncalvesoficial",       "(31) 3555-1155"),
    ("LUIZA BORGES DULCI",                     "PT",            "ver.luizadulci@cmbh.mg.gov.br",            "luizadulci",                  "(31) 3555-1128"),
    ("BRAULIO ALVES SILVA LARA",               "NOVO",          "ver.brauliolara@cmbh.mg.gov.br",           "brauliolaranovo",             "(31) 3555-1307"),
    ("JOSE DE JESUS FERREIRA",                 "PODE",          "ver.joseferreira@cmbh.mg.gov.br",          "joseferreira.projetoajudai",  "(31) 3555-1145"),
    ("EDMAR MARTINS CABRAL DA CRUZ",           "PCdoB",         "ver.edmarbranco@cmbh.mg.gov.br",           "edmar.branco",                "(31) 3555-1126"),
    ("JULIANO LOPES LOBATO",                   "PODE",          "ver.julianolopes@cmbh.mg.gov.br",          "professorjulianolopes",       "(31) 3555-1301"),
    ("WANDERLEY DE ARAUJO PORTO FILHO",        "PRD",           "ver.wanderleyporto@cmbh.mg.gov.br",        "wanderleyporto",              "(31) 3555-1191"),
    ("BRUNO MARTUCHELE DE SALES",              "PDT",           "ver.brunomiranda@cmbh.mg.gov.br",          "brunomirandasales",           "(31) 3555-1330"),
    ("ENEDINO JOSÉ DE ARRUDA",                 "REPUBLICANOS",  "ver.arruda@cmbh.mg.gov.br",                None,                          "(31) 3555-1305"),
    ("CLAUDIO MOTA CAMPOS",                    "PL",            "ver.claudiodomundonovo@cmbh.mg.gov.br",    "claudiodomundonovo",          "(31) 3555-1413"),
    ("HÉLIO MEDEIROS CORREA",                  "PSD",           "ver.heliodafarmacia@cmbh.mg.gov.br",       "vereadorhelinhobh",           "(31) 3555-1186"),
    ("HELTON VIEIRA FERNANDES JUNIOR",         "PSD",           "ver.heltonjunior@cmbh.mg.gov.br",          "heltonjuniorbh",              "(31) 3472-9355"),
    ("JANAINA ESTER CARDOSO",                  "UNIÃO",         "ver.janainacardoso@cmbh.mg.gov.br",        "janainaecardoso",             "(31) 3555-1202"),
    ("PEDRO LUIZ NEVES VICTER ANANIAS",        "PT",            "ver.pedropatrus@cmbh.mg.gov.br",           "pedro_patrus",                "(31) 3555-1323"),
    ("CLEITON XAVIER DA SILVA",                "UNIÃO",         "ver.cleitonxavier@cmbh.mg.gov.br",         "cleitonxavierpc",             "(31) 3555-1147"),
    ("JALYSON MAYCON GONCALVES",               "PL",            "ver.sargentojalyson@cmbh.mg.gov.br",       "sgt_jalyson",                 "(31) 3555-9360"),
    ("GLAUTON SANTIAGO FÉLIX DE JESUS",        "PSD",           "ver.maninhofelix@cmbh.mg.gov.br",          "maninho.felix",               "(31) 3472-9240"),
    ("JUHLIA ANDRÉ SANTOS",                    "PSOL",          "ver.juhliasantos@cmbh.mg.gov.br",          "juhliasantost",               "(31) 3555-1420"),
    ("RUDSON FELIPE DA PAIXÃO",                "SOLIDARIEDADE", "ver.rudsonpaixao@cmbh.mg.gov.br",          "rudsonpaixaobh",              "(31) 3555-1200"),
    ("MICHELLY CAROLINE LUIZ PEREIRA DE SIQUEIRA", "PRD",       "ver.dramichellysiqueira@cmbh.mg.gov.br",   "michelysiqueira",             "(31) 3472-9055"),
    ("MARILDA DE CASTRO PORTELA",              "PL",            "ver.marildaportela@cmbh.mg.gov.br",        "marildaportela.bh",           "(31) 3555-1172"),
    ("DIEGO DE SOUZA SANCHES",                 "SOLIDARIEDADE", "ver.diegosanches@cmbh.mg.gov.br",          "diegosanchesbh",              "(31) 3555-1426"),
    ("LEONARDO ÂNGELO DA SILVA",               "CIDADANIA",     "ver.leonardoangelo@cmbh.mg.gov.br",        "leonardoangelobh",            "(31) 3555-1166"),
    ("NARA LUCIA DE PAULA FAN",                "REDE",          "ver.professoranara@cmbh.mg.gov.br",        "professoranarabh",            "(31) 3555-1150"),
    ("LEONARDO JOSÉ RODRIGUES MARTINS",        "PP",            "ver.tileleo@cmbh.mg.gov.br",               "tileleo",                     "(31) 3555-9013"),
]

# Vereador eleito que não consta no top-70 do TSE (eleito por quociente partidário)
CMBH_ONLY_ENTRIES = [
    {
        "nome": "MOZAIR JOSÉ BRAGA",
        "partido": "MOBILIZA",
        "regional": "Venda Nova",
        "bairros_base": ["Venda Nova", "Mantiqueira", "Jardim Leblon", "Candelária"],
        "votos_total": 0,
        "email_gabinete": "ver.nenemdafarmacia@cmbh.mg.gov.br",
        "instagram": "nenemdafarmaciaoficial",
        "telefone_gabinete": "(31) 3555-1161",
        "eleito": True,
        "fonte": "cmbh_scrape_2026",
    }
]

# Entradas que são legendas de partido (não são pessoas)
PARTY_ENTRIES = {
    "Partido Liberal", "Partido dos Trabalhadores", "Partido Social Democrático",
    "REPUBLICANOS",
}


def _norm(nome: str) -> str:
    """Normaliza para uppercase sem acentos para comparação."""
    nfkd = unicodedata.normalize("NFKD", nome)
    ascii_str = nfkd.encode("ascii", "ignore").decode("ascii")
    return ascii_str.upper().strip()


def _is_person(nome: str) -> bool:
    if nome in PARTY_ENTRIES:
        return False
    # Entradas de pessoa no TSE são sempre CAIXA ALTA; legendas têm minúsculas
    return nome == nome.upper() and len(nome.split()) >= 2


def enrich():
    # Cria backup
    shutil.copy2(TSE_FILE, BACKUP_FILE)
    print(f"Backup salvo em: {BACKUP_FILE}")

    with open(TSE_FILE, encoding="utf-8") as f:
        dados = json.load(f)

    # Monta dicionário de enriquecimento: norm(tse_nome) → dados CMBH
    enriquecimentos = {}
    for row in CMBH_ENRICHMENTS:
        tse_nome, partido, email, instagram, telefone = row
        enriquecimentos[_norm(tse_nome)] = {
            "partido": partido,
            "email_gabinete": email,
            "instagram": instagram,
            "telefone_gabinete": telefone,
        }

    matches = 0
    sem_match = []

    saida = []
    for entry in dados:
        nome = entry.get("nome", "")

        # Remove entradas de legenda
        if not _is_person(nome):
            print(f"  [SKIP] Legenda: {nome}")
            continue

        chave = _norm(nome)
        if chave in enriquecimentos:
            cmbh = enriquecimentos[chave]
            entry["partido"] = cmbh["partido"]
            entry["email_gabinete"] = cmbh["email_gabinete"]
            entry["instagram"] = cmbh["instagram"]
            entry["telefone_gabinete"] = cmbh["telefone_gabinete"]
            entry["eleito"] = True
            entry["fonte"] = "cmbh_scrape_2026"
            matches += 1
        else:
            entry["eleito"] = False
            entry.setdefault("partido", "")
            sem_match.append(nome)

        # Completa bairros_base com defaults regionais se vazio
        if not entry.get("bairros_base"):
            regional = entry.get("regional", "")
            entry["bairros_base"] = REGIONAL_BAIRROS.get(regional, [])

        saida.append(entry)

    # Adiciona entradas CMBH que não estavam no TSE
    for extra in CMBH_ONLY_ENTRIES:
        if not extra.get("bairros_base"):
            extra["bairros_base"] = REGIONAL_BAIRROS.get(extra.get("regional", ""), [])
        saida.append(extra)
        print(f"  [ADD]  Entrada nova (CMBH-only): {extra['nome']}")

    with open(TSE_FILE, "w", encoding="utf-8") as f:
        json.dump(saida, f, ensure_ascii=False, indent=2)

    # Relatório
    eleitos = [e for e in saida if e.get("eleito")]
    nao_eleitos = [e for e in saida if not e.get("eleito")]
    com_email = [e for e in saida if e.get("email_gabinete")]
    com_partido = [e for e in saida if e.get("partido")]
    com_bairros = [e for e in saida if e.get("bairros_base")]

    print(f"\n{'='*60}")
    print(f"RELATÓRIO DE ENRIQUECIMENTO")
    print(f"{'='*60}")
    print(f"Total de entradas na saída:     {len(saida)}")
    print(f"  Eleitos (eleito=true):         {len(eleitos)}")
    print(f"  Não eleitos (eleito=false):    {len(nao_eleitos)}")
    print(f"  Com email_gabinete:            {len(com_email)}")
    print(f"  Com partido:                   {len(com_partido)}")
    print(f"  Com bairros_base:              {len(com_bairros)}")
    print(f"\nMatches TSE × CMBH:            {matches}/{len(CMBH_ENRICHMENTS)}")

    if sem_match:
        print(f"\nTSE entries sem match CMBH ({len(sem_match)}):")
        for n in sem_match:
            print(f"  - {n}")

    print(f"\nArquivo atualizado: {TSE_FILE}")


if __name__ == "__main__":
    enrich()
