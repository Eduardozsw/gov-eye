# Pendências para o curador

Estado da branch `Claude-auto-pilot`. Nada foi marcado como revisado: todos os atos, eventos e ações estão **pendentes** e não aparecem no build de publicação.

## 1. Revisões (só você)

```sh
uv run goveye pendentes              # lista tudo o que falta revisar
uv run goveye conferir-trechos       # confere os trechos dos eventos com o texto do DOU
uv run goveye site                   # exporta a prévia, com selos "pendente de revisão"
(cd web && npm run dev)              # abre a prévia em http://localhost:3000
uv run goveye revisar <objeto> <id> --revisor "Seu Nome"
```

Cada item precisa de duas revisões em dias diferentes. Ordem sugerida:

1. **Mapeamento de ações** (`data/curadoria/acoes.yaml`): 47 ações incluídas e 14 excluídas, com justificativa. O orçamento de um tema só aparece na publicação quando **todas** as ações dele forem revisadas. Pontos que pedem decisão:
   - `21EM` (Forças Armadas em terras indígenas): incluída porque o próprio orçamento a classifica na subfunção 423;
   - `21C0` (covid): incluída só a parte da subfunção 423;
   - `00XF` (crédito reembolsável do MCMV): excluída por ser empréstimo, não gasto;
   - `21CP` e `6414` no Bolsa Família: excluídas.
2. **Atos** (`data/curadoria/atos/`): conferir os cargos dos signatários (os nomes vêm do texto publicado; os cargos não).
3. **Eventos** (`data/curadoria/eventos/`): conferir valor, data de efeito e causa.

## 2. Decisões editoriais em aberto

- **1º de janeiro de 2023 (gasolina):** a LC 194/2022 zerava PIS/Cofins e CIDE até 31/12/2022, e a MP 1.157/2023 foi publicada em edição extra de 02/01/2023, com vigência a partir da publicação. A proposta registra só uma prorrogação em 02/01/2023 (o valor continua zero). Se preferir a leitura literal, troque por dois eventos: expiração em 01/01/2023 e novo ato em 02/01/2023.
- **Causa da LC 194/2022:** proposta como "Lei aprovada pelo Congresso". O projeto foi do Legislativo e a sanção, do Executivo; as duas assinaturas aparecem na página do ato.

## 3. Lacunas nas séries de combustíveis

| Série | Levantada até | O que falta |
|---|---|---|
| PIS/Cofins gasolina | 28/02/2023 | MP 1.163/2023 (R$ 0,47/L a partir de 01/03/2023) e reoneração posterior |
| PIS/Cofins diesel | 29/05/2018 | Decretos de maio de 2018 (após a greve dos caminhoneiros), 2018 a 2022, Decreto 10.638/2021 (já coletado), LC 192/2022, MP 1.157/2023, Lei 14.592/2023; depois disso, MPs 1.175 e 1.178 (rascunhos prontos, comentados no YAML) |
| CIDE gasolina | — | Valor inicial (Decreto 8.395/2015), LC 194/2022 (já coletada), MP 1.157/2023 art. 6º (já coletada) |
| CIDE diesel | — | Valor inicial (Decreto 8.395/2015) e atos de maio de 2018 |

O campo `levantado_ate` de cada indicador (`temas.yaml`) impede que o gráfico estenda o último valor além do período lido.

Achados sobre o DOU que afetam a coleta:

- Até 2018 o tipo do ato vem em caixa alta ("DECRETO") e sem id de matéria. O filtro já foi corrigido.
- Atos publicados em **edição extra** podem não estar no ZIP mensal (os Decretos 9.391 e 9.392/2018 e a MP 1.163/2023 não apareceram). Se não estiverem, a alternativa é a busca do in.gov.br por data e edição.
- O download mensal (~530 MB) às vezes cai no meio. A coleta agora repete até 3 vezes.

## 4. Orçamento

- Coletado de 2018 a 2026 (SIOP + Portal + IPCA até a última divulgação). Os instantâneos estão em `data/coletas/`.
- Há 29 divergências entre SIOP e Portal, quase todas em 2025 e 2026, nos estágios empenhado e pago. Parecem diferença de data de atualização entre as bases. Os anos com divergência ficam "em conferência" na publicação até serem explicados. A lista completa aparece na prévia de cada tema.
- A ação 218B (mulheres) cai de R$ 23 mi pagos em 2018 para perto de zero em 2021 e 2022. É um dado oficial, mas vale conferir antes de publicar, porque vai chamar atenção.

## 5. Fora do alcance desta etapa

- **`data/curadoria/site.yaml`:** preencher nome, apresentação, contato e endereço. O build de publicação recusa enquanto houver `PREENCHER`.
- **Cards de compartilhamento (OG/WhatsApp):** com Next.js dá para gerar o PNG no build (rota `opengraph-image`), sem dependência nova. Ainda não implementado.
- **Assinatura dos dados:** o manifesto SHA-256 já é gerado. A assinatura criptográfica precisa de uma chave sua.
- **Deploy na Cloudflare Pages e agendamento da coleta:** envolvem credenciais; ficaram de fora.
- **ADR 0002 (Next.js):** está como "proposto"; aprove ou peça mudança. Substitui a parte do ADR 0001 sobre o gerador em Jinja2.
- **Front-end:** as frases de exemplo da busca ficam em `SUGESTOES_BUSCA` (`src/goveye/site/gerar.py`); troque à vontade, o teste `npm test` avisa se alguma ficar sem resultado.
