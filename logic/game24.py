from fractions import Fraction

OPS = ("+", "-", "*", "/")


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


def can_make(values, target=24):
    values = [Fraction(v) for v in values]
    if len(values) == 1:
        return values[0] == target
    for i in range(len(values)):
        for j in range(len(values)):
            if i == j:
                continue
            rest = [v for k, v in enumerate(values) if k not in (i, j)]
            for op in OPS:
                result = apply_op(values[i], op, values[j])
                if result is not None and can_make(rest + [result], target):
                    return True
    return False


class Game24:

    def __init__(self, numbers, target=24):
        self.start = [Fraction(n) for n in numbers]
        self.target = target
        self.reset()

    def reset(self):
        self.values = list(self.start)
        self.first = None
        self.op = None

    def click_number(self, i):
        if self.values[i] is None:
            return
        if self.first is None:
            self.first = i
        elif self.op is None:
            self.first = None if i == self.first else i
        elif i != self.first:
            result = apply_op(self.values[self.first], self.op, self.values[i])
            if result is None:
                self.op = None
                return
            self.values[i] = result
            self.values[self.first] = None
            self.first = None
            self.op = None

    def click_op(self, op):
        if self.first is not None:
            self.op = op

    def remaining(self):
        return [v for v in self.values if v is not None]

    @property
    def solved(self):
        left = self.remaining()
        return len(left) == 1 and left[0] == self.target

    @property
    def failed(self):
        left = self.remaining()
        return len(left) == 1 and left[0] != self.target