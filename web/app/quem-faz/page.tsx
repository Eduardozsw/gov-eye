import type { Metadata } from "next";
import Link from "next/link";

import { site } from "@/lib/dados.ts";

export const metadata: Metadata = { title: "Quem faz" };

export default function QuemFaz() {
  const r = site.config.responsavel;
  return (
    <div className="pagina">
      <h1>Quem faz</h1>
      <p>
        O gov-eye é mantido por <strong>{r.nome}</strong>, pessoa física, sem vínculo com partido ou governo.
      </p>
      <p>{r.apresentacao}</p>
      <p>
        Encontrou um erro? Escreva para {r.contato} com o link da página. As correções são registradas e o histórico
        fica público.
      </p>
      <h2>Como saber se uma cópia é verdadeira</h2>
      <p>
        Cada arquivo de dados publicado tem uma impressão digital (SHA-256), listada na página{" "}
        <Link href="/dados/">Dados abertos</Link>. Se alguém divulgar um número atribuído ao gov-eye, confira se ele está
        aqui{site.config.endereco_site ? `, no endereço ${site.config.endereco_site}` : ""}, e siga o link até o ato
        oficial.
      </p>
    </div>
  );
}
