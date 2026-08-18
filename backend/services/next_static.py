"""Compatibilidade de payloads RSC para a exportação estática do Next.js."""

from __future__ import annotations

from pathlib import Path


def rsc_payload_path(static_dir: Path, request_path: str) -> Path | None:
    """Resolve o arquivo ``index.txt`` exportado para uma rota do App Router.

    O Next.js exporta o HTML da rota em ``<rota>/index.html`` e o payload RSC
    necessário às navegações internas em ``<rota>/index.txt``. O StaticFiles
    entrega o HTML corretamente, mas não transforma uma solicitação RSC da rota
    em seu payload correspondente. Esta função preserva o diretório estático e
    recusa qualquer caminho fora dele.
    """

    relative_route = request_path.strip("/")
    relative_payload = Path(relative_route) / "index.txt" if relative_route else Path("index.txt")

    root = static_dir.resolve()
    candidate = (root / relative_payload).resolve()
    try:
        candidate.relative_to(root)
    except ValueError:
        return None

    return candidate if candidate.is_file() else None
