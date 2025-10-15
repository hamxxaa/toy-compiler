# <regex>   ::= <union>
# <union>   ::= <concat> ("|" <concat>)*
# <concat>  ::= <factor>+
# <factor>  ::= <base> ("*" | "+" | "?")*
# <base>    ::= <char> | "[" <char> "-" <char> "]" | "(" <regex> ")"


class CharNode:
    def __init__(self, char):
        self.char = char


class CharSetNode:
    def __init__(self, charset):
        self.charset = set(charset)


class ConcatNode:
    def __init__(self, left, right):
        self.left = left
        self.right = right


class StarNode:
    def __init__(self, left):
        self.left = left


class UnionNode:
    def __init__(self, left, right):
        self.left = left
        self.right = right


class RegexParser:
    def __init__(self, regex):
        self.regex = regex
        self.pos = 0

    def parse(self):
        return self.parse_union()

    def parse_union(self):
        left = self.parse_concat()
        while self.peek() == "|":
            self.consume("|")
            right = self.parse_concat()
            left = UnionNode(left, right)
        return left

    def parse_concat(self):
        node = self.parse_factor()
        while self.peek() not in (None, "|", ")"):
            right = self.parse_factor()
            node = ConcatNode(node, right)
        return node

    def parse_factor(self):
        node = self.parse_base()
        while self.peek() in ("*", "+", "?"):
            operator = self.consume()
            kind = ""
            if operator == "*":
                node = StarNode(node)
            elif operator == "+":
                node = ConcatNode(node, StarNode(node))
            elif operator == "?":
                node = UnionNode(node, CharNode(""))
            else:
                raise SyntaxError(f"Unknown quantifier: {operator}")
        return node

    def parse_base(self):
        if self.peek() == "(":
            self.consume("(")
            node = self.parse_union()
            self.consume(")")
            return node
        elif self.peek() == "[":
            return self.parse_charset()
        else:
            char = self.consume()
            if char == "\\":
                char = self.control_escape()
            return CharNode(char)

    def parse_charset(self):
        self.consume("[")
        charset = []
        while self.peek() not in ("]", None):
            if self.peek() == "-":
                self.consume("-")
                if not charset:
                    raise SyntaxError("Invalid character range in charset")
                start = charset[0]
                end = self.consume()
                charset.extend(chr(c) for c in range(ord(start), ord(end) + 1))
            else:
                charset.append(self.consume())
        self.consume("]")
        return CharSetNode(charset)

    def control_escape(self):
        literal = self.consume()
        if literal in ("(", "\\", ")", "+", "*", "?","|", "[", "]"):
            return literal
        else:
            raise SyntaxError(f"Unknown escape sequence: \\{literal}")

    def peek(self):
        return self.regex[self.pos] if self.pos < len(self.regex) else None

    def consume(self, target=None):
        if self.pos >= len(self.regex):
            raise ValueError("Unexpected end")
        ch = self.regex[self.pos]
        if target and ch != target:
            raise ValueError(f"Expected {target}, got {ch}")
        self.pos += 1
        return ch


    def printAST(self, ast, indent=0):
        # use for only debug purposes
        if ast is None:
            return
        prefix = " " * indent
        if isinstance(ast, CharNode):
            print(f"{prefix}CharNode({ast.char})")
        elif isinstance(ast, CharSetNode):
            print(f"{prefix}CharSetNode({''.join(sorted(ast.charset))})")
        elif isinstance(ast, ConcatNode):
            print(f"{prefix}ConcatNode(")
            self.printAST(None, ast.left, indent + 2)
            self.printAST(None, ast.right, indent + 2)
            print(f"{prefix})")
        elif isinstance(ast, StarNode):
            print(f"{prefix}StarNode(")
            self.printAST(None, ast.left, indent + 2)
            print(f"{prefix})")
        elif isinstance(ast, UnionNode):
            print(f"{prefix}UnionNode(")
            self.printAST(None, ast.left, indent + 2)
            self.printAST(None, ast.right, indent + 2)
            print(f"{prefix})")
        else:
            raise ValueError("Unknown AST node type")


class State:
    def __init__(self):
        self.transitions = {}  # char -> set of states
        self.is_final = False


class NFA:
    def __init__(self, start, end):
        self.start = start
        self.end = end


