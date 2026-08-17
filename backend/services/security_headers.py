"""Cabeçalhos HTTP defensivos aplicados a respostas públicas do MarketMind."""

from starlette.responses import Response


def apply_security_headers(response: Response, *, production: bool) -> Response:
    """Aplica controles que não mudam o conteúdo renderizado da resposta."""
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    response.headers.setdefault("Permissions-Policy", "camera=(), geolocation=(), microphone=()")
    if production:
        response.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
    return response
