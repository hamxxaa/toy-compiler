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
from src.lexer.Tokenizer import Tokenizer
from src.parser.Parser import Parser
from src.codegen.TACGenerator import TACGenerator
from src.optimization.Optimizer import Optimizer
from src.backend.X86Backend import X86Backend

__all__ = [
    'compile_program',
    'Tokenizer',
    'Parser', 
    'TACGenerator',
    'Optimizer',
    'X86Backend'
]