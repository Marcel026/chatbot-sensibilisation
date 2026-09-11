"""Route de réception des événements WhatsApp transmis par Meta (Cloud API).

Flux :
1. GET  /webhook/whatsapp : vérification du webhook par Meta (hub.challenge).
2. POST /webhook/whatsapp : message entrant → réponse RAG → envoi via
   l'API WhatsApp Cloud, puis journalisation minimisée (aucun contenu ni
   numéro complet conservé).

Référence payload :
https://developers.facebook.com/docs/whatsapp/cloud-api/webhooks/payload-examples
"""

from __future__ import annotations

import asyncio
from collections import deque
from datetime import datetime, timezone
import hashlib
import hmac
import json
import logging
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import PlainTextResponse

from .. import rag_service
from ..cloud_api_client import send_message
from ..config import get_settings
from ..models.message import WebhookResponse

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

# Anti-doublon : Meta rejoue les webhooks non acquittés dans les temps.
_messages_deja_traites: deque[str] = deque(maxlen=500)
_dedup_lock = asyncio.Lock()

MESSAGE_NON_TEXTUEL = (
    "🩺 Je ne peux actuellement traiter que des messages écrits. "
    "Merci de poser votre question par texte, par exemple : "
    "« Quels sont les symptômes de la dengue ? »"
)


def _mask_sender(sender: str) -> str:
    return f"***{sender[-4:]}" if len(sender) > 4 else "***"


def _append_event(sender: str, text_length: int, reply_status: str) -> None:
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
            "from": _mask_sender(sender),
            "text_length": text_length,
            "reply_status": reply_status,
            "received_at": datetime.now(timezone.utc).isoformat(),
        }
    )
    temporary_path = EVENT_LOG_PATH.with_suffix(".tmp")
    with temporary_path.open("w", encoding="utf-8") as file:
        json.dump(events[-MAX_STORED_EVENTS:], file, ensure_ascii=False)
    temporary_path.replace(EVENT_LOG_PATH)


async def _store_event(
    sender: str, text_length: int, reply_status: str
) -> None:
    async with _event_log_lock:
        try:
            await asyncio.to_thread(
                _append_event, sender, text_length, reply_status
            )
        except (OSError, ValueError, json.JSONDecodeError) as error:
            logger.error("Unable to store minimized webhook event: %s", error)


async def _deja_traite(message_id: str) -> bool:
    async with _dedup_lock:
        if message_id in _messages_deja_traites:
            return True
        _messages_deja_traites.append(message_id)
        return False


def _valider_signature(request: Request, raw_body: bytes) -> None:
    """Valide l'en-tête X-Hub-Signature-256 (HMAC-SHA256 de l'App Secret)."""

    settings = get_settings()
    app_secret = settings.wa_app_secret

    if not app_secret:
        if settings.requires_signature:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="WA_APP_SECRET must be configured outside local mode",
            )
        logger.warning(
            "Webhook signature validation skipped (WA_APP_SECRET not set)"
        )
        return

    header = request.headers.get("X-Hub-Signature-256", "")
    if not header.startswith("sha256="):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing webhook signature",
        )
    signature_attendue = "sha256=" + hmac.new(
        app_secret.encode("utf-8"), raw_body, hashlib.sha256
    ).hexdigest()
    if not hmac.compare_digest(header, signature_attendue):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid webhook signature",
        )


def _extraire_messages(payload: Any) -> list[dict[str, str]]:
    """Extrait les messages entrants d'un payload webhook Meta.

    Retourne une liste de dictionnaires {id, from, text} pour les messages
    textuels et {id, from, text: ""} pour les autres types (audio, image…).
    Les mises à jour de statut (accusés de livraison) sont ignorées.
    """

    extraits: list[dict[str, str]] = []
    if not isinstance(payload, dict):
        return extraits

    for entry in payload.get("entry", []):
        if not isinstance(entry, dict):
            continue
        for change in entry.get("changes", []):
            if not isinstance(change, dict):
                continue
            value = change.get("value")
            if not isinstance(value, dict):
                continue
            for message in value.get("messages", []):
                if not isinstance(message, dict):
                    continue
                texte = ""
                bloc_texte = message.get("text")
                if isinstance(bloc_texte, dict):
                    texte = str(bloc_texte.get("body") or "")
                extraits.append(
                    {
                        "id": str(message.get("id") or ""),
                        "from": str(message.get("from") or ""),
                        "text": texte,
                        "type": str(message.get("type") or "unknown"),
                    }
                )
    return extraits


@router.get("/webhook/whatsapp", response_class=PlainTextResponse)
async def verify_whatsapp_webhook(request: Request) -> PlainTextResponse:
    """Vérification du webhook par Meta lors de l'enregistrement."""

    settings = get_settings()
    mode = request.query_params.get("hub.mode", "")
    token = request.query_params.get("hub.verify_token", "")
    challenge = request.query_params.get("hub.challenge", "")

    if (
        mode == "subscribe"
        and settings.wa_verify_token
        and hmac.compare_digest(token, settings.wa_verify_token)
    ):
        logger.info("Webhook WhatsApp vérifié avec succès par Meta.")
        return PlainTextResponse(challenge)

    logger.warning("Webhook WhatsApp : échec de la vérification GET.")
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Webhook verification failed",
    )


@router.post(
    "/webhook/whatsapp",
    response_model=WebhookResponse,
    responses={
        400: {"description": "Invalid JSON payload"},
        401: {"description": "Invalid webhook signature"},
        503: {"description": "Missing app secret outside local mode"},
    },
)
async def receive_whatsapp_webhook(request: Request) -> WebhookResponse:
    """Traite un message entrant : réponse RAG puis envoi WhatsApp Cloud."""

    raw_body = await request.body()
    _valider_signature(request, raw_body)

    try:
        payload = json.loads(raw_body)
    except (ValueError, UnicodeDecodeError) as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON payload",
        ) from error

    messages = _extraire_messages(payload)
    if not messages:
        logger.info("Webhook reçu sans message entrant (ignoré).")
        return WebhookResponse(status="ok", detail="No incoming message")

    for message in messages:
        message_id = message["id"]
        expediteur = message["from"]
        if message_id and await _deja_traite(message_id):
            logger.info("Message %s déjà traité (rejeu Meta ignoré).", message_id)
            continue

        texte = message["text"].strip()
        if message["type"] != "text" or not texte:
            reponse = MESSAGE_NON_TEXTUEL
        else:
            reponse = rag_service.repondre(texte)

        result = await send_message(expediteur, reponse)
        if not result.success:
            logger.warning(
                "Réponse non envoyée pour le message %s : %s",
                message_id,
                result.error,
            )

        await _store_event(
            expediteur, len(texte), result.status
        )

    return WebhookResponse(
        status="ok", detail=f"{len(messages)} message(s) processed"
    )
