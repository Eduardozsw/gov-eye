import { site } from "@/lib/dados.ts";

// O índice de busca vira um arquivo estático (/busca.json), baixado só quando o leitor
// abre a busca do topo. Assim as páginas internas não carregam o índice inteiro.
export const dynamic = "force-static";

export function GET() {
  return Response.json(site.busca);
}
