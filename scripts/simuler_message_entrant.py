"""Simule un webhook Meta entrant sur le backend local (test E2E sans Meta).

Prérequis : backend lancé localement :
    uvicorn backend.app.main:app --port 8000

Exemples :
    python scripts/simuler_message_entrant.py "Qu'est-ce que la lèpre ?"
    python scripts/simuler_message_entrant.py --url https://mon-service.onrender.com "Symptômes de la dengue ?"
"""

import argparse
import json
import sys

import httpx

DEFAULT_BACKEND_URL = "http://localhost:8000"


def construire_payload(texte: str, expediteur: str = "22890000000") -> dict:
    """Construit un payload webhook Meta réaliste."""

    return {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "simulation-entry",
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
                                {
                                    "profile": {"name": "Simulation"},
                                    "wa_id": expediteur,
                                }
                            ],
                            "messages": [
                                {
                                    "from": expediteur,
                                    "id": f"wamid.simulation.{len(texte)}",
                                    "timestamp": "1757580000",
                                    "type": "text",
                                    "text": {"body": texte},
                                }
                            ],
                        },
                    }
                ],
            }
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Simule un message WhatsApp entrant vers le webhook."
    )
    parser.add_argument("texte", help="Contenu du message à envoyer")
    parser.add_argument(
        "--url",
        default=DEFAULT_BACKEND_URL,
        help=f"URL de base du backend (défaut : {DEFAULT_BACKEND_URL})",
    )
    args = parser.parse_args()

    endpoint = f"{args.url.rstrip('/')}/webhook/whatsapp"
    payload = construire_payload(args.texte)

    try:
        response = httpx.post(endpoint, json=payload, timeout=30.0)
    except httpx.HTTPError as error:
        print(f"❌ Impossible de joindre le backend ({endpoint}) : {error}")
        print(
            "   Vérifiez qu'il est lancé : "
            "uvicorn backend.app.main:app --port 8000"
        )
        return 1

    print(f"Statut HTTP : {response.status_code}")
    try:
        print(
            f"Réponse : "
            f"{json.dumps(response.json(), ensure_ascii=False, indent=2)}"
        )
    except ValueError:
        print(f"Réponse (brute) : {response.text}")

    if response.status_code == 200:
        print(
            "✅ Webhook traité. Avec WA_ENABLED=false, la réponse RAG est "
            "visible dans les logs du backend (mode mock)."
        )
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
