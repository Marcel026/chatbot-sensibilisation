"""
Moteur RAG (Retrieval-Augmented Generation) pour le chatbot MTN.

Ce module encapsule l'ensemble de la logique de recherche et génération :
1. RETRIEVAL : Recherche vectorielle avec SentenceTransformers
2. GENERATION : Assemblage de la réponse finale
3. UTILS : Normalisation, détection d'intent, synonymes

Fonctions publiques (importées par app.py et src.whatsapp_bot.py) :
- rechercher_information(question, top_k=3) → Liste de résultats
- obtenir_reponse(question) → Texte réponse final

Configuration :
- DEBUG=False : Activer pour logs détaillés
- SEUIL_SIMILARITE=0.65 : Score minimum de similarité
"""

import re
import logging
import threading
import numpy as np
import unicodedata
from pathlib import Path
from sentence_transformers import SentenceTransformer

from .documents_mtn import DOCUMENTS_MTN

# ========================
# Configuration du logging
# ========================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ========================
# Configuration globale
# ========================
DEBUG = False  # Mode debug (affiche logs supplémentaires si True)
SEUIL_SIMILARITE = 0.65  # Score minimum de similarité pour retourner un résultat
MODELE_EMBEDDINGS = "all-MiniLM-L6-v2"

# Cache d'embeddings pré-calculés, versionné dans le dépôt (models/embeddings_mtn.npz).
# Régénérer avec : python scripts/build_embeddings.py
EMBEDDINGS_PATH = (
    Path(__file__).resolve().parents[1] / "models" / "embeddings_mtn.npz"
)
SYNONYMES = {
    "ub": "ulcere de buruli",
    "ulcère de buruli": "ulcere de buruli",
    "ulcere_de_buruli": "ulcere de buruli",
    "buruli": "ulcere de buruli",
    "bilharziose": "schistosomiase",
    "schistosomiases": "schistosomiase",
    "shistosomiase": "schistosomiase",
    "shistosomiases": "schistosomiase",
    "morsure de serpent": "ems",
    "envenimation": "ems",
    "symptomes": "symptomes",
    "signes": "symptomes"
}

SYNONYMES.update({
    "cancrum oris": "noma",
    "gangrene de la bouche": "noma",
    "gangrène de la bouche": "noma"
})

# ========================
# Initialisation du modèle (lazy) et des embeddings
# ========================
# Le modèle n'est chargé en mémoire que si la recherche vectorielle en a
# besoin (les boosters de catégories n'en requièrent pas). Les embeddings
# des documents sont lus depuis le cache .npz versionné s'il est valide.
_embedder = None
_embeddings = None
_chargement_lock = threading.Lock()

logger.debug("Préparation des chunks documentaires...")
chunks = []

for doc in DOCUMENTS_MTN:
    chunk = {
        "maladie": doc["maladie"],
        "categorie": doc["categorie"],
        "contenu": doc["contenu"]
    }
    chunks.append(chunk)

logger.debug(f"✅ {len(chunks)} chunks préparés.")


def _construire_textes():
    """Textes composés servant de clé de cohérence au cache d'embeddings."""
    return [
        f"{c['maladie']} {c['categorie']} {c['contenu']}"
        for c in chunks
    ]


def get_embedder():
    """Charge le modèle SentenceTransformer une seule fois (thread-safe)."""
    global _embedder
    if _embedder is None:
        with _chargement_lock:
            if _embedder is None:
                logger.info(
                    "Chargement du modèle SentenceTransformer (%s)...",
                    MODELE_EMBEDDINGS
                )
                _embedder = SentenceTransformer(MODELE_EMBEDDINGS)
                logger.info("✅ Modèle chargé avec succès.")
    return _embedder


def construire_embeddings(chemin=None, save=True):
    """Calcule les embeddings des chunks et les sauvegarde dans le cache .npz.

    Utilisé par scripts/build_embeddings.py pour régénérer le cache versionné,
    et en repli lorsque le cache est absent ou incohérent avec la base.
    """
    embeddings = get_embedder().encode(
        _construire_textes(),
        convert_to_numpy=True
    )
    if save:
        sortie = Path(chemin) if chemin else EMBEDDINGS_PATH
        sortie.parent.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(
            sortie,
            embeddings=embeddings,
            textes=np.array(_construire_textes())
        )
        logger.info(
            "✅ Embeddings sauvegardés dans %s (%d documents).",
            sortie, len(embeddings)
        )
    return embeddings


