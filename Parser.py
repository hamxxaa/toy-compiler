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

from parserNodes import (
    ProgramNode,
    DefinerNode,
    EqualizeNode,
    IfNode,
    WhileNode,
    PrintNode,
    ConditionNode,
    ExpressionNode,
    TermNode,
    FactorNode,
)


class TokenHelper:
    def __init__(self, tokens):
        self.tokens = tokens
        self.position = 0
        self.variables = []

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


class Parser:

    def __init__(self, tokens):
        self.tokens = TokenHelper(tokens)

    def parse_program(self):
        # <program> ::= <statement>+
        statements = []
        while self.tokens.peek():
            statements.append(self.parse_statement())
        return ProgramNode(statements)

    def parse_statement(self):
        # <statement> ::= <definer> | <equalize> | <if_structure> | <print> | <while_structure>
        token = self.tokens.peek()
        if token[1] == "var":
            return self.parse_definer()
        elif token[1] == "if":
            return self.parse_if_structure()
        elif token[1] == "while":
            return self.parse_while_structure()
        elif token[1] == "print":
            return self.parse_print()
        else:
            return self.parse_equalize()

    def parse_definer(self):
        # <definer>::= ( "var" <var> ";" ) | ( "var" <var> "=" <expression> ";" )
        self.tokens.consume("var", "KEYWORD")
        var_name = self.tokens.consume(expected_type="IDENTIFIER")[1]
        value = None
        if self.tokens.peek() and self.tokens.peek()[1] == "=":
            self.tokens.consume("=", "SYMBOL")
            value = self.parse_expression()
        self.tokens.consume(";", "SYMBOL")
        return DefinerNode(var_name, value)

    def parse_equalize(self):
        # <equalize>::= <var> "=" <expression> ";"
        var_name = self.tokens.consume(expected_type="IDENTIFIER")[1]
        self.tokens.consume("=", "SYMBOL")
        value = self.parse_expression()
        self.tokens.consume(";", "SYMBOL")
        return EqualizeNode(var_name, value)

    def parse_if_structure(self):
        # <if_structure> ::= "if" <condition> "do" "(" <statement>+ ")"
        self.tokens.consume("if", "KEYWORD")
        condition = self.parse_condition()
        self.tokens.consume("do", "KEYWORD")
        self.tokens.consume("(", "SYMBOL")
        statements = []
        while self.tokens.peek() and self.tokens.peek()[1] != ")":
            statements.append(self.parse_statement())
        self.tokens.consume(")", "SYMBOL")
        return IfNode(condition, statements)

    def parse_while_structure(self):
        # <while_structure> ::= "while" <condition> "do" "(" <statement>+ ")"
        self.tokens.consume("while", "KEYWORD")
        condition = self.parse_condition()
        self.tokens.consume("do", "KEYWORD")
        self.tokens.consume("(", "SYMBOL")
        statements = []
        while self.tokens.peek() and self.tokens.peek()[1] != ")":
            statements.append(self.parse_statement())
        self.tokens.consume(")", "SYMBOL")
        return WhileNode(condition, statements)

    def parse_print(self):
        # <print> ::= "print" "(" <var> ")" ";"
        self.tokens.consume("print", "KEYWORD")
        self.tokens.consume("(", "SYMBOL")
        var_name = self.tokens.consume(expected_type="IDENTIFIER")[1]
        self.tokens.consume(")", "SYMBOL")
        self.tokens.consume(";", "SYMBOL")
        return PrintNode(var_name)

    def parse_condition(self):
        # <condition> ::= <expression> <conditional_operator> <expression> | "(" <condition> ")" <logical_operator> "(" <condition> ")"
        if self.tokens.peek()[1] == "(":
            self.tokens.consume("(", "SYMBOL")
            node = self.parse_condition()
            self.tokens.consume(")", "SYMBOL")
            while self.tokens.peek() and self.tokens.peek()[1] in ("&", "|"):
                operator = self.tokens.consume(expected_type="LOGICAL_OPERATOR")[1]
                self.tokens.consume("(", "SYMBOL")
                right = self.parse_condition()
                self.tokens.consume(")", "SYMBOL")
                node = ConditionNode(node, operator, right)
            return node
        else:
            left = self.parse_expression()
            operator = self.tokens.consume(expected_type="CONDITIONAL_OPERATOR")[1]
            right = self.parse_expression()
            return ConditionNode(left, operator, right)

    def parse_expression(self):
        # <expression> ::= <term> (("+" | "-") <term>)*
        node = self.parse_term()
        while self.tokens.peek() and self.tokens.peek()[1] in ("+", "-"):
            operator = self.tokens.consume(expected_type="OPERATOR")[1]
            right = self.parse_term()
            node = ExpressionNode(node, operator, right)
        return node

    def parse_term(self):
        # <term> ::= <factor> (("*" | "/") <factor>)*
        node = self.parse_factor()
        while self.tokens.peek() and self.tokens.peek()[1] in ("*", "/"):
            operator = self.tokens.consume(expected_type="OPERATOR")[1]
            right = self.parse_factor()
            node = TermNode(node, operator, right)
        return node

    def parse_factor(self):
        # <factor> ::= <var> | <signed_number> | "(" <expression> ")"
        token = self.tokens.peek()
        if token[1] == "(":
            self.tokens.consume("(", "SYMBOL")
            node = self.parse_expression()
            self.tokens.consume(")", "SYMBOL")
            return ExpressionNode(node)
        elif token[0] == "IDENTIFIER":
            var_name = self.tokens.consume(expected_type="IDENTIFIER")[1]
            return FactorNode(var_name, is_variable=True)
        elif token[0] in ("NUMBER", "SIGNED_NUMBER"):
            number = self.tokens.consume(expected_type=token[0])[1]
            return FactorNode(number, is_variable=False)
        else:
            raise SyntaxError(
                f"Error, expected '(', 'IDENTIFIER', 'NUMBER' or 'SIGNED_NUMBER' but found '{token[1]}' at row {token[2]}, column {token[3]}"
            )

    def print_ast(self, node, indent=0):
        prefix = "  " * indent

        if isinstance(node, ProgramNode):
            print(f"{prefix}Program:")
            for stmt in node.statements:
                self.print_ast(stmt, indent + 1)

        elif isinstance(node, DefinerNode):
            print(f"{prefix}Definer: var {node.var_name}", end="")
            if node.value:
                print(" =")
                self.print_ast(node.value, indent + 1)
            else:
                print()

        elif isinstance(node, EqualizeNode):
            print(f"{prefix}Equalize: {node.var_name} =")
            self.print_ast(node.value, indent + 1)

        elif isinstance(node, IfNode):
            print(f"{prefix}If:")
            self.print_ast(node.condition, indent + 1)
            for stmt in node.statements:
                self.print_ast(stmt, indent + 1)

        elif isinstance(node, WhileNode):
            print(f"{prefix}While:")
            self.print_ast(node.condition, indent + 1)
            for stmt in node.statements:
                self.print_ast(stmt, indent + 1)

        elif isinstance(node, PrintNode):
            print(f"{prefix}Print: {node.var_name}")

        elif isinstance(node, ConditionNode):
            print(f"{prefix}Condition: {node.operator}")
            self.print_ast(node.left, indent + 1)
            self.print_ast(node.right, indent + 1)

        elif isinstance(node, ExpressionNode):
            print(f"{prefix}Expression: {node.operator}")
            self.print_ast(node.left, indent + 1)
            self.print_ast(node.right, indent + 1)

        elif isinstance(node, TermNode):
            print(f"{prefix}Term: {node.operator}")
            self.print_ast(node.left, indent + 1)
            self.print_ast(node.right, indent + 1)

        elif isinstance(node, FactorNode):
            if node.is_variable:
                print(f"{prefix}Var: {node.value}")
            else:
                print(f"{prefix}Num: {node.value}")
