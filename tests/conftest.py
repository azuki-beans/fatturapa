"""Fixture di pytest. Gli helper veri stanno in `tests/supporto.py`."""
from pathlib import Path

import pytest

from supporto import TRACCIATI


@pytest.fixture
def tracciati() -> Path:
    """Cartella con i tracciati di esempio dell'Agenzia delle Entrate."""
    return TRACCIATI