def _charger_embeddings():
    """Charge le cache .npz s'il correspond à la base, sinon recalcule."""
    global _embeddings
    if EMBEDDINGS_PATH.exists():
        try:
            cache = np.load(EMBEDDINGS_PATH, allow_pickle=False)
            textes_stockes = [str(t) for t in cache["textes"].tolist()]
            if textes_stockes == _construire_textes():
                _embeddings = cache["embeddings"]
                logger.info(
                    "✅ %d embeddings chargés depuis %s.",
                    len(textes_stockes), EMBEDDINGS_PATH.name
                )
                return
            logger.warning(
                "Le cache d'embeddings ne correspond plus à la base "
                "documentaire : recalcul en cours."
            )
        except (OSError, ValueError, KeyError) as error:
            logger.warning(
                "Cache d'embeddings illisible (%s) : recalcul en cours.",
                error
            )
    _embeddings = construire_embeddings(save=False)


def obtenir_embeddings():
    """Retourne la matrice d'embeddings (chargement paresseux, thread-safe)."""
    if _embeddings is None:
        with _chargement_lock:
            if _embeddings is None:
                _charger_embeddings()
    return _embeddings


def precharger_modele():
    """Force le chargement du modèle et des embeddings (warmup serveur)."""
    obtenir_embeddings()
    get_embedder().encode(["échauffement"], convert_to_numpy=True)
    logger.info("✅ Moteur RAG prêt (modèle et embeddings en mémoire).")

# =========================
# SECTION 1 : UTILITAIRES
# =========================

def normaliser_texte(texte):

    texte = texte.lower()

    texte = ''.join(
        c for c in unicodedata.normalize('NFD', texte)
        if unicodedata.category(c) != 'Mn'
    )

    return texte

# Préparer la liste de synonymes normalisés triée par longueur (desc) pour remplacements sûrs
SYNONYM_LIST = sorted(
    [(normaliser_texte(k), normaliser_texte(v)) for k, v in SYNONYMES.items()],
    key=lambda kv: -len(kv[0])
)

# -------------------------
# Configuration des boosters
# -------------------------
CATEGORY_BOOSTERS = {
    "definition": [
        r"\bqu'est-ce que\b",
        r"\bc'est quoi\b",
        r"\bc est quoi\b",
        r"\bdefinition\b",
        r"\bsignifie\b",
        r"\bveut dire\b",
        r"\bexplique\b",
        r"\bdécris\b",
        r"\bde quoi s'agit-il\b"
    ],
    "prevention": [
        r"\bcomment prévenir\b",
        r"\bprévenir\b",
        r"\bprevenir\b",
        r"\bprévention\b",
        r"\bprevention\b",
        r"\béviter\b",
        r"\beviter\b",
        r"\bprotection\b",
        r"\bprotéger\b",
        r"\bmesures\b",
        r"\bhygiène\b",
        r"\bprécautions\b"
    ],
    "conduite": [
        r"\bque faire\b",
        r"\bdois-je faire\b",
        r"\bje pense avoir\b",
        r"\bj'ai peur d'avoir\b",
        r"\bsuspicion\b",
        r"\bfaire face\b",
        r"\bpremier soin\b",
        r"\bpremiers secours\b",
        r"\btraitement\b",
        r"\bprise en charge\b"
    ],
    "gravite": [
        r"\bsignes de gravité\b",
        r"\bgravité\b",
        r"\bgrave\b",
        r"\bcomplication\b",
        r"\bcomplications\b"
    ],
    "signes_alerte": [
        r"\balerte\b",
        r"\bconsulter\b",
        r"\binquiéter\b",
        r"\binquieter\b",
        r"\burgence\b",
        r"\burgent\b",
        r"\bappeler\b",
        r"\baide\b",
        r"\bmédecin\b",
        r"\bhôpital\b",
        r"\bdanger\b",
        r"\bcrise\b",
        r"\baggravation\b"
    ],
    "symptomes": [
        r"\bsymptome(s)?\b",
        r"\bsignes?\b",
        r"\bmanifestation(s)?\b",
        r"\btableau\b",
        r"\bressent\b",
        r"\béprouve\b"
    ],
    "transmission": [
        r"\btransmet\b",
        r"\btransmission\b",
        r"\battrape\b",
        r"\bcontagieux\b",
        r"\bse transmet\b",
        r"\bcommunication\b",
        r"\bpropagation\b",
        r"\bcontamination\b",
        r"\bcomment attraper\b",
        r"\brisque d'attraper\b"
    ],
    "facteurs_risque": [
        r"\bfacteurs de risque\b",
        r"\brisque\b",
        r"\bexposé\b",
        r"\bexposés\b",
        r"\bplus exposé\b"
    ],
    "gestes_interdits": [
        r"\bne pas\b",
        r"\binterdit\b",
        r"\binterdits\b",
        r"\bpas faire\b"
    ]
}

