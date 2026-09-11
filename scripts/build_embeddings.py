"""Régénère le cache d'embeddings versionné (models/embeddings_mtn.npz).

À exécuter après toute modification de src/documents_mtn.py :
    python scripts/build_embeddings.py

Le fichier .npz est commité dans le dépôt afin que le backend déployé
(Render, CI) démarre rapidement sans recalculer ni retélécharger le modèle
pour la constitution de la base vectorielle.
"""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src import rag_mtn  # noqa: E402


def main() -> int:
    print(f"Base documentaire : {len(rag_mtn.chunks)} chunks.")
    print(f"Modèle : {rag_mtn.MODELE_EMBEDDINGS}")
    print("Calcul des embeddings...")

    embeddings = rag_mtn.construire_embeddings(save=True)

    print(
        f"✅ {embeddings.shape[0]} embeddings de dimension "
        f"{embeddings.shape[1]} sauvegardés dans "
        f"{rag_mtn.EMBEDDINGS_PATH.relative_to(ROOT_DIR)}"
    )

    # Vérification immédiate : le cache doit être chargeable tel quel.
    rag_mtn._embeddings = None
    recharge = rag_mtn.obtenir_embeddings()
    if recharge.shape != embeddings.shape:
        print("❌ Le cache relu ne correspond pas aux embeddings calculés.")
        return 1
    print("✅ Vérification de rechargement : OK.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
