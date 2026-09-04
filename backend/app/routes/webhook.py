"""Route de réception des événements WhatsApp transmis par OpenWA."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
import hmac
import json
import logging
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Request, status

from ..config import get_settings
from ..models.message import WebhookPayload, WebhookResponse

logger = logging.getLogger(__name__)
router = APIRouter(tags=["webhook"])
EVENT_LOG_PATH = (
    Path(__file__).resolve().parents[3]
    / "data"
    / "processed"
    / "whatsapp_webhook_events.json"
)
_event_log_lock = asyncio.Lock()
MAX_STORED_EVENTS = 500


def _mask_sender(sender: str) -> str:
    return f"***{sender[-4:]}" if len(sender) > 4 else "***"


def _append_event(payload: WebhookPayload) -> None:
    """Ajoute un événement minimisé.

    Les messages et numéros complets ne sont pas conservés.
    """

    EVENT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    if EVENT_LOG_PATH.exists():
        with EVENT_LOG_PATH.open(encoding="utf-8") as file:
            events: Any = json.load(file)
        if not isinstance(events, list):
            raise ValueError("Webhook event log must contain a JSON list")
    else:
        events = []

    events.append(
        {
            "from": _mask_sender(payload.from_number),
            "text_length": len(payload.text),
            "timestamp": payload.timestamp.isoformat(),
            "received_at": datetime.now(timezone.utc).isoformat(),
        }
    )
    temporary_path = EVENT_LOG_PATH.with_suffix(".tmp")
    with temporary_path.open("w", encoding="utf-8") as file:
        json.dump(events[-MAX_STORED_EVENTS:], file, ensure_ascii=False)
    temporary_path.replace(EVENT_LOG_PATH)


async def _store_event(payload: WebhookPayload) -> None:
    async with _event_log_lock:
        try:
            await asyncio.to_thread(_append_event, payload)
        except (OSError, ValueError, json.JSONDecodeError) as error:
            logger.error("Unable to store minimized webhook event: %s", error)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unable to store webhook event",
            ) from error


def _validate_secret(request: Request) -> None:
    settings = get_settings()
    expected_secret = settings.webhook_secret
    received_secret = (
        request.headers.get("X-Webhook-Secret")
        or request.query_params.get("secret")
    )

    if expected_secret:
        if not received_secret or not hmac.compare_digest(
            received_secret, expected_secret
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid webhook secret",
            )
        return

    if settings.requires_webhook_secret:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="WEBHOOK_SECRET must be configured outside local mode",
        )

    logger.warning("Webhook secret is not configured in local mode")


@router.post(
    "/webhook/whatsapp",
    response_model=WebhookResponse,
    responses={
        401: {"description": "Invalid webhook secret"},
        503: {"description": "Missing webhook secret outside local mode"},
    },
)
async def receive_whatsapp_webhook(
    payload: WebhookPayload, request: Request
) -> WebhookResponse:
    """Valide, minimise et persiste un événement entrant OpenWA."""

    _validate_secret(request)
    logger.info(
        "Received WhatsApp webhook from %s (text_length=%d)",
        _mask_sender(payload.from_number),
        len(payload.text),
    )
    await _store_event(payload)
    return WebhookResponse(status="ok", detail="Webhook received")
