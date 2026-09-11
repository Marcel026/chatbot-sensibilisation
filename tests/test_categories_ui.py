"""Tests de l'exploration par catégorie proposée par l'interface Streamlit.

Vérifie que :
- les boutons de l'interface couvrent exactement CATEGORIES_VALIDES ;
- chaque maladie possède un libellé d'affichage ;
- pour chaque maladie × catégorie, la question générée par le gabarit
  oriente le moteur RAG vers le bon chunk documentaire.
"""

import pytest

from src.documents_mtn import (
    CATEGORIES_UI,
    CATEGORIES_VALIDES,
    MALADIES_LABELS,
    MALADIES_VALIDES,
)
from src.rag_mtn import rechercher_information


def test_categories_ui_couvre_exactement_les_categories_valides():
    """Les boutons affichés correspondent 1-pour-1 aux catégories valides."""
    identifiants = {categorie for categorie, _, _, _ in CATEGORIES_UI}
    assert identifiants == CATEGORIES_VALIDES


def test_maladies_ont_toutes_un_libelle():
    """Chaque maladie valide possède un libellé d'affichage."""
    assert set(MALADIES_LABELS) == MALADIES_VALIDES


def test_gabarits_contiennent_un_unique_placeholder():
    """Chaque gabarit référence exactement la variable {maladie}."""
    for _, _, _, gabarit in CATEGORIES_UI:
        assert "{maladie}" in gabarit
        assert gabarit.count("{") == 1
        assert gabarit.count("}") == 1


@pytest.mark.parametrize("maladie", sorted(MALADIES_VALIDES))
@pytest.mark.parametrize(
    "categorie", [c[0] for c in CATEGORIES_UI]
)
def test_gabarit_retourne_la_bonne_information(maladie, categorie):
    """La question générée (maladie × catégorie) trouve le chunk exact."""
    gabarit = next(
        gabarit
        for identifiant, _, _, gabarit in CATEGORIES_UI
        if identifiant == categorie
    )
    question = gabarit.format(maladie=MALADIES_LABELS[maladie])

    resultats = rechercher_information(question)

    assert resultats, f"Aucun résultat pour : {question}"
    assert resultats[0]["maladie"] == maladie, (
        f"Maladie incorrecte pour : {question} "
        f"(obtenu : {resultats[0]['maladie']})"
    )
    assert resultats[0]["categorie"] == categorie, (
        f"Catégorie incorrecte pour : {question} "
        f"(obtenu : {resultats[0]['categorie']})"
    )
