import json
from datetime import date

import pytest

from conftest import escrever_yaml
from goveye import banco
from goveye import curadoria as cur
from goveye.site import formato, svg, textos
from goveye.site.gerar import ErroPublicacao, exportar

HOJE = date(2026, 6, 30)


@pytest.fixture
def banco_teste(tmp_path, pasta_curadoria, orcamento_sintetico):
    siop, portal, ipca = orcamento_sintetico
    return banco.construir(cur.carregar(pasta_curadoria), siop, portal, ipca, tmp_path / "teste.sqlite")


def _exportar(modo, banco_teste, pasta_curadoria, tmp_path) -> dict:
    caminho = exportar(modo, banco=banco_teste, saida=tmp_path / modo, curadoria=pasta_curadoria, hoje=HOJE)
    return json.loads(caminho.read_text(encoding="utf-8"))


def _tema(dados: dict, id_: str) -> dict:
    return next(t for t in dados["temas"] if t["id"] == id_)


def test_previa_mostra_todos_os_eventos(banco_teste, pasta_curadoria, tmp_path):
    dados = _exportar("previa", banco_teste, pasta_curadoria, tmp_path)
    assert dados["previa"]
    eventos = _tema(dados, "combustiveis")["series"][0]["eventos"]
    assert any(e["causa"] == "Prazo previsto no ato original terminou" and e["expiracao"] for e in eventos)
    assert "mp-teste-2" in {a["id"] for a in dados["atos"]}


def test_publicacao_nao_depende_de_revisao(banco_teste, pasta_curadoria, tmp_path):
    dados = _exportar("publicacao", banco_teste, pasta_curadoria, tmp_path)
    serie = _tema(dados, "combustiveis")["series"][0]
    assert not dados["previa"]
    # Só o valor inicial tem revisão registrada; os eventos seguintes aparecem do mesmo jeito.
    assert len(serie["eventos"]) > 1
    assert "mp-teste-2" in {a["id"] for a in dados["atos"]}


def test_publicacao_mostra_orcamento_sem_revisao(banco_teste, pasta_curadoria, tmp_path):
    o = _tema(_exportar("publicacao", banco_teste, pasta_curadoria, tmp_path), "politica-y")["orcamento"]
    assert o["tem_dados"]
    assert "<svg" in o["grafico_corrigido"] and o["tabela"]


def test_publicacao_bloqueia_ano_com_divergencia(banco_teste, pasta_curadoria, tmp_path):
    o = _tema(_exportar("publicacao", banco_teste, pasta_curadoria, tmp_path), "politica-y")["orcamento"]
    assert "<svg" in o["grafico_corrigido"]
    textos_ = [f["texto"] for f in o["frases"]]
    assert "2022: valores em conferência (as fontes oficiais divergem)." in textos_  # pago de 2022 diverge
    assert any(t.startswith("Em 2021, o orçamento autorizou") for t in textos_)
    assert o["divergencias"] == []  # a lista detalhada só aparece na prévia
    assert "<svg" in o["mini"] and "2021: R$" in o["mini"]
    assert "2022:" not in o["mini"]  # ano em conferência fica como lacuna no minigráfico


def test_publicacao_recusa_campos_a_preencher(banco_teste, pasta_curadoria, tmp_path):
    (pasta_curadoria / "site.yaml").write_text("responsavel:\n  nome: PREENCHER\n", encoding="utf-8")
    with pytest.raises(ErroPublicacao):
        _exportar("publicacao", banco_teste, pasta_curadoria, tmp_path)


