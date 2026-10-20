"""Application settings.

All environment lookups live here so the rest of the code depends on a single,
importable configuration object instead of scattered ``os.getenv`` calls.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional


def _int_env(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or raw == "":
        return default
    try:
        return int(raw)
    except ValueError:
        return default


@dataclass(frozen=True)
class Settings:
    # PostgreSQL
    postgres_user: str
    postgres_password: str
    postgres_db: str
    postgres_host: str
    postgres_port: int

    # Keycloak
    keycloak_url: str
    keycloak_url_public: str
    keycloak_realm: str
    keycloak_client_id: str

    # MetaHub
    metahub_host: str

    # File storage
    storage_root: str
    max_upload_mb: int

    # Frontend (served as a static SPA when set)
    frontend_dist: Optional[str]

    @property
    def keycloak_issuer(self) -> str:
        if self.keycloak_url_public and self.keycloak_realm:
            return f"{self.keycloak_url_public.rstrip('/')}/realms/{self.keycloak_realm}"
        return ""

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_mb * 1024 * 1024


def load_settings() -> Settings:
    keycloak_url = os.getenv("KEYCLOAK_URL", "")
    return Settings(
        postgres_user=os.getenv("POSTGRES_USER", "postgres"),
        postgres_password=os.getenv("POSTGRES_PASSWORD", "password"),
        postgres_db=os.getenv("POSTGRES_DB", "tc"),
        postgres_host=os.getenv("POSTGRES_HOST", "localhost"),
        postgres_port=_int_env("POSTGRES_PORT", 5432),
        keycloak_url=keycloak_url,
        keycloak_url_public=os.getenv("KEYCLOAK_URL_PUBLIC", "") or keycloak_url,
        keycloak_realm=os.getenv("KEYCLOAK_REALM", ""),
        keycloak_client_id=os.getenv("KEYCLOAK_CLIENT_ID", ""),
        metahub_host=os.getenv("TC_METAHUB", "localhost:8033"),
        storage_root=os.getenv("TC_STORAGE_ROOT", "./storage"),
        max_upload_mb=_int_env("TC_MAX_UPLOAD_MB", 25),
        frontend_dist=os.getenv("FRONTEND_DIST") or None,
    )


settings = load_settings()
