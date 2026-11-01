# gov-eye

Linha do tempo verificável de tributos e políticas públicas federais: o que mudou, por que mudou, quem assinou e onde está o documento oficial.

- Especificação: [docs/ESPECIFICACAO.md](docs/ESPECIFICACAO.md)
- Resultado da validação das fontes: [docs/FASE0.md](docs/FASE0.md)

## Como rodar

Requer [uv](https://docs.astral.sh/uv/).

```sh
uv run fase0                 # verifica todas as fontes oficiais
uv run fase0 --dou-completo  # também baixa um mês do DOU (~530 MB) e procura um ato conhecido
```

Para testar a API do Portal da Transparência, copie `.env.example` para `.env` e preencha a chave.

## Estrutura

```
src/goveye/fontes/   um módulo por fonte oficial, cada um com verificar()
src/goveye/fase0.py  executa as verificações e o cruzamento entre fontes
data/fase0/          relatório da última execução
data/raw/            downloads brutos (fora do git)
```

## Licença

Código: todos os direitos reservados. Dados publicados: CC BY-NC 4.0.
