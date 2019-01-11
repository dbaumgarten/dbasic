

class Programm:
    def __init__(self, parts):
        self.parts = parts


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


class Return:
    def __init__(self, expression):
        self.expression = expression


class Call:
    def __init__(self, name, args, isStatement=False):
        self.name = name
        self.args = args
        # This call was a stand-alone statement (and not part of an expression). The C-generator needs to know this to append a ';'
        self.isStatement = isStatement


class FuncDef:
    def __init__(self, name, args, statements):
        self.name = name
        self.args = args
        self.statements = statements


class GlobalDef:
    def __init__(self, name, value):
        self.name = name
        self.value = value


class LocalDef:
    def __init__(self, name, value):
        self.name = name
        self.value = value
