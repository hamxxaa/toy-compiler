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

keywords = ["print", "var", ";", "(", ")", "=", "if", "#"]
operators = ["+", "-", "*", "/"]
logical_operators = ["&", "|"]
conditional_operators = ["<", ">", "==", "<=", ">=", "!="]


def tokenize(input_str):
    tokens = []
    i = 0
    while i < len(input_str):
        if input_str[i].isspace():
            i += 1
        elif input_str[i].isalpha() or input_str[i] in keywords:
            lexeme = ""
            while i < len(input_str) and not input_str[i].isspace():
                lexeme += input_str[i]
                i += 1
            if lexeme in keywords:
                tokens.append(("KEYWORD", lexeme))
            else:
                tokens.append(("IDENTIFIER", lexeme))
        elif input_str[i].isdigit():
            lexeme = ""
            while i < len(input_str) and input_str[i].isdigit():
                lexeme += input_str[i]
                i += 1
            tokens.append(("NUMBER", lexeme))
        elif input_str[i] in operators:
            lexeme = input_str[i]
            i += 1
            if lexeme == "-" and input_str[i].isdigit():
                while i < len(input_str) and input_str[i].isdigit():
                    lexeme += input_str[i]
                    i += 1
                tokens.append(("SIGNED_NUMBER", lexeme))
            else:
                tokens.append(("OPERATOR", lexeme))
        else:
            raise SyntaxError("Invalid character found: " + input_str[i])
    return tokens


variables = []


def parser(tokens):
    program = []
    while tokens:
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
    # <statement> ::= <definer> | <equalize> | <if_structure>
    if tokens[0][1] == "var":
        return (parse_definer(tokens), "")
    elif tokens[0][1] == "print":
        return ("", parse_printer(tokens))
    # elif tokens[0][1] == "if":
    #   return ("", parse_if_structure(tokens))
    else:
        return ("", parse_equalizer(tokens))


# def parse_if_structure(tokens):
#     if tokens.pop(0)[1] != "if":
#         raise SyntaxError("Error, expected 'if' ")
#     code = parse_condition(tokens)

# def parse_condition(tokens):
#     code = ""
#     if tokens[0][1] == "(":
#         tokens.pop(0)
#         code += parse_condition(tokens)

#     elif tokens[0][1] == ")":
#         tokens.pop(0)
#         if tokens.pop(0)[1] not in logical_operators:
#             raise SyntaxError("Error, expected a logical operator ")

#     code += parse_expression(tokens)
#     if tokens.pop(0)[1] !=


def parse_printer(tokens):
    # <print> ::= "print" "(" <var> ")" ";"
    if tokens.pop(0)[1] != "print":
        raise SyntaxError("Error, expected 'print' ")
    if tokens.pop(0)[1] != "(":
        raise SyntaxError("Error, expected '(' ")
    if tokens[0][0] != "IDENTIFIER":
        raise SyntaxError("Error, expected identifier ")
    name = tokens.pop(0)[1]
    if tokens.pop(0)[1] != ")":
        raise SyntaxError("Error, expected ')' ")
    if tokens.pop(0)[1] != ";":
        raise SyntaxError("Error, expected ';' printer ")
    return (
        "mov eax, dword ["
        + name
        + "] \nmov dword [num], eax \ncall print_integer \nmov eax, 4 \nmov ebx, 1 \nmov ecx, newline \nmov edx, 1 \nint 0x80\n"
    )


def parse_definer(tokens):
    # <definer>::= "var" <var> ";"
    global variables

    if tokens.pop(0)[1] != "var":
        raise SyntaxError("Error, expected 'var' ")
    if tokens[0][0] != "IDENTIFIER":
        raise SyntaxError("Error, expected identifier ")
    name = tokens.pop(0)[1]
    variables.append(name)
    if tokens.pop(0)[1] != ";":
        raise SyntaxError("Error, expected ';' definer ")
    return "" + name + " dd 0 \n"


def parse_equalizer(tokens):
    # <equalize>::= <var> "=" <expression> ";"
    global variables

    if tokens[0][0] != "IDENTIFIER":
        raise SyntaxError("Error, expected identifier ")
    name = tokens.pop(0)[1]
    if name not in variables:
        raise SyntaxError("Error, variable " + name + " not defined")
    if tokens.pop(0)[1] != "=":
        raise SyntaxError("Error, expected '=' ")
    code = parse_expression(tokens)
    if tokens.pop(0)[1] != ";":
        raise SyntaxError("Error, expected ';' equalizer ")
    return code + "pop eax \nmov [" + name + "], eax \n"


def parse_expression(tokens):
    # <expression> ::= <term> (("+" | "-") <term>)*
    code = parse_term(tokens)
    while tokens and tokens[0][1] in ["+", "-"]:
        operator = tokens.pop(0)[1]
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
    while tokens and tokens[0][1] in ["*", "/"]:
        operator = tokens.pop(0)[1]
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
    if tokens[0][1] == "(":
        tokens.pop(0)
        code = parse_expression(tokens)
        if tokens.pop(0)[1] != ")":
            raise SyntaxError("Error, expected ')' ")
        return code
    elif tokens[0][0] == "NUMBER":
        return "mov eax, " + tokens.pop(0)[1] + " \npush eax \n"
    elif tokens[0][0] == "IDENTIFIER":
        return "mov eax, [" + tokens.pop(0)[1] + "] \npush eax \n"
    elif tokens[0][0] == "SIGNED_NUMBER":
        return "mov eax, " + tokens.pop(0)[1] + " \npush eax \n"
    else:
        raise SyntaxError("Error, expected number or identifier")


with open("code.txt", "r") as raw_code:
    code_string = raw_code.read()

code = parser(tokenize(code_string))
# parser(tokenize(" var z ; z = ( -5 * 1 ) ; var a ; a = z + 3 ; var b ; b = 10 ; print ( a ) ; print ( z ) ; print ( b ) ; "))


with open("temp.asm", "w") as f:
    f.write(code)
subprocess.run(["nasm", "-f", "elf32", "-o", "temp.o", "temp.asm"])
# subprocess.run(["ld", "-m", "elf_i386", "-o", "temp", "temp.o"])
subprocess.run(["ld", "-m", "elf_i386", "-o", "program", "temp.o", "print_integer.o"])
subprocess.run(["./program"])
