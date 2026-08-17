/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: "export",
  // O FastAPI usa StaticFiles(html=True); diretórios com index.html permitem
  // que /acoes, /fiis e demais rotas funcionem sem uma extensão no Render.
  trailingSlash: true,
};

module.exports = nextConfig;
