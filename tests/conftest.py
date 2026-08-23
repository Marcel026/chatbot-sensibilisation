"""Configuration pytest globale"""
import pytest
import sys
from pathlib import Path

# Ajouter le répertoire parent au path pour les imports
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))


@pytest.fixture(scope="session")
def project_root():
    """Fournit le chemin racine du projet"""
    return ROOT_DIR


@pytest.fixture
def sample_question():
    """Fournit une question d'exemple pour les tests"""
    return "Qu'est-ce que la lèpre ?"


@pytest.fixture
def sample_maladie():
    """Fournit une maladie d'exemple"""
    return "lepre"


@pytest.fixture
def sample_categorie():
    """Fournit une catégorie d'exemple"""
    return "definition"


def pytest_configure(config):
    """Configuration pytest au démarrage"""
    config.addinivalue_line(
        "markers", 
        "integration: mark test as integration test (vs unit)"
    )
    config.addinivalue_line(
        "markers",
        "slow: mark test as slow (deselect with '-m \"not slow\"')"
    )
