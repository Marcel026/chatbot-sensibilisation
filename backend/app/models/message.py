"""Modèles de requêtes et réponses de l'API WhatsApp."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

TOGO_E164_PATTERN = r"^\+228\d{8}$"


class SendMessageRequest(BaseModel):
    """Message sortant, limité aux numéros togolais au format E.164."""

    to: str = Field(pattern=TOGO_E164_PATTERN)
    text: str = Field(min_length=1, max_length=4_096)

    @field_validator("text")
    @classmethod
    def text_must_not_be_whitespace(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("text must not contain only whitespace")
        return value


class SendMessageResponse(BaseModel):
    """Résultat d'une tentative d'envoi."""

    status: Literal["success", "error"]
    message_id: str | None = None
    detail: str


class HealthResponse(BaseModel):
    """État de disponibilité du backend."""

    status: Literal["ok"]
    openwa_enabled: bool


class WebhookPayload(BaseModel):
    """Événement OpenWA entrant attendu par le webhook.

    Exemple de payload OpenWA simulé :
    {"from": "22890000000@c.us", "text": "Bonjour", "timestamp": "..."}
    """

    model_config = ConfigDict(populate_by_name=True)

    from_number: str = Field(alias="from", min_length=1, max_length=128)
    text: str = Field(min_length=1, max_length=4_096)
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


class WebhookResponse(BaseModel):
    """Accusé de réception du webhook."""

    status: Literal["ok"]
    detail: str