class ThompsonConstruction:
    def __init__(self, ast):
        self.ast = ast

    def createCharNFA(self, charnode):
        start = State()
        end = State()
        start.transitions.setdefault("".join(charnode.char), set()).add(end)
        return NFA(start, end)

    def createCharSetNFA(self, charsetnode):
        start = State()
        end = State()
        for char in charsetnode.charset:
            start.transitions.setdefault(char, set()).add(end)
        return NFA(start, end)

    def createConcatNFA(self, concatnode):
        left_nfa = self.build(concatnode.left)
        right_nfa = self.build(concatnode.right)
        left_nfa.end.transitions.setdefault("", set()).add(right_nfa.start)
        return NFA(left_nfa.start, right_nfa.end)

    def createUnionNFA(self, unionnode):
        start = State()
        end = State()
        left_nfa = self.build(unionnode.left)
        right_nfa = self.build(unionnode.right)
        start.transitions.setdefault("", set()).add(left_nfa.start)
        start.transitions.setdefault("", set()).add(right_nfa.start)
        left_nfa.end.transitions.setdefault("", set()).add(end)
        right_nfa.end.transitions.setdefault("", set()).add(end)
        return NFA(start, end)

    def createStarNFA(self, starnode):
        start = State()
        end = State()
        mid = self.build(starnode.left)
        start.transitions.setdefault("", set()).add(end)
        start.transitions.setdefault("", set()).add(mid.start)
        mid.end.transitions.setdefault("", set()).add(end)
        mid.end.transitions.setdefault("", set()).add(mid.start)
        return NFA(start, end)


    def build(self, ast=None):
        if ast is None:
            ast = self.ast
        if isinstance(ast, CharNode):
            return self.createCharNFA(ast)
        elif isinstance(ast, CharSetNode):
            return self.createCharSetNFA(ast)
        elif isinstance(ast, ConcatNode):
            return self.createConcatNFA(ast)
        elif isinstance(ast, UnionNode):
            return self.createUnionNFA(ast)
        elif isinstance(ast, StarNode):
            return self.createStarNFA(ast)

    def print_nfa(self, nfa):
        # Assign unique IDs to states for printing
        state_ids = {}
        def assign_ids(state, next_id=[0]):
            if state not in state_ids:
                state_ids[state] = next_id[0]
                next_id[0] += 1
                for chars, states in state.transitions.items():
                    for s in states:
                        assign_ids(s, next_id)
        assign_ids(nfa.start)

        # Print states and transitions
        printed = set()
        def print_state(state):
            if state in printed:
                return
            printed.add(state)
            sid = state_ids[state]
            final = " (final)" if state.is_final or state is nfa.end else ""
            print(f"State {sid}{final}:")
            for chars, states in state.transitions.items():
                for s in states:
                    target_id = state_ids[s]
                    label = chars if chars != "" else "ε"
                    print(f"  --{label}--> State {target_id}")
            for states in state.transitions.values():
                for s in states:
                    print_state(s)
        print_state(nfa.start)

class NFAExecutor:
    def __init__(self, nfa):
        self.nfa = nfa

    def epsilon_closure(self, states):
        stack = list(states)
        closure = set(states)
        while stack:
            state = stack.pop()
            for next_state in state.transitions.get("", []):
                if next_state not in closure:
                    closure.add(next_state)
                    stack.append(next_state)
        return closure

    def move(self, states, char):
        next_states = set()
        for state in states:
            for next_state in state.transitions.get(char, []):
                next_states.add(next_state)
        return next_states

    def accepts(self, string):
        current_states = self.epsilon_closure({self.nfa.start})
        for char in string:
            current_states = self.epsilon_closure(self.move(current_states, char))
        if any(state.is_final or state is self.nfa.end for state in current_states):
            return string
        return None
    
    def find_longest_match(self, string):
        current_states = self.epsilon_closure({self.nfa.start})
        last_match_pos = -1
        
        for i, char in enumerate(string):
            current_states = self.epsilon_closure(self.move(current_states, char))
            if not current_states:
                break
            if any(state.is_final or state is self.nfa.end for state in current_states):
                last_match_pos = i
        
        if last_match_pos >= 0:
            return string[:last_match_pos + 1], last_match_pos + 1
        return None, 0


class RegexEngine:
    def __init__(self, regex):
        self.regex = regex
        self.parser = RegexParser(regex)
        self.ast = self.parser.parse()
        self.thompson = ThompsonConstruction(self.ast)
        self.nfa = self.thompson.build()
        self.executor = NFAExecutor(self.nfa)
        self.nfa.end.is_final = True

    def check_full_match(self, string):
        return self.executor.accepts(string)

    def find_longest_match(self, string):
        return self.executor.find_longest_match(string)