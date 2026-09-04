"""Configuration partagée des pages Streamlit WhatsApp."""

from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000").rstrip("/")
BACKEND_TIMEOUT_SECONDS = int(
    os.getenv("BACKEND_TIMEOUT_SECONDS", "10")
)
