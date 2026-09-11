"""Configuration de l'intégration WhatsApp Cloud API (Meta)."""

from __future__ import annotations

from dataclasses import dataclass
import os
from functools import lru_cache

from dotenv import load_dotenv


def _read_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default

    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False

    raise ValueError(f"{name} must be a boolean value")


@dataclass(frozen=True)
class Settings:
    """Variables d'environnement consommées par le backend WhatsApp."""

    app_env: str
    debug: bool
    log_level: str
    backend_url: str
    wa_enabled: bool = False
    wa_api_version: str = "v23.0"
    wa_phone_number_id: str | None = None
    wa_access_token: str | None = None
    wa_verify_token: str | None = None
    wa_app_secret: str | None = None

    @property
    def is_production(self) -> bool:
        return self.app_env == "prod"

    @property
    def requires_signature(self) -> bool:
        """La signature des webhooks est obligatoire hors mode local."""
        return self.app_env in {"staging", "prod"}


@lru_cache
def get_settings() -> Settings:
    """Charge et normalise la configuration une seule fois par processus."""

    load_dotenv()

    app_env = os.getenv("APP_ENV", "local").strip().lower()
    if app_env not in {"local", "staging", "prod"}:
        raise ValueError("APP_ENV must be one of: local, staging, prod")

    return Settings(
        app_env=app_env,
        debug=_read_bool("DEBUG", False),
        log_level=os.getenv("LOG_LEVEL", "INFO").strip().upper(),
        backend_url=os.getenv(
            "BACKEND_URL", "http://localhost:8000"
        ).rstrip("/"),
        wa_enabled=_read_bool("WA_ENABLED", False),
        wa_api_version=os.getenv("WA_API_VERSION", "v23.0").strip(),
        wa_phone_number_id=os.getenv("WA_PHONE_NUMBER_ID") or None,
        wa_access_token=os.getenv("WA_ACCESS_TOKEN") or None,
        wa_verify_token=os.getenv("WA_VERIFY_TOKEN") or None,
        wa_app_secret=os.getenv("WA_APP_SECRET") or None,
    )
