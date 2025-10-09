import subprocess
from CodeGenerator import CodeGenerator
from Tokenizer import Tokenizer
from Parser import Parser


def create_tokenizer():
    tokenizer = Tokenizer()

    tokenizer.add_skip_pattern("( |\t|\n)+")

    tokenizer.add_pattern("KEYWORD", "(while|print|var|if|do)", priority=5)
    tokenizer.add_pattern(
        "IDENTIFIER", "([a-z]|[A-Z])([a-z]|[A-Z]|[0-9]|_)*", priority=4
    )
    tokenizer.add_pattern("SIGNED_NUMBER", "-[0-9]+", priority=6)
    tokenizer.add_pattern("NUMBER", "[0-9]+", priority=3)
    tokenizer.add_pattern("SYMBOL", "(;|\\(|\\)|=)", priority=2)
    tokenizer.add_pattern("OPERATOR", "(\\+|-|\\*|/)", priority=1)
    tokenizer.add_pattern("CONDITIONAL_OPERATOR", "(<|>|==|<=|>=|!=)", priority=1)
    tokenizer.add_pattern("LOGICAL_OPERATOR", "(&|\\|)", priority=1)

    return tokenizer


def tokenize(input_str):
    tokenizer = create_tokenizer()
    tokens = tokenizer.tokenize(input_str)
    return tokens


with open("code.txt", "r") as raw_code:
    code_string = raw_code.read()

tokens = tokenize(code_string)

parser = Parser(tokens)
ast = parser.parse_program()

cg = CodeGenerator()
code = cg.get_full_code(ast)

with open("temp.asm", "w") as f:
    f.write(code)
subprocess.run(["nasm", "-f", "elf32", "-o", "temp.o", "temp.asm"])
# subprocess.run(["ld", "-m", "elf_i386", "-o", "temp", "temp.o"])
subprocess.run(["ld", "-m", "elf_i386", "-o", "program", "temp.o", "print_integer.o"])
subprocess.run(["./program"])
