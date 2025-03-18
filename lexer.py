# L={
# <program> ::= <statement>+
# <statement> ::= <definer> | <equalize> | <if_structure> | <print> | <while_structure>
# <while_structure> ::= "while" <condition> "#" "(" <statement>+ ")" ";"
# <print> ::= "print" "(" <var> ")" ";"
# <if_structure> ::= "if" <condition> "#" "(" <statement>+ ")" ";"
# <condition> ::= <expression> <conditional_operator> <expression> | "(" <condition> ")" <logical_operator> "(" <condition> ")"
# <definer>::= "var" <var> ";"
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


keywords = ["while", "print", "var", ";", "(", ")", "=", "if", "#"]
operators = ["+", "-", "*", "/"]
logical_operators = ["&", "|"]
conditional_operators = ["<", ">", "==", "<=", ">=", "!="]


def tokenize(input_str):
    tokens = []
    i = 0
    row = 1
    col = 1
    while i < len(input_str):
        if input_str[i].isspace():
            if input_str[i] == "\n":
                row += 1
                col = 1
            i += 1
            col += 1
        elif input_str[i].isalpha() or input_str[i] in keywords:
            lexeme = ""
            while i < len(input_str) and not input_str[i].isspace():
                lexeme += input_str[i]
                i += 1
                col += 1
            if lexeme in keywords:
                tokens.append(("KEYWORD", lexeme, row, col - len(lexeme)))
            else:
                tokens.append(("IDENTIFIER", lexeme, row, col - len(lexeme)))
        elif input_str[i].isdigit():
            lexeme = ""
            while i < len(input_str) and input_str[i].isdigit():
                lexeme += input_str[i]
                i += 1
                col += 1
            tokens.append(("NUMBER", lexeme, row, col - len(lexeme)))
        elif (
            input_str[i] in operators
            or input_str[i] in logical_operators
            or input_str[i] in conditional_operators
        ):
            lexeme = input_str[i]
            i += 1
            col += 1
            if lexeme == "-" and input_str[i].isdigit():
                while i < len(input_str) and input_str[i].isdigit():
                    lexeme += input_str[i]
                    i += 1
                    col += 1
                tokens.append(("SIGNED_NUMBER", lexeme, row, col - len(lexeme)))
            else:
                if lexeme == "=" and input_str[i] == "=":
                    lexeme = "=="
                if lexeme == "<" and input_str[i] == "=":
                    lexeme = "<="
                if lexeme == ">" and input_str[i] == "=":
                    lexeme = ">="
                i += 1
                col += 1
                tokens.append(("OPERATOR", lexeme, row, col - len(lexeme)))
        else:
            raise SyntaxError(
                "Invalid character found: "
                + input_str[i]
                + " row: "
                + str(row)
                + " column: "
                + str(col)
            )
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
    # <while_structure> ::= "while" <condition> "#" "(" <statement>+ ")" ";"
    tokens.consume("while")
    testlabel = cg.create_unique_label()
    label = cg.create_unique_label()
    cg.start_label(testlabel)
    parse_condition(tokens, cg)
    tokens.consume("#")
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
    # <if_structure> ::= "if" <condition> "#" "(" <statement>+ ")" ";"
    tokens.consume("if")
    parse_condition(tokens, cg)
    tokens.consume("#")
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
        tokens.check_in_without_consuming(logical_operators + ["#"])
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
    # <definer>::= "var" <var> ";"
    tokens.consume("var")
    name = tokens.consume()[1]
    tokens.variables.append(name)
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

# print(tokenize(code_string))
tokens = TokenHelper(tokenize(code_string))
cg = CodeGenerator()
code = parser(tokens, cg)

with open("temp.asm", "w") as f:
    f.write(code)
subprocess.run(["nasm", "-f", "elf32", "-o", "temp.o", "temp.asm"])
# subprocess.run(["ld", "-m", "elf_i386", "-o", "temp", "temp.o"])
subprocess.run(["ld", "-m", "elf_i386", "-o", "program", "temp.o", "print_integer.o"])
subprocess.run(["./program"])
