import dbc.ast as ast
from dbc.visit import Visitor
from dbc.errors import CheckError
from collections import OrderedDict


class VariableChecker(Visitor):
    """ This class extends Visitor and is responsible for two things:
    - Extracting (global and local) variable and constant declarations and annotating the AST with information about them
    - Checking semantic rules regarding variables. (must be declared before used, can only be declared once etc.)
    """

    def __init__(self):
        """ Contains all global variables declared in the programm and their default values. See ast.Programm"""
        self.globalvars = dict()
        """ Contains all global variables declared in the programm and their types. See ast.Programm"""
        self.globalvartypes = dict()
        """ Contains all local variables and their default values of the function that is currently beeing analysed. Is ordered by declaratin-order. See ast.FuncDef"""
        self.localvars = OrderedDict()
        """ Contains all local variables and their types of the function that is currently beeing analysed."""
        self.localvartypes = OrderedDict()
        """ Contains all string constants declared in the programm. See ast.Programm"""
        self.constants = dict()
        """ Keep a counter of constants to generate unique labels for them"""
        self.constantcounter = 0
        super().__init__()

    def check(self, node):
        """ Main method for the checker. Checks the given programm and annotated it with variable information"""
        return self.visitProgramm(node)

    def visitProgramm(self, node):
        # first visit all global variables
        for glob in node.globaldefs:
            self.visit(glob)
        # then analyse all defined functions
        definedfunctions = set()
        for func in node.funcdefs:
            self.visit(func)
            # can not have two functions with the same name
            if func.name in definedfunctions:
                raise CheckError(
                    "Function {} has previously been defined.".format(func.name), func)
            definedfunctions.add(func.name)

        if not "main" in definedfunctions:
            raise CheckError(
                "Every programm needs to have a function called 'main'", None)

        # annotate the progamm node with information about globals and constants
        node.globalvars = self.globalvars
        node.globalvartypes = self.globalvartypes
        node.constants = self.constants

    def visitVar(self, node):
        # make sure variables are only used AFTER they have been declared
        if node.name not in self.globalvars and node.name not in self.localvars:
            raise CheckError(
                "Variable {} needs to be declared before use".format(node.name), node)

    def visitStr(self, node):
        # take note of all string constants
        self.constants[node.value] = ".Lstr"+str(self.constantcounter)
        self.constantcounter += 1

    def visitAssign(self, node):
        # make sure variables are only used AFTER they have been declared
        if node.name not in self.globalvars and node.name not in self.localvars:
            raise CheckError(
                "Variable {} needs to be declared before assignment".format(node.name), node)
        self.visit(node.value)

    def visitCall(self, node):
        # because of limitations in the code-generator for x86-64 assembler function calls can only take 6 or less arguments
        if len(node.args) > 6:
            raise CheckError(
                "Function-calls can take at most 6 arguments", node)
        for arg in node.args:
            self.visit(arg)

    def visitFuncdef(self, node):
        # initialize the localvars dict do en empty dict()
        # all following visitLocaldef() calls will write their variables to this dict
        self.localvars = OrderedDict()
        self.localvartypes = OrderedDict()
        for i, arg in enumerate(node.args):
            self.localvars[arg] = 0
            self.localvartypes[arg] = node.argtypes[i]
        for statement in node.statements:
            self.visit(statement)
        # annotate the funcdef node wicth information about local variables
        node.localvars = self.localvars
        node.localvartypes = self.localvartypes
        # this check does not really belong here as it is not variable relatet
        # but at the moment this is the only checker class and the check is to important to leave out
        if type(node.statements[-1]) != ast.Return:
            raise CheckError(
                "Functions must end with a return-statement", node)

    def visitGlobaldef(self, node):
        # make sure global variables are only declared once
        if node.name in self.globalvars:
            raise CheckError(
                "Global variable {} has already been declared".format(node.name), node)
        # globals can only be initialized using constants. Check it.
        if type(node.value) != ast.Const:
            raise CheckError(
                "Global variables can only be initialized using constants", node)
        # enter the global variable and it's type in the globalvar list
        self.globalvars[node.name] = node.value.value
        self.globalvartypes[node.name] = node.type

    def visitLocaldef(self, node):
        # make sure global variables are only declared once per function
        if node.name in self.globalvars:
            raise CheckError(
                "Local variable {} has already been declared".format(node.name), node)
        # enter the local variable and it's type in the localvar list forthe current function
        self.localvars[node.name] = node.value
        self.localvartypes[node.name] = node.type
