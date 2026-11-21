# gov-eye — Especificação do projeto

> Versão 0.1 · 01/11/2026 · Rascunho para discussão

## 1. Problema

A cada troca de governo surgem versões opostas da mesma história: "fulano zerou o imposto", "ciclano aumentou". Na prática, muitas mudanças têm causas que não aparecem no debate:

- um corte de imposto criado **com data para acabar**: quando ele expira, o governo seguinte é acusado de "aumentar";
- um orçamento **anunciado** (dotação) que nunca foi **gasto** (pago);
- valores comparados entre anos **sem correção pela inflação**;
- programas sociais que **mudam de nome ou de código** entre planos plurianuais e parecem ter sido "extintos" ou "criados".

Os dados para esclarecer tudo isso já são públicos, mas estão espalhados entre o Diário Oficial, a Receita, o Congresso e os portais de orçamento, em formatos difíceis para quem não é especialista.

## 2. Objetivo

Oferecer ao cidadão uma **linha do tempo verificável** de tributos e políticas públicas federais. Cada mudança mostra:

1. o que mudou (valor antes → depois);
2. **por que mudou**: novo ato, fim de prazo previsto, decisão judicial, revogação etc.;
3. qual ato oficial causou a mudança, quem o assinou e quando;
4. o link para o documento original.

O cidadão não precisa confiar no gov-eye: ele pode conferir cada informação na fonte.

## 3. Princípios (não negociáveis)

| # | Princípio | Na prática |
|---|---|---|
| P1 | **Toda informação tem fonte oficial** | Nenhum evento é publicado sem o link do ato ou da base oficial de origem. |
| P2 | **Fato, não opinião** | Sem adjetivos ("aumentou absurdamente"), sem atribuição de motivo ("para fingir de bonzinho"). Os textos são gerados por modelos fixos (seção 9). |
| P3 | **Mesmo critério para todos** | As regras de coleta, classificação e exibição não dependem de partido ou governo. Qualquer exceção é documentada publicamente. |
| P4 | **Causa explícita** | Toda mudança informa sua causa (seção 5.3). "Voltou ao valor anterior porque o prazo expirou" é diferente de "foi aumentado". |
| P5 | **Valores comparáveis** | Valores monetários são exibidos nominais **e** corrigidos pela inflação (IPCA), com a data-base indicada. |
| P6 | **Verificável** | Dados, metodologia e histórico de revisão abertos (CC BY 4.0) e código aberto (AGPL-3.0). Cada número publicado pode ser conferido na fonte oficial, e qualquer pessoa pode ler no código como ele foi coletado e calculado. |
| P7 | **Erros corrigidos às claras** | Correções ficam registradas num histórico público por evento. Nada é apagado em silêncio. |

## 4. Público e perguntas que o sistema responde

**Público principal:** cidadão comum, pelo celular, a partir de um link recebido em grupo de WhatsApp ou rede social.
**Público secundário:** jornalistas, checadores de fatos, professores e pesquisadores.

Perguntas-alvo:

- "É verdade que o governo X aumentou o imposto da gasolina?"
- "Esse imposto foi zerado de vez ou só até uma data?"
- "Quanto o governo realmente gastou com a política Y para indígenas em cada ano, já descontada a inflação?"
- "Quem votou a favor da lei que mudou isso?"
- "Esse programa foi extinto ou só mudou de nome?"

## 5. Modelo de dados

### 5.1 Entidades

```
Tema ─┬─< Indicador ─< Evento >─ Ato >─ Agente
      │                 │                  │
      │                 └─< Observação     └─ Mandato
      └─< Ação orçamentária (mapeamento)
Ato ─< Votação ─< Voto >─ Parlamentar
```

