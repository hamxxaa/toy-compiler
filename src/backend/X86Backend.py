from codegen.TACGenerator import Var, Const, TempVar, TACInstruction, TAC


class X86Backend:
    def __init__(self, TAC):
        self.data_section = "section .data \nmsg db 'code executed successfully', 0xA \nmsglen equ $ - msg \n"
        self.bss_section = "section .bss \nextern num \n"
        self.text_section = "section .text \nglobal _start \n_start: \n"
        self.exit = "mov eax, 4 \nmov ebx, 1 \nmov ecx, msg \nmov edx, msglen \nint 0x80 \nmov eax, 1 \nxor ebx, ebx \nint 0x80 \nextern print_integer \nextern newline \n"

        self.TAC = TAC
        self.counter = 0
        self.registers = ["eax", "ebx", "ecx", "edx"]
        self.register_descriptors = {reg: None for reg in self.registers}
        self.address_descriptors = {}
        temps = set()
        for instr in self.TAC.instructions:
            if isinstance(instr.result, TempVar):
                temps.add(instr.result.name)
        self.max_temp_count = len(temps)
        self.text_section += (
            f"push ebp\nmov ebp, esp\nsub esp, {self.max_temp_count * 4}\n"
        )
        self.temp_map = {}
        i = 0
        for temp in temps:
            i += 1
            self.temp_map[temp] = f"[ebp - {i*4}]"
        self.liveness_analyzer()

    def liveness_analyzer(self):
        self.live = [set() for _ in range(self.TAC.line_count)]
        instrs = self.TAC.instructions
        live = set()
        first_use = {}
        for i in range(self.TAC.line_count - 1, -1, -1):
            defs = set()
            instr = instrs[i]
            if instr.op == "def":
                defs.add(instr.result)
            if instr.op not in ["goto", "label"]:
                if instr.result and isinstance(instr.result, (Var, TempVar)):
                    if isinstance(instr.result, TempVar):
                        first_use[instr.result] = i
                    live.add(instr.result)
                if instr.arg1 and isinstance(instr.arg1, (Var, TempVar)):
                    if isinstance(instr.arg1, TempVar):
                        first_use[instr.arg1] = i
                    live.add(instr.arg1)
                if instr.arg2 and isinstance(instr.arg2, (Var, TempVar)):
                    if isinstance(instr.arg2, TempVar):
                        first_use[instr.arg2] = i
                    live.add(instr.arg2)
            live -= defs
            self.live[i] = live.copy()

        for var, line in first_use.items():
            for l in range(line):
                self.live[l].remove(var)

    def get_register(self, operand):
        if (
            operand in self.address_descriptors
            and self.address_descriptors[operand]
            and self.address_descriptors[operand] in self.registers
        ):
            return self.address_descriptors[operand]
        for reg in self.registers:
            if self.register_descriptors[reg] is None:
                self.register_descriptors[reg] = operand
                self.address_descriptors[operand] = reg
                if isinstance(operand, TempVar):
                    self.text_section += f"mov {reg}, {self.temp_map[operand.name]}\n"
                else:
                    self.text_section += f"mov {reg}, [{operand.name}]\n"
                return reg
        for reg in self.registers:
            if self.register_descriptors[reg] not in self.live:
                old_var = self.register_descriptors[reg]
                del self.address_descriptors[old_var]
                self.register_descriptors[reg] = operand
                self.address_descriptors[operand] = reg
                if isinstance(operand, TempVar):
                    self.text_section += f"mov {reg}, {self.temp_map[operand.name]}\n"
                else:
                    self.text_section += f"mov {reg}, [{operand.name}]\n"
                return reg
        for reg in self.registers:
            if isinstance(self.register_descriptors[reg], Var):
                old_var = self.register_descriptors[reg]
                self.text_section += f"mov [{old_var.name}], {reg}\n"
                if isinstance(operand, TempVar):
                    self.text_section += f"mov {reg}, {self.temp_map[operand.name]}\n"
                else:
                    self.text_section += f"mov {reg}, [{operand.name}]\n"
                self.address_descriptors[old_var] = f"[{old_var.name}]"
                self.register_descriptors[reg] = operand
                self.address_descriptors[operand] = reg
                return reg
        reg = self.registers[0]
        old_var = self.register_descriptors[reg]
        self.text_section += f"mov [{self.temp_map[old_var.name]}], {reg}\n"
        if isinstance(operand, TempVar):
            self.text_section += f"mov {reg}, {self.temp_map[operand.name]}\n"
        else:
            self.text_section += f"mov {reg}, [{operand.name}]\n"
        self.address_descriptors[old_var] = self.temp_map[old_var.name]
        self.register_descriptors[reg] = operand
        self.address_descriptors[operand] = reg
        return reg

    def when_will_it_die(self, operand):
        for i in range(self.counter, self.TAC.line_count):
            if operand not in self.live[i]:
                return i
        return self.TAC.line_count + 1

    def generate(self):
        for instr in self.TAC.instructions:
            self.counter += 1
            if instr.op == "def":
                self.handle_def(instr)
            elif instr.op == "eq":
                self.handle_eq(instr)
            elif instr.op in ["+", "-", "*", "/", "|", "&"]:
                self.handle_binary_op(instr)
            elif instr.op in ["<", ">", "<=", ">=", "==", "!="]:
                self.handle_comparison(instr)
            elif instr.op in ["goto"]:
                self.handle_goto(instr)
            elif instr.op in ["if"]:
                self.handle_if(instr)
            elif instr.op == "label":
                self.handle_label(instr)
            elif instr.op == "print":
                self.handle_print(instr)
        self.text_section += "mov eax, 1\nxor ebx, ebx\nint 0x80\n"
        return self.data_section + self.bss_section + self.text_section + self.exit

    def handle_def(self, instr):
        if instr.arg1 is not None:
            self.data_section += f"{instr.result.name} dd {instr.arg1.value}\n"
        else:
            self.data_section += f"{instr.result.name} dd 0\n"

    def handle_eq(self, instr):
        if isinstance(instr.arg1, Const):

            self.text_section += (
                f"mov dword [{instr.result.name}], {instr.arg1.value}\n"
            )
            self.address_descriptors[instr.result] = f"[{instr.result.name}]"
        elif isinstance(instr.arg1, (TempVar, Var)):
            reg = self.get_register(instr.arg1)
            self.text_section += f"mov [{instr.result.name}], {reg}\n"
            self.address_descriptors[instr.result] = f"[{instr.result.name}]"

    def handle_binary_op(self, instr):
        first_register = self.get_register(instr.arg1)
        life = self.when_will_it_die(instr.arg1) - self.counter
        if life != 0:
            if isinstance(instr.arg1, TempVar):
                self.text_section += (
                    f"mov {first_register}, {self.temp_map[instr.arg1.name]}\n"
                )
                self.address_descriptors[instr.arg1] = self.temp_map[instr.arg1.name]
            if isinstance(instr.arg1, Var):
                self.text_section += f"mov {first_register}, [{instr.arg1.name}]\n"
                self.address_descriptors[instr.arg1] = f"[{instr.arg1.name}]"
        if isinstance(instr.arg2, Const):
            second_register = instr.arg2.value
        else:
            second_register = self.get_register(instr.arg2)
        if instr.op == "+":
            self.text_section += f"add {first_register}, {second_register}\n"
        elif instr.op == "-":
            self.text_section += f"sub {first_register}, {second_register}\n"
        elif instr.op == "*":
            self.text_section += f"imul {first_register}, {second_register}\n"
        elif instr.op == "/":
            self.handle_division(first_register, second_register)
        elif instr.op == "&":
            self.text_section += f"and {first_register}, {second_register}\n"
        elif instr.op == "|":
            self.text_section += f"or {first_register}, {second_register}\n"
        self.address_descriptors[instr.result] = first_register
        self.register_descriptors[first_register] = instr.result

    def handle_comparison(self, instr):
        first_register = self.get_register(instr.arg1)
        if isinstance(instr.arg2, Const):
            second_register = instr.arg2.value
        else:
            second_register = self.get_register(instr.arg2)
        self.text_section += f"cmp {first_register}, {second_register}\n"
        if instr.op == "<":
            self.text_section += f"setl {first_register[1]}l\n"
        elif instr.op == "<=":
            self.text_section += f"setle {first_register[1]}l\n"
        elif instr.op == ">":
            self.text_section += f"setg {first_register[1]}l\n"
        elif instr.op == ">=":
            self.text_section += f"setge {first_register[1]}l\n"
        elif instr.op == "==":
            self.text_section += f"sete {first_register[1]}l\n"
        elif instr.op == "!=":
            self.text_section += f"setne {first_register[1]}l\n"
        self.text_section += f"movzx {first_register}, {first_register[1]}l\n"
        self.address_descriptors[instr.result] = first_register
        self.register_descriptors[first_register] = instr.result

    def handle_goto(self, instr):
        self.text_section += f"jmp {instr.result}\n"

    def handle_if(self, instr):
        if isinstance(instr.arg1, Const):
            self.text_section += f"mov edi, {instr.arg1.value}\n"
            reg = "edi"
        else:
            reg = self.get_register(instr.arg1)
        self.text_section += f"cmp {reg}, 0\n"
        self.text_section += f"jne {instr.result}\n"

    def handle_label(self, instr):
        self.text_section += f"{instr.result}:\n"

    def handle_print(self, instr):
        pushed = [0, 0, 0, 0]
        if self.register_descriptors["eax"]:
            self.text_section += "push eax\n"
        if self.register_descriptors["ebx"]:
            self.text_section += "push ebx\n"
        if self.register_descriptors["ecx"]:
            self.text_section += "push ecx\n"
        if self.register_descriptors["edx"]:
            self.text_section += "push edx\n"
        self.text_section += f"mov eax, dword [{instr.arg1.name}] \nmov dword [num], eax \ncall print_integer \nmov eax, 4 \nmov ebx, 1 \nmov ecx, newline \nmov edx, 1 \nint 0x80\n"
        for i, reg in enumerate(["eax", "ebx", "ecx", "edx"]):
            if pushed[i]:
                self.text_section += f"pop {reg}\n"

    def handle_division(self, first_register, second_register):
        eax_pushed = False
        edx_pushed = False
        if first_register == "eax" and second_register == "edx":
            self.text_section += "mov edi, edx\n"
            self.text_section += "cdq\n"
            self.text_section += "idiv edi\n"
            self.text_section += "mov edi, edx\n"
            return
        elif first_register == "edx" and second_register == "eax":
            self.text_section += "mov edi, eax\n"
            self.text_section += "mov eax, edx\n"
            self.text_section += "cdq\n"
            self.text_section += "idiv edi\n"
            self.text_section += "mov edx, eax\n"
            self.text_section += "mov eax, edi\n"
            return
        elif first_register == "eax":
            if self.register_descriptors["edx"]:
                self.text_section += "push edx\n"
                edx_pushed = True
            self.text_section += "cdq\n"
            self.text_section += f"idiv {second_register}\n"
            if edx_pushed:
                self.text_section += "pop edx\n"
            return
        elif second_register == "eax":
            if self.register_descriptors["edx"]:
                self.text_section += "push edx\n"
                edx_pushed = True
            self.text_section += "mov edi, eax\n"
            self.text_section += f"mov eax, {first_register}\n"
            self.text_section += "cdq\n"
            self.text_section += "idiv edi\n"
            self.text_section += f"mov {first_register}, eax\n"
            self.text_section += "mov eax, edi\n"
            if edx_pushed:
                self.text_section += "pop edx\n"
            return
        elif first_register == "edx":
            if self.register_descriptors["eax"]:
                self.text_section += "push eax\n"
            self.text_section += "mov eax, edx\n"
            self.text_section += "cdq\n"
            self.text_section += f"idiv {second_register}\n"
            self.text_section += "mov edx, eax\n"
            if self.register_descriptors["eax"]:
                self.text_section += "pop eax\n"
            return
        elif second_register == "edx":
            if self.register_descriptors["eax"]:
                self.text_section += "push eax\n"
                eax_pushed = True
            self.text_section += f"mov eax, {first_register}\n"
            self.text_section += "mov edi, edx\n"
            self.text_section += "cdq\n"
            self.text_section += "idiv edi\n"
            self.text_section += f"mov {first_register}, eax\n"
            self.text_section += "mov edx, edi\n"
            if eax_pushed:
                self.text_section += "pop eax\n"
        else:
            if self.register_descriptors["eax"]:
                self.text_section += "push eax\n"
                eax_pushed = True
            if self.register_descriptors["edx"]:
                self.text_section += "push edx\n"
                edx_pushed = True
            self.text_section += f"mov eax, {first_register}\n"
            self.text_section += "cdq\n"
            self.text_section += f"idiv {second_register}\n"
            self.text_section += f"mov {first_register}, eax\n"
            if edx_pushed:
                self.text_section += "pop edx\n"
            if eax_pushed:
                self.text_section += "pop eax\n"
