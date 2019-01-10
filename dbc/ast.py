

class Programm:
    def __init__(self, statements):
        self.statements = statements


class Print:
    def __init__(self, expressions):
        self.expressions = expressions


class Unary:
    def __init__(self, op, val):
        self.op = op
        self.val = val


class Binary:
    def __init__(self, op, val1, val2):
        self.op = op
        self.val1 = val1
        self.val2 = val2


class Var:
    def __init__(self, name):
        self.name = name


class Const:
    def __init__(self, value):
        self.value = value


class Str:
    def __init__(self, value):
        self.value = value


class Assign:
    def __init__(self, name, value):
        self.name = name
        self.value = value


class If:
    def __init__(self, exp, statements, elsestatements):
        self.exp = exp
        self.statements = statements
        self.elsestatements = elsestatements


class While:
    def __init__(self, exp, statements):
        self.exp = exp
        self.statements = statements


class Input:
    def __init__(self, name):
        self.name = name


class Return:
    def __init__(self, expression):
        self.expression = expression
