"use client";

import { useRouter } from "next/navigation";
import { useEffect, useId, useMemo, useRef, useState } from "react";

import { buscar, type ItemPreparado, preparar } from "@/lib/busca.ts";
import type { ItemBusca } from "@/lib/tipos.ts";

import { ListaResultados, useItemAtivo } from "./Resultados.tsx";

// Busca disponível em qualquer página, pelo botão do topo, por "/" ou por Ctrl+K.
// O índice (/busca.json) só é baixado na primeira vez que a busca abre.
export function BuscaGlobal() {
  const router = useRouter();
  const id = useId();
  const janela = useRef<HTMLDialogElement>(null);
  const campo = useRef<HTMLInputElement>(null);
  const [indice, setIndice] = useState<ItemPreparado[] | null>(null);
  const [erro, setErro] = useState(false);
  const [valor, setValor] = useState("");

  const resultados = useMemo(() => (indice ? buscar(indice, valor) : []), [indice, valor]);
  const { ativo, setAtivo, aoTeclar } = useItemAtivo(resultados.length);
  const listaId = `${id}-resultados`;

  function abrir() {
    janela.current?.showModal();
    campo.current?.select();
    if (indice || erro) return;
    fetch("/busca.json")
      .then((r) => (r.ok ? r.json() : Promise.reject(r.status)))
      .then((dados: ItemBusca[]) => setIndice(preparar(dados)))
      .catch(() => setErro(true));
  }

  function fechar() {
    janela.current?.close();
  }

  useEffect(() => {
    function atalho(e: KeyboardEvent) {
      const alvo = e.target as HTMLElement;
      const digitando = alvo.isContentEditable || ["INPUT", "TEXTAREA", "SELECT"].includes(alvo.tagName);
      if ((e.key === "k" && (e.ctrlKey || e.metaKey)) || (e.key === "/" && !digitando)) {
        e.preventDefault();
        abrir();
      }
    }
    window.addEventListener("keydown", atalho);
    return () => window.removeEventListener("keydown", atalho);
  });

  function aoEnviar(e: React.FormEvent) {
    e.preventDefault();
    const alvo = resultados[ativo >= 0 ? ativo : 0];
    if (alvo) {
      fechar();
      router.push(alvo.href);
    }
  }

  return (
    <>
      <button type="button" className="abrir-busca" onClick={abrir} aria-haspopup="dialog">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" aria-hidden="true">
          <circle cx="11" cy="11" r="7" />
          <path d="m20 20-3.5-3.5" strokeLinecap="round" />
        </svg>
        <span>Buscar</span>
        <kbd aria-hidden="true">/</kbd>
      </button>

      <dialog
        ref={janela}
        className="janela-busca"
        aria-label="Buscar no gov-eye"
        onClick={(e) => {
          // Clique no fundo escurecido (fora da caixa) fecha a busca.
          if (e.target === e.currentTarget) fechar();
        }}
      >
        <form role="search" onSubmit={aoEnviar} className="janela-busca__caixa">
          <div className="janela-busca__campo">
            <svg className="busca__icone" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" aria-hidden="true">
              <circle cx="11" cy="11" r="7" />
              <path d="m20 20-3.5-3.5" strokeLinecap="round" />
            </svg>
            <label htmlFor={`${id}-campo`} className="pular">
              Pesquise um imposto, programa, ato ou ano
            </label>
            <input
              ref={campo}
              id={`${id}-campo`}
              type="search"
              autoComplete="off"
              spellCheck={false}
              placeholder="Imposto, programa, ato ou ano"
              value={valor}
              onChange={(e) => {
                setValor(e.target.value);
                setAtivo(-1);
              }}
              onKeyDown={aoTeclar}
              role="combobox"
              aria-expanded={valor.trim() !== ""}
              aria-controls={listaId}
              aria-autocomplete="list"
              aria-activedescendant={ativo >= 0 ? `${listaId}-${ativo}` : undefined}
            />
            <button type="button" className="janela-busca__fechar" onClick={fechar}>
              Esc
            </button>
          </div>
          {erro ? (
            <p className="busca__vazio">Não foi possível carregar a busca. Tente recarregar a página.</p>
          ) : (
            <ListaResultados
              id={listaId}
              className="janela-busca__resultados"
              resultados={resultados}
              ativo={ativo}
              aberto={indice !== null && valor.trim() !== ""}
              aoEscolher={fechar}
            />
          )}
        </form>
      </dialog>
    </>
  );
}
