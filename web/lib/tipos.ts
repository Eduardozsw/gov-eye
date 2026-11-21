// Formato de web/dados/site.json, gravado por goveye.site.gerar.exportar.
// Os textos já chegam formatados do Python: o front-end não recalcula valores.

export type Ref = { id: string; titulo: string };

export type Correcao = { data: string; o_que_mudou: string; motivo: string };

export type Evento = {
  id: string;
  data_iso: string;
  data: string;
  governo: string | null;
  causa: string;
  expiracao: boolean;
  frase: string;
  valor: string;
  valor_antes: string | null;
  trecho: string;
  nota: string | null;
  ato: Ref;
  origem: Ref | null;
  correcoes: Correcao[];
};

export type Serie = {
  id: string;
  nome: string;
  descricao: string;
  unidade: string;
  grafico: string;
  levantado_ate: string | null;
  valor_atual: string | null;
  eventos: Evento[];
};

export type Orcamento = {
  tem_dados: boolean;
  destaque: { ano: number; pago: string } | null;
  ipca_referencia: string;
  grafico_nominal: string;
  grafico_corrigido: string;
  mini: string;
  anos_mini: string | null;
  frases: { ano: number; texto: string; divergente: boolean }[];
  estagios: string[];
  tabela: { ano: string; valores: string[] }[];
  acoes: { codigo: string; subfuncao: string | null; justificativa: string }[];
  excluidas: { codigo: string; motivo: string }[];
  detalhe: { anos: number[]; linhas: { acao: string; nome: string; valores: string[] }[] } | null;
  divergencias: { ano: number; chave: string; estagio: string; siop: string; portal: string }[];
};

export type Tema = {
  id: string;
  nome: string;
  categoria: "tributo" | "politica";
  descricao: string;
  series?: Serie[];
  orcamento?: Orcamento;
};

export type Ato = {
  id: string;
  titulo: string;
  tipo: string;
  ementa: string;
  assinatura: string;
  publicacao: string;
  governo: string | null;
  signatarios: string[];
  vigencia_fim: string | null;
  url_oficial: string;
  sha256: string | null;
  correcoes: Correcao[];
  eventos: { id: string; frase: string; indicador: string; tema_id: string }[];
};

export type Prazo = {
  ato: Ref;
  data: string;
  data_iso: string;
  futuro: boolean;
  itens: {
    indicador: string;
    tema_id: string;
    evento_id: string;
    frase: string;
    depois: { id: string; data: string; frase: string } | null;
    levantado_ate: string | null;
  }[];
};

export type ItemBusca = { tipo: string; titulo: string; resumo: string; href: string; texto: string };

export type Site = {
  modo: "previa" | "publicacao";
  previa: boolean;
  gerado_em: string;
  licenca: string;
  url_licenca: string;
  config: {
    responsavel: { nome?: string; apresentacao?: string; contato?: string };
    endereco_site: string | null;
  };
  mandatos: { id: string; presidente: string; nome_curto: string; partido: string; inicio: string; fim: string }[];
  temas: Tema[];
  atos: Ato[];
  prazos: Prazo[];
  correcoes: (Correcao & { titulo: string; href: string })[];
  glossario: { id: string; termo: string; definicao: string }[];
  metodologia: {
    tolerancia: string;
    ipca_referencia: string;
    estagios: string[];
    excluidas: { tema: string; codigo: string; motivo: string }[];
  };
  manifesto: { nome: string; kb: number; sha256: string }[];
  busca: ItemBusca[];
  sugestoes: string[];
};
