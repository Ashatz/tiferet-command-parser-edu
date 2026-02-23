"""Tiferet Command Parser - Educational Scanner"""

# *** exports

# ** app
from .events import (
    DomainEvent,
    TiferetError,
    ExtractText,
    LexerInitialized,
    PerformLexicalAnalysis,
    EmitScanResult,
)
from .interfaces import LexerService
from .utils import TiferetLexer

# *** version

__version__ = '0.1.0'
