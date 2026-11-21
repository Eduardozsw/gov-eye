"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const LINKS = [
  { href: "/#temas", rotulo: "Temas", prefixo: "/tema/" },
  { href: "/prazos/", rotulo: "Prazos", prefixo: "/prazos" },
  { href: "/metodologia/", rotulo: "Como verificamos", prefixo: "/metodologia" },
  { href: "/dados/", rotulo: "Dados abertos", prefixo: "/dados" },
  { href: "/quem-faz/", rotulo: "Quem faz", prefixo: "/quem-faz" },
];

export function Navegacao() {
  const caminho = usePathname();
  return (
    <nav aria-label="Principal">
      <ul>
        {LINKS.map((l) => (
          <li key={l.href}>
            <Link href={l.href} aria-current={caminho.startsWith(l.prefixo) ? "page" : undefined}>
              {l.rotulo}
            </Link>
          </li>
        ))}
      </ul>
    </nav>
  );
}