# Pré-calculer une version normalisée (et compilée) des patterns de boosters
# afin de les appliquer sur des questions déjà normalisées (sans accents).
CATEGORY_BOOSTERS_NORMALIZED = {
    cat: [re.compile(normaliser_texte(p)) for p in patterns]
    for cat, patterns in CATEGORY_BOOSTERS.items()
}

def detecter_categorie(question_lower):
    """Détecte la catégorie la plus pertinente à partir de l'intention de la question (question_lower doit être normalisé)."""
    for category in ["definition", "prevention", "conduite", "gravite", "signes_alerte", "symptomes", "transmission", "facteurs_risque", "gestes_interdits"]:
        for pat in CATEGORY_BOOSTERS_NORMALIZED.get(category, []):
            # pat est un regex compilé appliqué sur le texte normalisé
            if pat.search(question_lower):
                return category
    return None


def appliquer_synonymes(texte):
    """Applique les synonymes de maladie sur un texte déjà normalisé.

    Utilise des remplacements basés sur des bornes de mots pour éviter les
    remplacements partiels à l'intérieur d'autres mots. La liste des synonymes
    est déjà normalisée et triée par longueur (SYNONYM_LIST).
    """
    texte_normalise = normaliser_texte(texte)
    for ancien, nouveau in SYNONYM_LIST:
        pattern = r"\b" + re.escape(ancien) + r"\b"
        texte_normalise = re.sub(pattern, nouveau, texte_normalise)
    return texte_normalise


def detecter_maladie(question_lower):
    """Détecte la maladie mentionnée dans la question."""
    question_normalisee = appliquer_synonymes(question_lower)

    for chunk in chunks:
        maladie_normalisee = normaliser_texte(chunk["maladie"])
        if maladie_normalisee in question_normalisee:
            return chunk["maladie"]

    return None


def check_category_booster(question_lower):
    """
    Vérifie les boosters de catégorie et retourne le résultat si trouvé.
    Privilégie la catégorie attendue et la maladie détectée.
    """
    categorie = detecter_categorie(question_lower)
    if not categorie:
        return None

    maladie = detecter_maladie(question_lower)
    if not maladie:
        return None

    for chunk in chunks:
        if (
            chunk["categorie"] == categorie
            and chunk["maladie"] == maladie
        ):
            return [{
                "maladie": chunk["maladie"],
                "categorie": chunk["categorie"],
                "contenu": chunk["contenu"],
                "score": 1.0
            }]

    return None

