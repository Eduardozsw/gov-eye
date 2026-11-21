"use client";

import { useEffect, useState } from "react";

// Botões de compartilhar uma página. O endereço completo só é conhecido no navegador
// (o site é estático e pode estar em qualquer domínio), por isso é montado depois de carregar.
export function Compartilhar({ texto, caminho }: { texto: string; caminho: string }) {
  const [url, setUrl] = useState(caminho);
  const [podeNativo, setPodeNativo] = useState(false);
  const [copiado, setCopiado] = useState(false);

  useEffect(() => {
    setUrl(new URL(caminho, window.location.origin).href);
    setPodeNativo(typeof navigator.share === "function");
  }, [caminho]);

  async function copiar() {
    try {
      await navigator.clipboard.writeText(url);
      setCopiado(true);
      setTimeout(() => setCopiado(false), 2500);
    } catch {
      window.prompt("Copie o link:", url);
    }
  }

  return (
    <div className="compartilhar">
      <a className="botao botao--whatsapp" href={`https://wa.me/?text=${encodeURIComponent(`${texto}\n${url}`)}`}>
        Enviar no WhatsApp
      </a>
      <button type="button" className="botao" onClick={copiar}>
        {copiado ? "Link copiado" : "Copiar link"}
      </button>
      {podeNativo && (
        <button type="button" className="botao" onClick={() => navigator.share({ text: texto, url }).catch(() => {})}>
          Compartilhar…
        </button>
      )}
      <span className="sr-only" aria-live="polite">
        {copiado ? "Link copiado" : ""}
      </span>
    </div>
  );
}
