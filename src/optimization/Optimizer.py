from codegen.TACGenerator import *


class Optimizer:
    def __init__(self):
        pass

    def optimize(self, TAC):
        blocks = self.get_blocks(TAC.instructions)
        for block in blocks:
            changed = True
            while changed:
                f = self.constant_folding(block)
                p = self.constant_propagation(block)
                changed = f or p
        TAC.instructions = [instr for block in blocks for instr in block]
        TAC.line_count = len(TAC.instructions)

    def get_blocks(self, instructions):
        leader_indices = set()

        if instructions:
            leader_indices.add(0)

        label_map = {
            instr.result: i
            for i, instr in enumerate(instructions)
            if instr.op == "label"
        }

        for i, instr in enumerate(instructions):
            if instr.op in ["goto", "if"]:
                if instr.result in label_map:
                    leader_indices.add(label_map[instr.result])

                if i + 1 < len(instructions):
                    leader_indices.add(i + 1)

        sorted_leaders = sorted(list(leader_indices))

        blocks = []
        for i, start_index in enumerate(sorted_leaders):
            if i + 1 < len(sorted_leaders):
                end_index = sorted_leaders[i + 1]
            else:
                end_index = len(instructions)

            block = instructions[start_index:end_index]
            blocks.append(block)

        return blocks

    def constant_folding(self, instrs):
        def spread_constants(instrs, constant_map):
            changed = False
            for instr in instrs:
                if instr.arg1 in constant_map:
                    changed = True
                    instr.arg1 = Const(constant_map[instr.arg1], type=instr.arg1.type)
                if instr.arg2 in constant_map:
                    changed = True
                    instr.arg2 = Const(constant_map[instr.arg2], type=instr.arg2.type)
            return changed

        temp_map = {}
        changed = False

        for instr in instrs:
            if instr.op in [
                "+",
                "-",
                "*",
                "/",
                "|",
                "&",
                "<",
                "<=",
                ">",
                ">=",
                "==",
                "!=",
            ]:
                if (
                    isinstance(instr.arg1, Const)
                    and isinstance(instr.arg2, Const)
                    and isinstance(instr.result, TempVar)
                ):
                    changed = True
                    if instr.op == "+":
                        constant = instr.arg1.value + instr.arg2.value
                    elif instr.op == "-":
                        constant = instr.arg1.value - instr.arg2.value
                    elif instr.op == "*":
                        constant = instr.arg1.value * instr.arg2.value
                    elif instr.op == "/":
                        constant = instr.arg1.value / instr.arg2.value
                    elif instr.op == "&":
                        constant = instr.arg1.value & instr.arg2.value
                    elif instr.op == "|":
                        constant = instr.arg1.value | instr.arg2.value
                    elif instr.op == "<":
                        constant = 1 if int(instr.arg1.value < instr.arg2.value) else 0
                    elif instr.op == "<=":
                        constant = 1 if int(instr.arg1.value <= instr.arg2.value) else 0
                    elif instr.op == ">":
                        constant = 1 if int(instr.arg1.value > instr.arg2.value) else 0
                    elif instr.op == ">=":
                        constant = 1 if int(instr.arg1.value >= instr.arg2.value) else 0
                    elif instr.op == "==":
                        constant = 1 if int(instr.arg1.value == instr.arg2.value) else 0
                    elif instr.op == "!=":
                        constant = 1 if int(instr.arg1.value != instr.arg2.value) else 0
                    temp_map[instr.result] = constant
                    instrs.remove(instr)

        c = spread_constants(instrs, temp_map)
        return changed or c

    def constant_propagation(self, instrs):
        def spread_vars(instrs, var_map, when_to_del):
            changed = False
            for i, instr in enumerate(instrs):
                if instr.op == "print":
                    continue

                if instr.arg1 in var_map and (
                    i <= when_to_del[instr.arg1]
                    if when_to_del.get(instr.arg1)
                    else True
                ):

                    changed = True
                    instr.arg1 = Const(var_map[instr.arg1], type=instr.arg1.type)
                if instr.arg2 in var_map and (
                    i <= when_to_del[instr.arg2]
                    if when_to_del.get(instr.arg2)
                    else True
                ):
                    changed = True
                    instr.arg2 = Const(var_map[instr.arg2], type=instr.arg2.type)
            return changed

        var_map = {}
        when_to_del = {}
        for i, instr in enumerate(instrs):
            if instr.op in ["eq", "def"] and isinstance(instr.result, Var):
                if isinstance(instr.arg1, Const):
                    var_map[instr.result] = instr.arg1.value
                elif isinstance(instr.arg1, Var) and instr.arg1 in var_map:
                    var_map[instr.result] = var_map[instr.arg1]
                else:
                    if instr.result in var_map:
                        when_to_del[instr.result] = i

        c = spread_vars(instrs, var_map, when_to_del)
        return c
