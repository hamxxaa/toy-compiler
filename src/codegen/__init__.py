"""
Code Generation Module

This module contains intermediate code generation components:
- TACGenerator: Three Address Code generator
"""

from .TACGenerator import TACGenerator, TAC, TACInstruction, Var, Const, TempVar

__all__ = ['TACGenerator', 'TAC', 'TACInstruction', 'Var', 'Const', 'TempVar']