export function Selo({ pendente }: { pendente: boolean }) {
  return pendente ? <span className="selo">pendente de revisão</span> : null;
}

// Os gráficos chegam prontos (SVG gerado e escapado no Python); aqui só são inseridos.
export function Grafico({ svg }: { svg: string }) {
  return <div className="grafico-rolagem" dangerouslySetInnerHTML={{ __html: svg }} />;
}
