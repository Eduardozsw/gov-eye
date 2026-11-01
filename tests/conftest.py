"""Fixtures sem rede: uma curadoria mínima e fictícia (atos "de teste"), mais dados de orçamento sintéticos."""

import shutil
from pathlib import Path

import pytest
import yaml

FIXTURES = Path(__file__).parent / "fixtures"


def escrever_yaml(caminho: Path, conteudo) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(yaml.safe_dump(conteudo, allow_unicode=True, sort_keys=False), encoding="utf-8")


@pytest.fixture
def pasta_curadoria(tmp_path: Path) -> Path:
    destino = tmp_path / "curadoria"
    shutil.copytree(FIXTURES / "curadoria", destino)
    return destino


@pytest.fixture
def orcamento_sintetico() -> tuple[list[dict], dict, dict]:
    siop = [
        {"ano": 2021, "acao": "AAAA", "nome_acao": "Ação de teste", "programa": "0001", "nome_programa": "Programa",
         "subfuncao": "423", "projeto_lei": 90.0, "inicial": 100.0, "atualizada": 120.0, "empenhado": 110.0,
         "liquidado": 105.0, "pago": 100.0},
        {"ano": 2022, "acao": "AAAA", "nome_acao": "Ação de teste", "programa": "0001", "nome_programa": "Programa",
         "subfuncao": "423", "projeto_lei": 100.0, "inicial": 200.0, "atualizada": 220.0, "empenhado": 210.0,
         "liquidado": 205.0, "pago": 200.0},
        # Mesma ação em outra subfunção: não entra, porque o mapeamento restringe à 423.
        {"ano": 2022, "acao": "AAAA", "nome_acao": "Ação de teste", "programa": "0001", "nome_programa": "Programa",
         "subfuncao": "122", "projeto_lei": 0.0, "inicial": 999.0, "atualizada": 999.0, "empenhado": 999.0,
         "liquidado": 999.0, "pago": 999.0},
    ]
    portal = {
        2021: {"AAAA/423": {"inicial": 100.0, "atualizada": 120.0, "empenhado": 110.0, "pago": 100.0}},
        2022: {"AAAA/423": {"inicial": 200.0, "atualizada": 220.0, "empenhado": 210.0, "pago": 150.0}},
    }
    ipca = {"202112": 100.0, "202206": 105.0, "202212": 110.0}
    return siop, portal, ipca
