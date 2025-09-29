# L={
# <program> ::= <statement>+
# <statement> ::= <definer> | <equalize> | <if_structure> | <print> | <while_structure>
# <while_structure> ::= "while" <condition> "do" "(" <statement>+ ")"
# <print> ::= "print" "(" <var> ")" ";"
# <if_structure> ::= "if" <condition> "do" "(" <statement>+ ")"
# <condition> ::= <expression> <conditional_operator> <expression> | "(" <condition> ")" <logical_operator> "(" <condition> ")"
# <definer>::= ( "var" <var> ";" ) | ( "var" <var> "=" <expression> ";" )
# <var>::= <letter>+
# <number>::= <digit>+
# <signed_number>::? <number>|"-" <number>
# <expression> ::= <term> (("+" | "-") <term>)*
# <term> ::= <factor> (("*" | "/") <factor>)*
# <factor> ::= <var> | <signed_number> | "(" <expression> ")"
# <operator>::= "+" | "-" | "*" | "/"
# <conditional_operator>::= "<" | ">" | "==" | "<=" | ">=" | "!="
# <logical_operator>::= "&" | "|"
# <digit>::= 1|2|3|4|5|6|7|8|9|0
# <letter>::= a|b|c....z|A|B|C....Z
# <equalize>::= <var> "=" <expression> ";"
# }

import subprocess
from CodeGenerator import CodeGenerator
from TokenHelper import TokenHelper
from Tokenizer import Tokenizer

logical_operators = ["&", "|"]
conditional_operators = ["<", ">", "==", "<=", ">=", "!="]

def create_tokenizer():
    tokenizer = Tokenizer()
    
    tokenizer.add_skip_pattern("( |\t|\n)+")
    
    tokenizer.add_pattern("TWO_CHAR_OP", "(==|<=|>=|!=)", priority=10)
    tokenizer.add_pattern("KEYWORD", "(while|print|var|if|do)", priority=5)
    tokenizer.add_pattern("IDENTIFIER", "([a-z]|[A-Z])([a-z]|[A-Z]|[0-9]|_)*", priority=4)
    tokenizer.add_pattern("SIGNED_NUMBER", "-[0-9]+", priority=6)
    tokenizer.add_pattern("NUMBER", "[0-9]+", priority=3)
    tokenizer.add_pattern("SYMBOL", "(;|\\(|\\)|=)", priority=2)
    tokenizer.add_pattern("OPERATOR", "(\\+|-|\\*|/|&|\\||<|>)", priority=1)
    
    return tokenizer

def tokenize(input_str):
    tokenizer = create_tokenizer()
    tokens = tokenizer.tokenize(input_str)
    return tokens

variables = []

def parser(tokens, cg):
    program = []
    while tokens.peek():
        program.append(parse_statement(tokens, cg))

    code = "section .data \n"
    code += "msg db 'code executed successfully', 0xA \n"
    code += "msglen equ $ - msg \n"
    code += cg.data

    code += "section .bss \nextern num \n"

    code += "section .text \n"
    code += "global _start \n"

    code += "_start: \n"

    code += cg.code

    code += "mov eax, 4 \n"
    code += "mov ebx, 1 \n"
    code += "mov ecx, msg \n"
    code += "mov edx, msglen \n"
    code += "int 0x80 \n"

    code += "mov eax, 1 \n"
    code += "xor ebx, ebx \n"
    code += "int 0x80 \n"
    code += "extern print_integer \nextern newline"
    return code


def parse_statement(tokens, cg):
    # <statement> ::= <definer> | <equalize> | <if_structure> | <print>
    if tokens.peek()[1] == "var":
        return (parse_definer(tokens, cg), "")
    elif tokens.peek()[1] == "print":
        return ("", parse_printer(tokens, cg))
    elif tokens.peek()[1] == "if":
        return ("", parse_if_structure(tokens, cg))
    elif tokens.peek()[1] == "while":
        return ("", parse_while_structure(tokens, cg))
    else:
        return ("", parse_equalizer(tokens, cg))


def parse_while_structure(tokens, cg):
    # <while_structure> ::= "while" <condition> "do" "(" <statement>+ ")"
    tokens.consume("while")
    testlabel = cg.create_unique_label()
    label = cg.create_unique_label()
    cg.start_label(testlabel)
    parse_condition(tokens, cg)
    tokens.consume("do")
    cg.prepare_condition_jump()
    cg.jumpIfZero(label)
    tokens.consume("(")
    while tokens.peek()[1] != ")":
        parse_statement(tokens, cg)[1]
    tokens.consume(")")
    cg.jump(testlabel)
    cg.start_label(label)
    return


def parse_if_structure(tokens, cg):
    # <if_structure> ::= "if" <condition> "do" "(" <statement>+ ")"
    tokens.consume("if")
    parse_condition(tokens, cg)
    tokens.consume("do")
    cg.prepare_condition_jump()
    label = cg.create_unique_label()
    cg.jumpIfZero(label)
    tokens.consume("(")
    while tokens.peek()[1] != ")":
        parse_statement(tokens, cg)[1]
    tokens.consume(")")
    cg.start_label(label)
    return


