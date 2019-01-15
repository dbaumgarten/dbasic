import dbc.ast as ast
from dbc.visit import Visitor
from dbc.errors import CheckError
from collections import OrderedDict


class TypeChecker(Visitor):
    """ This class extends Visitor and is responsible for checking for any type errors like for example:
    - wrong type of arguments for function calls.
    - using the result of a function without return-values in calculations
    Additionaly it tags all expression Nodes with a type.
    """

    def __init__(self):
        """ Point at the root node of the programm"""
        self.rootnode = None
        """ Points at the function node that is currently processed """
        self.currentfunc = None
        super().__init__()

    def check(self, node):
        """ Main method for the checker. Checks the given programm for type errors"""
        self.rootnode = node
        return self.visitProgramm(node)

    def visitUnary(self, node):
        self.visit(node.val)
        # unary operations inherit the type of their operand
        node.type = node.val.type
        if node.type == None:
            raise CheckError(
                "Cannot perform unary operation on None-type", node)

    def visitBinary(self, node):
        self.visit(node.val1)
        self.visit(node.val2)
        # operations can only be performed if both operands have the same type
        if node.val1.type != node.val1.type:
            raise CheckError(
                "Both operands of a binary operation need to have the same type", node)
        node.type = node.val1.type
        if node.type == None:
            raise CheckError(
                "Cannot perform binary operation on None-type", node)

    def visitVar(self, node):
        # currently all variables have the type INT
        node.type = "INT"

    def visitConst(self, node):
        # currently all variables have the type INT
        node.type = "INT"

    def visitStr(self, node):
        # type for string-constants
        node.type = "CONSTSTR"

    def visitReturn(self, node):
        # a return inherits the type of it's expression, or none if it does not have an expression
        if node.expression:
            self.visit(node.expression)
            node.type = node.expression.type
        else:
            node.type = None
        # can not return a value from a 'void' function (or void from an INT function)
        if node.type != self.currentfunc.returntype:
            raise CheckError(
                "The type of the value to return must match the type of the function. Functype={}, Returntype={}".format(self.currentfunc.returntype, node.type), node)

    def visitFuncdef(self, node):
        self.currentfunc = node
        for statement in node.statements:
            self.visit(statement)

    def visitAssign(self, node):
        self.visit(node.value)
        # currently there is only INT or None as types. Stop them from assigning None to an INT-Var
        if node.value.type == None:
            raise CheckError(
                "Cannot assign None-type value to an INT-Variable", node)

    def visitLocaldef(self, node):
        self.visit(node.value)
        if node.value.type == None:
            raise CheckError(
                "Cannot assign None-type value to an INT-Variable", node)

    def visitIf(self, node):
        self.visit(node.exp)
        if node.exp.type == None:
            raise CheckError(
                "Cannot use None-type expression as condition for an IF statement", node)
        for statement in node.statements:
            self.visit(statement)
        if node.elsestatements:
            for statement in node.elsestatements:
                self.visit(statement)
        pass

    def visitWhile(self, node):
        self.visit(node.exp)
        if node.exp.type == None:
            raise CheckError(
                "Cannot use None-type expression as condition for a WHILE statement", node)
        for statement in node.statements:
            self.visit(statement)

    def visitCall(self, node):
        # special treatment for builtin functions
        if node.name == "input":
            node.type = "INT"
        else:
            # find the definition of the function
            funcdef = None
            for f in self.rootnode.funcdefs:
                if f.name == node.name:
                    funcdef = f
                    break

            if not funcdef:
                # we did not find a definition for this function. It is probably an extern function
                # there is no type checking to do
                node.type = None
                return

            # the type of the call's resut is the return-type of the function
            node.type = funcdef.returntype

        for arg in node.args:
            self.visit(arg)
            # we currently only have INT and None as types. Make sure we do not pass a None-type to a function
            if arg.type == None:
                raise CheckError(
                    "Cannot use None-type as function argument", node)
