"""Pont entre le backend WhatsApp et le moteur RAG (src/rag_mtn.py).

L'import du moteur RAG est paresseux : le processus FastAPI démarre et
répond aux health checks même si torch/sentence-transformers mettent du
temps à se charger. Le warmup s'effectue dans un thread dédié au boot.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

# Garantir l'import de src.rag_mtn quel que soit le répertoire de lancement.
ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

logger = logging.getLogger(__name__)

MESSAGE_ERREUR = (
    "⚠️ Désolé, une erreur est survenue lors du traitement de votre "
    "question. Merci de réessayer dans un instant."
)

_obtenir_reponse = None


def _charger_rag():
    """Importe obtenir_reponse une seule fois par processus."""
    global _obtenir_reponse
    if _obtenir_reponse is None:
        from src.rag_mtn import obtenir_reponse

        _obtenir_reponse = obtenir_reponse
    return _obtenir_reponse


def repondre(question: str) -> str:
    """Retourne la réponse RAG, ou un message d'erreur contrôlé."""
    try:
        return _charger_rag()(question)
    except Exception as error:  # noqa: BLE001 - barrière de robustesse
        logger.error("Moteur RAG indisponible : %s", error)
        return MESSAGE_ERREUR


def precharger_rag() -> None:
    """Précharge le moteur RAG en arrière-plan au démarrage du serveur."""
    try:
        from src import rag_mtn

        rag_mtn.precharger_modele()
    except Exception as error:  # noqa: BLE001 - le démarrage doit continuer
        logger.warning("Préchargement du moteur RAG impossible : %s", error)
