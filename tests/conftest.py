"""Test configuration and fixtures for pytest."""

import sys
from pathlib import Path

import pytest

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

src_path = project_root / "src"
sys.path.insert(0, str(src_path))


@pytest.fixture(scope="session")
def project_root_path():
    """Provide the project root path."""
    return project_root


@pytest.fixture(scope="session")
def src_path():
    """Provide the src directory path."""
    return project_root / "src"
