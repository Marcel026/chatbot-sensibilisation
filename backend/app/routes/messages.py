"""Routes d'envoi de messages et de supervision du backend."""

from fastapi import APIRouter, Response, status

from ..cloud_api_client import send_message
from ..config import get_settings
from ..models.message import (
    HealthResponse,
    SendMessageRequest,
    SendMessageResponse,
)

router = APIRouter(tags=["messages"])


@router.post(
    "/api/send_message",
    response_model=SendMessageResponse,
    responses={400: {"model": SendMessageResponse}},
)
async def send_whatsapp_message(
    payload: SendMessageRequest, response: Response
) -> SendMessageResponse:
    """Envoie un message via l'API WhatsApp Cloud ou le mode mock local."""

    result = await send_message(payload.to, payload.text)
    if result.success:
        detail = (
            "Message simulated because WhatsApp is disabled"
            if result.status == "mock"
            else "Message accepted by WhatsApp Cloud API"
        )
        return SendMessageResponse(
            status="success",
            message_id=result.message_id,
            detail=detail,
        )

    status_codes = {
        "invalid_input": status.HTTP_400_BAD_REQUEST,
        "configuration_error": status.HTTP_503_SERVICE_UNAVAILABLE,
        "timeout": status.HTTP_504_GATEWAY_TIMEOUT,
        "connection_error": status.HTTP_503_SERVICE_UNAVAILABLE,
        "http_error": status.HTTP_502_BAD_GATEWAY,
        "invalid_response": status.HTTP_502_BAD_GATEWAY,
        "api_error": status.HTTP_502_BAD_GATEWAY,
    }
    response.status_code = status_codes.get(
        result.status, status.HTTP_502_BAD_GATEWAY
    )
    return SendMessageResponse(
        status="error",
        detail=result.error or "WhatsApp Cloud API could not send the message",
    )


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Retourne l'état minimal du backend sans appeler WhatsApp."""

    return HealthResponse(
        status="ok",
        wa_enabled=get_settings().wa_enabled,
    )