| Entidade | Descrição | Campos principais |
|---|---|---|
| **Tema** | Assunto navegável pelo cidadão | `id`, `nome` ("Combustíveis", "Povos indígenas"), `categoria` (tributo / política pública), `descrição` |
| **Indicador** | Série que pode mudar ao longo do tempo | `id`, `tema_id`, `nome` ("PIS/Cofins sobre gasolina"), `unidade` (R$/litro, %, R$), `tipo` (alíquota / orçamento / regra) |
| **Observação** | Valor do indicador num intervalo de tempo | `indicador_id`, `valor`, `vigente_de`, `vigente_ate`, `fonte_url` |
| **Evento** | Mudança no valor de um indicador | `id`, `indicador_id`, `data_efeito`, `valor_antes`, `valor_depois`, `causa` (5.3), `ato_id`, `ato_origem_id` (para expirações), `fonte_url`, `status_revisao` |
| **Ato** | Documento oficial | `id`, `tipo` (Lei, LC, MP, Decreto, Portaria, Convênio, Decisão judicial), `numero`, `data_assinatura`, `data_publicacao`, `vigencia_inicio`, `vigencia_fim_prevista`, `ementa`, `url_dou`, `url_planalto`, `urn_lexml` |
| **Agente** | Quem assinou | `id`, `nome`, `cargo`, `mandato_id` |
| **Mandato** | Período de governo | `id`, `presidente`, `inicio`, `fim`, `partido_na_posse` |
| **Votação / Voto** | Votação no Congresso ligada a um ato | `casa`, `data`, `resultado`, voto por parlamentar e orientação de bancada |
| **Ação orçamentária** | Código do orçamento ligado a um tema | `codigo_acao`, `codigo_programa`, `ppa` (2016-19, 2020-23, 2024-27), `tema_id`, `justificativa_mapeamento` |

### 5.2 Orçamento: estágios separados

Valores de política pública são sempre exibidos por estágio, porque cada um conta uma história diferente:

| Estágio | Significado |
|---|---|
| Dotação inicial | O que a lei orçamentária previu |
| Dotação atualizada | Previsão após créditos e cortes durante o ano |
| Empenhado | Comprometido (reservado para um gasto) |
| Liquidado | Serviço ou bem entregue e verificado |
| Pago | Dinheiro que efetivamente saiu |
| Restos a pagar pagos | Pagos no ano, mas comprometidos em anos anteriores |

A visão padrão compara **dotação atualizada × pago**, a diferença que costuma separar o "anunciado" do "feito".

### 5.3 Causa da mudança (campo obrigatório)

| Código | Texto exibido | Atribuição |
|---|---|---|
| `ATO_NOVO` | Alterado por novo ato | Quem assinou o ato |
| `EXPIRACAO_PREVISTA` | Prazo previsto no ato original terminou | **Quem assinou o ato original**, com o ato original em destaque. Se o governo seguinte podia prorrogar e não prorrogou, isso também é informado. |
| `PRORROGACAO` | Prazo estendido | Quem assinou a prorrogação |
| `REVOGACAO` | Ato anterior revogado | Quem assinou a revogação |
| `DECISAO_JUDICIAL` | Determinado pela Justiça | Tribunal e processo |
| `LEI_CONGRESSO` | Lei aprovada pelo Congresso | Congresso, com link para a votação; sanção ou veto presidencial informados à parte |
| `REAJUSTE_AUTOMATICO` | Regra de reajuste já existente | Ato que criou a regra |

O caso `EXPIRACAO_PREVISTA` é o que mais desmonta a narrativa "zerou × aumentou", por isso a interface dá a ele um destaque próprio (seção 8).

### 5.4 Mapeamento entre planos plurianuais

Programas e ações do orçamento mudam de código e de nome a cada PPA. O mapeamento de ações para temas é feito **por curadoria humana**, com uma justificativa escrita e pública para cada ligação. Sem isso, um programa renomeado pareceria extinto.

## 6. Fontes de dados

> Validadas na Fase 0 em 01/11/2026. Detalhes em [FASE0.md](FASE0.md).

