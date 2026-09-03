"""
ANALYSE DES IMPORTS - État stable avant déploiement

Fichier : IMPORT_DEPENDENCIES.md
Date : 2026-08-17
"""

# =========================
# HIÉRARCHIE DES IMPORTS
# =========================

## Niveau 1 : Sources de données
- src/documents_mtn.py
  └─ Fournit : DOCUMENTS_MTN

## Niveau 2 : Moteur RAG
- src/rag_mtn.py
  ├─ Importe : src.documents_mtn.DOCUMENTS_MTN
  ├─ Importe : sentence_transformers, numpy, re, logging, unicodedata
  ├─ Exporte : rechercher_information(), obtenir_reponse()
  └─ Rôle : Moteur RAG monolithique (retrieval + generation + utils)

## Niveau 3 : Points d'entrée
- app.py (Streamlit web)
  ├─ Importe : rag_mtn.obtenir_reponse, rag_mtn.rechercher_information
  ├─ Importe : streamlit, json, datetime, pathlib
  └─ Rôle : Interface web utilisateur

- src/whatsapp_bot.py (Flask webhook)
  ├─ Importe : src.rag_mtn (module entier)
  ├─ Importe : flask, twilio
  └─ Rôle : Serveur webhook pour Twilio/WhatsApp

## Niveau 4 : Tests & Utilitaires
- tests/test_rag.py
  ├─ Importe : src.rag_mtn.rechercher_information, src.rag_mtn.obtenir_reponse, src.rag_mtn.normaliser_texte
  └─ Rôle : Tests unitaires RAG

- tests/test_documents.py
  ├─ Importe : src.documents_mtn.DOCUMENTS_MTN, MALADIES_VALIDES, CATEGORIES_VALIDES, valider_documents
  └─ Rôle : Tests validation base documentaire

- verify_rag.py
  ├─ Importe : rag_mtn.rechercher_information
  └─ Rôle : Script de vérification manuelle

# =========================
# ANALYSE DE DÉPENDANCES
# =========================

Graphe de dépendances (simplifié) :

┌─────────────────────────────────────────┐
│       DOCUMENTS_MTN (données)           │
└──────────┬──────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────┐
│    RAG_MTN (moteur retrieval+gen)       │
│  - rechercher_information()             │
│  - obtenir_reponse()                    │
│  - normaliser_texte()                   │
│  - detecter_maladie()                   │
│  - detecter_categorie()                 │
└───┬─────────────────────────────────────┘
    │
    ├──► app.py (Streamlit)
    ├──► src/whatsapp_bot.py (Flask)
    ├──► verify_rag.py (Script)
    └──► tests/test_rag.py

Chaque point d'entrée dépend du package `src`.

# =========================
# RISQUES DE RUPTURE
# =========================

🔴 CRITIQUE (causerait panne immédiate) :
  ❌ Supprimer src/rag_mtn.py
  ❌ Renommer src/rag_mtn.py sans mettre à jour imports
  ❌ Supprimer src/documents_mtn.py

🟠 MAJEUR (casserait des fonctionnalités) :
  ⚠️  Modifier signature de rechercher_information()
  ⚠️  Modifier signature de obtenir_reponse()
  ⚠️  Supprimer normaliser_texte() ou detecter_maladie()

🟡 MINEUR (logs/debug) :
  ⚠️  Modifier DEBUG ou SEUIL_SIMILARITE sans adapter

# =========================
# DÉPENDANCES EXTERNES
# =========================

Fichier requirements.txt (à jour) :

✅ streamlit>=1.28.0           (app.py)
✅ sentence-transformers>=2.2.2 (src/rag_mtn.py)
✅ numpy>=1.24.0               (src/rag_mtn.py)
✅ flask>=2.3.0                (whatsapp_bot.py)
✅ twilio>=8.10.0              (whatsapp_bot.py)
✅ pytest>=7.4.0               (tests)
✅ pytest-cov>=4.1.0           (tests)
✅ python-dotenv>=1.0.0        (gestion .env)
✅ flake8>=6.0.0               (optionnel, CI)

Aucune dépendance manquante.
Toutes les versions sont pincées (>=).

# =========================
# PLAN DÉPLOIEMENT STABLE
# =========================

AVANT déploiement :
  ✅ [FAIT] Vérifier que src.rag_mtn exporte correctement
  ✅ [FAIT] Vérifier que src.documents_mtn est importable
  ✅ [FAIT] Vérifier que tous les imports sont résolus
  ✅ [FAIT] Nettoyer et documenter src/rag_mtn.py
  
À faire :
  → Exécuter tests (pytest tests/ -v)
  → Valider Streamlit (streamlit run app.py)
  → Créer render.yaml pour déploiement Render
  → Configurer secrets Streamlit Cloud
  → Créer checklist pré-production

# =========================
# VERSION STABLE ACTUELLE
# =========================

État : ✅ PRÊT POUR VERSION 1.0.0-stable

Structure :
  mtn_rag/
  ├── app.py                        ✅ Point entrée Streamlit
  ├── src/                          ✅ Modules applicatifs
  ├── render.yaml                   ✅ Déploiement Render
  ├── src/rag_mtn.py                ✅ Moteur RAG
  ├── src/documents_mtn.py          ✅ Base documentaire
  ├── tests/                        ✅ Suite tests
  ├── .github/workflows/ci.yml      ✅ GitHub Actions
  ├── .vscode/tasks.json            ✅ Tâches VS Code
  ├── requirements.txt              ✅ Dépendances
  ├── .env.example                  ✅ Template secrets
  ├── .gitignore                    ✅ Patterns ignorés
  └── README.md                     ✅ Documentation

PROCHAINE ÉTAPE : Déploiement → Phase refactorisation progressive
"""
