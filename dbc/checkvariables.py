import dbc.ast as ast
from dbc.visit import Visitor
from dbc.errors import CheckError
from collections import OrderedDict


class VariableChecker(Visitor):
    def __init__(self):
        self.globalvars = dict()
        self.localvars = OrderedDict()
        self.constants = dict()
        self.constantcounter = 0
        super().__init__()

    def check(self, node):
        return self.visitProgramm(node)

    def visitProgramm(self, node):
        for part in node.parts:
            if type(part) == ast.GlobalDef:
                self.visit(part)
        for part in node.parts:
            if type(part) == ast.FuncDef:
                self.visit(part)
        node.globalvars = self.globalvars
        node.constants = self.constants

    def visitUnary(self, node):
        self.visit(node.val)

    def visitBinary(self, node):
        self.visit(node.val1)
        self.visit(node.val2)

    def visitVar(self, node):
        if node.name not in self.globalvars and node.name not in self.localvars:
            raise CheckError(
                "Variable {} is not defined before use".format(node.name))

    def visitConst(self, node):
        pass

    def visitStr(self, node):
        self.constants[node.value] = ".Lstr"+str(self.constantcounter)
        self.constantcounter += 1

    def visitAssign(self, node):
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
        if len(node.args) > 6:
            raise CheckError("Function-calls can only take 6 arguments")
        for arg in node.args:
            self.visit(arg)

    def visitFuncdef(self, node):
        self.localvars = OrderedDict()
        for arg in node.args:
            self.localvars[arg] = 0
        for statement in node.statements:
            self.visit(statement)
        node.localvars = self.localvars
        if type(node.statements[-1]) != ast.Return:
            raise CheckError("Functions must end with a return-statement!")

    def visitGlobaldef(self, node):
        if node.name in self.globalvars:
            raise CheckError("Redefinition of global var: "+node.name)
        self.globalvars[node.name] = node.value

    def visitLocaldef(self, node):
        if node.name in self.globalvars:
            raise CheckError("Redefinition of local var: "+node.name)
        self.localvars[node.name] = node.value
