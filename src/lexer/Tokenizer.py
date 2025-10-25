from .RegexEngine import RegexEngine


class TokenMatcher:
    def __init__(self):
        self.patterns = []

    def add_pattern(self, name, regex_str, priority=0):
        engine = RegexEngine(regex_str)
        self.patterns.append((priority, name, engine))
        # Sort by priority (higher priority first)
        self.patterns.sort(key=lambda x: -x[0])

    def match(self, string):
        longest_match = None
        longest_length = 0
        token_type = None

        for priority, name, engine in self.patterns:
            matched, length = engine.find_longest_match(string)
            if matched and length > longest_length:
                longest_match = matched
                longest_length = length
                token_type = name

        return token_type, longest_match, longest_length


class Tokenizer:
    def __init__(self):
        self.matcher = TokenMatcher()
        self.skip_patterns = []

    def add_pattern(self, name, regex_str, priority=0):
        self.matcher.add_pattern(name, regex_str, priority)
        return self

    def add_skip_pattern(self, regex_str):
        self.skip_patterns.append(RegexEngine(regex_str))
        return self

    def tokenize(self, input_str):
        tokens = []
        i = 0
        row = 1
        col = 1

        while i < len(input_str):
            skipped = False
            for skip_engine in self.skip_patterns:
                matched, length = skip_engine.find_longest_match(input_str[i:])
                if matched:
                    for char in matched:
                        if char == "\n":
                            row += 1
                            col = 1
                        else:
                            if char == "\t":
                                col += 4
                            else:
                                col += 1
                    i += length
                    skipped = True
                    break

            if skipped:
                continue

            token_type, matched, length = self.matcher.match(input_str[i:])

            if token_type:
                tokens.append((token_type, matched, row, col))
                col += length
                i += length
            else:
                raise SyntaxError(
                    f"Invalid character: {input_str[i]} at row {row}, col {col}"
                )

        return tokens
