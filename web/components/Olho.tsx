import { useId } from "react";

// A íris fica num <g> próprio porque a animação CSS (classe olho__iris) substitui o
// atributo transform; o deslocamento até o centro do olho fica no <g> de fora.
export function Olho({ atento }: { atento: boolean }) {
  const id = useId();
  const recorte = `${id}-recorte`;
  const gradiente = `${id}-iris`;
  const contorno = "M8 60 C 50 2, 150 2, 192 60 C 150 118, 50 118, 8 60 Z";
  return (
    <svg className={`olho${atento ? " olho--atento" : ""}`} viewBox="0 0 200 120" aria-hidden="true" focusable="false">
      <defs>
        <clipPath id={recorte}>
          <path d={contorno} />
        </clipPath>
        <radialGradient id={gradiente} cx="45%" cy="40%" r="65%">
          <stop offset="0%" stopColor="#5eead4" />
          <stop offset="45%" stopColor="#6366f1" />
          <stop offset="100%" stopColor="#1e1b4b" />
        </radialGradient>
      </defs>
      <g className="olho__palpebra">
        <path className="olho__esclera" d={contorno} />
        <g clipPath={`url(#${recorte})`}>
          <g transform="translate(100 60)">
            <g className="olho__iris">
              <circle r="31" fill={`url(#${gradiente})`} />
              <circle r="31" fill="none" stroke="#1e1b4b" strokeOpacity=".5" strokeWidth="2" />
              <circle r="13" fill="#070916" />
              <circle className="olho__brilho" cx="-10" cy="-11" r="5" />
              <circle className="olho__brilho" cx="8" cy="9" r="2" opacity=".5" />
            </g>
          </g>
        </g>
        <path className="olho__contorno" d={contorno} />
      </g>
    </svg>
  );
}

export function Marca() {
  return (
    <svg viewBox="0 0 40 24" aria-hidden="true" focusable="false">
      <path d="M2 12 C 10 1, 30 1, 38 12 C 30 23, 10 23, 2 12 Z" fill="none" stroke="currentColor" strokeWidth="2.4" />
      <circle cx="20" cy="12" r="5.5" fill="var(--destaque)" />
      <circle cx="18" cy="10" r="1.6" fill="var(--superficie)" />
    </svg>
  );
}
