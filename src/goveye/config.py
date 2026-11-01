"""Caminhos e parâmetros compartilhados."""

from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
DADOS = RAIZ / "data"
BRUTOS = DADOS / "raw"
CURADORIA = DADOS / "curadoria"
BANCO = DADOS / "goveye.sqlite"
SITE_SAIDA = RAIZ / "site"

ANO_INICIAL = 2018
ANO_FINAL = 2026

# Intervalo entre requisições à mesma fonte, para não sobrecarregar servidores públicos.
PAUSA_ENTRE_REQUISICOES = 2.0
