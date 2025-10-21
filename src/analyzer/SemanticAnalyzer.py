class SymbolTable:
    def __init__(self):
        self.symbols = {}

    def define(self, name, type):
        if name in self.symbols:
            raise Exception(f"Semantic Error: Variable '{name}' already defined.")
        self.symbols[name] = type

    def lookup(self, name):
        return self.symbols.get(name, None)


class SemanticAnalyzer:
    def __init__(self):
        self.symbol_table = SymbolTable()

    def analyze(self, ast):
        self.visit(ast)

    def visit(self, node):
        method_name = f"visit_{type(node).__name__}"
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node):
        raise Exception(f"No visit_{type(node).__name__} method")

    def visit_ProgramNode(self, node):
        for statement in node.statements:
            self.visit(statement)

    def visit_DefinerNode(self, node):
        self.symbol_table.define(node.name, node.type)
        if node.value:
            value_type = self.visit(node.value)
            if value_type != node.type:
                raise Exception(
                    f"Type Error: Cannot assign value of type '{value_type}' to variable '{node.name}' of type '{node.type}'."
                )

    def visit_EqualizeNode(self, node):
        var_type = self.symbol_table.lookup(node.name)
        if var_type is None:
            raise Exception(f"Semantic Error: Variable '{node.name}' not defined.")
        value_type = self.visit(node.value)
        if value_type != var_type:
            raise Exception(
                f"Type Error: Cannot assign value of type '{value_type}' to variable '{node.name}' of type '{var_type}'."
            )

    def visit_ConditionNode(self, node):
        left_type = self.visit(node.left)
        right_type = self.visit(node.right)

        if node.operator in ("!=", "<", ">", "<=", ">="):
            if left_type != right_type and "bool" not in (left_type, right_type):
                raise Exception(
                    f"Type Error: Cannot compare values of type '{left_type}' and '{right_type}'."
                )
            node.type = "bool"
            return "bool"
        elif node.operator in ("&", "|"):
            if left_type != "bool" or right_type != "bool":
                raise Exception(
                    f"Type Error: Logical operations require boolean operands, got '{left_type}' and '{right_type}'."
                )
            node.type = "bool"
            return "bool"
        elif node.operator in ("=="):
            if left_type != right_type:
                raise Exception(
                    f"Type Error: Cannot compare values of type '{left_type}' and '{right_type}'."
                )
            node.type = "bool"
            return "bool"
        else:
            raise Exception(f"Unknown operator '{node.operator}' in condition.")

    def visit_ExpressionNode(self, node):
        left_type = self.visit(node.left)
        right_type = self.visit(node.right)

        if node.operator in ("+", "-"):
            if left_type == "int" and right_type == "int":
                node.type = "int"
                return "int"
            else:
                raise Exception(
                    f"Type Error: Cannot perform '{node.operator}' on types '{left_type}' and '{right_type}'."
                )
        else:
            raise Exception(f"Unknown operator '{node.operator}' in expression.")

    def visit_TermNode(self, node):
        left_type = self.visit(node.left)
        right_type = self.visit(node.right)

        if node.operator in ("*", "/"):
            if left_type == "int" and right_type == "int":
                node.type = "int"
                return "int"
            else:
                raise Exception(
                    f"Type Error: Cannot perform '{node.operator}' on types '{left_type}' and '{right_type}'."
                )
        else:
            raise Exception(f"Unknown operator '{node.operator}' in term.")

    def visit_FactorNode(self, node):
        if node.is_variable:
            var_type = self.symbol_table.lookup(node.value)
            if var_type is None:
                raise Exception(f"Semantic Error: Variable '{node.value}' not defined.")
            node.type = var_type
            return var_type
        else:
            # Handle constant values (stored as strings from tokens)
            if self._is_integer_literal(node.value):
                node.type = "int"
                return "int"
            elif self._is_boolean_literal(node.value):
                node.type = "bool"
                return "bool"
            else:
                raise Exception(
                    f"Type Error: Unknown literal type for value '{node.value}', expected integer or boolean literal."
                )

    def _is_integer_literal(self, value):
        """Check if the value is an integer literal (handles both positive and negative)"""
        if isinstance(value, str):
            # Handle signed numbers like "-123" and regular numbers like "123"
            if value.startswith("-"):
                return value[1:].isdigit() and len(value) > 1
            return value.isdigit()
        return isinstance(value, int)

    def _is_boolean_literal(self, value):
        """Check if the value is a boolean literal"""
        if isinstance(value, str):
            return value.lower() in ("true", "false")
        return isinstance(value, bool)

    def visit_PrintNode(self, node):
        var_type = self.symbol_table.lookup(node.var.value)
        node.var.type = var_type
        if var_type is None:
            raise Exception(f"Semantic Error: Variable '{node.var.value}' not defined.")
        return var_type

    def visit_IfNode(self, node):
        condition_type = self.visit(node.condition)
        if condition_type != "bool":
            raise Exception(
                f"Type Error: If condition must be of type 'bool', got '{condition_type}'."
            )
        for statement in node.statements:
            self.visit(statement)

    def visit_WhileNode(self, node):
        condition_type = self.visit(node.condition)
        if condition_type != "bool":
            raise Exception(
                f"Type Error: While condition must be of type 'bool', got '{condition_type}'."
            )
        for statement in node.statements:
            self.visit(statement)
