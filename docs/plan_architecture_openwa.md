# Plan d'architecture – WhatsApp Santé Communautaire (OpenWA + Streamlit)

## 1. Objectif du projet

Construire une application communautaire en santé publique permettant :
- L'envoi de messages WhatsApp (rappels, sensibilisation, sondages).
- La réception de réponses via webhook.
- Une interface simple en Streamlit pour les agents de santé.
- Une stack 100% open source, gratuite, déployable sur Render ou petit VPS.

## 2. Stack technique

- **API WhatsApp** : OpenWA (self-hosted, open source, MIT)
- **Backend API + webhook** : Python + FastAPI (ou Flask si plus simple)
- **Interface utilisateur** : Streamlit
- **Conteneurisation** : Docker + Docker Compose
- **Déploiement** : Render / VPS (1–2 Go RAM)
- **Stockage** : Fichier JSON ou SQLite léger pour logs (MVP)

## 3. Schéma d'architecture global

```
[Utilisateur / Agent de santé]
↓ (HTTP)
[Streamlit]
↓ (POST /api/send_message)
[Backend FastAPI]
↓ (POST /api/send vers OpenWA)
[OpenWA]
→ WhatsApp

[WhatsApp]
→ [OpenWA]
→ (webhook POST /webhook/whatsapp)
[Backend FastAPI]
→ (log + stockage)
→ (optionnel) notification / historique
```

**Composants :**
1. **OpenWA** : service séparé (Docker), expose :
   - Dashboard (ex. port 2886)
   - API REST (ex. port 2785)
2. **Backend** : FastAPI, expose :
   - `POST /api/send_message` (depuis Streamlit)
   - `POST /webhook/whatsapp` (depuis OpenWA)
   - `GET /health` (monitoring)
3. **Streamlit** : l'application existante reste à la racine (`app.py`) et
   appelle le backend via HTTP. La fonctionnalité WhatsApp sera ajoutée dans
   `pages/whatsapp.py`.

## 4. Variables d'environnement

### Pour OpenWA

- `OPENWA_API_URL` : URL de l'API OpenWA (ex. `http://localhost:8080` ou `http://openwa:8080`)
- `OPENWA_API_KEY` : clé API générée dans le dashboard OpenWA
- `OPENWA_INSTANCE_ID` : ID de la session WhatsApp

### Pour le backend / Streamlit

- `APP_ENV` : `local`, `staging`, `prod`
- `OPENWA_ENABLED` : `true` / `false` (mode mock si false)
- `BACKEND_URL` : URL du backend vue par Streamlit (ex. `http://localhost:8000`)
- `WEBHOOK_SECRET` : token pour sécuriser le webhook (optionnel)

### Fallback Twilio (optionnel)

- `TWILIO_ACCOUNT_SID`
- `TWILIO_AUTH_TOKEN`
- `TWILIO_PHONE_NUMBER`

## 5. Étapes d'implémentation

### Étape 1 – Initialiser la structure du dépôt

- Conserver `app.py` et `pages/` à la racine, puis créer `backend/`,
  `docker/` et compléter `docs/`
- Fichiers de base : `.gitignore`, `.env.example`, `README.md`
- Prévoir l'intégration d'OpenWA comme service Docker séparé, documenté dans
  ce dépôt sans sous-module Git

### Étape 2 – Config et client OpenWA

- `backend/app/config.py` : chargement des variables d'environnement
- `backend/app/openwa_client.py` : fonction `send_message(to, text)` + mode mock

### Étape 3 – Endpoints FastAPI (send_message, health)

- `backend/app/main.py` : point d'entrée FastAPI
- `backend/app/routes/messages.py` : `POST /api/send_message`, `GET /health`
- Modèles Pydantic dans `backend/app/models/message.py`

### Étape 4 – Webhook WhatsApp

- `backend/app/routes/webhook.py` : `POST /webhook/whatsapp`
- Validation du secret, extraction des champs, log + stockage simple

### Étape 5 – Page WhatsApp dans Streamlit

- `pages/whatsapp.py` : formulaire (numéro, message, bouton)
- Une configuration Streamlit réutilise `BACKEND_URL` et un timeout
- Appel HTTP vers `POST /api/send_message` du backend

### Étape 6 – Dockerfile et docker-compose

- `backend/Dockerfile` : image du service backend
- `docker/docker-compose.yml` : services `openwa` et `backend`
- Exposition des ports, variables, healthcheck

### Étape 7 – Déploiement sur Render / VPS

- Variables d'environnement à configurer dans Render
- Adaptation du Dockerfile / docker-compose
- Procédure de déploiement pas à pas

### Étape 8 – Sécurité, logs et cas d'usage santé

- Validation des numéros (format E.164, indicatif +228)
- Rate limiting simple
- Logs des messages (sans données sensibles en clair)
- Cas d'usage : rappels RDV, sondages, sensibilisation
- Recommandations confidentialité et conformité WhatsApp

## 6. Structure de dossiers cible

```
.
├── app.py
├── pages/
│   └── whatsapp.py
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── openwa_client.py
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── messages.py
│   │   │   └── webhook.py
│   │   └── models/
│   │       ├── __init__.py
│   │       └── message.py
│   ├── requirements.txt
│   └── Dockerfile
├── docker/
│   └── docker-compose.yml
├── src/
│   ├── documents_mtn.py
│   ├── rag_mtn.py
│   └── whatsapp_bot.py
├── tests/
├── docs/
│   └── plan_architecture_openwa.md (ce fichier)
├── .env.example
├── .gitignore
└── README.md
```

## 7. Instructions pour Copilot

- Ce fichier est le **plan maître** à référence à chaque étape.
- À chaque session, l'utilisateur indiquera l'étape à travailler (ex. "Étape 2 – Config et client OpenWA").
- Copilot doit :
  - Se baser sur ce plan pour garder la cohérence (noms de variables, structure, endpoints).
  - Générer du code **complet et testable** pour les fichiers de l'étape.
  - Proposer les commandes à lancer et les points d'intervention humaine (variables, QR code, etc.).
- En cas de doute ou de conflit avec le plan, **demander confirmation** avant de modifier l'architecture.

## 8. Principes de conception

- **Simplicité** : MVP fonctionnel avant optimisation.
- **Maintenabilité** : code clair, commentaires minimaux mais utiles.
- **Gratuité** : pas de services payants, open source uniquement.
- **Adaptabilité** : facile à déployer sur Render ou petit VPS.
- **Confidentialité** : ne pas stocker de données sensibles en clair, logs minimaux.

---

**Fin du plan maître.**
