"""Page Streamlit d'envoi de messages WhatsApp."""

from __future__ import annotations

import requests
import streamlit as st

from pages.config import BACKEND_TIMEOUT_SECONDS, BACKEND_URL

SEND_MESSAGE_URL = f"{BACKEND_URL}/api/send_message"
HEALTH_URL = f"{BACKEND_URL}/health"

st.set_page_config(page_title="WhatsApp Santé", page_icon="💬")
st.title("💬 WhatsApp Santé Communautaire")
st.caption("Envoyez un message de sensibilisation via le backend WhatsApp.")

if st.button("Vérifier l'état du backend"):
    try:
        health_response = requests.get(
            HEALTH_URL,
            timeout=BACKEND_TIMEOUT_SECONDS,
        )
    except requests.Timeout:
        st.error("Backend : HS (le délai de réponse est dépassé).")
    except requests.ConnectionError:
        st.error("Backend : HS (impossible de le joindre).")
    except requests.RequestException:
        st.error("Backend : HS (erreur réseau).")
    else:
        try:
            health = health_response.json()
        except ValueError:
            st.error("Backend : HS (réponse invalide).")
        else:
            if health_response.ok and health.get("status") == "ok":
                st.success("Backend : OK")
            else:
                st.error("Backend : HS")

with st.form("send-whatsapp-message"):
    phone_number = st.text_input(
        "Numéro de téléphone",
        value="+228",
        help="Utilisez le format togolais E.164 : +228 suivi de 8 chiffres.",
    )
    message = st.text_area(
        "Message",
        max_chars=4_096,
        placeholder="Saisissez votre message de sensibilisation...",
    )
    submitted = st.form_submit_button("Envoyer")

if submitted:
    if not phone_number.startswith("+228") or len(phone_number) != 12:
        st.error(
            "Saisissez un numéro togolais valide au format +228XXXXXXXX."
        )
    elif not phone_number[1:].isdigit():
        st.error(
            "Le numéro ne doit contenir que des chiffres après le signe +."
        )
    elif not message.strip():
        st.error("Saisissez un message avant de l'envoyer.")
    else:
        try:
            response = requests.post(
                SEND_MESSAGE_URL,
                json={"to": phone_number, "text": message},
                timeout=BACKEND_TIMEOUT_SECONDS,
            )
        except requests.Timeout:
            st.error(
                "Le backend WhatsApp ne répond pas dans le délai imparti."
            )
        except requests.ConnectionError:
            st.error(
                "Impossible de joindre le backend WhatsApp. "
                "Vérifiez qu'il est lancé sur l'URL configurée."
            )
        except requests.RequestException:
            st.error("Une erreur réseau est survenue lors de l'envoi.")
        else:
            try:
                result = response.json()
            except ValueError:
                st.error(
                    "Le backend WhatsApp a retourné une réponse invalide."
                )
            else:
                detail = result.get("detail", "Aucun détail fourni.")
                if response.ok and result.get("status") == "success":
                    st.success(detail)
                else:
                    st.error(detail)
