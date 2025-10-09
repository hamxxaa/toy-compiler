from AsmGenerator import AsmGenerator


class CodeGenerator:
    def __init__(self):
        self.asm_generator = AsmGenerator()

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
        if node.value:
            self.generate(node.value)
            self.asm_generator.define(node.var_name, True)
        else:
            self.asm_generator.define(node.var_name, False)

    def visit_EqualizeNode(self, node):
        self.generate(node.value)
        self.asm_generator.equalize(node.var_name)

    def visit_IfNode(self, node):
        self.generate(node.condition)
        self.asm_generator.prepare_condition_jump()
        end_label = self.asm_generator.create_unique_label()
        self.asm_generator.jumpIfZero(end_label)
        for statement in node.statements:
            self.generate(statement)
        self.asm_generator.start_label(end_label)

    def visit_WhileNode(self, node):
        start_label = self.asm_generator.create_unique_label()
        end_label = self.asm_generator.create_unique_label()
        self.asm_generator.start_label(start_label)
        self.generate(node.condition)
        self.asm_generator.prepare_condition_jump()
        self.asm_generator.jumpIfZero(end_label)
        for statement in node.statements:
            self.generate(statement)
        self.asm_generator.jump(start_label)
        self.asm_generator.start_label(end_label)

    def visit_PrintNode(self, node):
        self.asm_generator.print(node.var_name)

    def visit_ConditionNode(self, node):
        if node.operator in ("&", "|"):
            self.generate(node.left)
            self.generate(node.right)
            if node.operator == "&":
                self.asm_generator.apply_binary_operation("and")
            else:
                self.asm_generator.apply_binary_operation("or")
        else:
            self.generate(node.left)
            self.generate(node.right)
            self.asm_generator.apply_cmp(node.operator)

    def visit_ExpressionNode(self, node):
        self.generate(node.left)
        self.generate(node.right)
        if node.operator == "+":
            self.asm_generator.apply_binary_operation("add")
        elif node.operator == "-":
            self.asm_generator.apply_binary_operation("sub")

    def visit_TermNode(self, node):
        self.generate(node.left)
        self.generate(node.right)
        if node.operator == "*":
            self.asm_generator.apply_binary_operation("imul")
        elif node.operator == "/":
            self.division()

    def visit_FactorNode(self, node):
        if node.is_variable:
            self.asm_generator.load_value_to(var=node.value)
        else:
            self.asm_generator.load_value_to(val=node.value)

    def get_full_code(self, ast):
        self.generate(ast)
        full_code = (
            "section .data \n"
            + "msg db 'code executed successfully', 0xA \n"
            + "msglen equ $ - msg \n"
            + self.asm_generator.data
            + "section .bss \nextern num \n"
            + "section .text \n"
            + "global _start \n"
            + "_start: \n"
            + self.asm_generator.code
            + "mov eax, 4 \n"
            + "mov ebx, 1 \n"
            + "mov ecx, msg \n"
            + "mov edx, msglen \n"
            + "int 0x80 \n"
            + "mov eax, 1 \n"
            + "xor ebx, ebx \n"
            + "int 0x80 \n"
            + "extern print_integer \n"
            + "extern newline \n"
        )
        return full_code
