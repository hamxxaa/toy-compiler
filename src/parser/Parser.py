# L={
# <program> ::= (<declaration>)+
# <declaration> ::= <definer> | <function_def>
# <function_def> ::= <type> <var> "(" <param_list>? ")" <scope>
# <param_list> ::= <param> ("," <param>)*
# <param> ::= <type> <var>
# <function_call> ::= <var> "(" <arg_list>? ")"
# <arg_list> ::= <expression> ("," <expression>)*
# <scope> ::= "{" <statement>+ "}"
# <statement> ::= <definer> | <equalize> | <if_structure> | <print> | <while_structure> | <scope> | <return_statement> | <function_call_stmt>
# <function_call_stmt> ::= <function_call> ";"
# <return_statement> ::= "return" <expression> ";"
# <while_structure> ::= "while" <condition> "do" <scope>
# <print> ::= "print" "(" <expression> ")" ";"
# <if_structure> ::= "if" <condition> "do" <scope>
# <condition> ::= <expression> | <expression> <conditional_operator> <expression> | "(" <condition> ")" <logical_operator> "(" <condition> ")"
# <definer>::= ( "var" <type> <var> ";" ) | ( "var" <type> <var> "=" <expression> ";" )
# <var>::= <letter>+
# <number>::= <digit>+
# <signed_number>::? <number>|"-" <number>
# <expression> ::= <term> (("+" | "-") <term>)*
# <term> ::= <factor> (("*" | "/") <factor>)*
# <factor> ::= <var> | <signed_number> | <boolean> | "(" <expression> ")" | <function_call>
# <operator>::= "+" | "-" | "*" | "/"
# <conditional_operator>::= "<" | ">" | "==" | "<=" | ">=" | "!="
# <logical_operator>::= "&" | "|"
# <digit>::= 1|2|3|4|5|6|7|8|9|0
# <letter>::= a|b|c....z|A|B|C....Z
# <type>::= "int" | "bool"
# <equalize>::= <var> "=" <expression> ";"
# }

