from src.parser.parserNodes import FunctionDefNode


class Symbol:
    def __init__(self, name, symbol_type, **kwargs):
        self.name = name
        self.symbol_type = symbol_type

        # For variables
        self.var_type = kwargs.get("var_type")
        self.storage = kwargs.get("storage")
        self.scope_id = kwargs.get("scope_id")

        # For functions
        self.return_type = kwargs.get("return_type")
        self.params = kwargs.get("params", [])


class SymbolTable:
    _scope_counter = 0

    def __init__(self, parent=None):
        self.symbols = {}
        self.parent = parent
        self.storage = "global" if parent is None else "local"
        self.scope_id = SymbolTable._scope_counter
        SymbolTable._scope_counter += 1

    def define_variable(self, name, var_type):
        if name in self.symbols:
            existing_symbol = self.symbols[name]
            if existing_symbol.symbol_type == "variable":
                raise Exception(f"Semantic Error: Variable '{name}' already defined in this scope.")
            else:
                raise Exception(f"Semantic Error: Name '{name}' already used for a function in this scope.")
            
        self.symbols[name] = Symbol(
            name,
            "variable",
            var_type=var_type,
            storage=self.storage,
            scope_id=self.scope_id,
        )

    def lookup_variable(self, name):
        symbol = self.symbols.get(name)
        if symbol and symbol.symbol_type == "variable":
            return symbol, symbol.storage, symbol.scope_id
        if self.parent:
            return self.parent.lookup_variable(name)
        return None, None, None

    def define_function(self, name, return_type, params):
        if name in self.symbols:
            existing_symbol = self.symbols[name]
            if existing_symbol.symbol_type == "variable":
                raise Exception(f"Semantic Error: Variable '{name}' already defined in this scope.")
            else:
                raise Exception(f"Semantic Error: Name '{name}' already used for a function in this scope.")
        if self.parent is not None:
             raise Exception("Semantic Error: Nested functions are not allowed. Functions can only be defined in the global scope.")
        
        self.symbols[name] = Symbol(
            name,
            "function",
            return_type=return_type,
            params=params,
        )

    def lookup_function(self, name):
        symbol = self.symbols.get(name)
        if symbol and symbol.symbol_type == "function":
            return symbol
        if self.parent:
            return self.parent.lookup_function(name)
        return None

    def lookup(self, name):
        symbol = self.symbols.get(name)
        if symbol:
            return symbol, symbol.storage, symbol.scope_id
        if self.parent:
            return self.parent.lookup(name)
        return None


class SemanticAnalyzer:
    def __init__(self):
        self.current_scope = SymbolTable()
        self.global_scope = self.current_scope
        self.current_function = None

    def analyze(self, ast):
        self.visit(ast)

    def visit(self, node):
        method_name = f"visit_{type(node).__name__}"
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node):
        raise Exception(f"No visit_{type(node).__name__} method")

    def visit_ProgramNode(self, node):
            
        for decl in node.declarations:
            if isinstance(decl, FunctionDefNode):
                self.global_scope.define_function(decl.name, decl.return_type[1], decl.params)
        for decl in node.declarations:
                self.visit(decl)

    def visit_FunctionDefNode(self, node):
        self.current_function = node
        parent_scope = self.current_scope
        self.current_scope = SymbolTable(parent=parent_scope)
        for param_type, param_name in node.params:
            self.current_scope.define_variable(param_name, param_type[1])
        self.visit(node.body)
        self.current_scope = parent_scope
        self.current_function = None

    def visit_FunctionCallNode(self, node):
        function_symbol = self.global_scope.lookup_function(node.name)
        if function_symbol is None:
            raise Exception(f"Semantic Error: Function '{node.name}' not defined.")
        if len(node.args) != len(function_symbol.params):
            raise Exception(
                f"Semantic Error: Function '{node.name}' expects {len(function_symbol.params)} arguments, got {len(node.args)}."
            )
        for arg_node, (param_type, param_name) in zip(node.args, function_symbol.params):
            arg_type = self.visit(arg_node)
            if arg_type != param_type[1]:
                raise Exception(
                    f"Type Error: Argument for parameter '{param_name}' expects type '{param_type[1]}', got '{arg_type}'."
                )
        node.type = function_symbol.return_type
        return function_symbol.return_type
    
    def visit_ReturnNode(self, node):
        if self.current_function is None:
            raise Exception("Semantic Error: 'return' statement not inside a function.")
        expected_type = self.current_function.return_type[1]
        actual_type = self.visit(node.expression)
        if expected_type != actual_type:
            raise Exception(
                f"Type Error: Function '{self.current_function.name}' expects return type '{expected_type}', got '{actual_type}'."
            )
        return actual_type

    def visit_ScopeNode(self, node):
        parent_scope = self.current_scope
        self.current_scope = SymbolTable(parent=parent_scope)
        for statement in node.statements:
            self.visit(statement)
        self.current_scope = parent_scope

    def visit_DefinerNode(self, node):
        self.current_scope.define_variable(node.name, node.type)
        node.storage = self.current_scope.storage
        node.scope_id = self.current_scope.scope_id
        if node.value:
            value_type = self.visit(node.value)
            if value_type != node.type:
                raise Exception(
                    f"Type Error: Cannot assign value of type '{value_type}' to variable '{node.name}' of type '{node.type}'."
                )

    def visit_EqualizeNode(self, node):
        var_type, storage, scope_id = self.current_scope.lookup_variable(node.name)
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
            var_type, storage, scope_id = self.current_scope.lookup_variable(node.value)
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
