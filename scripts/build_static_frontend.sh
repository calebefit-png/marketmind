#!/usr/bin/env sh
# Gera a exportação estática do Next.js no diretório servido pelo FastAPI.
# Execute antes de publicar mudanças de interface quando o Render estiver
# configurado como serviço Python com rootDir=backend.
set -eu

ROOT_DIR=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
FRONTEND_DIR="$ROOT_DIR/frontend"
STATIC_DIR="$ROOT_DIR/backend/static"

cd "$FRONTEND_DIR"
pnpm install --frozen-lockfile
# O Webpack apresenta consumo de memória mais previsível que o padrão Turbopack
# neste projeto durante a exportação estática completa.
NODE_ENV=production pnpm exec next build --webpack

rm -rf "$STATIC_DIR"
mkdir -p "$STATIC_DIR"
cp -R "$FRONTEND_DIR/out/." "$STATIC_DIR/"
# Alguns chunks minificados podem ser emitidos com espaço final. A remoção torna
# a revisão do patch determinística sem afetar a execução no navegador.
find "$STATIC_DIR" -type f -exec sed -i 's/[[:space:]]\+$//' {} +

printf '%s\n' "Exportação do frontend atualizada em backend/static"
