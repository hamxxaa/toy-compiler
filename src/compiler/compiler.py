import subprocess
import argparse
import sys
import platform
import os
from src.lexer.Tokenizer import Tokenizer
from src.parser.Parser import Parser
from src.codegen.TACGenerator import TAC, TACGenerator
from src.optimization.Optimizer import Optimizer
from src.backend.X86Backend import X86Backend
from src.analyzer.SemanticAnalyzer import SemanticAnalyzer


def create_tokenizer():
    tokenizer = Tokenizer()

    tokenizer.add_skip_pattern("( |\t|\n)+")

    tokenizer.add_pattern("KEYWORD", "(while|print|var|if|do|return)", priority=5)
    tokenizer.add_pattern("TYPE", "(int|bool)", priority=5)
    tokenizer.add_pattern("BOOLEAN", "(true|false)", priority=6)
    tokenizer.add_pattern(
        "IDENTIFIER", "([a-z]|[A-Z])([a-z]|[A-Z]|[0-9]|_)*", priority=4
    )
    tokenizer.add_pattern("SIGNED_NUMBER", "-[0-9]+", priority=6)
    tokenizer.add_pattern("NUMBER", "[0-9]+", priority=3)
    tokenizer.add_pattern("SYMBOL", "(;|\\(|\\)|=|}|{|,)", priority=2)
    tokenizer.add_pattern("OPERATOR", "(\\+|-|\\*|/)", priority=1)
    tokenizer.add_pattern("CONDITIONAL_OPERATOR", "(<|>|==|<=|>=|!=)", priority=1)
    tokenizer.add_pattern("LOGICAL_OPERATOR", "(&|\\|)", priority=1)

    return tokenizer


def tokenize(input_str):
    tokenizer = create_tokenizer()
    tokens = tokenizer.tokenize(input_str)
    return tokens


def get_os_commands():
    """Detect operating system and return appropriate commands"""
    system = platform.system().lower()

    if system == "windows":
        return {
            "nasm": ["nasm", "-f", "win32"],
            "linker": ["link", "/subsystem:console", "/entry:main"],
            "executable_ext": ".exe",
            "object_ext": ".obj",
            "run_prefix": "",
        }
    else:  # Linux, macOS and other Unix-like systems
        return {
            "nasm": ["nasm", "-f", "elf32"],
            "linker": ["ld", "-m", "elf_i386"],
            "executable_ext": "",
            "object_ext": ".o",
            "run_prefix": "./",
        }


def compile_program(
    input_file,
    optimize=True,
    output_file="program",
    print_tokens=False,
    print_ast=False,
    print_tac=False,
    print_optimized_tac=False,
    save_asm=None,
):
    input_str = ""
    try:
        with open(input_file, "r") as raw_code:
            input_str = raw_code.read()
    except FileNotFoundError:
        print(f"Error: Input file '{input_file}' not found.")
        sys.exit(1)
    except PermissionError:
        print(f"Error: Permission denied when reading '{input_file}'.")
        sys.exit(1)
    if not input_str.strip():
        print("Error: Input file is empty.")
        sys.exit(1)

    tokens = tokenize(input_str)
    parser = Parser(tokens)
    if print_tokens:
        for token in tokens:
            print(token)
    ast = parser.parse_program()
    if print_ast:
        parser.print_ast(ast)
    sa = SemanticAnalyzer()
    sa.analyze(ast)
    tacg = TACGenerator()
    tac = tacg.generate_tac(ast)
    if print_tac:
        for instr in tac.instructions:
            print(instr)
    if optimize:
        op = Optimizer()
        op.optimize(tac)
        if print_optimized_tac:
            print("After optimization:")
            for instr in tac.instructions:
                print(instr)

    x86 = X86Backend(tac)
    code = x86.generate()

    # Detect operating system and get appropriate commands
    os_commands = get_os_commands()

    # Determine file paths
    build_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", "build")
    objects_dir = os.path.join(build_dir, "objects")
    executables_dir = os.path.join(build_dir, "executables")

    # Ensure directories exist
    os.makedirs(objects_dir, exist_ok=True)
    os.makedirs(executables_dir, exist_ok=True)

    # Determine file names
    if save_asm:
        # If save_asm is specified, save the asm file with that name
        asm_file = os.path.join(objects_dir, save_asm)
        if not asm_file.endswith(".asm"):
            asm_file += ".asm"
    else:
        # Use temporary asm file that will be deleted later
        asm_file = os.path.join(objects_dir, "temp.asm")

    object_file = os.path.join(objects_dir, "temp" + os_commands["object_ext"])
    executable_file = os.path.join(
        executables_dir, output_file + os_commands["executable_ext"]
    )

    # Write assembly file
    with open(asm_file, "w") as f:
        f.write(code)

    try:
        # Compile assembly with NASM
        nasm_cmd = os_commands["nasm"] + ["-o", object_file, asm_file]
        subprocess.run(
            nasm_cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE
        )

        if platform.system().lower() == "windows":
            # Windows linking
            link_cmd = os_commands["linker"] + [object_file, "/out:" + executable_file]
            subprocess.run(
                link_cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE
            )

            # Run on Windows
            subprocess.run([executable_file], check=True)
        else:
            # Linux/Unix linking
            link_cmd = os_commands["linker"] + [
                "-o",
                executable_file,
                object_file,
            ]
            subprocess.run(
                link_cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE
            )

            # Run on Linux/Unix
            subprocess.run([executable_file], check=True)

        # Clean up temporary ASM file if not saving it
        if not save_asm and os.path.exists(asm_file):
            os.remove(asm_file)

    except subprocess.CalledProcessError as e:
        print(f"Error: Command execution failed: {e}")
        if e.stderr:
            print(f"Details: {e.stderr.decode()}")
        # Clean up temporary ASM file if compilation failed and not saving it
        if not save_asm and os.path.exists(asm_file):
            os.remove(asm_file)
        sys.exit(1)
    except FileNotFoundError as e:
        print(f"Error: Required tool not found: {e}")
        print("Please ensure that NASM and the required linker tools are installed.")
        # Clean up temporary ASM file if compilation failed and not saving it
        if not save_asm and os.path.exists(asm_file):
            os.remove(asm_file)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Toy Compiler")
    parser.add_argument("input_file", help="Input source file to compile")
    parser.add_argument(
        "-o",
        "--output",
        default="program",
        help="Output executable name (default: program)",
    )
    parser.add_argument(
        "--no-optimize", action="store_true", help="Disable optimization"
    )
    parser.add_argument("--print-tokens", action="store_true", help="Print tokens")
    parser.add_argument("--print-ast", action="store_true", help="Print AST")
    parser.add_argument("--print-tac", action="store_true", help="Print TAC")
    parser.add_argument(
        "--print-optimized-tac", action="store_true", help="Print optimized TAC"
    )
    parser.add_argument(
        "--save-asm",
        help="Save assembly file with specified name (default: don't save)",
    )

    args = parser.parse_args()

    compile_program(
        input_file=args.input_file,
        optimize=not args.no_optimize,
        output_file=args.output,
        print_tokens=args.print_tokens,
        print_ast=args.print_ast,
        print_tac=args.print_tac,
        print_optimized_tac=args.print_optimized_tac,
        save_asm=args.save_asm,
    )


if __name__ == "__main__":
    main()
