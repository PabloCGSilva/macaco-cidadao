"""
Cruza dados extraídos de cmbh.mg.gov.br/vereadores/lista-de-contatos
com data/vereadores_bh_tse2024.json e preenche campos em branco.

Chave de matching: instagram handle (único e confiável).
Campos novos: sala, facebook, twitter_x, youtube, site_pessoal.
Campos atualizados: telefone_gabinete (versão completa com múltiplos).
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

JSON_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "vereadores_bh_tse2024.json")

# ── Dados extraídos de cmbh.mg.gov.br/vereadores/lista-de-contatos ─────────
# Chave: instagram handle atual no JSON
# Fonte: https://www.cmbh.mg.gov.br/vereadores/lista-de-contatos (mai/2026)
CMBH = {
    # instagram → {sala, telefone_completo, facebook, twitter_x, youtube, site_pessoal}
    "pabloalmeidabh": {
        "sala": "B-301",
        "telefone_gabinete": "(31) 3555-1178",
        "facebook": None,
        "twitter_x": None,
        "youtube": None,
        "site_pessoal": None,
    },
    "professora.marli": {
        "sala": "B-313",
        "telefone_gabinete": "(31) 3555-1176 / (31) 3555-1177",
        "facebook": "professoramarlioficial",
        "twitter_x": None,
        "youtube": "professora marli",
        "site_pessoal": None,
    },
    "izalourenca": {
        "sala": "B-216",
        "telefone_gabinete": "(31) 3555-1205",
        "facebook": "izalourenca",
        "twitter_x": "Izalourenca",
        "youtube": "izalourenca",
        "site_pessoal": "izalourenca.com.br",
    },
    "fernandapereiraaltoe": {
        "sala": "B-214",
        "telefone_gabinete": "(31) 3555-1159 / (31) 3555-1160",
        "facebook": "fernandaelisa.pereiraaltoe",
        "twitter_x": None,
        "youtube": None,
        "site_pessoal": "fernandapereiraaltoe.com",
    },
    "marcelatropia": {
        "sala": "A-316",
        "telefone_gabinete": "(31) 3555-1168 / (31) 3555-1169",
        "facebook": "marcela.tropia",
        "twitter_x": "marcelatropia",
        "youtube": "marcelatropia",
        "site_pessoal": "marcelatropia.com.br",
    },
    "pedrorousseff": {
        "sala": "A-315",
        "telefone_gabinete": "(31) 3555-1182",
        "facebook": "pedrorousseffmg",
        "twitter_x": "pedrorousseff",
        "youtube": "pedrorousseff",
        "site_pessoal": None,
    },
    "flaviaborjaoficial": {
        "sala": "B-305",
        "telefone_gabinete": "(31) 3555-1184",
        "facebook": "flavia.ferreiraborjapinto",
        "twitter_x": "flaviaborjaofc",
        "youtube": None,
        "site_pessoal": None,
    },
    "vilebr": {
        "sala": "B-320",
        "telefone_gabinete": "(31) 3555-1418",
        "facebook": "vilebr",
        "twitter_x": None,
        "youtube": None,
        "site_pessoal": None,
    },
    "uneraugusto": {
        "sala": "B-308",
        "telefone_gabinete": "(31) 3555-1188",
        "facebook": "uner.augusto",
        "twitter_x": None,
        "youtube": None,
        "site_pessoal": None,
    },
    "irlan.melo": {
        "sala": "A-314",
        "telefone_gabinete": "(31) 3555-1153 / (31) 3555-1154 / (31) 3555-1412 / (31) 3555-1332",
        "facebook": "irlan.melo",
        "twitter_x": "irlanmelo",
        "youtube": "IrlanMelo",
        "site_pessoal": "irlanmelo.com.br",
    },
    "juninholoshermanos": {
        "sala": "A-305",
        "telefone_gabinete": "(31) 3555-1151 / (31) 3555-1152 / (31) 3555-1341 / (31) 3555-1421",
        "facebook": "juninholoshermanosvereador",
        "twitter_x": "jrloshermanos",
        "youtube": None,
        "site_pessoal": None,
    },
    "euwagnerferreira": {
        "sala": "B-312",
        "telefone_gabinete": "(31) 3472-9077",
        "facebook": "euwagnerferreira",
        "twitter_x": "wagnerservidor",
        "youtube": "WagnerFerreiraServidor",
        "site_pessoal": "wagnerferreira.com.br",
    },
    "brunopedralvabh": {
        "sala": "B-318",
        "telefone_gabinete": "(31) 3472-9193",
        "facebook": "brunopedralvabh",
        "twitter_x": "brunopedralva",
        "youtube": "brunopedralva",
        "site_pessoal": None,
    },
    "lucasganem.mg": {
        "sala": "B-311",
        "telefone_gabinete": "(31) 3555-1157",
        "facebook": "lucasganem.mg",
        "twitter_x": None,
        "youtube": None,
        "site_pessoal": None,
    },
    "osvaldolopescba": {
        "sala": "B-314",
        "telefone_gabinete": "(31) 3555-1352",
        "facebook": "osvaldolopescba",
        "twitter_x": None,
        "youtube": None,
        "site_pessoal": None,
    },
    "loidegoncalvesoficial": {
        "sala": "A-310",
        "telefone_gabinete": "(31) 3555-1155",
        "facebook": "loidegoncalvesoficial",
        "twitter_x": None,
        "youtube": None,
        "site_pessoal": None,
    },
    "luizadulci": {
        "sala": "B-321",
        "telefone_gabinete": "(31) 3555-1128",
        "facebook": "luizadulci",
        "twitter_x": "luizadulci",
        "youtube": None,
        "site_pessoal": None,
    },
    "brauliolaranovo": {
        "sala": "A-301",
        "telefone_gabinete": "(31) 3555-1307 / (31) 3555-1308",
        "facebook": "brauliolaranovo",
        "twitter_x": "brauliolaranovo",
        "youtube": "brauliolara",
        "site_pessoal": "brauliolara.com.br",
    },
    "joseferreira.projetoajudai": {
        "sala": "B-306",
        "telefone_gabinete": "(31) 3555-1145",
        "facebook": "jose.ferreira.ajudai",
        "twitter_x": "joseferreirarug",
        "youtube": None,
        "site_pessoal": None,
    },
    "edmar.branco": {
        "sala": "A-312",
        "telefone_gabinete": "(31) 3555-1126",
        "facebook": None,
        "twitter_x": None,
        "youtube": "EdmarBranco",
        "site_pessoal": None,
    },
    "professorjulianolopes": {
        "sala": "B-215",
        "telefone_gabinete": "(31) 3555-1301 / (31) 3555-1302",
        "facebook": "ProfessorJulianoLopes",
        "twitter_x": None,
        "youtube": None,
        "site_pessoal": "julianolopesvereador.com.br",
    },
    "wanderleyporto": {
        "sala": "A-311",
        "telefone_gabinete": "(31) 3555-1191 / (31) 3472-9130",
        "facebook": "wanderley.araujoportofilho",
        "twitter_x": "wanderleyporto4",
        "youtube": "wanderleyporto4",
        "site_pessoal": None,
    },
    "brunomirandasales": {
        "sala": "A-306",
        "telefone_gabinete": "(31) 3555-1330",
        "facebook": "brunomirandaoficial",
        "twitter_x": "brunomirandasal",
        "youtube": None,
        "site_pessoal": None,
    },
    "claudiodomundonovo": {
        "sala": "B-322",
        "telefone_gabinete": "(31) 3555-1413",
        "facebook": "claudiodomundonovo",
        "twitter_x": "claudiomnovo",
        "youtube": "claudiodomundonovo",
        "site_pessoal": None,
    },
    "vereadorhelinhobh": {
        "sala": "A-304",
        "telefone_gabinete": "(31) 3555-1186 / (31) 3555-1187 / (31) 3555-1401",
        "facebook": "vereadorhelinhobh",
        "twitter_x": "verhelinhobh",
        "youtube": None,
        "site_pessoal": None,
    },
    "heltonjuniorbh": {
        "sala": "B-302",
        "telefone_gabinete": "(31) 3472-9355",
        "facebook": None,
        "twitter_x": "heltonjuniorbh",
        "youtube": None,
        "site_pessoal": None,
    },
    "janainaecardoso": {
        "sala": "A-307",
        "telefone_gabinete": "(31) 3555-1202",
        "facebook": "janainaecardosodias",
        "twitter_x": "janainaecardoso",
        "youtube": "JanainaCardoso",
        "site_pessoal": None,
    },
    "pedro_patrus": {
        "sala": "A-313",
        "telefone_gabinete": "(31) 3555-1323 / (31) 3555-1224",
        "facebook": "patruspedro",
        "twitter_x": "PedroPatrus",
        "youtube": None,
        "site_pessoal": None,
    },
    "cleitonxavierpc": {
        "sala": "A-308",
        "telefone_gabinete": "(31) 3555-1147",
        "facebook": "prcleitonxavier",
        "twitter_x": "CleitonXavierpc",
        "youtube": None,
        "site_pessoal": None,
    },
    "janainaecardoso": {
        "sala": "A-307",
        "telefone_gabinete": "(31) 3555-1202",
        "facebook": "janainaecardosodias",
        "twitter_x": "janainaecardoso",
        "youtube": "JanainaCardoso",
        "site_pessoal": None,
    },
    "juhliasantost": {
        "sala": "B-319",
        "telefone_gabinete": "(31) 3555-1420",
        "facebook": "juhlia.santos.9",
        "twitter_x": "juhliasantost",
        "youtube": None,
        "site_pessoal": None,
    },
    "leonardoangelobh": {
        "sala": "B-317",
        "telefone_gabinete": "(31) 3555-1166",
        "facebook": "leoangeloitatiaia",
        "twitter_x": "leoangelobh",
        "youtube": "LeonardoAngelo",
        "site_pessoal": None,
    },
    "maninho.felix": {
        "sala": "B-209",
        "telefone_gabinete": "(31) 3472-9240 / (31) 3472-9239 / (31) 3555-1194 / (31) 3555-1195",
        "facebook": "vereadormaninhofelix",
        "twitter_x": "maninhofelixbh",
        "youtube": None,
        "site_pessoal": None,
    },
    "marildaportela.bh": {
        "sala": "B-309",
        "telefone_gabinete": "(31) 3555-1172 / (31) 3555-1173 / (31) 3555-1324 / (31) 3555-1404",
        "facebook": "marildaportelamg",
        "twitter_x": "marilda_portela",
        "youtube": None,
        "site_pessoal": None,
    },
    "nenemdafarmaciaoficial": {
        "sala": "B-316",
        "telefone_gabinete": "(31) 3555-1161",
        "facebook": "nenemdafarmacia",
        "twitter_x": None,
        "youtube": "nenemdafarmacia",
        "site_pessoal": None,
    },
    "rudsonpaixaobh": {
        "sala": "B-307",
        "telefone_gabinete": "(31) 3555-1200",
        "facebook": "rudson.felipe.5",
        "twitter_x": None,
        "youtube": None,
        "site_pessoal": None,
    },
    "sgt_jalyson": {
        "sala": "B-303",
        "telefone_gabinete": "(31) 3555-9360",
        "facebook": None,
        "twitter_x": None,
        "youtube": None,
        "site_pessoal": None,
    },
    "tileleo": {
        "sala": "B-310",
        "telefone_gabinete": "(31) 3555-9013",
        "facebook": "Tileleo17",
        "twitter_x": None,
        "youtube": "Tileleo17",
        "site_pessoal": "tileleo.com.br",
    },
    "michelysiqueira": {
        "sala": "B-304",
        "telefone_gabinete": "(31) 3472-9055",
        "facebook": None,
        "twitter_x": None,
        "youtube": None,
        "site_pessoal": "michellysiqueira.com.br",
    },
    "diegosanchesbh": {
        "sala": "B-315",
        "telefone_gabinete": "(31) 3555-1426",
        "facebook": "diego.sanchebh",
        "twitter_x": None,
        "youtube": None,
        "site_pessoal": None,
    },
    "professoranarabh": {
        "sala": "B-217",
        "telefone_gabinete": "(31) 3555-1150",
        "facebook": None,
        "twitter_x": None,
        "youtube": None,
        "site_pessoal": None,
    },
}

# Arruda não tem handle instagram no CMBH — match por email
CMBH_BY_EMAIL = {
    "ver.arruda@cmbh.mg.gov.br": {
        "sala": "A-303",
        "telefone_gabinete": "(31) 3555-1305",
        "facebook": None,
        "twitter_x": None,
        "youtube": None,
        "site_pessoal": None,
    },
}


def merge():
    with open(JSON_PATH, encoding="utf-8") as f:
        vereadores = json.load(f)

    campos_novos = ["sala", "facebook", "twitter_x", "youtube", "site_pessoal"]
    stats = {c: 0 for c in campos_novos + ["telefone_atualizado"]}
    nao_encontrados = []

    for v in vereadores:
        if not v.get("eleito"):
            continue

        ig = v.get("instagram")
        email = v.get("email_gabinete")
        dados = None

        if ig and ig in CMBH:
            dados = CMBH[ig]
        elif email and email in CMBH_BY_EMAIL:
            dados = CMBH_BY_EMAIL[email]

        if dados is None:
            nao_encontrados.append(v["nome"])
            continue

        # Sala
        if not v.get("sala") and dados.get("sala"):
            v["sala"] = dados["sala"]
            stats["sala"] += 1

        # Telefone (atualiza se o novo tem mais informação)
        tel_novo = dados.get("telefone_gabinete")
        tel_atual = v.get("telefone_gabinete", "")
        if tel_novo and (not tel_atual or len(tel_novo) > len(tel_atual)):
            v["telefone_gabinete"] = tel_novo
            stats["telefone_atualizado"] += 1

        # Redes sociais
        for campo in ["facebook", "twitter_x", "youtube", "site_pessoal"]:
            if not v.get(campo) and dados.get(campo):
                v[campo] = dados[campo]
                stats[campo] += 1

    # Ordenar campos de forma consistente
    campos_ordem = [
        "nome", "partido", "regional", "bairros_base", "votos_total",
        "instagram", "facebook", "twitter_x", "youtube", "site_pessoal",
        "email_gabinete", "telefone_gabinete", "sala",
        "eleito", "fonte", "whatsapp_gabinete",
    ]

    def ordenar(v):
        result = {}
        for c in campos_ordem:
            if c in v:
                result[c] = v[c]
        for c in v:
            if c not in result:
                result[c] = v[c]
        return result

    vereadores = [ordenar(v) for v in vereadores]

    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(vereadores, f, ensure_ascii=False, indent=2)

    return stats, nao_encontrados, vereadores


def relatorio(stats, nao_encontrados, vereadores):
    eleitos = [v for v in vereadores if v.get("eleito")]
    total = len(eleitos)

    print("=" * 60)
    print("RELATORIO DE ENRIQUECIMENTO - CMBH mai/2026")
    print("=" * 60)
    print(f"\nTotal de vereadores eleitos: {total}")
    print()

    campos_relatorio = [
        ("instagram",     "Instagram"),
        ("facebook",      "Facebook"),
        ("twitter_x",     "Twitter/X"),
        ("youtube",       "YouTube"),
        ("site_pessoal",  "Site pessoal"),
        ("email_gabinete","E-mail gabinete"),
        ("telefone_gabinete", "Telefone gabinete"),
        ("sala",          "Sala"),
        ("whatsapp_gabinete", "WhatsApp gabinete"),
    ]

    print("COBERTURA POR CAMPO (eleitos):")
    print(f"  {'Campo':<22} {'Preenchidos':>11}  {'Barra'}")
    print(f"  {'-'*22} {'-'*11}  {'-'*20}")
    for campo, label in campos_relatorio:
        preenchidos = sum(1 for v in eleitos if v.get(campo))
        pct = preenchidos / total * 100
        barra = "#" * int(pct / 5)
        print(f"  {label:<22} {preenchidos:>3}/{total}  ({pct:4.0f}%)  {barra}")

    print()
    print("CAMPOS ADICIONADOS NESTA EXECUCAO:")
    for campo, qtd in stats.items():
        if qtd > 0:
            label = campo.replace("_", " ").title()
            print(f"  {label}: +{qtd}")

    if nao_encontrados:
        print()
        print(f"NAO ENCONTRADOS ({len(nao_encontrados)}):")
        for n in nao_encontrados:
            print(f"  - {n}")

    print()
    print(f"Arquivo salvo: {JSON_PATH}")
    print("=" * 60)


if __name__ == "__main__":
    stats, nao_enc, vereadores = merge()
    relatorio(stats, nao_enc, vereadores)