def parse_condition(tokens, cg):
    # <condition> ::= <expression> <conditional_operator> <expression> | "(" <condition> ")" <logical_operator> "(" <condition> ")"
    def logic(tokens, cg):
        parse_expression(tokens, cg)
        operator = tokens.consume_in(conditional_operators)[1]
        parse_expression(tokens, cg)
        cg.apply_binary_operation("cmp")
        if operator == "<":
            cg.add_to_code("setl al \n")
        elif operator == ">":
            cg.add_to_code("setg al \n")
        elif operator == "==":
            cg.add_to_code("sete al \n")
        elif operator == "<=":
            cg.add_to_code("setle al \n")
        elif operator == ">=":
            cg.add_to_code("setge al \n")
        elif operator == "!=":
            cg.add_to_code("setne al \n")
        cg.extend_al_register()
        return

    if tokens.peek()[1] == "(":
        tokens.consume("(")
        logic(tokens, cg)
        tokens.consume(")")
        tokens.check_in_without_consuming(logical_operators + ["do"])
        while tokens.peek()[1] in logical_operators:
            operator = tokens.consume()[1]
            tokens.consume("(")
            logic(tokens, cg)
            tokens.consume(")")
            if operator == "&":
                cg.apply_binary_operation("and")
            elif operator == "|":
                cg.apply_binary_operation("or")
        return
    else:
        return logic(tokens, cg)


def parse_printer(tokens, cg):
    # <print> ::= "print" "(" <var> ")" ";"
    tokens.consume("print")
    tokens.consume("(")
    name = tokens.check_next_var()[1]
    tokens.consume(")")
    tokens.consume(";")
    cg.print(name)


def parse_definer(tokens, cg):
    # <definer>::= ( "var" <var> ";" ) | ( "var" <var> "=" <expression> ";" )
    tokens.consume("var")
    name = tokens.consume()[1]
    tokens.variables.append(name)
    if tokens.peek()[1] == "=":
        tokens.consume("=")
        parse_expression(tokens, cg)
        cg.define(name, True)
        tokens.consume(";")
    else:
        tokens.consume(";")
        cg.define(name)


def parse_equalizer(tokens, cg):
    # <equalize>::= <var> "=" <expression> ";"
    name = tokens.check_next_var()[1]
    tokens.consume("=")
    parse_expression(tokens, cg)
    tokens.consume(";")
    cg.equalize(name)


def parse_expression(tokens, cg):
    # <expression> ::= <term> (("+" | "-") <term>)*
    parse_term(tokens, cg)

    while tokens.peek()[1] in ["+", "-"]:
        operator = tokens.consume()[1]
        parse_term(tokens, cg)
        if operator == "+":
            cg.apply_binary_operation("add")
        else:
            cg.apply_binary_operation("sub")
    return


def parse_term(tokens, cg):
    # <term> ::= <factor> (("*" | "/") <factor>)*
    parse_factor(tokens, cg)
    while tokens.peek()[1] in ["*", "/"]:
        operator = tokens.consume()[1]
        parse_factor(tokens, cg)
        if operator == "*":
            cg.apply_binary_operation("imul")
        else:
            cg.division()
    return


def parse_factor(tokens, cg):
    # <factor> ::= <var> | <signed_number> | "(" <expression> ")"
    if tokens.peek()[1] == "(":
        tokens.consume("(")
        code = parse_expression(tokens, cg)
        tokens.consume(")")
        return code
    elif tokens.peek()[0] == "NUMBER":
        cg.load_value_to(val=tokens.consume()[1])
        return
    elif tokens.peek()[0] == "IDENTIFIER":
        cg.load_value_to(var=tokens.check_next_var()[1])
        return
    elif tokens.peek()[0] == "SIGNED_NUMBER":
        cg.load_value_to(val=tokens.consume()[1])
        return "mov eax, " + tokens.consume()[1] + " \npush eax \n"
    else:
        raise SyntaxError(
            "Error, expected number or identifier row: "
            + str(tokens.peek()[2])
            + " column: "
            + str(tokens.peek()[3])
        )


with open("code.txt", "r") as raw_code:
    code_string = raw_code.read()

print(tokenize(code_string))
tokens = TokenHelper(tokenize(code_string))
cg = CodeGenerator()
code = parser(tokens, cg)

with open("temp.asm", "w") as f:
    f.write(code)
subprocess.run(["nasm", "-f", "elf32", "-o", "temp.o", "temp.asm"])
# subprocess.run(["ld", "-m", "elf_i386", "-o", "temp", "temp.o"])
subprocess.run(["ld", "-m", "elf_i386", "-o", "program", "temp.o", "print_integer.o"])
subprocess.run(["./program"])
