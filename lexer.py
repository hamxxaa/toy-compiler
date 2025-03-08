# L={
# <program> ::= <statement>+
# <statement> ::= <definer> | <equalize> | <if_structure> | <print>
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


class TokenHelper:
    def __init__(self, tokens):
        self.tokens = tokens
        self.position = 0

    def peek(self):
        if self.position < len(self.tokens):
            return self.tokens[self.position]
        return None

    def consume(self, expected_value=None, expected_type=None):
        if self.position >= len(self.tokens):
            raise SyntaxError(f"Error, expected '{expected_value}' but found none")
        token = self.tokens[self.position]
        if expected_value and token[1] != expected_value:
            raise SyntaxError(
                f"Error, expected '{expected_value}' but found '{token[1]}' at row {token[2]}, column {token[3]}"
            )
        if expected_type and token[0] != expected_type:
            raise SyntaxError(
                f"Error, expected {expected_type} but found {token[0]} at row {token[2]}, column {token[3]}"
            )
        self.position += 1
        return token

    def consume_in(self, valid_values, expected_type=None):
        if self.position >= len(self.tokens):
            raise SyntaxError(f"Error, expected one of {valid_values} but found none")
        token = self.tokens[self.position]
        if token[1] not in valid_values:
            raise SyntaxError(
                f"Error, expected one of {valid_values} but found '{token[1]}' at row {token[2]}, column {token[3]}"
            )
        if expected_type and token[0] != expected_type:
            raise SyntaxError(
                f"Error, expected {expected_type} but found {token[0]} at row {token[2]}, column {token[3]}"
            )
        self.position += 1
        return token

    def check_without_consuming(self, expected_value=None, expected_type=None):
        if self.position >= len(self.tokens):
            raise SyntaxError(f"Error, expected '{expected_value}' but found none")
        token = self.tokens[self.position]
        if expected_value and token[1] != expected_value:
            raise SyntaxError(
                f"Error, expected '{expected_value}' but found '{token[1]}' at row {token[2]}, column {token[3]}"
            )
        if expected_type and token[0] != expected_type:
            raise SyntaxError(
                f"Error, expected {expected_type} but found {token[0]} at row {token[2]}, column {token[3]}"
            )
        return token

    def check_in_without_consuming(self, valid_values, expected_type=None):
        if self.position >= len(self.tokens):
            raise SyntaxError(f"Error, expected one of {valid_values} but found none")
        token = self.tokens[self.position]
        if token[1] not in valid_values:
            raise SyntaxError(
                f"Error, expected one of {valid_values} but found '{token[1]}' at row {token[2]}, column {token[3]}"
            )
        if expected_type and token[0] != expected_type:
            raise SyntaxError(
                f"Error, expected {expected_type} but found {token[0]} at row {token[2]}, column {token[3]}"
            )
        return token


keywords = ["print", "var", ";", "(", ")", "=", "if", "#"]
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


def parser(tokens):
    program = []
    while tokens.peek():
        program.append(parse_statement(tokens))

    code = "section .data \n"
    code += "msg db 'code executed successfully', 0xA \n"
    code += "msglen equ $ - msg \n"
    for statement in program:
        code += statement[0]

    code += "section .bss \nextern num \n"

    code += "section .text \n"
    code += "global _start \n"

    code += "_start: \n"

    for statement in program:
        code += statement[1]

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


def parse_statement(tokens):
    # <statement> ::= <definer> | <equalize> | <if_structure> | <print>
    if tokens.peek()[1] == "var":
        return (parse_definer(tokens), "")
    elif tokens.peek()[1] == "print":
        return ("", parse_printer(tokens))
    elif tokens.peek()[1] == "if":
        return ("", parse_if_structure(tokens))
    else:
        return ("", parse_equalizer(tokens))


def parse_if_structure(tokens):
    # <if_structure> ::= "if" <condition> "#" "(" <statement>+ ")" ";"
    tokens.consume("if")
    code = parse_condition(tokens)
    tokens.consume("#")
    unique_label = "label" + str(hash(str(tokens.peek()))).replace("-", "")
    code += "pop eax \ntest eax, eax \njz " + unique_label + " \n"
    tokens.consume("(")
    while tokens.peek()[1] != ")":
        code += parse_statement(tokens)[1]
    tokens.consume(")")
    code += "" + unique_label + ": \n"
    return code


