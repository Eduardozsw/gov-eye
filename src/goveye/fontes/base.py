"""Tipos e utilitários comuns às verificações de fontes."""

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

import httpx

USER_AGENT = "gov-eye/0.1 (verificacao de fontes oficiais)"
TIMEOUT = httpx.Timeout(60.0, connect=20.0)


class Status(StrEnum):
    OK = "OK"
    PARCIAL = "PARCIAL"  # responde, mas falta algo para uso pleno
    PENDENTE = "PENDENTE"  # depende de ação do autor (ex.: chave de API)
    BLOQUEADO = "BLOQUEADO"  # a fonte recusa acesso automatizado
    FALHA = "FALHA"


@dataclass
class Resultado:
    fonte: str
    status: Status
    resumo: str
    detalhes: list[str] = field(default_factory=list)
    # Valores extraídos, usados nas verificações cruzadas entre fontes.
    amostra: dict[str, Any] = field(default_factory=dict)


def novo_cliente() -> httpx.Client:
    return httpx.Client(
        headers={"User-Agent": USER_AGENT},
        timeout=TIMEOUT,
        follow_redirects=True,
    )
