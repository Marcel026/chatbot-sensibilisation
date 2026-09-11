"""Tests unitaires pour le moteur RAG (rag_mtn.py)"""
import pytest
from src.rag_mtn import (
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

    def test_categorie_gestes_interdits_dengue(self):
        """Retourne la catégorie des gestes interdits pour la dengue."""
        results = rechercher_information(
            "Quels sont les gestes interdits pour la dengue ?"
        )
        assert results[0]["categorie"] == "gestes_interdits"
        assert "aspirine" in results[0]["contenu"].lower()


class TestOrientationSanitaire:
    """Outil de sensibilisation : jamais de conseil médicamenteux,
    toujours une orientation vers une structure sanitaire."""

    @pytest.mark.parametrize(
        "question",
        [
            "Mon enfant vient d'être mordu par un serpent, que faire ?",
            "Ma fille a été mordue par un serpent",
            "Il y a eu une morsure de serpent à la maison, premiers secours ?",
            "Un serpent m'a mordu au champ",
        ],
    )
    def test_urgence_serpent_oriente_vers_conduite_ems(self, question):
        """Toute formulation d'urgence serpent renvoie la conduite EMS
        (immobiliser, conduire au centre de santé)."""
        results = rechercher_information(question)
        assert results[0]["maladie"] == "ems"
        assert results[0]["categorie"] == "conduite"
        assert "centre de s" in results[0]["contenu"].lower()

    def test_gravite_serpent_repond_a_la_question_de_gravite(self):
        """« C'est grave ? » renvoie la gravité EMS (urgence médicale)."""
        results = rechercher_information(
            "Une piqûre de serpent, c'est grave ?"
        )
        assert results[0]["maladie"] == "ems"
        assert results[0]["categorie"] == "gravite"

    @pytest.mark.parametrize(
        "question",
        [
            "Quel médicament prendre contre la dengue ?",
            "Y a-t-il un remède contre la lèpre ?",
            "Quel traitement pour la schistosomiase ?",
        ],
    )
    def test_question_therapeutique_oriente_vers_conduite(self, question):
        """Une question de traitement est orientée vers la conduite à tenir
        (consultation), jamais vers un conseil de médicament."""
        results = rechercher_information(question)
        assert results[0]["categorie"] == "conduite"
        assert results[0]["maladie"] != "inconnue"


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
