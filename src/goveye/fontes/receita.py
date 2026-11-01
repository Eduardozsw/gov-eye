"""Receita Federal: sistema de normas (instruções normativas, atos declaratórios etc.)."""

import httpx

from .base import Resultado, Status

NOME = "Receita Federal (normas)"
BASE = "https://normas.receita.fazenda.gov.br/api"


def verificar(cliente: httpx.Client) -> Resultado:
    resp = cliente.get(f"{BASE}/tipoAto/ativo")
    resp.raise_for_status()
    tipos = resp.json()
    return Resultado(
        NOME,
        Status.PARCIAL,
        "API interna sem documentação",
        [
            f"/api/tipoAto/ativo responde: {len(tipos)} tipos de ato",
            "A busca (POST /api/indexacao/ato/pesquisar) responde, mas o formato da consulta não é público",
            "Dispensável no MVP: leis, MPs e decretos de combustíveis saem no DOU",
        ],
    )
