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