from .parserNodes import (
    ProgramNode,
    FunctionDefNode,
    FunctionCallNode,
    ReturnNode,
    ScopeNode,
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

conditional_operators = {"<", ">", "==", "<=", ">=", "!="}
logical_operators = {"&", "|"}


class TokenHelper:
    def __init__(self, tokens):
        self.tokens = tokens
        self.position = 0

    def peek(self, offset=0):
        pos = self.position + offset
        if pos < len(self.tokens):
            return self.tokens[pos]
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
        # <program> ::= (<function_def>)+
        declarations = []
        while self.tokens.peek():
            declarations.append(self.parse_declaration())
        print(declarations)
        return ProgramNode(declarations)

    def parse_declaration(self):
        # <declaration> ::= <definer> | <function_def>
        if self.tokens.peek() and self.tokens.peek()[1] == "var":
            return self.parse_definer()
        else:
            print("Parsing function definition")
            return self.parse_function_def()
        
    def parse_function_def(self):
        # <function_def> ::= <type> <var> "(" <param_list>? ")" <scope>
        return_type = self.tokens.consume(expected_type="TYPE")
        func_name = self.tokens.consume(expected_type="IDENTIFIER")[1]
        self.tokens.consume("(", "SYMBOL")
        param_list = self.parse_param_list()
        self.tokens.consume(")", "SYMBOL")
        body = self.parse_scope()
        return FunctionDefNode(return_type, func_name, param_list, body)

    def parse_param_list(self):
        # <param_list> ::= <param> ("," <param>)*
        params = []
        if self.tokens.peek() and self.tokens.peek()[1] != ")":
            params.append(self.parse_param())
            while self.tokens.peek() and self.tokens.peek()[1] == ",":
                self.tokens.consume(",", "SYMBOL")
                params.append(self.parse_param())
        return params

    def parse_param(self):
        # <param> ::= <type> <var>
        param_type = self.tokens.consume(expected_type="TYPE")[1]
        param_name = self.tokens.consume(expected_type="IDENTIFIER")[1]
        return FactorNode(param_name, True, param_type)

    def parse_function_call(self):
        # <function_call> ::= <var> "(" <arg_list>? ")"
        func_name = self.tokens.consume(expected_type="IDENTIFIER")[1]
        self.tokens.consume("(", "SYMBOL")
        arg_list = self.parse_arg_list()
        self.tokens.consume(")", "SYMBOL")
        return FunctionCallNode(func_name, arg_list)

    def parse_arg_list(self):
        # <arg_list> ::= <expression> ("," <expression>)*
        args = []
        if self.tokens.peek() and self.tokens.peek()[1] != ")":
            args.append(self.parse_expression())
            while self.tokens.peek() and self.tokens.peek()[1] == ",":
                self.tokens.consume(",", "SYMBOL")
                args.append(self.parse_expression())
        return args

    def parse_function_call_stmt(self):
        # <function_call_stmt> ::= <function_call> ";"
        func_call = self.parse_function_call()
        self.tokens.consume(";", "SYMBOL")
        return func_call

    def parse_return_statement(self):
        # <return_statement> ::= "return" <expression> ";"
        self.tokens.consume("return", "KEYWORD")
        expr = self.parse_expression()
        self.tokens.consume(";", "SYMBOL")
        return ReturnNode(expr)

    def parse_scope(self):
        # <scope> ::= "{" <statement>+ "}"
        self.tokens.consume("{", "SYMBOL")
        statements = []
        while self.tokens.peek() and self.tokens.peek()[1] != "}":
            statements.append(self.parse_statement())
        self.tokens.consume("}", "SYMBOL")
        return ScopeNode(statements)

    def parse_statement(self):
        # <statement> ::= <definer> | <equalize> | <if_structure> | <print> | <while_structure> | <scope> | <return_statement> | <function_call_stmt>
        token = self.tokens.peek()
        if token[1] == "var":
            return self.parse_definer()
        elif token[1] == "if":
            return self.parse_if_structure()
        elif token[1] == "while":
            return self.parse_while_structure()
        elif token[1] == "print":
            return self.parse_print()
        elif token[1] == "{":
            return self.parse_scope()
        elif token[1] == "return":
            return self.parse_return_statement()
        elif (
            token[0] == "IDENTIFIER"
            and self.tokens.peek(1)
            and self.tokens.peek(1)[1] == "("
        ):
            return self.parse_function_call_stmt()
        else:
            return self.parse_equalize()

    def parse_definer(self):
        # <definer>::= ( "var" <type> <var> ";" ) | ( "var" <type> <var> "=" <expression> ";" )
        self.tokens.consume("var", "KEYWORD")
        var_type = self.tokens.consume(expected_type="TYPE")[1]
        var_name = self.tokens.consume(expected_type="IDENTIFIER")[1]
        value = None
        if self.tokens.peek() and self.tokens.peek()[1] == "=":
            self.tokens.consume("=", "SYMBOL")
            value = self.parse_expression()
        self.tokens.consume(";", "SYMBOL")
        return DefinerNode(var_name, value, var_type)

    def parse_equalize(self):
        # <equalize>::= <var> "=" <expression> ";"
        var_name = self.tokens.consume(expected_type="IDENTIFIER")[1]
        self.tokens.consume("=", "SYMBOL")
        value = self.parse_expression()
        self.tokens.consume(";", "SYMBOL")
        return EqualizeNode(var_name, value)

    def parse_if_structure(self):
        # <if_structure> ::= "if" <condition> "do" <scope>
        self.tokens.consume("if", "KEYWORD")
        condition = self.parse_condition()
        self.tokens.consume("do", "KEYWORD")
        scope = self.parse_scope()
        return IfNode(condition, scope)

    def parse_while_structure(self):
        # <while_structure> ::= "while" <condition> "do" <scope>
        self.tokens.consume("while", "KEYWORD")
        condition = self.parse_condition()
        self.tokens.consume("do", "KEYWORD")
        scope = self.parse_scope()
        return WhileNode(condition, scope)

    def parse_print(self):
        # <print> ::= "print" "(" <expression> ")" ";"
        self.tokens.consume("print", "KEYWORD")
        self.tokens.consume("(", "SYMBOL")
        expression = self.parse_expression()
        self.tokens.consume(")", "SYMBOL")
        self.tokens.consume(";", "SYMBOL")
        return PrintNode(expression)

    def parse_condition(self):
        # <condition> ::= <expression> | <expression> <conditional_operator> <expression> | "(" <condition> ")" <logical_operator> "(" <condition> ")"
        if self.tokens.peek()[1] == "(":
            self.tokens.consume("(", "SYMBOL")
            node = self.parse_condition()
            self.tokens.consume(")", "SYMBOL")
            while self.tokens.peek() and self.tokens.peek()[1] in logical_operators:
                operator = self.tokens.consume(expected_type="LOGICAL_OPERATOR")[1]
                self.tokens.consume("(", "SYMBOL")
                right = self.parse_condition()
                self.tokens.consume(")", "SYMBOL")
                node = ConditionNode(node, operator, right)
            return node
        else:
            left = self.parse_expression()
            if (
                not self.tokens.peek()
                or self.tokens.peek()[1] not in conditional_operators
            ):
                return left
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
        # <factor> ::= <var> | <signed_number> | <boolean> | "(" <expression> ")" | <function_call>
        token = self.tokens.peek()
        if token[1] == "(":
            self.tokens.consume("(", "SYMBOL")
            node = self.parse_expression()
            self.tokens.consume(")", "SYMBOL")
            return node
        elif (
            token[0] == "IDENTIFIER"
            and self.tokens.peek()
            and self.tokens.peek(1)[1] == "("
        ):
            return self.parse_function_call()
        elif token[0] == "IDENTIFIER":
            var_name = self.tokens.consume(expected_type="IDENTIFIER")[1]
            return FactorNode(var_name, is_variable=True)
        elif token[0] in ("NUMBER", "SIGNED_NUMBER"):
            number = self.tokens.consume(expected_type=token[0])[1]
            return FactorNode(number, is_variable=False)
        elif token[0] == "BOOLEAN":
            boolean = self.tokens.consume(expected_type="BOOLEAN")[1]
            return FactorNode(boolean, is_variable=False)

        else:
            raise SyntaxError(
                f"Error, expected '(', 'IDENTIFIER', 'NUMBER', 'SIGNED_NUMBER', or 'BOOLEAN' but found '{token[1]}' at row {token[2]}, column {token[3]}"
            )

    def print_ast(self, node, indent=0):
        prefix = "  " * indent

        if isinstance(node, ProgramNode):
            print(f"{prefix}Program:")
            for decl in node.declarations:
                self.print_ast(decl, indent + 1)

        elif isinstance(node, FunctionDefNode):
            ret_type = node.return_type if isinstance(node.return_type, str) else node.return_type[1] if node.return_type else None
            print(f"{prefix}FunctionDef: {ret_type} {node.name}(")
            for i, param in enumerate(node.params):
                print(f"{prefix}  Param {i}: {param.type} {param.value}")
            print(f"{prefix}) Body:")
            self.print_ast(node.body, indent + 1)

        elif isinstance(node, FunctionCallNode):
            print(f"{prefix}FunctionCall: {node.name}(")
            for i, arg in enumerate(node.args):
                print(f"{prefix}  Arg {i}:")
                self.print_ast(arg, indent + 2)
            print(f"{prefix})")

        elif isinstance(node, ReturnNode):
            print(f"{prefix}Return:")
            self.print_ast(node.expression, indent + 1)

        elif isinstance(node, ScopeNode):
            print(f"{prefix}Scope:")
            for stmt in node.statements:
                self.print_ast(stmt, indent + 1)

        elif isinstance(node, DefinerNode):
            print(f"{prefix}Definer: var {node.name}", end="")
            if node.value:
                print(" =")
                self.print_ast(node.value, indent + 1)
            else:
                print()

        elif isinstance(node, EqualizeNode):
            print(f"{prefix}Equalize: {node.name} =")
            self.print_ast(node.value, indent + 1)

        elif isinstance(node, IfNode):
            print(f"{prefix}If:")
            self.print_ast(node.condition, indent + 1)
            self.print_ast(node.scope, indent + 1)

        elif isinstance(node, WhileNode):
            print(f"{prefix}While:")
            self.print_ast(node.condition, indent + 1)
            self.print_ast(node.scope, indent + 1)

        elif isinstance(node, PrintNode):
            print(f"{prefix}Print:")
            self.print_ast(node.expression, indent + 1)

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
