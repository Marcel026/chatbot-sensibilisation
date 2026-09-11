"""Client asynchrone pour l'API HTTP de wa-automate."""

from __future__ import annotations

from dataclasses import dataclass
import logging

import httpx

from .config import Settings, get_settings

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SendMessageResult:
    """Résultat explicite d'une tentative d'envoi de message."""

    success: bool
    status: str
    message_id: str | None = None
    error: str | None = None


def _masked_destination(destination: str) -> str:
    return f"***{destination[-4:]}" if len(destination) > 4 else "***"


def _to_chat_id(destination: str) -> str:
    """Convertit un numéro E.164 en identifiant de discussion OpenWA."""
    normalized = destination.strip()
    if normalized.endswith(("@c.us", "@g.us")):
        return normalized
    return f"{normalized.lstrip('+')}@c.us"


async def send_message(
    to: str,
    text: str,
    *,
    settings: Settings | None = None,
    http_client: httpx.AsyncClient | None = None,
) -> SendMessageResult:
    """Envoie un texte avec OpenWA.

    Simule l'envoi lorsque OpenWA est desactive.
    """

    if not to.strip():
        return SendMessageResult(
            False, "invalid_input", error="'to' must not be empty"
        )
    if not text.strip():
        return SendMessageResult(
            False, "invalid_input", error="'text' must not be empty"
        )

    current_settings = settings or get_settings()
    if not current_settings.openwa_enabled:
        logger.info(
            "OpenWA mock: message accepted for %s (text_length=%d)",
            _masked_destination(to),
            len(text),
        )
        return SendMessageResult(True, "mock")

    if not current_settings.openwa_api_key:
        return SendMessageResult(
            False,
            "configuration_error",
            error=(
                "OPENWA_API_KEY is required when OPENWA_ENABLED is true"
            ),
        )

    headers = {"apiKey": current_settings.openwa_api_key}
    endpoint = f"{current_settings.openwa_api_url}/sendText"
    payload = {"to": _to_chat_id(to), "content": text}

    try:
        if http_client is not None:
            response = await http_client.post(
                endpoint, json=payload, headers=headers
            )
        else:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    endpoint, json=payload, headers=headers
                )
    except httpx.TimeoutException:
        logger.warning(
            "OpenWA request timed out for %s", _masked_destination(to)
        )
        return SendMessageResult(
            False, "timeout", error="OpenWA request timed out"
        )
    except httpx.RequestError as error:
        logger.warning(
            "OpenWA request failed for %s: %s",
            _masked_destination(to),
            error.__class__.__name__,
        )
        return SendMessageResult(
            False, "connection_error", error=str(error)
        )

    if response.status_code < 200 or response.status_code >= 300:
        logger.warning(
            "OpenWA returned HTTP %d for %s",
            response.status_code,
            _masked_destination(to),
        )
        return SendMessageResult(
            False,
            "http_error",
            error=f"OpenWA returned HTTP {response.status_code}",
        )

    try:
        body = response.json()
    except ValueError:
        return SendMessageResult(
            False,
            "invalid_response",
            error="OpenWA returned a non-JSON response",
        )

    if not isinstance(body, dict) or body.get("success") is not True:
        return SendMessageResult(
            False,
            "api_error",
            error="OpenWA did not confirm message delivery",
        )

    message_id = body.get("data")
    return SendMessageResult(
        True,
        "sent",
        message_id=str(message_id) if message_id is not None else None,
    )
