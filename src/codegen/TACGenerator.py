from locale import atoi


class TACInstruction:
    def __init__(self, op, arg1=None, arg2=None, result=None):
        self.op = op
        self.arg1 = arg1
        self.arg2 = arg2
        self.result = result

    def __str__(self):
        parts = [self.op]
        if self.arg1 is not None:
            parts.append(str(self.arg1))
        if self.arg2 is not None:
            parts.append(str(self.arg2))
        if self.result is not None:
            parts.append(str(self.result))
        return " ".join(parts)


class Operand:
    pass


class TempVar(Operand):
    def __init__(self, id):
        self.id = id
        self.name = f"t{id}"

    def __str__(self):
        return self.name

    def __eq__(self, other):
        return isinstance(other, TempVar) and self.name == other.name

    def __hash__(self):
        return hash(self.name)


class Var(Operand):
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return self.name

    def __eq__(self, other):
        return isinstance(other, Var) and self.name == other.name

    def __hash__(self):
        return hash(self.name)


class Const(Operand):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)

    def __eq__(self, other):
        return isinstance(other, Const) and self.value == other.value

    def __hash__(self):
        return hash(self.value)


class TAC:
    def __init__(self, instructions):
        self.instructions = instructions
        self.line_count = len(instructions)


class TACGenerator:
    def __init__(self):
        self.instructions = []
        self.temp_count = 0
        self.label_count = 0

    def generate_tac(self, ast):
        self.generate(ast)
        return TAC(self.instructions)

    def new_temp(self):
        temp = TempVar(self.temp_count)
        self.temp_count += 1
        return temp

    def new_label(self):
        label_name = f"L{self.label_count}"
        self.label_count += 1
        return label_name

    def create_instruction(self, op, arg1=None, arg2=None, result=None):
        instruction = TACInstruction(op, arg1, arg2, result)
        self.instructions.append(instruction)
        return instruction

    def generate(self, node):
        method_name = f"visit_{type(node).__name__}"
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node):
        raise Exception(f"No visit_{type(node).__name__} method")

    def visit_ProgramNode(self, node):
        for statement in node.statements:
            self.generate(statement)

    def visit_DefinerNode(self, node):
        value = self.generate(node.value) if node.value else None
        if isinstance(value, Const):
            self.create_instruction("def", arg1=value, result=Var(node.var_name))
        elif value is not None:
            self.create_instruction("def", result=Var(node.var_name))
            self.create_instruction("eq", arg1=value, result=Var(node.var_name))
        else:
            self.create_instruction("def", result=Var(node.var_name))

    def visit_EqualizeNode(self, node):
        value = self.generate(node.value)
        self.create_instruction("eq", arg1=value, result=Var(node.var_name))

    def visit_IfNode(self, node):
        condition = self.generate(node.condition)
        start_label = self.new_label()
        self.create_instruction("if", arg1=condition, result=start_label)
        end_label = self.new_label()
        self.create_instruction("goto", result=end_label)
        self.create_instruction("label", result=start_label)
        for statement in node.statements:
            self.generate(statement)
        self.create_instruction("label", result=end_label)

    def visit_WhileNode(self, node):
        start_label = self.new_label()
        self.create_instruction("label", result=start_label)
        condition = self.generate(node.condition)
        mid_label = self.new_label()
        end_label = self.new_label()
        self.create_instruction("if", arg1=condition, result=mid_label)
        self.create_instruction("goto", result=end_label)
        self.create_instruction("label", result=mid_label)
        for statement in node.statements:
            self.generate(statement)
        self.create_instruction("goto", result=start_label)
        self.create_instruction("label", result=end_label)

    def visit_PrintNode(self, node):
        self.create_instruction("print", arg1=Var(node.var_name))

    def visit_ConditionNode(self, node):
        left = self.generate(node.left)
        right = self.generate(node.right)
        temp = self.new_temp()
        self.create_instruction(node.operator, arg1=left, arg2=right, result=temp)
        return temp

    def visit_ExpressionNode(self, node):
        left = self.generate(node.left)
        right = self.generate(node.right)
        temp = self.new_temp()
        self.create_instruction(node.operator, arg1=left, arg2=right, result=temp)
        return temp

    def visit_TermNode(self, node):
        left = self.generate(node.left)
        right = self.generate(node.right)
        temp = self.new_temp()
        self.create_instruction(node.operator, arg1=left, arg2=right, result=temp)
        return temp

    def visit_FactorNode(self, node):
        if node.is_variable:
            return Var(node.value)
        else:
            return Const(atoi(node.value))
