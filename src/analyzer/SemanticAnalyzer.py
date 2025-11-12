class SymbolTable:
    _scope_counter = 0 
    
    def __init__(self, parent=None):
        self.symbols = {}
        self.parent = parent
        self.storage = "global" if parent is None else "local"
        self.scope_id = SymbolTable._scope_counter
        SymbolTable._scope_counter += 1

    def define(self, name, type):
        if name in self.symbols:
            raise Exception(f"Semantic Error: Variable '{name}' already defined.")
        self.symbols[name] = type

    def lookup(self, name):
        symbol = self.symbols.get(name)
        if symbol:
            return symbol, self.storage, self.scope_id
        if self.parent:
            return self.parent.lookup(name)
        return None, None, None


class SemanticAnalyzer:
    def __init__(self):
        self.current_scope = None

    def analyze(self, ast):
        self.visit(ast)

    def visit(self, node):
        method_name = f"visit_{type(node).__name__}"
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node):
        raise Exception(f"No visit_{type(node).__name__} method")

    def visit_ProgramNode(self, node):
        self.visit(node.scope)

    def visit_ScopeNode(self, node):
        parent_scope = self.current_scope
        self.current_scope = SymbolTable(parent=parent_scope)
        for statement in node.statements:
            self.visit(statement)
        self.current_scope = parent_scope

    def visit_DefinerNode(self, node):
        self.current_scope.define(node.name, node.type)
        node.storage = self.current_scope.storage
        node.scope_id = self.current_scope.scope_id
        if node.value:
            value_type = self.visit(node.value)
            if value_type != node.type:
                raise Exception(
                    f"Type Error: Cannot assign value of type '{value_type}' to variable '{node.name}' of type '{node.type}'."
                )

    def visit_EqualizeNode(self, node):
        var_type, storage, scope_id = self.current_scope.lookup(node.name)
        node.storage = storage
        node.scope_id = scope_id
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
            if left_type != right_type or "bool" in (left_type, right_type):
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
            var_type, storage, scope_id = self.current_scope.lookup(node.value)
            if var_type is None:
                raise Exception(f"Semantic Error: Variable '{node.value}' not defined.")
            node.type = var_type
            node.storage = storage
            node.scope_id = scope_id
            return var_type
        else:
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
        if isinstance(value, str):
            if value.startswith("-"):
                return value[1:].isdigit() and len(value) > 1
            return value.isdigit()
        return isinstance(value, int)

    def _is_boolean_literal(self, value):
        if isinstance(value, str):
            return value.lower() in ("true", "false")
        return isinstance(value, bool)

    def visit_PrintNode(self, node):
        expression_type = self.visit(node.expression)
        node.expression.type = expression_type
        return expression_type

    def visit_IfNode(self, node):
        condition_type = self.visit(node.condition)
        if condition_type != "bool":
            raise Exception(
                f"Type Error: If condition must be of type 'bool', got '{condition_type}'."
            )
        self.visit(node.scope)

    def visit_WhileNode(self, node):
        condition_type = self.visit(node.condition)
        if condition_type != "bool":
            raise Exception(
                f"Type Error: While condition must be of type 'bool', got '{condition_type}'."
            )
        self.visit(node.scope)
