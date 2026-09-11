"""Client asynchrone pour l'API WhatsApp Cloud (Meta Graph API).

Documentation : https://developers.facebook.com/docs/whatsapp/cloud-api
- Envoi : POST /{API_VERSION}/{PHONE_NUMBER_ID}/messages
- Le numéro destinataire est au format chiffres, sans « + ».
- Limite d'un message texte : 4096 caractères.
"""

from __future__ import annotations

from dataclasses import dataclass
import logging

import httpx

from .config import Settings, get_settings

logger = logging.getLogger(__name__)

GRAPH_API_BASE_URL = "https://graph.facebook.com"
LIMITE_CARACTERES = 4_096


@dataclass(frozen=True)
class SendMessageResult:
    """Résultat explicite d'une tentative d'envoi de message."""

    success: bool
    status: str
    message_id: str | None = None
    error: str | None = None


def _masked_destination(destination: str) -> str:
    return f"***{destination[-4:]}" if len(destination) > 4 else "***"


def _to_wa_id(destination: str) -> str:
    """Convertit un numéro E.164 en identifiant WhatsApp Cloud.

    Accepte également les identifiants de discussion hérités
    (« 228XXXXXXXX@c.us ») et supprime le signe « + ».
    """
    normalized = destination.strip()
    if normalized.endswith("@c.us"):
        normalized = normalized[: -len("@c.us")]
    return normalized.lstrip("+")


async def send_message(
    to: str,
    text: str,
    *,
    settings: Settings | None = None,
    http_client: httpx.AsyncClient | None = None,
) -> SendMessageResult:
    """Envoie un texte via l'API WhatsApp Cloud.

    Simule l'envoi lorsque WhatsApp est désactivé (WA_ENABLED=false).
    """

    if not to.strip():
        return SendMessageResult(
            False, "invalid_input", error="'to' must not be empty"
        )
    if not text.strip():
        return SendMessageResult(
            False, "invalid_input", error="'text' must not be empty"
        )
    if len(text) > LIMITE_CARACTERES:
        return SendMessageResult(
            False,
            "invalid_input",
            error=f"'text' must not exceed {LIMITE_CARACTERES} characters",
        )

    current_settings = settings or get_settings()
    if not current_settings.wa_enabled:
        logger.info(
            "WhatsApp mock : message accepté pour %s (longueur=%d)",
            _masked_destination(to),
            len(text),
        )
        return SendMessageResult(True, "mock")

    if not current_settings.wa_access_token or not current_settings.wa_phone_number_id:
        return SendMessageResult(
            False,
            "configuration_error",
            error=(
                "WA_ACCESS_TOKEN et WA_PHONE_NUMBER_ID sont requis "
                "quand WA_ENABLED est true"
            ),
        )

    endpoint = (
        f"{GRAPH_API_BASE_URL}/{current_settings.wa_api_version}"
        f"/{current_settings.wa_phone_number_id}/messages"
    )
    headers = {
        "Authorization": f"Bearer {current_settings.wa_access_token}"
    }
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": _to_wa_id(to),
        "type": "text",
        "text": {"preview_url": False, "body": text},
    }

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
            "Requête WhatsApp Cloud expirée pour %s",
            _masked_destination(to),
        )
        return SendMessageResult(
            False, "timeout", error="WhatsApp Cloud request timed out"
        )
    except httpx.RequestError as error:
        logger.warning(
            "Requête WhatsApp Cloud échouée pour %s : %s",
            _masked_destination(to),
            error.__class__.__name__,
        )
        return SendMessageResult(
            False, "connection_error", error=str(error)
        )

    if response.status_code < 200 or response.status_code >= 300:
        logger.warning(
            "WhatsApp Cloud a retourné HTTP %d pour %s",
            response.status_code,
            _masked_destination(to),
        )
        return SendMessageResult(
            False,
            "http_error",
            error=f"WhatsApp Cloud returned HTTP {response.status_code}",
        )

    try:
        body = response.json()
    except ValueError:
        return SendMessageResult(
            False,
            "invalid_response",
            error="WhatsApp Cloud returned a non-JSON response",
        )

    messages = body.get("messages") if isinstance(body, dict) else None
    if not isinstance(messages, list) or not messages:
        logger.warning(
            "WhatsApp Cloud n'a pas confirmé la remise pour %s",
            _masked_destination(to),
        )
        return SendMessageResult(
            False,
            "api_error",
            error="WhatsApp Cloud did not confirm message delivery",
        )

    message_id = messages[0].get("id") if isinstance(messages[0], dict) else None
    return SendMessageResult(
        True,
        "sent",
        message_id=str(message_id) if message_id is not None else None,
    )