def test_manifesto_dos_dados(banco_teste, pasta_curadoria, tmp_path):
    import hashlib

    dados = _exportar("previa", banco_teste, pasta_curadoria, tmp_path)
    pasta = tmp_path / "previa" / "public" / "dados"
    for linha in (pasta / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines():
        soma, nome = linha.split("  ")
        assert hashlib.sha256((pasta / nome).read_bytes()).hexdigest() == soma
    assert {a["nome"] for a in dados["manifesto"]} >= {"eventos.csv", "goveye.json"}


def test_indice_de_busca_aponta_para_paginas_existentes(banco_teste, pasta_curadoria, tmp_path):
    dados = _exportar("previa", banco_teste, pasta_curadoria, tmp_path)
    temas = {t["id"] for t in dados["temas"]}
    atos = {a["id"] for a in dados["atos"]}
    eventos = {e["id"] for t in dados["temas"] for s in t.get("series", []) for e in s["eventos"]}
    assert dados["sugestoes"]
    for item in dados["busca"]:
        partes = item["href"].strip("/").split("/")
        assert ((partes[0] == "tema" and partes[1] in temas) or (partes[0] == "ato" and partes[1] in atos)
                or (partes[0] == "mudanca" and partes[1] in eventos)), item
    assert any(i["tipo"] == "Ato oficial" for i in dados["busca"])
    assert any(i["href"] == "/mudanca/tributo-x-zerado/" for i in dados["busca"])


def test_prazo_vencido_mostra_o_que_veio_depois(banco_teste, pasta_curadoria, tmp_path):
    dados = _exportar("previa", banco_teste, pasta_curadoria, tmp_path)
    [prazo] = dados["prazos"]
    assert prazo["ato"]["id"] == "mp-teste-2" and not prazo["futuro"]
    [item] = prazo["itens"]
    assert item["evento_id"] == "tributo-x-zerado"
    assert item["frase"] == ("O valor de Tributo X sobre a gasolina foi fixado em R$ 0,0000 até 31 de dezembro de 2022 "
                             "pela Medida Provisória nº 2.000/2022.")
    assert item["depois"]["id"] == "tributo-x-volta"
    assert "terminou o prazo" in item["depois"]["frase"]


def test_prazo_futuro(banco_teste, pasta_curadoria, tmp_path):
    caminho = exportar("previa", banco=banco_teste, saida=tmp_path, curadoria=pasta_curadoria, hoje=date(2022, 7, 1))
    [prazo] = json.loads(caminho.read_text(encoding="utf-8"))["prazos"]
    assert prazo["futuro"] and prazo["data"] == "31 de dezembro de 2022"


def test_publicacao_mostra_prazo_sem_revisao(banco_teste, pasta_curadoria, tmp_path):
    [prazo] = _exportar("publicacao", banco_teste, pasta_curadoria, tmp_path)["prazos"]
    assert prazo["ato"]["id"] == "mp-teste-2"


def test_evento_traz_valor_anterior(banco_teste, pasta_curadoria, tmp_path):
    eventos = _tema(_exportar("previa", banco_teste, pasta_curadoria, tmp_path), "combustiveis")["series"][0]["eventos"]
    por_id = {e["id"]: e for e in eventos}
    assert por_id["tributo-x-inicial"]["valor_antes"] is None
    assert (por_id["tributo-x-zerado"]["valor_antes"], por_id["tributo-x-zerado"]["valor"]) == ("R$ 0,5000", "R$ 0,0000")


def _com_correcoes(pasta_curadoria, orcamento_sintetico, tmp_path):
    cur.registrar_correcao("evento", "tributo-x-inicial", "Trecho do ato corrigido", "Citação incompleta",
                           date(2026, 3, 1), pasta_curadoria)
    cur.registrar_correcao("evento", "tributo-x-zerado", "Valor corrigido", "Erro de digitação",
                           date(2026, 3, 2), pasta_curadoria)
    siop, portal, ipca = orcamento_sintetico
    return banco.construir(cur.carregar(pasta_curadoria), siop, portal, ipca, tmp_path / "b.sqlite")


def test_correcoes_aparecem_no_evento_e_no_historico(tmp_path, pasta_curadoria, orcamento_sintetico):
    caminho = _com_correcoes(pasta_curadoria, orcamento_sintetico, tmp_path)
    dados = _exportar("previa", caminho, pasta_curadoria, tmp_path)
    eventos = {e["id"]: e for e in _tema(dados, "combustiveis")["series"][0]["eventos"]}
    assert eventos["tributo-x-zerado"]["correcoes"] == [
        {"data": "02/03/2026", "o_que_mudou": "Valor corrigido", "motivo": "Erro de digitação"}
    ]
    assert [x["href"] for x in dados["correcoes"]] == ["/mudanca/tributo-x-zerado/", "/mudanca/tributo-x-inicial/"]


def test_publicacao_inclui_correcoes_nos_dados_abertos(tmp_path, pasta_curadoria, orcamento_sintetico):
    caminho = _com_correcoes(pasta_curadoria, orcamento_sintetico, tmp_path)
    dados = _exportar("publicacao", caminho, pasta_curadoria, tmp_path)
    assert [x["href"] for x in dados["correcoes"]] == ["/mudanca/tributo-x-zerado/", "/mudanca/tributo-x-inicial/"]
    csv_ = (tmp_path / "publicacao" / "public" / "dados" / "correcoes.csv").read_text(encoding="utf-8")
    assert "tributo-x-inicial" in csv_ and "tributo-x-zerado" in csv_


def test_glossario(banco_teste, pasta_curadoria, tmp_path):
    assert _exportar("previa", banco_teste, pasta_curadoria, tmp_path)["glossario"] == [
        {"id": "pago", "termo": "Pago", "definicao": "Dinheiro que saiu do caixa."}
    ]
    (pasta_curadoria / "glossario.yaml").write_text(
        "termos:\n  - {id: pago, termo: Pago, definicao: a}\n  - {id: pago, termo: Pago, definicao: b}\n",
        encoding="utf-8",
    )
    with pytest.raises(ErroPublicacao, match="repetido"):
        _exportar("previa", banco_teste, pasta_curadoria, tmp_path)


def test_formatos_brasileiros():
    assert formato.moeda(1234567.891) == "R$ 1.234.567,89"
    assert formato.aliquota(0.7925) == "R$ 0,7925"
    assert formato.moeda_curta(2_500_000_000) == "R$ 2,5 bi"
    assert formato.moeda_curta(12_000_000) == "R$ 12 mi"
    assert formato.data_br("2023-01-01") == "01/01/2023"
    assert formato.data_extenso("2023-03-01") == "1º de março de 2023"


def test_frase_de_expiracao_atribui_ao_ato_de_origem():
    ato = {"tipo": "Medida Provisória", "titulo": "Medida Provisória nº 2.000/2022", "data_assinatura": "2022-06-01",
           "signatarios": [{"nome": "Presidente A", "cargo": "Presidente"}]}
    evento = {"data_efeito": "2023-01-01", "causa": "EXPIRACAO_PREVISTA", "valor_antes": 0.0, "valor_depois": 0.5,
              "texto_causa": "Prazo previsto no ato original terminou"}
    frase = textos.frase_evento(evento, {"nome": "Tributo X"}, ato, None, ato, {"nome_curto": "A"}, formato.aliquota)
    assert "voltou a ser cobrado" in frase
    assert "na Medida Provisória nº 2.000/2022, assinada em 1º de junho de 2022" in frase
    assert "(governo A)" in frase
    assert "Nenhum ato novo" in frase


def test_nome_do_tema_no_meio_da_frase_preserva_nomes_proprios():
    assert textos.nome_no_meio_da_frase("Educação básica") == "educação básica"
    assert textos.nome_no_meio_da_frase("Combustíveis") == "combustíveis"
    assert textos.nome_no_meio_da_frase("Bolsa Família") == "Bolsa Família"
    assert textos.nome_no_meio_da_frase("FIES") == "FIES"
    assert textos.nome_no_meio_da_frase("Pé-de-Meia") == "Pé-de-Meia"


def test_mini_barras_escala_pelo_maior_pago():
    mini = svg.mini_barras([svg.Barra(2020, 10, 4), svg.Barra(2021, 10, 8), svg.Barra(2022, 10, 2, em_andamento=True)],
                           "Teste", largura=90, altura=40)
    assert mini.count("<rect") == 3
    assert 'y="0.0"' not in mini and 'height="38.0"' in mini  # a maior barra ocupa a altura útil
    assert 'class="pago andamento"' in mini and "2022*:" in mini


def test_topo_do_eixo():
    assert svg.topo_eixo(0.87) == 1.0
    assert svg.topo_eixo(0.3) == 0.5
    assert svg.topo_eixo(1.6e11) == 2e11
    assert svg.topo_eixo(0) == 1.0


def test_serie_nao_passa_da_data_de_levantamento(tmp_path, pasta_curadoria, orcamento_sintetico):
    temas = cur._ler(pasta_curadoria / "temas.yaml")
    temas["temas"][0]["indicadores"][0]["levantado_ate"] = date(2023, 6, 30)
    escrever_yaml(pasta_curadoria / "temas.yaml", temas)
    siop, portal, ipca = orcamento_sintetico
    caminho = banco.construir(cur.carregar(pasta_curadoria), siop, portal, ipca, tmp_path / "b.sqlite")
    serie = _tema(_exportar("previa", caminho, pasta_curadoria, tmp_path), "combustiveis")["series"][0]
    assert serie["levantado_ate"] == "30/06/2023"
    assert serie["valor_atual"] is None  # sem levantamento até hoje, não há valor atual
