class TokenHelper:
    def __init__(self, tokens):
        self.tokens = tokens
        self.position = 0
        self.variables = []

    def peek(self):
        if self.position < len(self.tokens):
            return self.tokens[self.position]
        return None

    def check_next_var(self):
        if self.position >= len(self.tokens):
            raise SyntaxError(f"Error, expected 'IDENTIFIER' but found none")
        token = self.tokens[self.position]
        if token[1] not in self.variables:
            raise SyntaxError(
                f"Error, '{token[1]}' is not a variable at row {token[2]}, column {token[3]}"
            )
        self.position += 1
        return token

    def consume(self, expected_value=None, expected_type=None):
        if self.position >= len(self.tokens):
            raise SyntaxError(f"Error, expected '{expected_value}' but found none")
        token = self.tokens[self.position]
        if expected_value and token[1] != expected_value:
            raise SyntaxError(
                f"Error, expected '{expected_value}' but found '{token[1]}' at row {token[2]}, column {token[3]}"
            )
        if expected_type and token[0] != expected_type:
            raise SyntaxError(
                f"Error, expected {expected_type} but found {token[0]} at row {token[2]}, column {token[3]}"
            )
        self.position += 1
        return token

    def consume_in(self, valid_values, expected_type=None):
        if self.position >= len(self.tokens):
            raise SyntaxError(f"Error, expected one of {valid_values} but found none")
        token = self.tokens[self.position]
        if token[1] not in valid_values:
            raise SyntaxError(
                f"Error, expected one of {valid_values} but found '{token[1]}' at row {token[2]}, column {token[3]}"
            )
        if expected_type and token[0] != expected_type:
            raise SyntaxError(
                f"Error, expected {expected_type} but found {token[0]} at row {token[2]}, column {token[3]}"
            )
        self.position += 1
        return token

    def check_without_consuming(self, expected_value=None, expected_type=None):
        if self.position >= len(self.tokens):
            raise SyntaxError(f"Error, expected '{expected_value}' but found none")
        token = self.tokens[self.position]
        if expected_value and token[1] != expected_value:
            raise SyntaxError(
                f"Error, expected '{expected_value}' but found '{token[1]}' at row {token[2]}, column {token[3]}"
            )
        if expected_type and token[0] != expected_type:
            raise SyntaxError(
                f"Error, expected {expected_type} but found {token[0]} at row {token[2]}, column {token[3]}"
            )
        return token

    def check_in_without_consuming(self, valid_values, expected_type=None):
        if self.position >= len(self.tokens):
            raise SyntaxError(f"Error, expected one of {valid_values} but found none")
        token = self.tokens[self.position]
        if token[1] not in valid_values:
            raise SyntaxError(
                f"Error, expected one of {valid_values} but found '{token[1]}' at row {token[2]}, column {token[3]}"
            )
        if expected_type and token[0] != expected_type:
            raise SyntaxError(
                f"Error, expected {expected_type} but found {token[0]} at row {token[2]}, column {token[3]}"
            )
        return token
