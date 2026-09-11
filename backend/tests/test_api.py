"""Tests ciblés de l'API FastAPI WhatsApp."""

import asyncio
import json
from pathlib import Path

import httpx

from backend.app.config import Settings
from backend.app.main import app
from backend.app.openwa_client import SendMessageResult, send_message
from backend.app.routes import messages, webhook


def request(method: str, path: str, **kwargs) -> httpx.Response:
    """Exécute une requête ASGI sans serveur ni client déprécié."""

    async def send() -> httpx.Response:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            return await client.request(method, path, **kwargs)

    return asyncio.run(send())


def test_health_reports_openwa_disabled(monkeypatch):
    settings = Settings(
        "local",
        False,
        "INFO",
        "http://localhost:8000",
        False,
        "http://localhost:8080",
        None,
        None,
        None,
        None,
        None,
        None,
    )
    monkeypatch.setattr(messages, "get_settings", lambda: settings)

    response = request("GET", "/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "openwa_enabled": False}


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


def test_openwa_client_uses_mock_when_disabled():
    settings = Settings(
        "local",
        False,
        "INFO",
        "http://localhost:8000",
        False,
        "http://openwa:8080",
        None,
        None,
        None,
        None,
        None,
        None,
    )

    result = asyncio.run(
        send_message("+22890000000", "Bonjour", settings=settings)
    )

    assert result.success is True
    assert result.status == "mock"


def test_openwa_client_uses_wa_automate_http_contract():
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.url == httpx.URL("http://openwa:8080/sendText")
        assert request.headers["apiKey"] == "openwa-api-key"
        assert json.loads(request.content) == {
            "to": "22890000000@c.us",
            "content": "Bonjour",
        }
        return httpx.Response(
            200,
            json={"success": True, "data": "message-id"},
        )

    settings = Settings(
        "prod",
        False,
        "INFO",
        "http://localhost:8000",
        True,
        "http://openwa:8080",
        "openwa-api-key",
        None,
        "webhook-secret",
        None,
        None,
        None,
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
    assert result.message_id == "message-id"


def test_send_message_rejects_invalid_togolese_number():
    response = request(
        "POST",
        "/api/send_message",
        json={"to": "+33123456789", "text": "Bonjour"},
    )

    assert response.status_code == 422
    assert response.json()["status"] == "error"


def test_webhook_rejects_an_invalid_secret(monkeypatch):
    settings = Settings(
        "staging",
        False,
        "INFO",
        "http://localhost:8000",
        False,
        "http://localhost:8080",
        None,
        None,
        "expected-secret",
        None,
        None,
        None,
    )
    monkeypatch.setattr(webhook, "get_settings", lambda: settings)

    response = request(
        "POST",
        "/webhook/whatsapp",
        headers={"X-Webhook-Secret": "wrong-secret"},
        json={
            "from": "22890000000@c.us",
            "text": "Bonjour",
            "timestamp": "2026-09-04T08:00:00Z",
        },
    )

    assert response.status_code == 401


def test_webhook_stores_only_minimized_metadata(monkeypatch, tmp_path: Path):
    settings = Settings(
        "local",
        False,
        "INFO",
        "http://localhost:8000",
        False,
        "http://localhost:8080",
        None,
        None,
        "test-secret",
        None,
        None,
        None,
    )
    event_log_path = tmp_path / "events.json"
    monkeypatch.setattr(webhook, "get_settings", lambda: settings)
    monkeypatch.setattr(webhook, "EVENT_LOG_PATH", event_log_path)

    response = request(
        "POST",
        "/webhook/whatsapp",
        headers={"X-Webhook-Secret": "test-secret"},
        json={
            "from": "22890000000@c.us",
            "text": "Contenu confidentiel",
            "timestamp": "2026-09-04T08:00:00Z",
        },
    )

    saved_event = event_log_path.read_text(encoding="utf-8")
    assert response.status_code == 200
    assert "Contenu confidentiel" not in saved_event
    assert "22890000000" not in saved_event
