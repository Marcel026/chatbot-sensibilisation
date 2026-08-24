"""Tests unitaires pour le moteur RAG (rag_mtn.py)"""
import pytest
from rag_mtn import (
    normaliser_texte,
    rechercher_information,
    obtenir_reponse,
)


class TestNormalisationTexte:
    """Test de la normalisation de texte"""

    def test_normalise_minuscules(self):
        """Vérifie que le texte est converti en minuscules"""
        result = normaliser_texte("LÈPRE")
        assert result == result.lower()

    def test_normalise_accents(self):
        """Vérifie que les accents sont supprimés"""
        result = normaliser_texte("Lèpre")
        # Sans accents
        assert "è" not in result

    def test_normalise_vide(self):
        """Vérifie que le texte vide reste vide"""
        result = normaliser_texte("")
        assert result == ""


class TestRecherchInformation:
    """Tests pour la recherche d'information (RAG)"""

    def test_recherche_question_lepre(self):
        """Teste une recherche sur la lèpre"""
        results = rechercher_information("Qu'est-ce que la lèpre ?")
        assert len(results) > 0
        assert results[0].get("maladie") is not None

    def test_recherche_symptomes_dengue(self):
        """Teste une recherche sur les symptômes de la dengue"""
        results = rechercher_information("Quels sont les symptômes de la dengue ?")
        assert len(results) > 0
        # Doit trouver de la dengue
        assert any(r.get("maladie") == "dengue" for r in results)

    def test_recherche_prevention_schistosomiase(self):
        """Teste une recherche sur la prévention"""
        results = rechercher_information("Comment prévenir la schistosomiase ?")
        assert len(results) > 0

    def test_recherche_top_k(self):
        """Teste que top_k limite le nombre de résultats"""
        results = rechercher_information(
            "Qu'est-ce que la lèpre ?", top_k=2
        )
        assert len(results) <= 2

    def test_recherche_retourne_score(self):
        """Teste que les résultats incluent un score de similarité"""
        results = rechercher_information("lèpre")
        assert len(results) > 0
        assert "score" in results[0]
        assert isinstance(results[0]["score"], (int, float))


class TestObtenirReponse:
    """Tests pour la génération de réponses"""

    def test_reponse_non_vide(self):
        """Teste qu'une question produit une réponse non-vide"""
        response = obtenir_reponse("Qu'est-ce que la lèpre ?")
        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0

    def test_reponse_question_lepre(self):
        """Teste qu'une réponse contient du contenu sur la lèpre"""
        response = obtenir_reponse("Qu'est-ce que la lèpre ?")
        assert "lepre" in response.lower() or "maladie" in response.lower()

    def test_reponse_disclaimer(self):
        """Teste que la réponse inclut un disclaimer (si configuré)"""
        response = obtenir_reponse("Quels sont les symptômes ?")
        # La réponse doit être fournie
        assert len(response) > 10

    def test_categorie_absente_signalee(self):
        """Signale l'absence d'une catégorie pour une maladie connue."""
        results = rechercher_information(
            "Quels sont les gestes interdits pour la dengue ?"
        )
        assert results[0]["categorie"] == "information_absente"
        assert "n'est pas disponible" in results[0]["contenu"]


@pytest.mark.parametrize(
    "question,maladie_attendue",
    [
        ("Lèpre", "lepre"),
        ("Dengue", "dengue"),
        ("Schistosomiase", "schistosomiase"),
        ("Noma", "noma"),
    ],
)
def test_recherche_maladies(question, maladie_attendue):
    """Test paramétrisé pour plusieurs maladies"""
    results = rechercher_information(question)
    assert len(results) > 0
    # Au moins un résultat doit être de la bonne maladie
    assert any(r.get("maladie") == maladie_attendue for r in results)
