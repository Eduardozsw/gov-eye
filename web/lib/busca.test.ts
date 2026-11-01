import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { test } from "node:test";

import { buscar, normalizar, preparar, termos } from "./busca.ts";
import type { Site } from "./tipos.ts";

const INDICE = preparar([
  { tipo: "Tema", titulo: "Povos indígenas", resumo: "", href: "/tema/povos-indigenas/", texto: "Povos indígenas orçamento" },
  { tipo: "Mudança", titulo: "PIS/Cofins sobre a gasolina, 23/06/2022", resumo: "", href: "/tema/combustiveis/#x",
    texto: "o valor de PIS/Cofins sobre a gasolina foi zerado (era R$ 0,7925) imposto" },
  { tipo: "Ato oficial", titulo: "Medida Provisória nº 1.157/2023", resumo: "", href: "/ato/mp-1157-2023/", texto: "" },
]);

test("normaliza acentos e números com ponto", () => {
  assert.equal(normalizar("Indígena 1.157"), "indigena 1157");
  assert.deepEqual(termos("Quem zerou o imposto da gasolina?"), ["zerou", "imposto", "gasolina"]);
});

test("encontra por sinônimo, plural e número", () => {
  assert.equal(buscar(INDICE, "Quem zerou o imposto da gasolina?")[0].href, "/tema/combustiveis/#x");
  assert.equal(buscar(INDICE, "indígena")[0].href, "/tema/povos-indigenas/");
  assert.equal(buscar(INDICE, "MP 1.157")[0].href, "/ato/mp-1157-2023/");
  assert.deepEqual(buscar(INDICE, "o que é isso"), []);
});

test("toda sugestão da página inicial tem resultado nos dados exportados", (t) => {
  const caminho = path.join(import.meta.dirname, "..", "dados", "site.json");
  if (!fs.existsSync(caminho)) return t.skip("web/dados/site.json ainda não foi gerado");
  const site = JSON.parse(fs.readFileSync(caminho, "utf-8")) as Site;
  const indice = preparar(site.busca);
  for (const s of site.sugestoes) {
    assert.ok(buscar(indice, s).length > 0, `sem resultado para: ${s}`);
  }
});
