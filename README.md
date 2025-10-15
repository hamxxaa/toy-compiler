# Toy Compiler

A simple compiler that compiles a toy language to x86 assembly and runs it.

## Project Structure

```
src/
├── lexer/          # Tokenization
├── parser/         # Syntax analysis & AST
├── codegen/        # Three Address Code generation
├── optimization/   # Code optimization
├── backend/        # x86 assembly generation
├── utils/          # Legacy utilities
└── compiler/       # Main orchestrator
```

## Usage

```bash
python3 main.py examples/code.txt
```

Or use the platform scripts:
```bash
scripts/compile.sh examples/code.txt        # Linux/macOS
scripts/compile.bat examples/code.txt       # Windows
```

## Options

- `-o, --output`: Output executable name
- `--no-optimize`: Disable optimization
- `--print-tokens`: Show tokenization
- `--print-ast`: Show AST
- `--print-tac`: Show Three Address Code
- `--print-optimized-tac`: Show optimized TAC

## Requirements

- Python 3.x
- NASM assembler
- System linker (ld on Unix, link.exe on Windows)

Build files go to `build/`, examples are in `examples/`.