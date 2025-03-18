class CodeGenerator:
    def __init__(self):
        self.available_registers = [
            "eax",
            "ebx",
            "ecx",
            "edx",
            "edi",
        ]  # esi reserved for stack management
        self.used_registers = set()
        self.outer_stack = []
        self.stack_size = 0
        self.data = ""
        self.code = ""
        self.label_count = 0

    def get_free_register(self):
        for register in self.available_registers:
            if register not in self.used_registers:
                self.used_registers.add(register)
                return register
        return None

    def load_value_to(self, val=None, var=None):
        register = self.get_free_register()
        if register:
            if val:
                self.code += f"mov {register}, {str(val)}\n"
                self.outer_stack.append([register, val])
                self.used_registers.add(register)
            else:
                self.code += f"mov {register}, [{var}]\n"
                self.outer_stack.append([register, var])
                self.used_registers.add(register)

        else:
            if val:
                self.code += f"mov esi, {str(val)}\n"
                self.code += f"push esi\n"
                self.outer_stack.append(["stack", val])
            else:
                self.code += f"mov esi, [{var}]\n"
                self.code += f"push esi\n"
                self.outer_stack.append(["stack", var])
        self.stack_size += 1

    def get_register_from_stack(self):
        if not self.outer_stack:
            raise ValueError("Stack is empty")
        register = self.outer_stack.pop()[0]
        self.stack_size -= 1

        if register == "stack":
            return "esi"
        self.used_registers.remove(register)
        return register

    def apply_binary_operation(self, operation):

        second_register = self.get_register_from_stack()
        first_register = self.get_register_from_stack()

        if first_register == "esi" and second_register == "esi":
            self.code += "pop esi\n"
            self.code += "push eax\n"
            self.code += "mov eax, [esp+4]\n"
            self.code += f"{operation} eax, esi\n"
            self.code += "mov esi, eax\n"
            self.code += "pop eax\n"
            self.code += "mov [esp], esi\n"
            self.outer_stack.append(["stack", None])
            self.stack_size += 1

            return

        self.code += f"{operation} {first_register}, {second_register}\n"
        self.outer_stack.append([first_register, None])
        self.used_registers.add(first_register)
        self.stack_size += 1

    def create_unique_label(self):
        label = f"label{self.label_count}"
        self.label_count += 1
        return label
    
    def jumpIfZero(self, label):
        self.code += f"jz {label}\n"
    
    def jumpIfNotZero(self, label):
        self.code += f"jnz {label}\n"

    def jump(self, label):
        self.code += f"jmp {label}\n"

    def division(self):
        second_register = self.get_register_from_stack()
        first_register = self.get_register_from_stack()

        if first_register == "esi" and second_register == "esi":
            self.code += "pop esi\n"
            self.code += "push eax\n"
            self.code += "push edx\n"
            self.code += "mov eax, [esp+8]\n"
            self.code += "cdq\n"
            self.code += "idiv esi\n"
            self.code += "mov esi, eax\n"
            self.code += "pop edx\n"
            self.code += "pop eax\n"
            self.code += "mov [esp], esi\n"
            self.outer_stack.append(["stack", None])

        elif second_register == "esi" and first_register == "edi":
            self.code += "pop esi\n"
            self.code += "push eax\n"
            self.code += "push edx\n"
            self.code += f"mov eax, edi\n"
            self.code += "cdq\n"
            self.code += "idiv esi\n"
            self.code += "mov esi, eax\n"
            self.code += "pop edx\n"
            self.code += "pop eax\n"
            self.code += "mov edi, esi\n"
            self.used_registers.add("edi")
            self.outer_stack.append(["edi", None])

        elif first_register == "edx":
            self.code += "push eax\n"
            self.code += "mov eax, edx\n"
            self.code += "cdq\n"
            self.code += f"idiv {second_register}\n"
            self.code += "mov edx, eax\n"
            self.code += "pop eax\n"
            self.used_registers.add("edx")
            self.outer_stack.append(["edx", None])

        elif second_register == "edx":
            self.code += "mov edi, eax\n"
            self.code += "mov esi, edx\n"
            self.code += f"mov eax, {first_register}\n"
            self.code += "cdq\n"
            self.code += "idiv esi\n"
            self.code += "mov esi, eax\n"
            self.code += "mov eax, edi\n"
            self.code += f"mov {first_register}, esi\n"
            self.used_registers.add(first_register)
            self.outer_stack.append([first_register, None])

        elif first_register == "eax":
            self.code += "cdq\n"
            self.code += f"idiv {second_register}\n"
            self.used_registers.add("eax")
            self.outer_stack.append(["eax", None])

        else:
            self.code += "mov edi, eax\n"
            self.code += f"mov eax, {first_register}\n"
            self.code += "cdq\n"
            self.code += f"idiv {second_register}\n"
            self.code += f"mov {first_register}, eax\n"
            self.code += "mov eax, edi\n"
            self.used_registers.add(first_register)
            self.outer_stack.append([first_register, None])

    def start_label(self, label):
        self.code += label + ":\n"

    def extend_al_register(self):
        reg = self.get_free_register()
        if reg:
            self.code += f"movzx {reg}, al\n"
            self.used_registers.add(reg)
            self.outer_stack.append([reg, None])
        else:
            self.code += f"movzx esi, al\n"
            self.code += f"push esi\n"
            self.outer_stack.append(["stack", None])

    def prepare_condition_jump(self):
        reg = self.get_register_from_stack()
        if reg == "esi":
            self.code += "pop esi\n"
        self.code += f"test {reg}, {reg}\n"

    def add_to_code(self, code):
        self.code += code

    def print(self, name):
        self.code += f"mov eax, dword [{name}] \nmov dword [num], eax \ncall print_integer \nmov eax, 4 \nmov ebx, 1 \nmov ecx, newline \nmov edx, 1 \nint 0x80\n"

    def define(self, name):
        self.data += name + " dd 0 \n"

    def equalize(self, name):
        reg = self.get_register_from_stack()
        if reg == "esi":
            self.code += "pop esi\n"
        self.code += f"mov [{name}], {reg}\n"
