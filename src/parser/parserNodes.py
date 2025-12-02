class ProgramNode:
    def __init__(self, declarations):
        self.declarations = declarations

class FunctionDefNode:
    def __init__(self, return_type, name, params, body):
        self.return_type = return_type
        self.name = name
        self.params = params
        self.body = body
class FunctionCallNode:
    def __init__(self, name, args):
        self.name = name
        self.args = args
        self.type = None

class ReturnNode:
    def __init__(self, expression):
        self.expression = expression

class ScopeNode:
    def __init__(self, statements):
        self.statements = statements

class DefinerNode:
    def __init__(self, name, value=None, type=None):
        self.name = name
        self.value = value
        self.type = type
        self.storage = None
        self.scope_id = None

class EqualizeNode:
    def __init__(self, name, value):
        self.name = name
        self.value = value
        self.storage = None
        self.scope_id = None


class IfNode:
    def __init__(self, condition, scope):
        self.condition = condition
        self.scope = scope


class WhileNode:
    def __init__(self, condition, scope):
        self.condition = condition
        self.scope = scope


class PrintNode:
    def __init__(self, expression):
        self.expression = expression


class ConditionNode:
    def __init__(self, left, operator, right):
        self.left = left
        self.operator = operator
        self.right = right
        self.type = None


class ExpressionNode:
    def __init__(self, left, operator, right):
        self.left = left
        self.operator = operator
        self.right = right
        self.type = None


class TermNode:
    def __init__(self, left, operator, right):
        self.left = left
        self.operator = operator
        self.right = right
        self.type = None


class FactorNode:
    def __init__(self, value, is_variable):
        self.value = value
        self.is_variable = is_variable
        self.type = None
        self.storage = None
        self.scope_id = None

    def __repr__(self):
        return f"FactorNode(value={self.value}, is_variable={self.is_variable})"
