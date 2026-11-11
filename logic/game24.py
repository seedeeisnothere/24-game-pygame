from fractions import Fraction

OPS = ("+", "-", "*", "/")


# Apply one operator to a and b. Returns None for divide by zero.
def apply_op(a, op, b):
    if op == "+":
        return a + b
    if op == "-":
        return a - b
    if op == "*":
        return a * b
    if op == "/":
        return None if b == 0 else a / b
    raise ValueError(f"unknown operator: {op}")


# Recursive solver: can these numbers make the target (24)?
# Fractions keep division exact, e.g. 8 / (3 - 8/3) = 24.
def can_make(values, target=24):
    values = [Fraction(v) for v in values]
    # Base case: one number left, check if it is the target
    if len(values) == 1:
        return values[0] == target
    # Try every ordered pair (i, j) with every operator
    for i in range(len(values)):
        for j in range(len(values)):
            if i == j:
                continue
            rest = [v for k, v in enumerate(values) if k not in (i, j)]
            for op in OPS:
                result = apply_op(values[i], op, values[j])
                # Replace the pair with its result and solve the smaller list
                if result is not None and can_make(rest + [result], target):
                    return True
    return False


# The state of one 24 puzzle while the player clicks numbers and operators.
# A used number becomes None; the result goes into the second number's slot.
class Game24:
    def __init__(self, numbers, target=24):
        self.start = [Fraction(n) for n in numbers]
        self.target = target
        self.reset()

    # Go back to the starting numbers with nothing selected.
    def reset(self):
        self.values = list(self.start)
        self.first = None   # index of the first selected number
        self.op = None      # selected operator

    # Handle a click on the number at index i.
    def click_number(self, i):
        if self.values[i] is None:
            return
        if self.first is None:
            self.first = i
        elif self.op is None:
            # No operator yet: click same number to deselect, else switch
            self.first = None if i == self.first else i
        elif i != self.first:
            result = apply_op(self.values[self.first], self.op, self.values[i])
            if result is None:
                # Divide by zero: cancel the operator, keep the numbers
                self.op = None
                return
            self.values[i] = result
            self.values[self.first] = None
            # The result stays selected so the player can keep going
            self.first = i
            self.op = None

    # Select an operator (only after a number is selected).
    def click_op(self, op):
        if self.first is not None:
            self.op = op

    # Numbers that have not been used up yet.
    def remaining(self):
        return [v for v in self.values if v is not None]

    # True when one number is left and it equals the target.
    @property
    def solved(self):
        left = self.remaining()
        return len(left) == 1 and left[0] == self.target

    # True when one number is left and it is not the target.
    @property
    def failed(self):
        left = self.remaining()
        return len(left) == 1 and left[0] != self.target
