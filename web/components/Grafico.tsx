"use client";

import { useEffect, useRef } from "react";

// Os gráficos chegam prontos (SVG gerado e escapado no Python); aqui só são inseridos.
// No celular o gráfico rola na horizontal: começa no fim, onde estão as mudanças recentes.
export function Grafico({ svg }: { svg: string }) {
  const caixa = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const c = caixa.current;
    if (c) c.scrollLeft = c.scrollWidth;
  }, []);
  return <div ref={caixa} className="grafico-rolagem" dangerouslySetInnerHTML={{ __html: svg }} />;
}
