import fs from "node:fs";
import path from "node:path";

import type { Site } from "./tipos.ts";

// Lido só no build (componentes de servidor). Componentes de cliente recebem o que
// precisam por props.
const CAMINHO = path.join(process.cwd(), "dados", "site.json");

function carregar(): Site {
  if (!fs.existsSync(CAMINHO)) {
    throw new Error(
      `${CAMINHO} não existe. Gere antes com: uv run goveye carregar && uv run goveye site --modo previa`,
    );
  }
  return JSON.parse(fs.readFileSync(CAMINHO, "utf-8")) as Site;
}

export const site = carregar();

export function tema(id: string) {
  return site.temas.find((t) => t.id === id);
}

export function ato(id: string) {
  return site.atos.find((a) => a.id === id);
}

export function mudancas() {
  return site.temas.flatMap((tema) =>
    (tema.series ?? []).flatMap((serie) => serie.eventos.map((evento) => ({ tema, serie, evento }))),
  );
}

export function mudanca(id: string) {
  return mudancas().find((m) => m.evento.id === id);
}

// Endereço público, usado nos links absolutos dos cards de compartilhamento.
// Enquanto site.yaml tiver "PREENCHER", não há endereço válido.
export function enderecoSite(): URL | undefined {
  const e = site.config.endereco_site;
  return e && /^https?:\/\//.test(e) ? new URL(e) : undefined;
}

// E-mail público para avisos de erro; enquanto site.yaml tiver "PREENCHER", não há.
export function contato(): string | undefined {
  const c = site.config.responsavel.contato;
  return c && /^[^\s@]+@[^\s@]+$/.test(c.trim()) ? c.trim() : undefined;
}

export function termo(id: string) {
  return site.glossario.find((t) => t.id === id);
}
