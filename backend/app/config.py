"""Configuration de l'intégration OpenWA."""

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
    openwa_enabled: bool
    openwa_api_url: str
    openwa_api_key: str | None
    openwa_instance_id: str | None
    webhook_secret: str | None
    twilio_account_sid: str | None
    twilio_auth_token: str | None
    twilio_phone_number: str | None

    @property
    def is_production(self) -> bool:
        return self.app_env == "prod"


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
        openwa_enabled=_read_bool("OPENWA_ENABLED", False),
        openwa_api_url=os.getenv(
            "OPENWA_API_URL", "http://localhost:8080"
        ).rstrip("/"),
        openwa_api_key=os.getenv("OPENWA_API_KEY") or None,
        openwa_instance_id=os.getenv("OPENWA_INSTANCE_ID") or None,
        webhook_secret=os.getenv("WEBHOOK_SECRET") or None,
        twilio_account_sid=os.getenv("TWILIO_ACCOUNT_SID") or None,
        twilio_auth_token=os.getenv("TWILIO_AUTH_TOKEN") or None,
        twilio_phone_number=os.getenv("TWILIO_PHONE_NUMBER") or None,
    )
