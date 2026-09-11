"""Tests ciblés de l'API FastAPI WhatsApp (Cloud API Meta + RAG)."""

import asyncio
import hashlib
import hmac
import json
from pathlib import Path

import httpx
import pytest

from backend.app.cloud_api_client import SendMessageResult, send_message
from backend.app.config import Settings
from backend.app.main import app
from backend.app.routes import messages, webhook


@pytest.fixture(autouse=True)
def _reinitialiser_etat_webhook():
    """Isole l'anti-doublon des webhooks entre les tests."""
    webhook._messages_deja_traites.clear()
    yield


def request(method: str, path: str, **kwargs) -> httpx.Response:
    """Exécute une requête ASGI sans serveur ni client déprécié."""

    async def send() -> httpx.Response:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            return await client.request(method, path, **kwargs)

    return asyncio.run(send())


def settings_local(**overrides) -> Settings:
    base = dict(
        app_env="local",
        debug=False,
        log_level="INFO",
        backend_url="http://localhost:8000",
    )
    base.update(overrides)
    return Settings(**base)


META_TEXT_PAYLOAD = {
    "object": "whatsapp_business_account",
    "entry": [
        {
            "id": "123456789",
            "changes": [
                {
                    "field": "messages",
                    "value": {
                        "messaging_product": "whatsapp",
                        "metadata": {
                            "display_phone_number": "22890000000",
                            "phone_number_id": "phone-number-id",
                        },
                        "contacts": [
                            {"profile": {"name": "Test"}, "wa_id": "22890000000"}
                        ],
                        "messages": [
                            {
                                "from": "22890000000",
                                "id": "wamid.abcdef123456",
                                "timestamp": "1757580000",
                                "type": "text",
                                "text": {"body": "Qu'est-ce que la lèpre ?"},
                            }
                        ],
                    },
                }
            ],
        }
    ],
}

META_STATUS_PAYLOAD = {
    "object": "whatsapp_business_account",
    "entry": [
        {
            "id": "123456789",
            "changes": [
                {
                    "field": "messages",
                    "value": {
                        "messaging_product": "whatsapp",
                        "statuses": [
                            {
                                "id": "wamid.reply.1",
                                "status": "delivered",
                                "timestamp": "1757580001",
                            }
                        ],
                    },
                }
            ],
        }
    ],
}


# =========================
# Health et envoi
# =========================

