"""Planalto: texto consolidado de leis, MPs e decretos."""

import time

import httpx

from .base import Resultado, Status

NOME = "Planalto (legislação)"
# Lei 14.601/2023, que recriou o Programa Bolsa Família.
URL = "https://www.planalto.gov.br/ccivil_03/_ato2023-2026/2023/lei/l14601.htm"
TRECHO = "Programa Bolsa Fam"
TENTATIVAS, ESPERA_SEGUNDOS = 3, 10


def verificar(cliente: httpx.Client) -> Resultado:
    for tentativa in range(1, TENTATIVAS + 1):
        try:
            resp = cliente.get(URL)
            break
        except httpx.TransportError as erro:
            if tentativa == TENTATIVAS:
                return Resultado(
                    NOME,
                    Status.BLOQUEADO,
                    "Servidor derruba a conexão",
                    [
                        f"{TENTATIVAS} tentativas com {ESPERA_SEGUNDOS}s de intervalo: {erro}",
                        "Respondeu normalmente no primeiro acesso: indica limite de acessos por IP",
                        "Alternativa: o XML do DOU traz o texto original de cada ato",
                    ],
                )
            time.sleep(ESPERA_SEGUNDOS)

    resp.raise_for_status()
    # As páginas não declaram charset de forma confiável; buscar em bytes evita erro de decodificação.
    encontrado = TRECHO.encode("latin-1") in resp.content or TRECHO.encode() in resp.content
    detalhes = [f"{len(resp.content) // 1024} KB de HTML para a Lei 14.601/2023"]
    if not encontrado:
        return Resultado(NOME, Status.FALHA, "Página não contém o trecho esperado", detalhes)
    detalhes.append("HTML legado (FrontPage): a extração de texto vai precisar de limpeza")
    return Resultado(NOME, Status.OK, "Páginas HTML públicas, URL previsível por ano e número", detalhes)
