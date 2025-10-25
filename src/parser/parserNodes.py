class ProgramNode:
    def __init__(self, statements):
        self.statements = statements


class DefinerNode:
    def __init__(self, name, value=None, type=None):
        self.name = name
        self.value = value
        self.type = type


class EqualizeNode:
    def __init__(self, name, value):
        self.name = name
        self.value = value


class IfNode:
    def __init__(self, condition, statements):
        self.condition = condition
        self.statements = statements


class WhileNode:
    def __init__(self, condition, statements):
        self.condition = condition
        self.statements = statements


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

    def __repr__(self):
        return f"FactorNode(value={self.value}, is_variable={self.is_variable})"
