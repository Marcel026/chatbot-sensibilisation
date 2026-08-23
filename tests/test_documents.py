"""Tests de validation pour la base documentaire (documents_mtn.py)"""
import pytest
from documents_mtn import (
    DOCUMENTS_MTN,
    MALADIES_VALIDES,
    CATEGORIES_VALIDES,
    CATEGORIES_REQUISES,
    valider_documents,
)


class TestStructureDocuments:
    """Tests de structure de la base documentaire"""

    def test_documents_non_vides(self):
        """Vérifie qu'il y a des documents"""
        assert len(DOCUMENTS_MTN) > 0

    def test_documents_sont_dicts(self):
        """Vérifie que tous les documents sont des dictionnaires"""
        for doc in DOCUMENTS_MTN:
            assert isinstance(doc, dict)

    def test_documents_ont_cles_requises(self):
        """Vérifie que chaque document a les clés requises"""
        for doc in DOCUMENTS_MTN:
            assert "maladie" in doc
            assert "categorie" in doc
            assert "contenu" in doc

    def test_documents_contenu_non_vide(self):
        """Vérifie que le contenu n'est pas vide"""
        for doc in DOCUMENTS_MTN:
            assert len(doc["contenu"].strip()) > 0


class TestMaladiesValides:
    """Tests des maladies"""

    def test_toutes_maladies_dans_valides(self):
        """Vérifie que chaque maladie du document est valide"""
        for doc in DOCUMENTS_MTN:
            assert doc["maladie"] in MALADIES_VALIDES, \
                f"Maladie inconnue: {doc['maladie']}"

    def test_maladies_valides_presentes(self):
        """Vérifie que toutes les maladies valides sont documentées"""
        maladies_presentes = {doc["maladie"] for doc in DOCUMENTS_MTN}
        for maladie in MALADIES_VALIDES:
            assert maladie in maladies_presentes, \
                f"Maladie {maladie} pas documentée"


class TestCategoriesValides:
    """Tests des catégories"""

    def test_toutes_categories_valides(self):
        """Vérifie que chaque catégorie est valide"""
        for doc in DOCUMENTS_MTN:
            assert doc["categorie"] in CATEGORIES_VALIDES, \
                f"Catégorie inconnue: {doc['categorie']}"

    def test_categories_requises_presentes(self):
        """Vérifie que chaque maladie a les catégories requises"""
        couverture = {}
        for doc in DOCUMENTS_MTN:
            maladie = doc["maladie"]
            couverture.setdefault(maladie, set()).add(doc["categorie"])

        for maladie in MALADIES_VALIDES:
            categories = couverture.get(maladie, set())
            missing = CATEGORIES_REQUISES - categories
            assert len(missing) == 0, \
                f"{maladie} manque les catégories: {missing}"


class TestValidation:
    """Tests de la fonction de validation"""

    def test_validation_pass(self):
        """Teste que la validation détecte une base valide"""
        result = valider_documents()
        assert "erreurs" in result
        assert "couverture" in result
        # Une base bien formée doit avoir peu d'erreurs
        # (Adapter selon votre tolérance)

    def test_validation_retourne_dict(self):
        """Teste que la validation retourne un dictionnaire"""
        result = valider_documents()
        assert isinstance(result, dict)


class TestContenuDocumentaire:
    """Tests du contenu des documents"""

    def test_contenu_format_valide(self):
        """Vérifie que le contenu est formaté correctement"""
        for doc in DOCUMENTS_MTN:
            # Le contenu doit être une chaîne de caractères
            assert isinstance(doc["contenu"], str)
            # Ne doit pas être juste du whitespace
            assert doc["contenu"].strip() != ""

    def test_documents_ont_metadata(self):
        """Vérifie la présence des métadonnées (source, date_maj)"""
        for doc in DOCUMENTS_MTN:
            # Ces champs sont optionnels mais recommandés
            if "source" in doc:
                assert isinstance(doc["source"], str)
            if "date_maj" in doc:
                assert isinstance(doc["date_maj"], str)


@pytest.mark.parametrize("maladie", [
    "lepre",
    "dengue",
    "ems",
    "schistosomiase",
    "ulcere de buruli",
    "noma",
])
def test_maladie_a_definition(maladie):
    """Test paramétrisé : chaque maladie doit avoir une définition"""
    docs = [d for d in DOCUMENTS_MTN 
            if d["maladie"] == maladie and d["categorie"] == "definition"]
    assert len(docs) > 0, f"{maladie} n'a pas de définition"


@pytest.mark.parametrize("maladie", [
    "lepre",
    "dengue",
    "ems",
    "schistosomiase",
    "ulcere de buruli",
    "noma",
])
def test_maladie_a_symptomes(maladie):
    """Test paramétrisé : chaque maladie doit avoir des symptômes"""
    docs = [d for d in DOCUMENTS_MTN 
            if d["maladie"] == maladie and d["categorie"] == "symptomes"]
    assert len(docs) > 0, f"{maladie} n'a pas de symptômes documentés"
