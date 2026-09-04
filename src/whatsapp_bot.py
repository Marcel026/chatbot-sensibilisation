"""Mini-serveur Flask destiné à héberger le webhook WhatsApp (ex: Render.com)

Endpoints:
- POST /whatsapp-webhook : reçu des messages Twilio et répond avec le texte provenant de rag_mtn.obtenir_reponse

Notes:
- Configurez TWILIO sandbox pour pointer sur https://<your-service>.onrender.com/whatsapp-webhook
- Ne stockez pas vos clés dans ce fichier; utilisez les variables d'environnement.
"""
from flask import Flask, request, Response
import os
from dotenv import load_dotenv

load_dotenv()

try:
    # Importer le moteur RAG local et s'assurer que les embeddings sont initialisés
    from . import rag_mtn
except Exception:
    rag_mtn = None

app = Flask(__name__)

@app.route('/whatsapp-webhook', methods=['POST'])
def whatsapp_webhook():
    """Receives incoming WhatsApp messages from Twilio and replies with RAG answer."""
    # Body param from Twilio
    incoming = request.values.get('Body', '')
    if not incoming:
        return Response("", status=400)

    # Ensure embeddings/model are ready (lazy init)
    try:
        if rag_mtn is not None:
            if hasattr(rag_mtn, 'ensure_embeddings_initialized'):
                rag_mtn.ensure_embeddings_initialized()
    except Exception as e:
        print(f"Erreur initialisation rag: {e}")

    # Get answer (safe: obtenir_reponse returns a string)
    answer = "Désolé, je n'ai pas pu traiter la demande."
    try:
        if rag_mtn is not None:
            answer = rag_mtn.obtenir_reponse(incoming)
    except Exception as e:
        print(f"Erreur lors de la recherche: {e}")

    # Build Twilio-compatible response (text/plain with TwiML)
    from twilio.twiml.messaging_response import MessagingResponse
    resp = MessagingResponse()
    resp.message(answer)
    return Response(str(resp), mimetype='application/xml')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port)
