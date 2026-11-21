import type { Metadata } from "next";
import { Inter, Space_Grotesk } from "next/font/google";
import Link from "next/link";
import type { ReactNode } from "react";

import { Marca } from "@/components/Olho.tsx";
import { site } from "@/lib/dados.ts";

import "./globals.css";

const texto = Inter({ subsets: ["latin"], variable: "--fonte-texto", display: "swap" });
const titulo = Space_Grotesk({ subsets: ["latin"], variable: "--fonte-titulo", display: "swap" });

export const metadata: Metadata = {
  title: { default: "gov-eye · Quem mudou o quê, e quando", template: "%s · gov-eye" },
  description:
    "Linha do tempo verificável de tributos e políticas públicas federais, com cada mudança ligada ao ato oficial que a causou.",
  // A prévia inclui itens não revisados: não pode ser indexada.
  robots: site.previa ? { index: false, follow: false } : undefined,
};

export default function Layout({ children }: { children: ReactNode }) {
  return (
    <html lang="pt-BR" className={`${texto.variable} ${titulo.variable}`}>
      <body>
        <a className="pular" href="#conteudo">
          Pular para o conteúdo
        </a>
        {site.previa && (
          <div className="faixa-previa" role="note">
            PRÉVIA INTERNA: inclui itens ainda não revisados, marcados com{" "}
            <span className="selo">pendente de revisão</span>. Não divulgue esta versão.
          </div>
        )}
        <header className="topo">
          <div className="topo__dentro">
            <Link className="marca" href="/">
              <Marca />
              gov-eye
            </Link>
            <nav aria-label="Principal">
              <ul>
                <li><Link href="/#temas">Temas</Link></li>
                <li><Link href="/metodologia/">Como verificamos</Link></li>
                <li><Link href="/dados/">Dados abertos</Link></li>
                <li><Link href="/quem-faz/">Quem faz</Link></li>
              </ul>
            </nav>
          </div>
        </header>
        <main id="conteudo">{children}</main>
        <footer className="rodape">
          <div className="rodape__dentro">
            <div>
              <h2>gov-eye</h2>
              <p>
                Todos os números vêm de fontes oficiais do governo federal, com link para o ato ou a base de origem.
                Dados sob licença{" "}
                <a href={site.url_licenca} rel="license">
                  {site.licenca}
                </a>
                . Código aberto sob AGPL-3.0 no <a href="https://github.com/Eduardozsw/gov-eye">GitHub</a>.
              </p>
            </div>
            <div>
              <h2>Temas</h2>
              <ul>
                {site.temas.map((t) => (
                  <li key={t.id}>
                    <Link href={`/tema/${t.id}/`}>{t.nome}</Link>
                  </li>
                ))}
              </ul>
            </div>
            <div>
              <h2>Sobre</h2>
              <ul>
                <li><Link href="/metodologia/">Como verificamos</Link></li>
                <li><Link href="/dados/">Dados abertos</Link></li>
                <li><Link href="/quem-faz/">Quem faz</Link></li>
              </ul>
              <p>Gerado em {site.gerado_em}.</p>
            </div>
          </div>
        </footer>
      </body>
    </html>
  );
}
