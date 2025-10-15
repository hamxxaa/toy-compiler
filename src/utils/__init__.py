"""
Utilities Module

This module contains utility components:
- AsmGenerator: Legacy assembly generator
- CodeGenerator: Legacy code generator
"""

# These are legacy files, may be removed in future versions
try:
    from .AsmGenerator import AsmGenerator
except ImportError:
    AsmGenerator = None

try:
    from .CodeGenerator import CodeGenerator
except ImportError:
    CodeGenerator = None

__all__ = ['AsmGenerator', 'CodeGenerator']