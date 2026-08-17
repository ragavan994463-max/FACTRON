"""FACTRON application package.

The application layer exposes the runtime entry points of FACTRON while
keeping domain logic inside the dedicated architecture layers.
"""

from .main import FactronApplication, create_application

__all__ = [
    "FactronApplication",
    "create_application",
]
