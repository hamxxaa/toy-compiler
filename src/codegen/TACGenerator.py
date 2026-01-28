from src.parser.parserNodes import FunctionDefNode


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
    def __init__(self, id, type):
        self.id = id
        self.name = f"t{id}"
        self.type = type

    def __str__(self):
        return f"{self.name} ({self.type})"

    def __eq__(self, other):
        return (
            isinstance(other, TempVar)
            and self.name == other.name
            and self.type == other.type
        )

    def __hash__(self):
        return hash((self.name, self.type))


class Var(Operand):
    def __init__(self, name, type, storage="global", scope_id=0):
        self.name = name
        self.type = type
        self.storage = storage
        self.scope_id = scope_id

    def __str__(self):
        if self.storage == "local":
            return f"{self.name}_s{self.scope_id} ({self.type}, {self.storage})"
        return f"{self.name} ({self.type}, {self.storage})"

    def __eq__(self, other):
        return (
            isinstance(other, Var)
            and self.name == other.name
            and self.type == other.type
            and self.storage == other.storage
            and self.scope_id == other.scope_id
        )

    def __hash__(self):
        return hash((self.name, self.type, self.storage, self.scope_id))


class Const(Operand):
    def __init__(self, value, type):
        self.value = value
        self.type = type

    def __str__(self):
        return f"{self.value} ({self.type})"

    def __eq__(self, other):
        return (
            isinstance(other, Const)
            and self.value == other.value
            and self.type == other.type
        )

    def __hash__(self):
        return hash((self.value, self.type))


class TAC:
    def __init__(self, instructions):
        self.instructions = instructions
        self.line_count = len(instructions)
        self.functions = {}
        self.global_vars = []


class TACGenerator:
    def __init__(self):
        self.instructions = []
        self.temp_count = 0
        self.label_count = 0

    def generate_tac(self, ast):
        self.generate(ast)
        self.split_tac_into_functions(TAC(self.instructions))
        return TAC(self.instructions)

    def new_temp(self, type):
        temp = TempVar(self.temp_count, type)
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

    def split_tac_into_functions(self, tac):
        functions = {}
        current_function = None
        current_instructions = []
        global_vars = []

        for instr in tac.instructions:
            if instr.op == "func_start":
                if current_function is not None:
                    functions[current_function] = TAC(current_instructions)
                    current_instructions = []
                current_function = instr.result
            elif instr.op == "func_end":
                if current_function is not None:
                    functions[current_function] = TAC(current_instructions)
                    current_function = None
                    current_instructions = []
            elif instr.op == "def" and instr.result.storage == "global":
                global_vars.append(instr)
            else:
                if current_function is not None:
                    current_instructions.append(instr)

        tac.functions = functions
        tac.global_vars = global_vars

    def generic_visit(self, node):
        raise Exception(f"No visit_{type(node).__name__} method")

    def visit_ProgramNode(self, node):
        main_func = None
        other_funcs = []
        for decl in node.declarations:
            if isinstance(decl, FunctionDefNode):
                if decl.name == "main":
                    main_func = decl
                else:
                    other_funcs.append(decl)
            else:
                self.generate(decl)
        for func in other_funcs:
            self.generate(func)
        if main_func:
            self.generate(main_func)
        else:
            raise Exception("No 'main' function defined.")

    def visit_FunctionDefNode(self, node):
        self.create_instruction("func_start", result=node.name)
        for param in node.params:
            self.create_instruction(
                "param",
                result=Var(
                    param.value,
                    type=param.type,
                    storage="param",
                    scope_id=param.scope_id,
                ),
            )
        self.generate(node.body)
        self.create_instruction("func_end", result=node.name)

    def visit_FunctionCallNode(self, node):
        for arg in reversed(node.args):
            arg_result = self.generate(arg)
            self.create_instruction("arg", result=arg_result)
        temp = self.new_temp(type=node.type)
        self.create_instruction(
            "call", arg1=node.name, arg2=len(node.args), result=temp
        )
        return temp

    def visit_ReturnNode(self, node):
        result = self.generate(node.expression)
        self.create_instruction("ret", arg1=result)

    def visit_ScopeNode(self, node):
        for statement in node.statements:
            self.generate(statement)

    def visit_DefinerNode(self, node):
        value = self.generate(node.value) if node.value else None
        if isinstance(value, Const):
            self.create_instruction(
                "def",
                arg1=value,
                result=Var(
                    node.name,
                    type=node.type,
                    storage=node.storage,
                    scope_id=node.scope_id,
                ),
            )
        elif value is not None:
            self.create_instruction(
                "def",
                result=Var(
                    node.name,
                    type=node.type,
                    storage=node.storage,
                    scope_id=node.scope_id,
                ),
            )
            self.create_instruction(
                "eq",
                arg1=value,
                result=Var(
                    node.name,
                    type=node.type,
                    storage=node.storage,
                    scope_id=node.scope_id,
                ),
            )
        else:
            self.create_instruction(
                "def",
                result=Var(
                    node.name,
                    type=node.type,
                    storage=node.storage,
                    scope_id=node.scope_id,
                ),
            )

    def visit_EqualizeNode(self, node):
        value = self.generate(node.value)
        self.create_instruction(
            "eq",
            arg1=value,
            result=Var(
                node.name, type=value.type, storage=node.storage, scope_id=node.scope_id
            ),
        )

    def visit_IfNode(self, node):
        condition = self.generate(node.condition)
        start_label = self.new_label()
        self.create_instruction("if", arg1=condition, result=start_label)
        end_label = self.new_label()
        self.create_instruction("goto", result=end_label)
        self.create_instruction("label", result=start_label)
        self.generate(node.scope)
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
        self.generate(node.scope)
        self.create_instruction("goto", result=start_label)
        self.create_instruction("label", result=end_label)

    def visit_PrintNode(self, node):
        expression_result = self.generate(node.expression)
        self.create_instruction("print", arg1=expression_result)

    def visit_ConditionNode(self, node):
        left = self.generate(node.left)
        right = self.generate(node.right)
        temp = self.new_temp(type=node.type)
        self.create_instruction(node.operator, arg1=left, arg2=right, result=temp)
        return temp

    def visit_ExpressionNode(self, node):
        left = self.generate(node.left)
        right = self.generate(node.right)
        temp = self.new_temp(type=node.type)
        self.create_instruction(node.operator, arg1=left, arg2=right, result=temp)
        return temp

    def visit_TermNode(self, node):
        left = self.generate(node.left)
        right = self.generate(node.right)
        temp = self.new_temp(type=node.type)
        self.create_instruction(node.operator, arg1=left, arg2=right, result=temp)
        return temp

    def visit_FactorNode(self, node):
        if node.is_variable:
            return Var(
                node.value, type=node.type, storage=node.storage, scope_id=node.scope_id
            )
        else:
            if node.type == "bool":
                if node.value.lower() == "true":
                    value = 1
                elif node.value.lower() == "false":
                    value = 0
                else:
                    raise ValueError(f"Invalid boolean value: {node.value}")
            else:
                value = int(node.value)
                if value < -2147483648 or value > 2147483647:
                    raise ValueError(
                        f"Integer constant out of bounds (32-bit): {value}"
                    )
            return Const(value, type=node.type)