| Fonte | Uso no gov-eye | Acesso | Fase 0 |
|---|---|---|---|
| **SIOP** (`www1.siop.planejamento.gov.br/sparql/`) | **Orçamento: fonte principal.** Todos os estágios, de projeto de lei a pago | SPARQL público, sem chave, anos 2000–2026 | ✅ OK |
| **Portal da Transparência**, arquivos (`/download-de-dados/orcamento-despesa/{ano}`) | Orçamento: conferência automática do SIOP | CSV anual, sem chave; sem estágio "liquidado" | ✅ OK, bate com o SIOP |
| **IBGE** (`servicodados.ibge.gov.br`, tabela 1737) | IPCA para correção monetária | API pública, sem chave | ✅ OK |
| **Diário Oficial da União** (in.gov.br, base de dados) | **Atos: fonte principal.** Tipo, órgão, ementa, texto e link do PDF | ZIP mensal por seção (~530 MB), sem download parcial | ✅ OK |
| **Câmara dos Deputados** (`dadosabertos.camara.leg.br/api/v2`) | Votações (Fase 3) | API REST, sem chave; contém registros de teste a filtrar | ✅ OK |
| **Senado Federal** (`legis.senado.leg.br/dadosabertos/votacao`) | Votações (Fase 3) | API REST, sem chave; o serviço antigo foi desativado em 02/2026 | ✅ OK |
| **Portal da Transparência**, API | Opcional | Chave gratuita | ⏳ Pendente (chave) |
| **Planalto** | Fora do MVP | HTML; derruba conexões após poucos acessos | ⛔ Bloqueado |
| **LexML** | Fora do MVP | Página anti-robô | ⛔ Bloqueado |
| **Receita Federal** (normas) | Fora do MVP | API interna sem documentação | ⚠️ Parcial |

**Regra de precedência:** quando duas fontes divergirem, vale o texto publicado no DOU. A divergência é registrada e exibida. No orçamento, uma divergência entre SIOP e Portal da Transparência bloqueia a publicação do valor até revisão.

## 7. Pipeline de dados

```
[1 Coleta] → [2 Normalização] → [3 Extração de eventos] → [4 Conferência automática] → [5 Publicação]
```

1. **Coleta:** scripts agendados baixam as fontes e guardam o arquivo bruto com data e hash, para auditoria.
2. **Normalização:** os dados são convertidos para o modelo da seção 5.
3. **Extração de eventos:**
   - Orçamento: automática (valores numéricos estruturados por ação e ano).
   - Alíquotas e regras: **semiautomática**. O sistema identifica atos candidatos (por palavras-chave e NCM nas ementas) e propõe o evento, com o trecho literal do ato que comprova o valor.
4. **Conferência automática:** o curador único não tem como revisar cada item a cada coleta, então a publicação não depende de revisão humana. No lugar dela:
   - no orçamento, a divergência entre SIOP e Portal da Transparência bloqueia o ano (seção 6);
   - em cada evento, o trecho citado é conferido com o texto do DOU coletado (`goveye conferir-trechos`) quando o evento entra na curadoria. Os textos filtrados do DOU ficam fora do git, por isso essa conferência ainda não roda na publicação agendada;
   - o site diz na metodologia que os itens não passam por revisão humana individual, mostra o trecho e o link oficial em cada evento e oferece "reportar erro"; correções ficam públicas (P7).
   - A revisão humana continua possível e opcional (`goveye revisar`). Quando feita, fica registrada nos dados abertos (`status_revisao`).
5. **Publicação:** geração do site e dos arquivos de dados abertos (CSV/JSON).

## 8. Interface

### 8.1 Telas

| Tela | Conteúdo |
|---|---|
| **Início** | Busca ("gasolina", "Bolsa Família", "indígenas") e temas em destaque |
| **Tema** | Lista de indicadores do tema, com resumo das mudanças recentes |
| **Linha do tempo** (principal) | Gráfico em degraus do valor ao longo do tempo, com faixas de fundo por mandato. Cada mudança é um ponto clicável; o painel do ponto traz valor antes → depois, causa, ato, signatário e link oficial. |
| **Ato** | Ementa, datas, quem assinou, votação (se houver), todos os eventos causados por ele, links oficiais |
| **Orçamento de um tema** | Barras por ano com dotação × pago, alternância nominal/corrigido pelo IPCA |
| **Metodologia** | Regras deste documento em linguagem simples, fontes e histórico de correções |

