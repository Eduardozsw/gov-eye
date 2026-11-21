import { ImageResponse } from "next/og";

import { mudanca, mudancas, site } from "@/lib/dados.ts";

// Card que aparece quando o link de uma mudança é colado no WhatsApp ou numa rede social:
// valor antes → depois, causa e fonte, legível mesmo em miniatura. Gerado no build (PNG estático).
// É uma rota, e não opengraph-image.tsx, para o arquivo exportado terminar em .png: sem extensão,
// a hospedagem estática não serve o tipo image/png e o WhatsApp descarta a imagem.

const TAMANHO = { width: 1200, height: 630 };

export const dynamic = "force-static";
export const dynamicParams = false;

export function generateStaticParams() {
  const todas = mudancas();
  return todas.length ? todas.map((m) => ({ id: m.evento.id })) : [{ id: "nenhuma" }];
}

const COR = {
  fundo: "#0b0d1c",
  texto: "#eef0ff",
  suave: "#a5abc9",
  destaque: "#8b8cff",
  verde: "#5eead4",
  expiracao: "#fb923c",
  alerta: "#fde68a",
};

export async function GET(_: Request, { params }: { params: Promise<{ id: string }> }) {
  const m = mudanca((await params).id);
  if (!m) return new ImageResponse(<div style={{ display: "flex", background: COR.fundo, width: "100%", height: "100%" }} />, TAMANHO);
  const { serie, evento: e } = m;
  const previa = site.previa;

  return new ImageResponse(
    (
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          width: "100%",
          height: "100%",
          padding: "56px 64px",
          background: COR.fundo,
          backgroundImage: "radial-gradient(circle at 85% 0%, #2a2a6e 0%, transparent 55%)",
          color: COR.texto,
        }}
      >
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 16, fontSize: 34 }}>
            <svg width="62" height="38" viewBox="0 0 40 24">
              <path d="M2 12 C 10 1, 30 1, 38 12 C 30 23, 10 23, 2 12 Z" fill="none" stroke={COR.texto} strokeWidth="2.4" />
              <circle cx="20" cy="12" r="5.5" fill={COR.destaque} />
              <circle cx="18" cy="10" r="1.6" fill={COR.fundo} />
            </svg>
            gov-eye
          </div>
          {previa && (
            <div style={{ display: "flex", background: COR.alerta, color: "#3b2a00", padding: "6px 18px", borderRadius: 999, fontSize: 24 }}>
              PRÉVIA · NÃO DIVULGAR
            </div>
          )}
        </div>

        <div style={{ display: "flex", marginTop: 44, fontSize: 40, color: COR.suave }}>{serie.nome}</div>

        <div style={{ display: "flex", alignItems: "baseline", gap: 24, marginTop: 16, whiteSpace: "nowrap" }}>
          {e.valor_antes && (
            <div style={{ display: "flex", fontSize: 64, color: COR.suave, textDecoration: "line-through" }}>{e.valor_antes}</div>
          )}
          {e.valor_antes && <div style={{ display: "flex", fontSize: 64, color: COR.verde }}>→</div>}
          <div style={{ display: "flex", fontSize: e.valor_antes ? 88 : 96, color: COR.texto }}>{e.valor}</div>
          <div style={{ display: "flex", fontSize: 30, color: COR.suave }}>por litro</div>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: 20, marginTop: 28, fontSize: 32 }}>
          <div style={{ display: "flex" }}>{e.data}</div>
          {e.governo && <div style={{ display: "flex", color: COR.suave }}>governo {e.governo}</div>}
          <div
            style={{
              display: "flex",
              padding: "6px 20px",
              borderRadius: 999,
              background: e.expiracao ? "#431407" : "#1f2150",
              color: e.expiracao ? COR.expiracao : COR.texto,
            }}
          >
            {e.causa}
          </div>
        </div>

        <div
          style={{
            display: "flex",
            marginTop: "auto",
            paddingTop: 24,
            borderTop: `2px solid #262b4d`,
            justifyContent: "space-between",
            fontSize: 28,
            color: COR.suave,
          }}
        >
          <div style={{ display: "flex" }}>Fonte: {e.ato.titulo} · Diário Oficial da União</div>
          <div style={{ display: "flex", color: COR.verde }}>Confira no link</div>
        </div>
      </div>
    ),
    TAMANHO,
  );
}
