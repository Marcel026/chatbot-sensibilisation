"""Modèles de requêtes et réponses de l'API WhatsApp."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator

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
    wa_enabled: bool


class WebhookResponse(BaseModel):
    """Accusé de réception du webhook."""

    status: Literal["ok"]
    detail: str