def test_health_reports_whatsapp_disabled(monkeypatch):
    monkeypatch.setattr(
        messages, "get_settings", lambda: settings_local(wa_enabled=False)
    )

    response = request("GET", "/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "wa_enabled": False}


def test_send_message_uses_mock_client(monkeypatch):
    async def mock_send_message(to, text):
        assert to == "+22890000000"
        assert text == "Bonjour"
        return SendMessageResult(True, "mock")

    monkeypatch.setattr(messages, "send_message", mock_send_message)

    response = request(
        "POST",
        "/api/send_message",
        json={"to": "+22890000000", "text": "Bonjour"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "success"


def test_cloud_client_uses_mock_when_disabled():
    result = asyncio.run(
        send_message(
            "+22890000000",
            "Bonjour",
            settings=settings_local(wa_enabled=False),
        )
    )

    assert result.success is True
    assert result.status == "mock"


def test_cloud_client_uses_graph_api_contract():
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.url == httpx.URL(
            "https://graph.facebook.com/v23.0/phone-number-id/messages"
        )
        assert request.headers["Authorization"] == "Bearer wa-token"
        assert json.loads(request.content) == {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": "22890000000",
            "type": "text",
            "text": {"preview_url": False, "body": "Bonjour"},
        }
        return httpx.Response(
            200,
            json={
                "messaging_product": "whatsapp",
                "messages": [{"id": "wamid.sent.1"}],
            },
        )

    settings = settings_local(
        wa_enabled=True,
        wa_phone_number_id="phone-number-id",
        wa_access_token="wa-token",
    )

    async def send() -> SendMessageResult:
        transport = httpx.MockTransport(handler)
        async with httpx.AsyncClient(transport=transport) as client:
            return await send_message(
                "+22890000000",
                "Bonjour",
                settings=settings,
                http_client=client,
            )

    result = asyncio.run(send())

    assert result.success is True
    assert result.status == "sent"
    assert result.message_id == "wamid.sent.1"


def test_cloud_client_requires_configuration_when_enabled():
    result = asyncio.run(
        send_message(
            "+22890000000",
            "Bonjour",
            settings=settings_local(
                wa_enabled=True,
                wa_phone_number_id=None,
                wa_access_token=None,
            ),
        )
    )

    assert result.success is False
    assert result.status == "configuration_error"


def test_send_message_rejects_invalid_togolese_number():
    response = request(
        "POST",
        "/api/send_message",
        json={"to": "+33123456789", "text": "Bonjour"},
    )

    assert response.status_code == 422
    assert response.json()["status"] == "error"


# =========================
# Webhook : vérification GET (hub.challenge)
# =========================

def test_webhook_get_verification_echoes_challenge(monkeypatch):
    monkeypatch.setattr(
        webhook,
        "get_settings",
        lambda: settings_local(wa_verify_token="jeton-verification"),
    )

    response = request(
        "GET",
        "/webhook/whatsapp",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": "jeton-verification",
            "hub.challenge": "challenge-123",
        },
    )

    assert response.status_code == 200
    assert response.text == "challenge-123"


def test_webhook_get_verification_rejects_wrong_token(monkeypatch):
    monkeypatch.setattr(
        webhook,
        "get_settings",
        lambda: settings_local(wa_verify_token="jeton-verification"),
    )

    response = request(
        "GET",
        "/webhook/whatsapp",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": "mauvais-jeton",
            "hub.challenge": "challenge-123",
        },
    )

    assert response.status_code == 403


# =========================
# Webhook POST : traitement des messages
# =========================

def _signature(secret: str, body: bytes) -> str:
    return "sha256=" + hmac.new(
        secret.encode("utf-8"), body, hashlib.sha256
    ).hexdigest()


def test_webhook_replies_with_rag_answer(monkeypatch, tmp_path: Path):
    monkeypatch.setattr(webhook, "get_settings", lambda: settings_local())
    monkeypatch.setattr(
        webhook.rag_service, "repondre", lambda question: "Réponse RAG"
    )
    envois = []

    async def mock_send_message(to, text):
        envois.append((to, text))
        return SendMessageResult(True, "mock")

    monkeypatch.setattr(webhook, "send_message", mock_send_message)
    event_log_path = tmp_path / "events.json"
    monkeypatch.setattr(webhook, "EVENT_LOG_PATH", event_log_path)

    response = request("POST", "/webhook/whatsapp", json=META_TEXT_PAYLOAD)

    saved_event = event_log_path.read_text(encoding="utf-8")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert envois == [("22890000000", "Réponse RAG")]
    assert "22890000000" not in saved_event
    assert "lèpre" not in saved_event


def test_webhook_ignores_duplicate_delivery(monkeypatch, tmp_path: Path):
    monkeypatch.setattr(webhook, "get_settings", lambda: settings_local())
    monkeypatch.setattr(
        webhook.rag_service, "repondre", lambda question: "Réponse RAG"
    )
    envois = []

    async def mock_send_message(to, text):
        envois.append((to, text))
        return SendMessageResult(True, "mock")

    monkeypatch.setattr(webhook, "send_message", mock_send_message)
    monkeypatch.setattr(webhook, "EVENT_LOG_PATH", tmp_path / "events.json")

    first = request("POST", "/webhook/whatsapp", json=META_TEXT_PAYLOAD)
    second = request("POST", "/webhook/whatsapp", json=META_TEXT_PAYLOAD)

    assert first.status_code == 200
    assert second.status_code == 200
    assert len(envois) == 1


def test_webhook_ignores_status_updates(monkeypatch, tmp_path: Path):
    monkeypatch.setattr(webhook, "get_settings", lambda: settings_local())
    envois = []

    async def mock_send_message(to, text):
        envois.append((to, text))
        return SendMessageResult(True, "mock")

    monkeypatch.setattr(webhook, "send_message", mock_send_message)
    monkeypatch.setattr(webhook, "EVENT_LOG_PATH", tmp_path / "events.json")

    response = request("POST", "/webhook/whatsapp", json=META_STATUS_PAYLOAD)

    assert response.status_code == 200
    assert envois == []


def test_webhook_answers_non_text_with_help_message(
    monkeypatch, tmp_path: Path
):
    payload = json.loads(json.dumps(META_TEXT_PAYLOAD))
    message = payload["entry"][0]["changes"][0]["value"]["messages"][0]
    message["type"] = "audio"
    message.pop("text")
    message["audio"] = {"id": "media-1"}

    monkeypatch.setattr(webhook, "get_settings", lambda: settings_local())
    monkeypatch.setattr(
        webhook.rag_service, "repondre", lambda question: "ne doit pas être appelé"
    )
    envois = []

    async def mock_send_message(to, text):
        envois.append((to, text))
        return SendMessageResult(True, "mock")

    monkeypatch.setattr(webhook, "send_message", mock_send_message)
    monkeypatch.setattr(webhook, "EVENT_LOG_PATH", tmp_path / "events.json")

    response = request("POST", "/webhook/whatsapp", json=payload)

    assert response.status_code == 200
    assert len(envois) == 1
    assert "messages écrits" in envois[0][1]


def test_webhook_rejects_invalid_signature(monkeypatch):
    monkeypatch.setattr(
        webhook,
        "get_settings",
        lambda: settings_local(wa_app_secret="app-secret"),
    )

    response = request(
        "POST",
        "/webhook/whatsapp",
        headers={"X-Hub-Signature-256": "sha256=" + "0" * 64},
        json=META_TEXT_PAYLOAD,
    )

    assert response.status_code == 401


def test_webhook_requires_app_secret_outside_local(monkeypatch):
    monkeypatch.setattr(
        webhook,
        "get_settings",
        lambda: settings_local(app_env="prod", wa_app_secret=None),
    )

    response = request("POST", "/webhook/whatsapp", json=META_TEXT_PAYLOAD)

    assert response.status_code == 503


def test_webhook_rejects_invalid_json(monkeypatch):
    monkeypatch.setattr(webhook, "get_settings", lambda: settings_local())

    response = request(
        "POST",
        "/webhook/whatsapp",
        headers={"Content-Type": "application/json"},
        content=b"ceci n'est pas du json",
    )

    assert response.status_code == 400
