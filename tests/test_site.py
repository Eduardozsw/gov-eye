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


def test_previa_mostra_pendentes_marcados(banco_teste, pasta_curadoria, tmp_path):
    dados = _exportar("previa", banco_teste, pasta_curadoria, tmp_path)
    assert dados["previa"]
    eventos = _tema(dados, "combustiveis")["series"][0]["eventos"]
    assert any(e["pendente"] for e in eventos)
    assert any(e["causa"] == "Prazo previsto no ato original terminou" and e["expiracao"] for e in eventos)
    assert "mp-teste-2" in {a["id"] for a in dados["atos"]}


def test_publicacao_para_no_primeiro_evento_pendente(banco_teste, pasta_curadoria, tmp_path):
    dados = _exportar("publicacao", banco_teste, pasta_curadoria, tmp_path)
    serie = _tema(dados, "combustiveis")["series"][0]
    assert not dados["previa"]
    assert [e["valor"] for e in serie["eventos"]] == ["R$ 0,5000"]  # valor inicial, revisado duas vezes
    assert serie["interrompida"]  # eventos seguintes ainda pendentes
    assert "mp-teste-2" not in {a["id"] for a in dados["atos"]}
    assert "Medida Provisória nº 2.000/2022" not in json.dumps(dados, ensure_ascii=False)


def test_publicacao_esconde_orcamento_com_mapeamento_pendente(banco_teste, pasta_curadoria, tmp_path):
    o = _tema(_exportar("publicacao", banco_teste, pasta_curadoria, tmp_path), "politica-y")["orcamento"]
    assert not o["liberado"]
    assert o["grafico_corrigido"] == "" and o["tabela"] == [] and o["frases"] == []


def test_publicacao_bloqueia_ano_com_divergencia(tmp_path, pasta_curadoria, orcamento_sintetico):
    cur.registrar_revisao("acao", "politica-y:AAAA", "Curador", date(2026, 1, 1), pasta_curadoria)
    cur.registrar_revisao("acao", "politica-y:AAAA", "Curador", date(2026, 1, 2), pasta_curadoria)
    siop, portal, ipca = orcamento_sintetico
    caminho = banco.construir(cur.carregar(pasta_curadoria), siop, portal, ipca, tmp_path / "b.sqlite")
    o = _tema(_exportar("publicacao", caminho, pasta_curadoria, tmp_path), "politica-y")["orcamento"]
    assert "<svg" in o["grafico_corrigido"]
    textos_ = [f["texto"] for f in o["frases"]]
    assert "2022: valores em conferência (as fontes oficiais divergem)." in textos_  # pago de 2022 diverge
    assert any(t.startswith("Em 2021, o orçamento autorizou") for t in textos_)
    assert o["divergencias"] == []  # a lista detalhada só aparece na prévia


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
    assert dados["sugestoes"]
    for item in dados["busca"]:
        partes = item["href"].strip("/").split("/")
        assert (partes[0] == "tema" and partes[1] in temas) or (partes[0] == "ato" and partes[1] in atos), item
    assert any(i["tipo"] == "Ato oficial" for i in dados["busca"])


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
