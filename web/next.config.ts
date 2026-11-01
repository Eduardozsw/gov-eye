import type { NextConfig } from "next";

// Site 100% estático (web/out/): pode ser hospedado em qualquer servidor de arquivos,
// sem servidor Node em produção.
const config: NextConfig = {
  output: "export",
  trailingSlash: true,
  images: { unoptimized: true },
};

export default config;
