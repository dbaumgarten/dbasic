""" This module contains the definitions for all the possible not of the AST(Abstract-Syntax-Tree).
    The AST is created by the parser (from a stream of tokens). All future tasks (semantic checks, code-generation etc.) will happen on this Tree

    Whenever a node has a field value (unless specifically stated otherwise) this is not a fixed 'value' but mostly another Node that represents this value.
    Example: Binary operations can have different things as value (const,variables,other binary or unary operations etc.).

    Nodes that represent a value are called 'expressions'.
    Nodes that do something with a value (like return it) are called 'statements'.
    Nodes that define something ("there is function called test doing the following") are called 'definitions' or 'declarations'
    """


class Programm:
    """ The root node of the whole Programm"""

    def __init__(self, parts):
        """ A list of parts. A part can be a FUncDef or a GlobalDef"""
        self.parts = parts
        """ This field is not populated by the parser but later by the VariableChecker.
        It contains all string-constants used in the programm.
        It is a dict with the constant's value as string and a unique identifier for this constant value as value."""
        self.constants = None
        """ This field is not populated by the parser but later by the VariableChecker.
        It contains all global variables used in the programm.
        It is a dict with the variables name as key and the initial value as value"""
        self.globalvars = None


class Unary:
    """ An unary operation(-, !)as part of an expression"""

    def __init__(self, op, val):
        """ The operation to perform(as string)"""
        self.op = op
        """ The value(an expression) to perform this operation on"""
        self.val = val


class Binary:
    """ A binary operation (+, -, *, ==, != etc.)as part of an expression"""

    def __init__(self, op, val1, val2):
        """ The operation to perform(as string)"""
        self.op = op
        """ The left value of the operation """
        self.val1 = val1
        """ The right value of the operation """
        self.val2 = val2


class Var:
    """ A variable is referenced. (Something wants to use the value of a variable)"""

    def __init__(self, name):
        """ The name of the referenced variable"""
        self.name = name


class Const:
    """ An integer constant is referenced. (Something wants to use the value of a constant)"""

    def __init__(self, value):
        """ The value of the constant as int"""
        self.value = value


class Str:
    """ An stringconstant is referenced. (Something wants to use the value of a constant)"""

    def __init__(self, value):
        """ The value of the constant as string"""
        self.value = value


class Assign:
    """ A value is assigned to a variable """

    def __init__(self, name, value):
        """ The name of the variable """
        self.name = name
        """ The value to assign """
        self.value = value


class If:
    """ An if statement"""

    def __init__(self, exp, statements, elsestatements):
        """ The condition to evaluate for this if"""
        self.exp = exp
        """ A list of statements to execute if the condition is True"""
        self.statements = statements
        """ A list of statements to execute if the condition is False"""
        self.elsestatements = elsestatements


class While:
    """ A while statement """

    def __init__(self, exp, statements):
        """ The condition to evaluate for this while"""
        self.exp = exp
        """ A list of statements that will be executed until the condition is False"""
        self.statements = statements


class Return:
    """ A function wants to return a value"""

    def __init__(self, expression):
        """ The value to return """
        self.expression = expression


class Call:
    """ A function is called"""

    def __init__(self, name, args, isStatement=False):
        """ The name of the function to call"""
        self.name = name
        """ A list of values(expressions) used as arguments to the function """
        self.args = args
        """If true: This call was a stand-alone statement(and not part of an expression). The C-generator needs to know this to append a ';'"""
        self.isStatement = isStatement


class FuncDef:
    """ The definiton of a function """

    def __init__(self, name, args, statements):
        """ The name of the defined function """
        self.name = name
        """ A list of names(string) of aguments to this function"""
        self.args = args
        """ A list of statements that are the body for this function"""
        self.statements = statements
        """ This field is not populated by the parser but later by the VariableChecker.
        It contains all local variables (including arguments) used in this function.
        It is a dict with the variable's name as key and the initial value as value"""
        self.localvars = None


class GlobalDef:
    """ The definiton of a global variable"""

    def __init__(self, name, value):
        """ The name of the variable """
        self.name = name
        """ The initial value of the variable"""
        self.value = value


class LocalDef:
    """ The definiton of a local(inside of a function) variable"""

    def __init__(self, name, value):
        """ The name of the variable """
        self.name = name
        """ The initial value of the variable"""
        self.value = value