def parse_condition(tokens):
    # <condition> ::= <expression> <conditional_operator> <expression> | "(" <condition> ")" <logical_operator> "(" <condition> ")"
    def logic(tokens):
        code = parse_expression(tokens)
        operator = tokens.consume_in(conditional_operators)[1]
        code += parse_expression(tokens)
        code += "pop ebx \npop eax \ncmp eax,ebx \n"
        if operator == "<":
            code += "setl al \n"
        elif operator == ">":
            code += "setg al \n"
        elif operator == "==":
            code += "sete al \n"
        elif operator == "<=":
            code += "setle al \n"
        elif operator == ">=":
            code += "setge al \n"
        elif operator == "!=":
            code += "setne al \n"
        code += "movzx eax, al \npush eax \n"
        return code

    if tokens.peek()[1] == "(":
        tokens.consume("(")
        code = logic(tokens)
        tokens.consume(")")
        tokens.check_in_without_consuming(logical_operators + ["#"])
        while tokens.peek()[1] in logical_operators:
            operator = tokens.consume()[1]
            tokens.consume("(")
            code += logic(tokens)
            tokens.consume(")")
            code += "pop ebx \npop eax \n"
            if operator == "&":
                code += "and eax, ebx \n"
            elif operator == "|":
                code += "or eax, ebx \n"
            code += "push eax \n"
        return code
    else:
        return logic(tokens)

    # code = parse_expression(tokens)
    # if tokens[0][1] not in conditional_operators:
    #     raise SyntaxError("Error, expected a conditional operator "row: "
    #         + str(tokens[0][2])
    #         + " column: "
    #         + str(tokens[0][3]))
    # # operator = tokens.pop(0)[1]
    # # code += parse_expression(tokens)
    # # code += "pop eax \npop ebx \ncmp eax,ebx \n"
    # if operator == "<":
    #     code += "jge fail \n"
    # elif operator == ">":
    #     code += "jle fail \n"
    # elif operator == "==":
    #     code += "jne fail \n"
    # elif operator == "<=":
    #     code += "jg fail \n"
    # elif operator == ">=":
    #     code += "jl fail \n"
    # elif operator == "!=":
    #     code += "je fail\n"
    # return code


def parse_printer(tokens):
    # <print> ::= "print" "(" <var> ")" ";"
    tokens.consume("print")
    tokens.consume("(")
    name = tokens.consume(expected_type="IDENTIFIER")[1]
    tokens.consume(")")
    tokens.consume(";")
    return (
        "mov eax, dword ["
        + name
        + "] \nmov dword [num], eax \ncall print_integer \nmov eax, 4 \nmov ebx, 1 \nmov ecx, newline \nmov edx, 1 \nint 0x80\n"
    )


def parse_definer(tokens):
    # <definer>::= "var" <var> ";"
    global variables

    tokens.consume("var")
    name = tokens.consume(expected_type="IDENTIFIER")[1]
    variables.append(name)
    tokens.consume(";")
    return "" + name + " dd 0 \n"


def parse_equalizer(tokens):
    # <equalize>::= <var> "=" <expression> ";"
    global variables

    name = tokens.consume(expected_type="IDENTIFIER")[1]
    if name not in variables:
        raise SyntaxError(
            "Error, variable "
            + name
            + " not defined row: "
            + str(tokens.peek()[2])
            + " column: "
            + str(tokens.peek()[3])
        )
    tokens.consume("=")
    code = parse_expression(tokens)
    tokens.consume(";")
    return code + "pop eax \nmov [" + name + "], eax \n"


def parse_expression(tokens):
    # <expression> ::= <term> (("+" | "-") <term>)*
    code = parse_term(tokens)

    while tokens.peek()[1] in ["+", "-"]:
        operator = tokens.consume()[1]
        term_code = parse_term(tokens)
        code += term_code
        code += "pop eax \npop ebx\n"
        if operator == "+":
            code += "add eax, ebx \n"
        else:
            code += "sub eax, ebx \n"
        code += "push eax\n"
    return code


def parse_term(tokens):
    # <term> ::= <factor> (("*" | "/") <factor>)*
    code = parse_factor(tokens)
    while tokens.peek()[1] in ["*", "/"]:
        operator = tokens.consume()[1]
        factor_code = parse_factor(tokens)
        code += factor_code
        if operator == "*":
            code += "pop eax \npop ebx\n"
            code += "imul eax, ebx \n"
        else:
            code += "pop ebx \npop eax\n"
            code += "cdq \nidiv ebx \n"
        code += "push eax\n"
    return code


def parse_factor(tokens):
    # <factor> ::= <var> | <signed_number> | "(" <expression> ")"
    if tokens.peek()[1] == "(":
        tokens.consume("(")
        code = parse_expression(tokens)
        tokens.consume(")")
        return code
    elif tokens.peek()[0] == "NUMBER":
        return "mov eax, " + tokens.consume()[1] + " \npush eax \n"
    elif tokens.peek()[0] == "IDENTIFIER":
        return "mov eax, [" + tokens.consume()[1] + "] \npush eax \n"
    elif tokens.peek()[0] == "SIGNED_NUMBER":
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
code = parser(tokens)

with open("temp.asm", "w") as f:
    f.write(code)
subprocess.run(["nasm", "-f", "elf32", "-o", "temp.o", "temp.asm"])
# subprocess.run(["ld", "-m", "elf_i386", "-o", "temp", "temp.o"])
subprocess.run(["ld", "-m", "elf_i386", "-o", "program", "temp.o", "print_integer.o"])
subprocess.run(["./program"])