# =========================
# SECTION 2 : RECHERCHE VECTORIELLE (RETRIEVAL)
# =========================
def rechercher_information(question, top_k=3):
    """
    Recherche les informations les plus pertinentes pour une question donnée.
    Combine les boosters de catégorie avec une recherche vectorielle.
    """
    # Validation des paramètres
    if not question or not isinstance(question, str):
        return [{
            "maladie": "erreur",
            "categorie": "parametre_invalide",
            "contenu": "Veuillez poser une question non-vide.",
            "score": 0.0
        }]
    
    if top_k < 1:
        return [{
            "maladie": "erreur",
            "categorie": "parametre_invalide",
            "contenu": "top_k doit être au moins 1.",
            "score": 0.0
        }]
    
    if not chunks:
        return [{
            "maladie": "erreur",
            "categorie": "source_vide",
            "contenu": "Aucun document disponible dans la base.",
            "score": 0.0
        }]

    question_lower = normaliser_texte(question)
    question_lower = appliquer_synonymes(question_lower)

    maladie_detectee = detecter_maladie(question_lower)
    categorie_attendue = detecter_categorie(question_lower)

    if DEBUG:
        logger.debug(f"Question détectée: {question_lower}")
        logger.debug(f"Maladie détectée: {maladie_detectee}")
        logger.debug(f"Catégorie attendue: {categorie_attendue}")
    # =========================
    # MALADIES NON ENCORE AJOUTÉES
    # =========================

    maladies_non_disponibles = [
        "onchocercose",
        "filariose",
        "pian",
        "trypanosomiase",
        "leishmaniose"
    ]

    if any(maladie in question_lower for maladie in maladies_non_disponibles):

        return [{
            "maladie": "inconnue",
            "categorie": "information_absente",
            "contenu": (
                "Je ne dispose pas encore d'informations sur cette maladie dans ma base documentaire."
            ),
            "score": 0.0
        }]

    if maladie_detectee and categorie_attendue:
        categories_disponibles = {
            chunk["categorie"]
            for chunk in chunks
            if chunk["maladie"] == maladie_detectee
        }
        if categorie_attendue not in categories_disponibles:
            return [{
                "maladie": maladie_detectee,
                "categorie": "information_absente",
                "contenu": (
                    f"L'information sur la catégorie « {categorie_attendue} » "
                    f"n'est pas disponible pour la maladie « {maladie_detectee} » "
                    "dans ma base documentaire."
                ),
                "score": 0.0
            }]

    # =========================
    # BOOSTERS DE CATÉGORIE (REFACTORISÉS)
    # =========================
    booster_result = check_category_booster(question_lower)
    if booster_result:
        return booster_result

    if maladie_detectee and categorie_attendue:
        preferred_chunks = [
            chunk for chunk in chunks
            if chunk["maladie"] == maladie_detectee and chunk["categorie"] == categorie_attendue
        ]
        if preferred_chunks:
            return [{
                "maladie": preferred_chunks[0]["maladie"],
                "categorie": preferred_chunks[0]["categorie"],
                "contenu": preferred_chunks[0]["contenu"],
                "score": 1.0
            }]

    if maladie_detectee:
        maladie_chunks = [
            chunk for chunk in chunks
            if chunk["maladie"] == maladie_detectee
        ]
        if maladie_chunks:
            fallback_chunk = next(
                (chunk for chunk in maladie_chunks if chunk["categorie"] == "definition"),
                maladie_chunks[0]
            )
            return [{
                "maladie": fallback_chunk["maladie"],
                "categorie": fallback_chunk["categorie"],
                "contenu": fallback_chunk["contenu"],
                "score": 0.9
            }]

    # =========================
    # RECHERCHE VECTORIELLE
    # =========================

    question_embedding = get_embedder().encode(
        [question],
        convert_to_numpy=True
    )

    embeddings = obtenir_embeddings()

    question_norm = (
        question_embedding /
        np.linalg.norm(question_embedding)
    )

    embeddings_norm = (
        embeddings /
        np.linalg.norm(
            embeddings,
            axis=1,
            keepdims=True
        )
    )

    similarites = np.dot(
        embeddings_norm,
        question_norm.T
    ).flatten()

    top_indices = np.argsort(similarites)[-top_k:][::-1]

    results = []
    # Construction des résultats trouvés
    for idx in top_indices:
        if similarites[idx] < SEUIL_SIMILARITE:
            continue

        if DEBUG:
            logger.debug(
                f"Résultat trouvé: {chunks[idx]['maladie']} | "
                f"{chunks[idx]['categorie']} | "
                f"score={similarites[idx]:.3f}"
            )

        entry = {
            "maladie": chunks[idx]["maladie"],
            "categorie": chunks[idx]["categorie"],
            "contenu": chunks[idx]["contenu"],
            "score": float(similarites[idx])
        }

        if maladie_detectee and chunks[idx]["maladie"] == maladie_detectee:
            entry["score"] += 0.05
        if categorie_attendue and chunks[idx]["categorie"] == categorie_attendue:
            entry["score"] += 0.04

        results.append(entry)

    # Aucun résultat pertinent trouvé
    if not results:
        return [{
            "maladie": "inconnue",
            "categorie": "information_absente",
            "contenu": (
                "Je ne dispose pas encore d'informations sur cette maladie dans ma base documentaire."
            ),
            "score": 0.0
        }]

    results.sort(key=lambda item: item["score"], reverse=True)

    # Résultats trouvés
    return results

# =========================
# SECTION 3 : GÉNÉRATION (GENERATION)
# =========================

def obtenir_reponse(question):
    """
    Retourne directement le texte de la meilleure réponse.
    """
    try:
        if not question or not isinstance(question, str):
            return "Veuillez poser une question."
        
        resultats = rechercher_information(question)
        
        # La fonction retourne toujours au moins un résultat
        if resultats and resultats[0]["contenu"]:
            return resultats[0]["contenu"]
        
        return (
            "Je ne dispose pas encore d'informations sur cette maladie "
            "dans ma base documentaire."
        )
    except Exception as e:
        return f"Erreur lors de la recherche: {str(e)}"