# 🩺 Sensibilisation sur les Maladies Tropicales Négligées

Application Streamlit pour l'éducation et la sensibilisation aux **Maladies Tropicales Négligées (MTN)** : lèpre, dengue, envenimations par morsure de serpent (EMS), schistosomiase, ulcère de Buruli et noma.

## 🎯 Objectifs

- ✅ Fournir des informations précises et accessibles sur les MTN
- ✅ Sensibiliser le public via Streamlit
- ✅ Utiliser un moteur RAG (Retrieval-Augmented Generation) avec embeddings
- ✅ Faciliter le déploiement sur Streamlit Community Cloud

## 📦 Architecture

```
mtn_rag/
├── app.py                      # Interface Streamlit (web)
├── pages/
│   └── whatsapp.py             # Page Streamlit d'envoi WhatsApp (agents)
├── streamlit_config/
│   └── config.py               # BACKEND_URL partagé des pages
├── backend/                    # API WhatsApp Cloud (Meta) déployable sur Render
│   ├── app/
│   │   ├── main.py             # FastAPI + warmup RAG au démarrage
│   │   ├── config.py           # Variables WA_* (WhatsApp Cloud API)
│   │   ├── cloud_api_client.py # Client Graph API (envoi de messages)
│   │   ├── rag_service.py      # Pont vers le moteur RAG (src/rag_mtn.py)
│   │   └── routes/
│   │       ├── messages.py     # POST /api/send_message, GET /health
│   │       └── webhook.py      # Webhook Meta : message entrant → réponse RAG
│   ├── requirements.txt        # Dépendances autonomes du backend
│   └── tests/                  # Tests API (contrat Cloud API + RAG)
├── scripts/
│   ├── build_embeddings.py     # Régénère models/embeddings_mtn.npz
│   └── simuler_message_entrant.py  # Test E2E local sans Meta
├── models/
│   └── embeddings_mtn.npz      # Cache d'embeddings versionné (54 × 384)
├── src/
│   ├── rag_mtn.py              # Moteur RAG (lazy, cache .npz)
│   ├── documents_mtn.py        # Base documentaire structurée
│   └── whatsapp_bot.py         # [LEGACY] webhook Flask/Twilio, non déployé
├── data/                       # Données brutes et traitées (hors dépôt)
├── docs/                       # Documentation étendue
├── notebooks/                  # Exploration reproductible
├── tests/                      # Tests unitaires et d'intégration
├── .github/workflows/ci.yml    # GitHub Actions CI (tests + flake8)
├── render.yaml                 # Déploiement Render du backend
├── requirements.txt            # Dépendances Python (interface web)
├── .env.example                # Template variables d'environnement
└── README.md                   # Cette documentation
```

## 💬 Canal WhatsApp (WhatsApp Cloud API officielle)

```
[Utilisateur WhatsApp]
   → (message) → [Meta Cloud API]
   → (webhook POST signé) → [Backend FastAPI sur Render]
   → réponse RAG (src/rag_mtn) → [POST Graph API /messages]
   → [Utilisateur WhatsApp]
```

- **API officielle Meta** : pas de risque de bannissement, conforme pour un usage santé.
- **Coût nul** pour le cas d'usage du bot : les réponses aux messages initiés
  par les utilisateurs (fenêtre de service 24 h) sont gratuites.
