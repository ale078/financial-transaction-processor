"""Extractors package for financial consolidated statements."""

from src.extractors.base_extractor import BaseExtractor
from src.extractors.galicia_extractor import GaliciaExtractor
from src.extractors.balanz_extractor import BalanzExtractor
from src.extractors.mercadopago_extractor import MercadoPagoExtractor
from src.extractors.uala_extractor import UalaExtractor

ALL_EXTRACTORS = [
    GaliciaExtractor,
    BalanzExtractor,
    MercadoPagoExtractor,
    UalaExtractor
]

__all__ = [
    "BaseExtractor",
    "GaliciaExtractor",
    "BalanzExtractor",
    "MercadoPagoExtractor",
    "UalaExtractor",
    "ALL_EXTRACTORS"
]
