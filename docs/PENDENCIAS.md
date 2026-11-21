# Pendências

O que o site mostra vem das fontes oficiais e das definições em `data/definicoes/`. Não há revisão humana item a item: as checagens são automáticas (especificação, seção 7), e erros apontados depois da publicação viram correções públicas.

## 1. Lacunas nas séries de combustíveis

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

## 2. Orçamento

- Coletado de 2018 a 2026 (SIOP + Portal + IPCA até a última divulgação). Os instantâneos estão em `data/coletas/`.
- Há 29 divergências entre SIOP e Portal, quase todas em 2025 e 2026, nos estágios empenhado e pago. Parecem diferença de data de atualização entre as bases. Os anos com divergência ficam "em conferência" na publicação até serem explicados. A lista completa aparece na prévia de cada tema.
- A ação 218B (mulheres) cai de R$ 23 mi pagos em 2018 para perto de zero em 2021 e 2022. É o dado oficial.

## 3. Segunda leva de temas (orçamento)

Nove temas novos, todos com o mesmo critério do MVP (a ação entra quando o nome oficial se refere ao público ou ao programa; salários e custeio genérico ficam fora). Candidatas levantadas no SIOP de 2018 a 2026.

| Tema | Ações | Observações |
|---|---|---|
| Educação básica | complementação do Fundeb (`0E36` → `00SB`), PNAE, PDDE, livro didático, transporte, obras, creches, formação de professores, EJA, avaliações | Excluídas: `0C33` (parte do Fundeb formada por impostos de estados e municípios), `0369` (cotas do salário-educação), `0312`/`00WX` (Fundo Constitucional do DF) e os colégios militares |
| Universidades e institutos federais | funcionamento (`20RK`, `20RL`), assistência estudantil, obras e implantação de novas universidades | Sem salários (são a maior parte do custo); hospitais universitários, ensino militar e Museu Nacional excluídos |
| Pé-de-Meia | `00W2` (aportes ao fundo do programa) | 2024 aparece quase zerado porque os aportes daquele ano vieram do FGO e do Fgeduc, fora do orçamento (TCU, Acórdão 61/2025). O texto do tema explica |
| FIES | `00IG` e `00YG` (empréstimos) | Administração (`20RZ`) e fundos garantidores (`00M2`) excluídos para não somar gasto com crédito, como no `00XF` do MCMV. A `00YG` é nova em 2026 |
| Farmácia Popular | gratuidade (`20YR`) e copagamento (`20YS`) | — |
| Mais Médicos | `214U` (até 2019), `21BG` (a partir de 2020), `00QC` | A `21BG` também paga residências e formação; a quebra em 2020 está explicada no texto do tema |
| Atenção primária à saúde | Piso da APS, incremento temporário, agentes comunitários, obras de UBS | `21BG` fica só no Mais Médicos; `21DX` (Adaps/AgSUS) e `20AE` (remédios da atenção básica) excluídas |
| Fiscalização ambiental e áreas protegidas | fiscalização do Ibama, incêndios, unidades de conservação (ICMBio) | `21EK` e `21EN` contam aqui e em Povos indígenas |
| Bolsas de pesquisa e pós-graduação | `0487` (Capes) e `00LV` (CNPq) | — |

Ficaram de fora, por não ser possível separar com o critério atual:

- **Vacinação:** a ação `20YE` mistura vacinas com outros insumos, e as vacinas de covid estão dentro da `21C0`, junto com o resto do gasto da pandemia.
- **FNDCT:** as ações do fundo não trazem "FNDCT" no nome. Separar exige guardar a unidade orçamentária (UO 24901) na coleta e permitir filtrar o mapeamento por ela, como já se faz com a subfunção.

**Divergências SIOP × Portal nos temas novos:** quase todos os anos das universidades (e vários de educação básica, meio ambiente e bolsas) têm diferenças entre as bases, mas pequenas: por exemplo, R$ 2 mil em R$ 4,8 bi pagos na `20RK` em 2018. Com a tolerância atual de R$ 1 (`TOLERANCIA_CONFERENCIA`), esses anos ficam "em conferência" na publicação. Decidir se a tolerância passa a ser relativa (por exemplo, 0,01% do valor) ou se cada caso é explicado.

## 4. Fora do alcance desta etapa

- **`data/definicoes/site.yaml`:** preencher nome, apresentação, contato e endereço. O build de publicação recusa enquanto houver `PREENCHER`.
- **Cards de compartilhamento (OG/WhatsApp):** cada mudança tem página própria (`/mudanca/<id>/`) e card PNG gerado no build (`/mudanca/<id>/card.png`). O WhatsApp só mostra o card com endereço absoluto: enquanto `endereco_site` em `site.yaml` estiver com `PREENCHER`, o build usa `http://localhost:3000` (e avisa).
- **Glossário (`data/definicoes/glossario.yaml`):** 22 definições. Aparecem num balão ao tocar nos termos sublinhados (orçamento, tipo de ato, IPCA etc.) e em `/glossario/`.
- **"Reportar erro":** o link de e-mail em cada mudança, ato e tema só aparece quando `responsavel.contato` em `site.yaml` for um e-mail. Até lá, aponta para "Quem faz".
- **Prazos com mais de uma data no mesmo ato:** a página `/prazos/` e a linha tracejada do gráfico usam o único `vigencia_fim_prevista` do ato. A MP 1.157/2023 tem dois prazos (gasolina e álcool até 28/02/2023; diesel, biodiesel e GLP até 31/12/2023). Quando os eventos do diesel ligados a ela entrarem, o prazo precisa passar a ser por evento (ou por indicador), senão o diesel aparece com 28/02/2023.
- **Assinatura dos dados:** o manifesto SHA-256 já é gerado. A assinatura criptográfica precisa de uma chave sua.
- **Deploy na Cloudflare Pages e agendamento da coleta:** envolvem credenciais; ficaram de fora.
- **ADR 0002 (Next.js):** está como "proposto"; aprove ou peça mudança. Substitui a parte do ADR 0001 sobre o gerador em Jinja2.
- **Front-end:** as frases de exemplo da busca ficam em `SUGESTOES_BUSCA` (`src/goveye/site/gerar.py`); troque à vontade, o teste `npm test` avisa se alguma ficar sem resultado.
