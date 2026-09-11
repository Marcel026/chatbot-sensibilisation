"""Point d'entrée de l'API FastAPI WhatsApp."""

from contextlib import asynccontextmanager
import threading

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .models.message import SendMessageResponse
from .rag_service import precharger_rag
from .routes import messages, webhook


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Précharge le moteur RAG en arrière-plan sans bloquer le démarrage."""

    threading.Thread(
        target=precharger_rag, daemon=True, name="rag-warmup"
    ).start()
    yield


app = FastAPI(
    title="MTN RAG WhatsApp API",
    version="0.2.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501", "http://127.0.0.1:8501"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


@app.exception_handler(RequestValidationError)
async def validation_error_handler(
    _request: Request, error: RequestValidationError
) -> JSONResponse:
    """Retourne un format d'erreur API cohérent pour les requêtes invalides."""

    del _request
    first_error = error.errors()[0]
    detail = str(first_error["msg"])
    body = SendMessageResponse(status="error", detail=detail)
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content=body.model_dump(),
    )


app.include_router(messages.router)
app.include_router(webhook.router)
