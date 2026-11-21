import type { ItemBusca } from "./tipos.ts";

// Busca feita no navegador, sobre o índice exportado pelo Python. Sem servidor:
// o site continua estático.

const PALAVRAS_VAZIAS = new Set(
  ("a o as os um uma uns umas de da do das dos e em no na nos nas para pra por pelo pela " +
    "com sem que qual quais quem quanto quanta quantos quantas foi foram era e ser sobre " +
    "ao aos se seu sua como onde quando ate n")
    .split(" "),
);

// Palavras do leitor -> palavras que aparecem nos textos oficiais e nas frases do site.
const SINONIMOS: Record<string, string[]> = {
  zerou: ["zerado", "zero"],
  zerar: ["zerado", "zero"],
  zeraram: ["zerado", "zero"],
  aumentou: ["subiu", "voltou"],
  aumento: ["subiu", "voltou"],
  aumentaram: ["subiu", "voltou"],
  voltou: ["voltou", "cobrado"],
  baixou: ["caiu", "zerado", "reduz"],
  reduziu: ["caiu", "zerado", "reduz"],
  cortou: ["caiu", "pago"],
  corte: ["caiu", "pago"],
  gastou: ["pago"],
  gasto: ["pago", "orcamento"],
  verba: ["orcamento", "autorizado"],
  dinheiro: ["orcamento", "pago"],
  mp: ["medida", "provisoria"],
  lc: ["lei", "complementar"],
  violencia: ["violencia", "enfrentamento"],
  feminicidio: ["violencia", "mulheres"],
  moradia: ["casa", "habitacao"],
  casas: ["casa", "habitacao"],
  combustivel: ["combustiveis", "gasolina", "diesel"],
  faculdade: ["faculdade", "universidade"],
  faculdades: ["faculdade", "universidade"],
  creche: ["creche", "infantil"],
  remedio: ["remedio", "farmacia"],
  remedios: ["remedio", "farmacia"],
  queimada: ["incendio"],
  queimadas: ["incendio"],
  desmatamento: ["desmatamento", "fiscalizacao"],
};

export function normalizar(texto: string): string {
  return texto
    .normalize("NFD")
    .replace(/\p{Diacritic}/gu, "")
    .toLowerCase()
    .replace(/(\d)\.(\d)/g, "$1$2"); // 1.157 -> 1157
}

export function palavras(texto: string): string[] {
  return normalizar(texto).split(/[^a-z0-9]+/).filter(Boolean);
}

export function termos(consulta: string): string[] {
  return palavras(consulta).filter((p) => !PALAVRAS_VAZIAS.has(p));
}

export type ItemPreparado = ItemBusca & { _titulo: string[]; _texto: string[] };

export function preparar(indice: ItemBusca[]): ItemPreparado[] {
  return indice.map((i) => ({ ...i, _titulo: palavras(i.titulo), _texto: palavras(i.texto) }));
}

function casa(lista: string[], termo: string): boolean {
  const alternativas = [termo, ...(SINONIMOS[termo] ?? [])];
  // Prefixo cobre plural e flexão ("indígena" encontra "indígenas"); termos curtos exigem igualdade.
  return lista.some((p) => alternativas.some((a) => (a.length >= 3 ? p.startsWith(a) : p === a)));
}

const PRIORIDADE: Record<string, number> = {
  Tema: 3,
  Imposto: 2,
  Mudança: 2,
  "Ato oficial": 2,
  Orçamento: 1,
  "Ação do orçamento": 0,
};

export function buscar(indice: ItemPreparado[], consulta: string, limite = 8): ItemBusca[] {
  const ts = termos(consulta);
  if (ts.length === 0) return [];
  const minimo = Math.max(1, Math.ceil(ts.length / 2));
  return indice
    .map((item) => {
      let achados = 0;
      let pontos = 0;
      for (const t of ts) {
        if (casa(item._titulo, t)) {
          achados += 1;
          pontos += 2;
        } else if (casa(item._texto, t)) {
          achados += 1;
          pontos += 1;
        }
      }
      return { item, achados, pontos };
    })
    .filter((r) => r.achados >= minimo)
    .sort(
      (a, b) =>
        b.achados - a.achados ||
        b.pontos - a.pontos ||
        (PRIORIDADE[b.item.tipo] ?? 0) - (PRIORIDADE[a.item.tipo] ?? 0),
    )
    .slice(0, limite)
    .map(({ item: { _titulo, _texto, ...resto } }) => resto);
}