- Sécurité : signature `X-Hub-Signature-256` (HMAC de l'App Secret) validée
  sur chaque webhook ; logs minimisés (numéros masqués, aucun contenu conservé).
- Mode mock : `WA_ENABLED=false` simule les envois (développement et tests).
- Anti-rejeu : les webhooks rejoués par Meta sont dédupliqués par identifiant.

## 🚀 Installation & Démarrage

### 1. **Cloner et configurer**

```bash
git clone <repo-url>
cd mtn_rag
cp .env.example .env
# Éditer .env avec vos vraies clés (optionnel)
```

Important : ce projet est validé et recommandé avec Python 3.11.x. Sur Windows, utilisez :

```bash
py -3.11 -m venv .venv
.\.venv\Scripts\activate
```

### 2. **Installer les dépendances**

```bash
python -m pip install --upgrade pip
pip install --index-url https://pypi.org/simple --trusted-host pypi.org --trusted-host files.pythonhosted.org --trusted-host pypi.python.org -r requirements.txt
```

### 3. **Lancer l'application**

**Interface web (Streamlit)** ✨
```bash
streamlit run app.py
# Ouvre http://localhost:8501
```

## 🧪 Tests

### Exécuter tous les tests
```bash
pytest tests/ -v
```

### Exécuter avec couverture
```bash
pytest tests/ --cov=. --cov-report=html
```

### Exécuter via VS Code
```bash
# Raccourci: Ctrl+Shift+B (ou Cmd+Shift+B sur Mac)
# Sélectionner "Exécuter tests"
```

## 📝 Structure des Documents

Les documents MTN sont structurés dans `src/documents_mtn.py` :

```python
{
    "maladie": "lepre",              # identifiant normalisé
    "categorie": "definition",        # type de contenu
    "contenu": "La lèpre est...",    # texte informatif
    "source": "OMS",                 # référence (optionnel)
    "date_maj": "2026-08-08"         # date MAJ (optionnel)
}
```

### Maladies documentées
- `lepre` - Lèpre
- `dengue` - Dengue
- `ems` - Envenimations par morsure de serpent
- `schistosomiase` - Schistosomiase
- `ulcere de buruli` - Ulcère de Buruli
- `noma` - Noma

### Catégories de contenu
- `definition` - Définition de la maladie
- `transmission` - Modes de transmission
- `symptomes` - Symptômes
- `signes_alerte` - Signes de gravité
- `prevention` - Mesures de prévention
- `conduite` - Conduite à tenir
- `facteurs_risque` - Facteurs de risque
- `gravite` - Degré de gravité
- `gestes_interdits` - Ce qu'il ne faut pas faire

## 🔍 Moteur RAG

Le système utilise **SentenceTransformers** avec le modèle `all-MiniLM-L6-v2` pour :
- Créer des embeddings des documents (cache versionné `models/embeddings_mtn.npz`)
- Calculer la similarité cosinus avec les requêtes
- Retourner les k résultats les plus pertinents

**Coût API : 0 €** — retrieval pur sans génération LLM, le contenu affiché
provient exclusivement de la base documentaire validée (aucune hallucination).

**Seuil de similarité** : 0.65 (configurable)

### Utilisation programmatique

```python
from src.rag_mtn import rechercher_information, obtenir_reponse

# Recherche directe (retourne liste des résultats)
results = rechercher_information("Quels sont les symptômes de la dengue ?", top_k=3)
for r in results:
    print(f"{r['maladie']} - {r['categorie']}: score {r['score']:.3f}")

# Génération de réponse
response = obtenir_reponse("Qu'est-ce que la lèpre ?")
print(response)
```

## 🌐 Déploiement

### **Streamlit Cloud** (Interface web)

1. Pusher sur GitHub
2. Aller sur https://streamlit.io/cloud
3. Cliquer "New app" et sélectionner le repo
4. Choisir `app.py` comme point d'entrée
5. Renseigner `BACKEND_URL` dans les secrets (URL Render du backend)

### **Render** (Backend WhatsApp)

Le fichier `render.yaml` déploie le backend FastAPI (plan gratuit) :

1. Sur https://render.com → New → Blueprint → sélectionner le repo
2. Renseigner les secrets `WA_PHONE_NUMBER_ID`, `WA_ACCESS_TOKEN`,
   `WA_VERIFY_TOKEN`, `WA_APP_SECRET` puis passer `WA_ENABLED` à `true`
3. Sur [Meta for Developers](https://developers.facebook.com) :
   créer une app (type Business) → produit WhatsApp → configurer le
   webhook sur `https://<service>.onrender.com/webhook/whatsapp`
   avec le `WA_VERIFY_TOKEN`
4. Ping gratuit de `/health` via UptimeRobot pour éviter la mise en
   veille du plan gratuit Render

### **GitHub Actions** (Tests automatisés)

Chaque push sur `main` exécute automatiquement :
- Installation des dépendances (racine + backend)
- Exécution des tests (pytest : `tests/` + `backend/tests/`)
- Vérification lint (flake8)

Statut visible sur le badge README ou dans l'onglet "Actions".

## 🔐 Secrets & Environnement

**Fichier `.env`** (NE PAS COMMITTER) — voir `.env.example` :
- `WA_ENABLED`, `WA_API_VERSION`, `WA_PHONE_NUMBER_ID`, `WA_ACCESS_TOKEN`,
  `WA_VERIFY_TOKEN`, `WA_APP_SECRET` (WhatsApp Cloud API)
- `BACKEND_URL`, `BACKEND_TIMEOUT_SECONDS` (pages Streamlit)

**Streamlit Cloud Secrets** :
Settings → Secrets → Coller `.env`

## 🧰 Scripts utilitaires

```bash
# Régénérer le cache d'embeddings après modification de la base documentaire
python scripts/build_embeddings.py

# Simuler un message WhatsApp entrant (test E2E local, backend requis)
uvicorn backend.app.main:app --port 8000
python scripts/simuler_message_entrant.py "Qu'est-ce que la lèpre ?"
```

## 🐛 Débogage

### Mode DEBUG
```python
# Dans src/rag_mtn.py
DEBUG = True
```

Affiche :
- Logs du chargement du modèle
- Scores de similarité
- Chunks utilisés

### Streamlit Debug
```bash
streamlit run app.py --logger.level=debug
```

## 📊 Retours Utilisateur

Les feedbacks sont sauvegardés dans `feedback.json` :
```json
[
  {
    "timestamp": "2026-07-24T21:06:24.026757",
    "question": "...",
    "reponse_preview": "...",
    "feedback": "utile"
  }
]
```

**TODO** : Implémenter rotation de fichier et base de données.

## 🤝 Contribution

1. Fork le repo
2. Créer une branche : `git checkout -b feature/amélioration`
3. Committer : `git commit -m "Ajout: description"`
4. Pousser : `git push origin feature/amélioration`
5. Ouvrir une Pull Request

## 📋 Checklist Avant Déploiement

- [ ] Tests en vert (`pytest tests/ -v`)
- [ ] Secrets bien configurés (pas dans `.env` committé)
- [ ] `.gitignore` à jour
- [ ] Application Streamlit Cloud configurée sur `app.py`
- [ ] Documentation README à jour

## 📚 Ressources

- [Streamlit docs](https://docs.streamlit.io)
- [Sentence Transformers](https://www.sbert.net)
- [OMS MTN](https://www.who.int/teams/control-of-neglected-tropical-diseases)

## 📄 Licence

[À définir]

## 📧 Support

Pour les problèmes ou suggestions :
- 📝 Créer une issue GitHub
- 💬 Contacter l'équipe

---

**Mise à jour**: 2026-09-11 | **Version**: 1.1.0-beta (pivot WhatsApp Cloud API)
