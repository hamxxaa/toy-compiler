"""
Toy Compiler Package

This package contains the main components of a simple toy compiler:
- Tokenizer: Breaks source code into tokens (in lexer module)
- Parser: Converts tokens into AST (in parser module)
- TACGenerator: Generates Three Address Code from AST (in codegen module)
- Optimizer: Optimizes TAC (in optimization module)
- X86Backend: Generates x86 assembly code from TAC (in backend module)
"""

__version__ = "1.0.0"
__author__ = "Toy Compiler Team"

from .compiler import compile_program
from lexer import Tokenizer
from parser import Parser
from codegen import TACGenerator
from optimization import Optimizer
from backend import X86Backend

__all__ = [
    'compile_program',
    'Tokenizer',
    'Parser', 
    'TACGenerator',
    'Optimizer',
    'X86Backend'
]