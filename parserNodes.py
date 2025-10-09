class ProgramNode:
    def __init__(self, statements):
        self.statements = statements


class DefinerNode:
    def __init__(self, var_name, value=None):
        self.var_name = var_name
        self.value = value


class EqualizeNode:
    def __init__(self, var_name, value):
        self.var_name = var_name
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
    def __init__(self, var_name):
        self.var_name = var_name


class ConditionNode:
    def __init__(self, left, operator, right):
        self.left = left
        self.operator = operator
        self.right = right


class ExpressionNode:
    def __init__(self, left, operator, right):
        self.left = left
        self.operator = operator
        self.right = right


class TermNode:
    def __init__(self, left, operator, right):
        self.left = left
        self.operator = operator
        self.right = right


class FactorNode:
    def __init__(self, value, is_variable):
        self.value = value
        self.is_variable = is_variable
