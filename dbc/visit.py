""" Implements a kind of visitor-pattern for the AST.
    All checkers and code-generators operate on the AST. This pattern helps them to traverse the AST. Everyone of them just inherits from
    Visitor and overrides the visitXXX methods with their own logic.

"""
import dbc.ast as ast


class VisitorError(Exception):
    """ Is thrown when visit() is called with an unkown type."""

    def __init__(self, msg, node):
        self.msg = msg
        self.fullmessage = "Unknown AST-Node-Type: {}. {}".format(
            str(node), msg)
        super().__init__(self.fullmessage)


class Visitor():
    """ The baseclass for all visitores. It knows which function to call for which ast-type.
    All visitors override the provided default-methods with their own logic.
    The un-overriden method contain the logic to visit all the children of the specifi node type.
    If a visitor does not need to perform special actions for some specific type it does not need to override the specific method.
    """

    def __init__(self):
        self.funcmapping = {
            ast.Programm: self.visitProgramm,
            ast.Unary: self.visitUnary,
            ast.Binary: self.visitBinary,
            ast.Var: self.visitVar,
            ast.Const: self.visitConst,
            ast.Str: self.visitStr,
            ast.Assign: self.visitAssign,
            ast.If: self.visitIf,
            ast.While: self.visitWhile,
            ast.Return: self.visitReturn,
            ast.Call: self.visitCall,
            ast.FuncDef: self.visitFuncdef,
            ast.GlobalDef: self.visitGlobaldef,
            ast.LocalDef: self.visitLocaldef,
        }

    def visit(self, node):
        """ Main visit-function. Calles the correct visitXX method based on the type of node"""
        visitfunc = self.funcmapping[type(node)]
        if not visitfunc:
            raise VisitorError("Unkown AST-Node-Type:", node)
        return visitfunc(node)

    def visitProgramm(self, node):
        for part in node.parts:
            self.visit(part)

    def visitUnary(self, node):
        self.visit(node.val)

    def visitBinary(self, node):
        self.visit(node.val1)
        self.visit(node.val2)

    def visitVar(self, node):
        pass

    def visitConst(self, node):
        pass

    def visitStr(self, node):
        pass

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
        for arg in node.args:
            self.visit(arg)

    def visitFuncdef(self, node):
        for statement in node.statements:
            self.visit(statement)

    def visitGlobaldef(self, node):
        pass

    def visitLocaldef(self, node):
        self.visit(node.value)
