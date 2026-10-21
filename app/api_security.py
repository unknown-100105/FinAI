"""Optional bearer authentication boundary for the FinAI HTTP API.

Development stays frictionless by default. Production deployments fail closed unless
a strong server-side token is configured. For browser deployments, prefer an identity-
aware reverse proxy/OIDC gateway rather than embedding a shared secret in frontend code.
"""
from __future__ import annotations

import hmac
import os

from starlette.responses import JSONResponse


class FinAIAPIAuthMiddleware:
    """ASGI middleware that protects every HTTP route except the health probe."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "")
        method = scope.get("method", "GET").upper()
        if path == "/health" or method == "OPTIONS":
            await self.app(scope, receive, send)
            return

        mode = os.getenv("FINAI_API_AUTH_MODE", "development").strip().casefold()
        environment = os.getenv("FINAI_ENV", "development").strip().casefold()
        production = environment in {"production", "prod"}
        auth_required = production or mode == "bearer"

        if mode not in {"development", "bearer"}:
            response = JSONResponse(
                status_code=503,
                content={"detail": "Invalid FINAI_API_AUTH_MODE configuration."},
            )
            await response(scope, receive, send)
            return

        if not auth_required:
            await self.app(scope, receive, send)
            return

        expected = os.getenv("FINAI_API_BEARER_TOKEN", "").strip()
        if len(expected) < 32:
            response = JSONResponse(
                status_code=503,
                content={
                    "detail": (
                        "API authentication is required but FINAI_API_BEARER_TOKEN "
                        "is missing or shorter than 32 characters."
                    )
                },
            )
            await response(scope, receive, send)
            return

        headers = {
            key.lower(): value
            for key, value in scope.get("headers", [])
        }
        authorization = headers.get(b"authorization", b"").decode("latin-1")
        scheme, separator, supplied = authorization.partition(" ")
        if (
            not separator
            or scheme.casefold() != "bearer"
            or not supplied
            or not hmac.compare_digest(supplied, expected)
        ):
            response = JSONResponse(
                status_code=401,
                content={"detail": "A valid bearer token is required."},
                headers={"WWW-Authenticate": "Bearer"},
            )
            await response(scope, receive, send)
            return

        await self.app(scope, receive, send)
