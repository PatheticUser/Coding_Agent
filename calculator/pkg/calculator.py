# calculator.py


class Calculator:
    def __init__(self):
        self.operators = {
            "+": lambda a, b: a + b,
            "-": lambda a, b: a - b,
            "*": lambda a, b: a * b,
            "/": lambda a, b: self._divide(a, b), # Modified to use a helper method for division
        }
        self.precedence = {
            "+": 1,
            "-": 1,
            "*": 2,
            "/": 2,
            "(": 0, # Parentheses have the lowest precedence on the stack
        }

    def _divide(self, a, b):
        if b == 0:
            raise ValueError("division by zero")
        return a / b

    def evaluate(self, expression):
        if not expression or expression.isspace():
            return None
        # Modified to tokenize expression to handle parentheses and multi-digit numbers
        tokens = self._tokenize(expression)
        return self._evaluate_infix(tokens)

    def _tokenize(self, expression):
        # This is a basic tokenizer, a more robust solution might use regex
        # It separates numbers, operators, and parentheses
        import re
        return [token for token in re.findall(r'(\d+\.?\d*|\S)', expression) if token.strip()]

    def _evaluate_infix(self, tokens):
        values = []
        operators = []

        for token in tokens:
            if token == '(':
                operators.append(token)
            elif token == ')':
                while operators and operators[-1] != '(':
                    self._apply_operator(operators, values)
                if not operators or operators[-1] != '(':
                    raise ValueError("mismatched parentheses")
                operators.pop() # Pop the '('
            elif token in self.operators:
                while (
                    operators
                    and operators[-1] != '('
                    and self.precedence.get(operators[-1], 0) >= self.precedence.get(token, 0)
                ):
                    self._apply_operator(operators, values)
                operators.append(token)
            else:
                try:
                    values.append(float(token))
                except ValueError:
                    raise ValueError(f"invalid token: {token}")

        while operators:
            if operators[-1] == '(':
                raise ValueError("mismatched parentheses")
            self._apply_operator(operators, values)

        if len(values) != 1:
            raise ValueError("invalid expression")

        return values[0]

    def _apply_operator(self, operators, values):
        if not operators:
            return

        operator = operators.pop()
        if len(values) < 2:
            raise ValueError(f"not enough operands for operator {operator}")

        b = values.pop()
        a = values.pop()
        values.append(self.operators[operator](a, b))