### 8.2 Destaque para prazos

Quando um ato tem `vigencia_fim_prevista`, a linha do tempo mostra uma linha tracejada até essa data com o rótulo "prazo previsto no ato". Se a mudança seguinte é uma `EXPIRACAO_PREVISTA`, o ponto liga visualmente os dois atos: o que criou o corte e o prazo em que ele acabou.

### 8.3 Compartilhamento

Cada evento tem uma URL própria e uma imagem de prévia (card) com valor antes → depois, causa e fonte, pensada para circular em WhatsApp e redes sociais, que é onde as versões distorcidas circulam.

### 8.4 Requisitos

- Funciona bem em celular simples e em conexão lenta.
- Acessível (WCAG 2.1 AA), com gráficos acompanhados de tabela.
- Linguagem simples, com glossário para termos como "empenho" e "alíquota ad rem".

## 9. Regras editoriais

Todo texto de evento é gerado por um modelo fixo, por exemplo:

> **{indicador}** passou de **{valor_antes}** para **{valor_depois}** em {data_efeito}.
> Causa: {texto_da_causa}. Ato: {tipo} nº {numero}, assinado por {agente} ({cargo}) em {data_assinatura}. [Ver documento oficial]

- Proibido: adjetivos de juízo, suposição de intenção, comparação entre governos que não seja numérica.
- Permitido: notas de contexto factuais e com fonte (ex.: "O ato original previa vigência até 31/12").
- Notas de contexto seguem as mesmas regras: só fatos com fonte, sem adjetivos de juízo.

## 10. Arquitetura técnica

| Camada | Escolha proposta | Motivo |
|---|---|---|
| Coleta e ETL | Python (httpx, lxml, pandas) | Ecossistema forte para dados públicos |
| Repositório | GitHub, público, código sob AGPL-3.0 | Seção 13 |
| Agendamento | GitHub Actions (cron) | Gratuito e sem cota de minutos para repositórios públicos |
| Armazenamento | YAML de curadoria e instantâneos JSON das coletas, versionados; SQLite derivado, reconstruído a cada carga (ADR 0001) | Simples, auditável, histórico via git |
| Conferência | Checagens automáticas no carregamento e na exportação (seção 7); revisão humana opcional registrada em `revisoes.yaml` | Publicação sem depender da disponibilidade do curador; o que for revisado fica registrado nos dados abertos |
| Site | Next.js com exportação estática; regras, frases e gráficos SVG continuam no Python, que exporta `site.json` (ADR 0002) | Identidade visual e busca no navegador sem perder as regras num lugar só; hospedagem sem servidor |
| Hospedagem | Cloudflare Pages | Custo zero e permite uso comercial (o plano gratuito da Vercel é só para uso não comercial). Com o repositório público, o GitHub Pages também passou a ser gratuito |
| Dados abertos | CSV e JSON publicados junto com o site, licença CC BY 4.0 | Princípio P6 |

## 11. Escopo e fases

### MVP: governo federal, 2018 até hoje

**Fatia 1, tributos:** PIS/Cofins e CIDE sobre gasolina, diesel e etanol.
**Fatia 2, políticas públicas:** orçamento (dotação × pago, nominal e corrigido) das ações ligadas a quatro temas:

| Tema | Observação |
|---|---|
| Povos indígenas | Inclui Funai e saúde indígena |
| Mulheres / enfrentamento à violência | Partir da metodologia do Painel Orçamento Mulher do Senado |
| Bolsa Família | Caso de troca de nome (Bolsa Família → Auxílio Brasil → Bolsa Família); valida o mapeamento da seção 5.4 |
| Minha Casa Minha Vida | Caso de troca de nome (Minha Casa Minha Vida → Casa Verde e Amarela → Minha Casa Minha Vida) |

