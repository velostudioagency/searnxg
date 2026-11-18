"""Lightweight API key / admin key authentication."""

from __future__ import annotations

import secrets

from fastapi import HTTPException, Request

from .config import AppSettings


def _provided_key(request: Request) -> str:
    auth = request.headers.get("authorization", "")
    if auth.lower().startswith("bearer "):
        return auth[7:].strip()
    return (
        request.headers.get("x-api-key")
        or request.query_params.get("api_key")
        or request.query_params.get("key")
        or ""
    )


def require_api_key(request: Request, settings: AppSettings) -> None:
    if not settings.require_api_key or not settings.api_keys:
        return
    provided = _provided_key(request)
    if not any(secrets.compare_digest(provided, key) for key in settings.api_keys):
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing API key. Pass it as 'Authorization: Bearer <key>' or 'X-API-Key'.",
        )


def require_admin(request: Request, settings: AppSettings) -> None:
    if not settings.admin_key:
        return
    provided = (
        request.headers.get("x-admin-key")
        or request.query_params.get("admin_key")
        or _provided_key(request)
    )
    if not secrets.compare_digest(provided, settings.admin_key):
        raise HTTPException(status_code=403, detail="Invalid admin key.")
