# Fase 0: validação das fontes

> Executada em 01/11/2026. Para repetir: `uv run fase0` (rápida) ou `uv run fase0 --dou-completo` (baixa ~530 MB do DOU).
> O resultado de cada execução fica em `data/fase0/relatorio.json`.

## Resultado

| Fonte | Status | Uso no MVP | Conclusão |
|---|---|---|---|
| **SIOP (SPARQL)** | ✅ OK | Orçamento | **Fonte principal de orçamento.** Público, sem chave, anos 2000–2026, com todos os estágios: projeto de lei, dotação inicial, atualizada, empenhado, liquidado e pago. |
| **Portal da Transparência (arquivos)** | ✅ OK | Orçamento (conferência) | CSV anual por ação, sem chave. Não tem o estágio "liquidado". Serve para conferir o SIOP. |
| **Cruzamento SIOP × Portal** | ✅ OK | — | Na ação 20YP (saúde indígena) em 2023, os quatro estágios comuns batem até o centavo. Isso também confirma que "realizado" no Portal significa **pago**. |
| **IBGE (IPCA)** | ✅ OK | Correção pela inflação | API pública, sem chave. Série mensal desde 2018 conferida contra um valor publicado. |
| **Diário Oficial da União** | ✅ OK | Atos (tributos) | **Fonte principal de atos.** ZIP mensal com um XML por ato, contendo tipo, órgão, ementa, texto e link do PDF oficial. O teste localizou a MP 1.157/2023 (prorrogação da redução de PIS/Cofins sobre combustíveis). |
| **Câmara dos Deputados** | ✅ OK | Fase 3 | API pública. Atenção: há registros de teste (órgão `TESTECOM`) misturados aos dados reais, que precisarão ser filtrados. |
| **Senado Federal** | ✅ OK | Fase 3 | O serviço antigo foi desativado em 01/02/2026. O novo (`/dadosabertos/votacao`) funciona. |
| **Portal da Transparência (API)** | ⏳ Pendente | Opcional | Exige chave gratuita. Não é necessária para o MVP, porque SIOP e arquivos cobrem o orçamento. |
| **Planalto** | ⛔ Bloqueado | Opcional | Respondeu no primeiro acesso e depois passou a derrubar as conexões (provável limite por IP). Substituível pelo texto do DOU. |
| **LexML** | ⛔ Bloqueado | Dispensável | Devolve página anti-robô. A URN de um ato pode ser montada a partir de tipo, data e número. |
| **Receita Federal (normas)** | ⚠️ Parcial | Dispensável | API interna sem documentação. Os atos de combustíveis do MVP saem no DOU. |

## O que muda no plano

1. **Orçamento:** SIOP como fonte principal, Portal da Transparência como conferência automática. Uma divergência entre os dois bloqueia a publicação até revisão.
2. **Atos:** DOU como fonte única no MVP. Planalto, LexML e Receita ficam fora do pipeline.
3. **Volume do DOU:** cada mês da Seção 1 tem ~530 MB e o servidor não aceita download parcial. O coletor vai baixar mês a mês, filtrar só os atos relevantes (por tipo e palavras-chave) e descartar o resto. Estimando pelo mês testado, são ~60 GB para 2018–2026, baixados uma única vez.
4. **Limites de acesso:** o bloqueio do Planalto mostra que os coletores precisam de intervalos entre requisições e de cache local, para não repetir downloads.

## Próximos passos (Fase 1)

- Mapear as ações orçamentárias dos quatro temas (seção 5.4 da especificação), começando pela subfunção 423 "Assistência aos povos indígenas", que já aparece nos dados.
- Montar o coletor do DOU com filtro por PIS/Cofins/CIDE e combustíveis.
- Modelar o banco SQLite conforme a seção 5 da especificação.
