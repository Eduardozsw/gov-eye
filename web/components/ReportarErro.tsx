"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

// Abre o e-mail do leitor já com o link da página e um roteiro do que informar.
export function ReportarErro({ contato, assunto, caminho }: { contato?: string; assunto: string; caminho: string }) {
  const [url, setUrl] = useState(caminho);

  useEffect(() => {
    setUrl(new URL(caminho, window.location.origin).href);
  }, [caminho]);

  if (!contato) {
    return (
      <p className="reportar">
        Encontrou um erro? <Link href="/quem-faz/">Veja como avisar</Link>.
      </p>
    );
  }
  const corpo = [
    `Página: ${url}`,
    "",
    "O que está errado:",
    "",
    "Onde está a informação correta (link do documento oficial, se tiver):",
    "",
  ].join("\n");
  return (
    <p className="reportar">
      Encontrou um erro?{" "}
      <a href={`mailto:${contato}?subject=${encodeURIComponent(`Erro no gov-eye: ${assunto}`)}&body=${encodeURIComponent(corpo)}`}>
        Avise por e-mail
      </a>
      . Cada correção fica registrada no <Link href="/correcoes/">histórico público</Link>.
    </p>
  );
}
