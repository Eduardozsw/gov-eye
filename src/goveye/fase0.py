"""Fase 0: verifica se cada fonte oficial está acessível e no formato esperado.

Uso:
    uv run fase0                 # verificação rápida de todas as fontes
    uv run fase0 --dou-completo  # também baixa um mês do DOU (~530 MB) e procura um ato
"""

import argparse
import json
import os
import sys
from dataclasses import asdict
from datetime import datetime
from functools import partial
from pathlib import Path

import httpx

from .fontes import camara, dou, ibge, lexml, planalto, receita, senado, siop, transparencia
from .fontes.base import Resultado, Status, novo_cliente

RELATORIO = Path("data/fase0/relatorio.json")
# Diferença máxima aceita entre fontes, em reais (arredondamento de centavos).
TOLERANCIA = 1.0


def carregar_env(caminho: Path = Path(".env")) -> None:
    if not caminho.exists():
        return
    for linha in caminho.read_text(encoding="utf-8").splitlines():
        linha = linha.strip()
        if linha and not linha.startswith("#") and "=" in linha:
            chave, valor = linha.split("=", 1)
            os.environ.setdefault(chave.strip(), valor.strip())


def verificacao_cruzada(resultados: dict[str, Resultado]) -> Resultado:
    nome = "Cruzamento SIOP × Portal da Transparência"
    a = resultados[siop.NOME].amostra
    b = resultados["Portal da Transparência (arquivos)"].amostra
    if not a or not b:
        return Resultado(nome, Status.FALHA, "Uma das fontes não trouxe valores")

    divergencias = [
        f"{estagio}: SIOP {a[estagio]:,.2f} × Portal {b[estagio]:,.2f}"
        for estagio in ("inicial", "atualizada", "empenhado", "pago")
        if abs(a[estagio] - b[estagio]) > TOLERANCIA
    ]
    if divergencias:
        return Resultado(nome, Status.FALHA, "Valores divergem", divergencias)
    return Resultado(
        nome,
        Status.OK,
        f"Ação {b['acao']} em {b['ano']}: os quatro estágios batem",
        ["Confirma que 'realizado' no Portal é o valor pago"],
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Verifica as fontes oficiais do gov-eye")
    parser.add_argument("--dou-completo", action="store_true", help="baixa um mês do DOU e procura um ato conhecido")
    args = parser.parse_args()
    carregar_env()

    verificacoes = [
        (ibge.NOME, ibge.verificar),
        (siop.NOME, siop.verificar),
        ("Portal da Transparência (arquivos)", transparencia.verificar_arquivos),
        ("Portal da Transparência (API)", transparencia.verificar_api),
        (dou.NOME, partial(dou.verificar, completo=args.dou_completo)),
        (planalto.NOME, planalto.verificar),
        (camara.NOME, camara.verificar),
        (senado.NOME, senado.verificar),
        (lexml.NOME, lexml.verificar),
        (receita.NOME, receita.verificar),
    ]

    resultados: dict[str, Resultado] = {}
    with novo_cliente() as cliente:
        for nome, verificar in verificacoes:
            print(f"Verificando {nome}...", flush=True)
            try:
                resultados[nome] = verificar(cliente)
            except (httpx.HTTPError, ValueError, KeyError, IndexError) as erro:
                resultados[nome] = Resultado(nome, Status.FALHA, f"{type(erro).__name__}: {erro}")
    resultados["cruzamento"] = verificacao_cruzada(resultados)

    print()
    for r in resultados.values():
        print(f"[{r.status:<9}] {r.fonte}: {r.resumo}")
        for d in r.detalhes:
            print(f"             - {d}")

    RELATORIO.parent.mkdir(parents=True, exist_ok=True)
    RELATORIO.write_text(
        json.dumps(
            {
                "executado_em": datetime.now().isoformat(timespec="seconds"),
                "resultados": [asdict(r) for r in resultados.values()],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"\nRelatório salvo em {RELATORIO}")
    sys.exit(1 if any(r.status == Status.FALHA for r in resultados.values()) else 0)


if __name__ == "__main__":
    main()
