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
        """ Contains all global variables declared in the programm. See ast.Programm"""
        self.globalvars = dict()
        """ Contains all local variables of the function that is currently beeing analysed. Is ordered by declaratin-order. See ast.FuncDef"""
        self.localvars = OrderedDict()
        """ Contains all string constants declared in the programm. See ast.Programm"""
        self.constants = dict()
        """ Keep a counter of constants to generate unique labels for them"""
        self.constantcounter = 0
        super().__init__()

    def check(self, node):
        """ Main method for the checker. Checks the given programm and annotated it with variable information"""
        return self.visitProgramm(node)

    def visitProgramm(self, node):
        # first find all global variables
        for part in node.parts:
            if type(part) == ast.GlobalDef:
                self.visit(part)
        # then analyse all defined functions
        for part in node.parts:
            if type(part) == ast.FuncDef:
                self.visit(part)
        # annotate the progamm node with information about globals and constants
        node.globalvars = self.globalvars
        node.constants = self.constants

    def visitUnary(self, node):
        self.visit(node.val)

    def visitBinary(self, node):
        self.visit(node.val1)
        self.visit(node.val2)

    def visitVar(self, node):
        # make sure variables are only used AFTER they have been declared
        if node.name not in self.globalvars and node.name not in self.localvars:
            raise CheckError(
                "Variable {} is not defined before use".format(node.name))

    def visitConst(self, node):
        pass

    def visitStr(self, node):
        # take note of all string constants
        self.constants[node.value] = ".Lstr"+str(self.constantcounter)
        self.constantcounter += 1

    def visitAssign(self, node):
        # make sure variables are only used AFTER they have been declared
        if node.name not in self.globalvars and node.name not in self.localvars:
            raise CheckError(
                "Variable {} is not defined before assignment".format(node.name))
        self.visit(node.value)

    def visitIf(self, node):
        self.visit(node.exp)
        for statement in node.statements:
            self.visit(statement)
        if node.elsestatements:
            for statement in node.elsestatements:
                self.visit(statement)
        pass

    def visitWhile(self, node):
        self.visit(node.exp)
        for statement in node.statements:
            self.visit(statement)

    def visitReturn(self, node):
        self.visit(node.expression)

    def visitCall(self, node):
        # because of limitations in the code-generator for x86-64 assembler function calls can only take 6 or less arguments
        if len(node.args) > 6:
            raise CheckError("Function-calls can only take 6 arguments")
        for arg in node.args:
            self.visit(arg)

    def visitFuncdef(self, node):
        # initialize the localvars dict do en empty dict()
        # all following visitLocaldef() calls will write their variables to this dict
        self.localvars = OrderedDict()
        for arg in node.args:
            self.localvars[arg] = 0
        for statement in node.statements:
            self.visit(statement)
        # annotate the funcdef node wicth information about local variables
        node.localvars = self.localvars
        # this check does not really belong here as it is not variable relatet
        # but at the moment this is the only checker class and the check is to important to leave out
        if type(node.statements[-1]) != ast.Return:
            raise CheckError("Functions must end with a return-statement!")

    def visitGlobaldef(self, node):
        # make sure global variables are only declared once
        if node.name in self.globalvars:
            raise CheckError("Redefinition of global var: "+node.name)
        self.globalvars[node.name] = node.value

    def visitLocaldef(self, node):
        # make sure global variables are only declared once per function
        if node.name in self.globalvars:
            raise CheckError("Redefinition of local var: "+node.name)
        self.localvars[node.name] = node.value
