import os
from codegen.TACGenerator import Var, Const, TempVar, TACInstruction, TAC


class X86Backend:
    def __init__(self, TAC):
        self.data_section = "section .data\n"
        self.bss_section = "section .bss\n"
        self.text_section = "section .text\nglobal _start\n_start:\n"
        try:
            runtime_path = os.path.join(
                os.path.dirname(__file__), "..", "..", "runtime", "runtime.asm"
            )
            with open(runtime_path, "r") as f:
                self.runtime_code = f.read()
        except FileNotFoundError:
            raise RuntimeError(
                "runtime.asm not found! Cannot include runtime functions."
            )
        self.exit_code = "\nmov eax, 1\nxor ebx, ebx\nint 0x80\n"

        self.TAC = TAC
        self.counter = 0
        self.registers = ["eax", "ebx", "ecx", "edx"]
        self.register_descriptors = {reg: None for reg in self.registers}
        self.address_descriptors = {}
        self.stack_map = {}
        self.never_alive_vars = set()
        for instr in self.TAC.instructions:
            if isinstance(instr.result, TempVar) or (
                isinstance(instr.result, Var) and instr.result.storage == "local"
            ):
                self.stack_map[instr.result] = None
        self.stack_map_count = len(self.stack_map)
        self.live_set_line_count = 0
        self.liveness_analyzer()
        max_count, max_local_and_temp_var_set, max_var_size = (
            self.get_max_alive_temp_and_local_vars()
        )
        self.text_section += (
            f"push ebp\nmov ebp, esp\nsub esp, {max_count*max_var_size}\n"
        )
        self.set_local_and_tempvar_addresses(max_count, max_var_size)

    def set_local_and_tempvar_addresses(self, max_count, max_var_size):
        available_slots = []
        for i in range(max_count):
            available_slots.append(f"[ebp - {i * max_var_size}]")
        for i in range(self.live_set_line_count):
            for var in self.live[i]:
                if (var in self.stack_map) and (self.stack_map[var] is None):
                    self.stack_map[var] = available_slots.pop(0)
                deads = self.live[i - 1] - self.live[i]
                for dead in deads:
                    if dead in self.stack_map and self.stack_map[dead] is not None:
                        available_slots.append(self.stack_map[dead])
        for var in self.stack_map:
            if self.stack_map[var] is None:
                self.never_alive_vars.add(var)

    def liveness_analyzer(self):
        self.live = [set() for _ in range(self.TAC.line_count + 1)]
        instrs = self.TAC.instructions
        live = set()
        first_use = {}
        for i in range(self.TAC.line_count, 0, -1):
            defs = set()
            instr = instrs[i - 1]
            if (
                instr.result
                and isinstance(instr.result, (Var, TempVar))
                and instr.op not in ["goto", "label", "if", "print"]
            ):
                defs.add(instr.result)

            if instr.op not in ["goto", "label"]:
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
                self.live[l].discard(var)
        self.live_set_line_count = len(self.live)

    def get_max_alive_temp_and_local_vars(self):
        max_count = 0
        max_set = set()
        max_var_size = 0
        for live_set in self.live:
            current_count = 0
            current_var_size = 0
            for var in live_set:
                if isinstance(var, TempVar) or (
                    isinstance(var, Var) and var.storage == "local"
                ):
                    if var.type == "int":
                        current_var_size = 4
                    current_count += 1
            if current_count > max_count:
                max_count = current_count
                max_set = set(
                    var
                    for var in live_set
                    if isinstance(var, (TempVar))
                    or (isinstance(var, Var) and var.storage == "local")
                )
            if current_var_size > max_var_size:
                max_var_size = current_var_size
        return max_count, max_set, max_var_size

    def get_type_specifier(self, type):
        if type == "int":
            return "dd", "dword"
        elif type == "bool":
            return "db", "byte"
        else:
            raise Exception(f"Unknown type: {type}")

    def get_var_location(self, var):
        if var.storage == "global":
            return f"[{var.name}]"
        else:
            return self.stack_map[var]

    def get_register_part(self, reg_name, size_specifier):
        if size_specifier == "dword":
            return reg_name

        if size_specifier == "byte":
            if reg_name == "eax":
                return "al"
            if reg_name == "ebx":
                return "bl"
            if reg_name == "ecx":
                return "cl"
            if reg_name == "edx":
                return "dl"

        raise Exception(f"Cannot get byte-part of register: {reg_name}")

    def get_register(self, operand):
        def get_operand_address(operand):
            if isinstance(operand, TempVar):
                return self.stack_map[operand]
            elif isinstance(operand, Var):
                return self.get_var_location(operand)
            else:
                return f"[{operand.value}]"

        def spill_register(reg):
            # Dont forget to update address descriptor after using this function
            operand = self.register_descriptors[reg]
            ts, ss = self.get_type_specifier(operand.type)
            reg_part = self.get_register_part(reg, ss)
            address = get_operand_address(operand)
            self.text_section += f"mov {ss} {address}, {reg_part}\n"
            # self.register_descriptors[reg] = None # Not needed as we will overwrite it right after
            self.address_descriptors[operand] = address

        def load_operand_into_register(operand, reg):
            ts, ss = self.get_type_specifier(operand.type)
            address = get_operand_address(operand)
            op = "mov" if operand.type == "int" else "movzx"
            self.text_section += f"{op} {reg}, {ss} {address}\n"
            self.register_descriptors[reg] = operand
            self.address_descriptors[operand] = reg

        def find_reg_to_free():
            live_set = self.live[self.counter]
            for reg in self.registers:
                if self.register_descriptors[reg] not in live_set:
                    return reg, False
            for reg in self.registers:
                if isinstance(self.register_descriptors[reg], Var):
                    return reg, True
            return self.registers[0], True

        if (
            operand in self.address_descriptors
            and self.address_descriptors[operand] in self.registers
        ):
            return self.address_descriptors[operand]

        for reg in self.registers:
            if self.register_descriptors[reg] is None:
                load_operand_into_register(operand, reg)
                return reg
        reg, should_spill = find_reg_to_free()
        if should_spill:
            spill_register(reg)
        load_operand_into_register(operand, reg)
        return reg

    def when_will_it_die(self, operand):
        # returns the last line where operand is alive
        for i in range(self.counter, self.TAC.line_count):
            if operand not in self.live[i]:
                return i - 1
        return self.TAC.line_count

    def is_alive(self, operand):
        return operand in self.live[self.counter]

    def generate(self):
        for instr in self.TAC.instructions:
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
            self.counter += 1

        runtime_lines = self.runtime_code.split("\n")
        runtime_text = []
        runtime_data = []
        runtime_bss = []
        current_section = "text"

        for line in runtime_lines:
            line = line.strip()
            if line.startswith("section .data"):
                current_section = "data"
                continue
            elif line.startswith("section .bss"):
                current_section = "bss"
                continue
            elif line.startswith("section .text"):
                current_section = "text"
                continue

            if current_section == "data":
                runtime_data.append(line)
            elif current_section == "bss":
                runtime_bss.append(line)
            else:
                runtime_text.append(line)

        final_data = self.data_section
        if runtime_data:
            final_data += "\n".join(runtime_data) + "\n"

        final_bss = self.bss_section
        if runtime_bss:
            final_bss += "\n".join(runtime_bss) + "\n"

        final_text = self.text_section + self.exit_code
        if runtime_text:
            final_text += "\n".join(runtime_text) + "\n"

        return final_data + final_bss + final_text

    def handle_def(self, instr):
        ts, ss = self.get_type_specifier(instr.result.type)
        if instr.result.storage == "global":
            if instr.arg1 is not None:
                self.data_section += f"{instr.result.name} {ts} {instr.arg1.value}\n"
            else:
                self.data_section += f"{instr.result.name} {ts} 0\n"
        else:  # local
            if instr.arg1 is not None and instr.result not in self.never_alive_vars:
                location = self.get_var_location(instr.result)
                self.text_section += f"mov {ss} {location}, {instr.arg1.value}\n"
                self.address_descriptors[instr.result] = location

    def handle_eq(self, instr):
        ts, ss = self.get_type_specifier(instr.result.type)
        location = self.get_var_location(instr.result)
        if isinstance(instr.arg1, Const):
            self.text_section += f"mov {ss} {location}, {instr.arg1.value}\n"
            self.address_descriptors[instr.result] = location
        elif isinstance(instr.arg1, (TempVar, Var)):
            reg = self.get_register(instr.arg1)
            reg_part = self.get_register_part(reg, ss)
            self.text_section += f"mov {ss} {location}, {reg_part}\n"
            self.address_descriptors[instr.result] = location

    def handle_binary_op(self, instr):
        first_register = self.get_register(instr.arg1)
        life = self.when_will_it_die(instr.arg1) - self.counter
        if life != 0:
            if isinstance(instr.arg1, TempVar):
                self.text_section += (
                    f"mov {self.stack_map[instr.arg1]}, {first_register}\n"
                )
                self.address_descriptors[instr.arg1] = self.stack_map[instr.arg1]
            if isinstance(instr.arg1, Var):
                location = self.get_var_location(instr.arg1)
                self.text_section += f"mov {location}, {first_register}\n"
                self.address_descriptors[instr.arg1] = location
        if isinstance(instr.arg2, Const):
            second_register = instr.arg2.value
        elif self.address_descriptors[instr.arg2]:  # memory to reg operations allowed
            second_register = self.address_descriptors[instr.arg2]
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

        result_register = self.get_register(instr.result)
        result_register_part = self.get_register_part(result_register, "byte")
        self.text_section += f"xor {result_register}, {result_register}\n"

        self.text_section += f"cmp {first_register}, {second_register}\n"

        if instr.op == "<":
            self.text_section += f"setl {result_register_part}\n"
        elif instr.op == "<=":
            self.text_section += f"setle {result_register_part}\n"
        elif instr.op == ">":
            self.text_section += f"setg {result_register_part}\n"
        elif instr.op == ">=":
            self.text_section += f"setge {result_register_part}\n"
        elif instr.op == "==":
            self.text_section += f"sete {result_register_part}\n"
        elif instr.op == "!=":
            self.text_section += f"setne {result_register_part}\n"
        # self.text_section += f"movzx {result_register}, {result_register_part}\n" # Not needed as we zeroed the register at the start. this might cause issues afterwards so i wont delete this line
        self.address_descriptors[instr.result] = result_register
        self.register_descriptors[result_register] = instr.result

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
        if isinstance(instr.arg1, Const):
            regs = ["eax", "ebx", "ecx", "edx"]
            pushed_regs = []
            alive = {"eax": False, "ebx": False, "ecx": False, "edx": False}
            for reg in regs:
                alive[reg] = self.register_descriptors[reg] in self.live[self.counter]
                if self.register_descriptors[reg] and alive[reg]:
                    self.text_section += f"push {reg}\n"
                    pushed_regs.append(reg)

            self.text_section += f"mov eax, {instr.arg1.value}\n"

            if instr.arg1.type == "bool":
                self.text_section += f"call print_boolean\n"
            else:
                self.text_section += f"call print_integer\n"

            for reg in reversed(pushed_regs):
                self.text_section += f"pop {reg}\n"
        else:
            reg_to_print = self.get_register(instr.arg1)
            regs = ["eax", "ebx", "ecx", "edx"]
            pushed_regs = []
            alive = {"eax": False, "ebx": False, "ecx": False, "edx": False}
            for reg in regs:
                alive[reg] = self.register_descriptors[reg] in self.live[self.counter]
                if (
                    reg != reg_to_print
                    and self.register_descriptors[reg]
                    and alive[reg]
                ):
                    self.text_section += f"push {reg}\n"
                    pushed_regs.append(reg)
            if reg_to_print != "eax":
                self.text_section += f"mov eax, {reg_to_print}\n"
            if self.register_descriptors[reg_to_print] in self.live[self.counter]:
                self.text_section += f"push eax\n"
                pushed_regs = pushed_regs + ["eax"]

            if instr.arg1.type == "bool":
                self.text_section += f"call print_boolean\n"
            else:
                self.text_section += f"call print_integer\n"

            for reg in reversed(pushed_regs):
                self.text_section += f"pop {reg}\n"

        newline_pushed_regs = []
        for reg in regs:
            if (
                self.register_descriptors[reg]
                and self.register_descriptors[reg] in self.live[self.counter]
            ):
                self.text_section += f"push {reg}\n"
                newline_pushed_regs.append(reg)

        self.text_section += (
            f"mov eax, 4\nmov ebx, 1\nmov ecx, newline\nmov edx, 1\nint 0x80\n"
        )

        for reg in reversed(newline_pushed_regs):
            self.text_section += f"pop {reg}\n"

        for reg in regs:
            if not alive[reg]:
                if self.register_descriptors[reg]:
                    var_to_clear = self.register_descriptors[reg]
                    if var_to_clear in self.address_descriptors and self.address_descriptors[var_to_clear] == reg:
                        del self.address_descriptors[var_to_clear]
                self.register_descriptors[reg] = None

    def handle_division(self, first_register, second_register):
        eax_pushed = False
        edx_pushed = False
        if first_register == "eax" and second_register == "edx":
            self.text_section += "mov edi, edx\n"
            self.text_section += "cdq\n"
            self.text_section += "idiv edi\n"
            self.text_section += "mov edx, edi\n"
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
