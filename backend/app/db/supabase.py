"""Supabase client singleton."""

from __future__ import annotations

from supabase import Client, create_client

from app.config import settings

_client: Client | None = None


def get_client() -> Client:
    global _client
    if _client is None:
        if not settings.supabase_url or not settings.supabase_key:
            raise RuntimeError(
                "SUPABASE_URL and SUPABASE_KEY must be set in environment / .env"
            )
        _client = create_client(settings.supabase_url, settings.supabase_key)
    return _client