**Fora do MVP:** estados e municípios (ICMS, CONFAZ), decisões judiciais automatizadas, comparação entre países, qualquer tipo de ranking ou nota de governos.

### Fases

| Fase | Entrega | Critério de pronto |
|---|---|---|
| **0. Validação das fontes** | Script de teste para cada fonte da seção 6; tabela de validação atualizada | Cada fonte do MVP baixada com sucesso e com formato documentado |
| **1. Dados do MVP** | Banco com as duas fatias | 100% dos eventos com fonte oficial, causa e trecho conferido no DOU (seção 7) |
| **2. Site do MVP** | Telas da seção 8.1 (exceto votações) | Funciona em celular; todos os pontos levam ao documento oficial |
| **3. Votações** | Ligação entre atos e votações da Câmara e do Senado, com orientação de bancada por partido | Votos por parlamentar e orientações exibidos nos atos do MVP |
| **4. Expansão** | Novos temas e tributos; avaliar estados | Definido após o feedback do MVP |

## 12. Riscos

| Risco | Mitigação |
|---|---|
| Ser acusado de favorecer um lado | Princípios P2/P3, textos por modelo, metodologia pública, histórico de correções aberto, página "Quem faz" com o responsável identificado |
| Alguém publicar uma cópia alterada do código | A AGPL-3.0 obriga quem publicar uma versão alterada, inclusive como site, a abrir o código dela e indicar as mudanças. A licença não protege o nome: contra quem se passar pelo gov-eye valem as medidas da linha abaixo |
| Terceiros se passarem pelo gov-eye ou divulgarem dados adulterados em nome dele | Domínio oficial único; registro da marca no INPI quando o projeto ganhar alcance; arquivos de dados publicados com hash e assinatura digital para qualquer pessoa conferir a origem; cada evento aponta para o documento oficial, o que expõe números inventados; a licença CC BY 4.0 exige indicar alterações e proíbe sugerir endosso do gov-eye |
| Erro de dado viralizar | Trecho do ato e link oficial ao lado de cada valor; conferência automática (seção 7); botão "reportar erro" em cada evento; correções visíveis (P7). Sem revisão humana obrigatória, o risco é maior nas escolhas editoriais (mapeamento de ações, causa de cada evento) |
| Mudança ou queda de APIs públicas | Arquivo bruto guardado na coleta; testes de contrato por fonte no agendamento |
| Mapeamento de programas contestável | Justificativa pública para cada ligação ação → tema |
| Período eleitoral | Manter a neutralidade e evitar qualquer conteúdo que possa ser lido como propaganda; consultar orientação jurídica antes de campanhas de divulgação |
| Sustentabilidade da curadoria | Começar pequeno; documentar o processo para voluntários; explorar parceria com checadores e universidades |

## 13. Decisões e questões em aberto

### Decidido

- **Revisão no MVP:** a publicação não depende de revisão humana (seção 7). O autor revisa quando puder, sem prazo; os critérios para aceitar revisores voluntários serão definidos depois.
- **Orientação de bancada por partido:** fica para a Fase 3, junto com as votações.
- **Temas do MVP:** povos indígenas, mulheres / enfrentamento à violência, Bolsa Família e Minha Casa Minha Vida (seção 11).
- **Responsável:** pessoa física. O site terá uma página "Quem faz" com o nome do responsável, um contato e uma declaração sobre filiação partidária.
- **Código:** aberto, sob AGPL-3.0, em repositório público. Qualquer pessoa pode usar, estudar e modificar; quem publicar uma versão alterada, inclusive como site, precisa abrir o código dela. Chaves de API ficam só nos secrets do GitHub, nunca no código.
- **Dados:** CC BY 4.0. Uso livre, inclusive comercial, com crédito ao gov-eye e indicação das alterações.

### Em aberto

1. Critério para aceitar revisores voluntários.
2. Orientação jurídica sobre responsabilidade pelo conteúdo antes de uma divulgação ampla, sobretudo em período eleitoral.
