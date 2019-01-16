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
        # currently there is only one unary operation and it can only be applied to INTs
        if node.val.type != "INT":
            raise CheckError(
                "Unary operation '-' can only be performed on INTs and not on "+node.val.type, node)
        # unary operations inherit the type of their operand
        node.type = node.val.type

    def visitBinary(self, node):
        self.visit(node.val1)
        self.visit(node.val2)
        if node.op in ["+", "-", "*", "/"] and (node.val1.type != "INT" or node.val2.type != "INT"):
            raise CheckError(
                "Both operands of operations +-*/ must be of type INT", node)

        # operations can only be performed if both operands have the same type
        if node.val1.type != node.val1.type:
            raise CheckError(
                "Both operands of a binary operation need to have the same type", node)

        # at this point it is guaranteed that val1 and val2 have the same type. If one of them is None also val1 is.
        if node.val1 == None:
            raise CheckError(
                "Cannot perform binary operation on None-type", node)

        # comparisons always return BOOL. Everything else inherits the type of the operands
        if node.op in ["==", "!=", ">=", "<=", "<", ">"]:
            node.type = "BOOL"
        else:
            node.type = node.val1.type

    def visitVar(self, node):
        # get the type from the declaration of the variable
        if node.name in self.currentfunc.localvartypes:
            node.type = self.currentfunc.localvartypes[node.name]
        else:
            node.type = self.rootnode.globalvartypes[node.name]

    def visitConst(self, node):
        # consts are getting their type set by the parser. (Yes, this is a strange exception...)
        pass

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
                "The type of the value to return ({}) must match the type of the function ({})".format(node.type, self.currentfunc.returntype), node)

    def visitFuncdef(self, node):
        self.currentfunc = node
        for statement in node.statements:
            self.visit(statement)

    def visitAssign(self, node):
        self.visit(node.value)
        # find the type of the variable. Could be a global or a local variable
        if self.currentfunc != None and node.name in self.currentfunc.localvartypes:
            vartype = self.currentfunc.localvartypes[node.name]
        else:
            vartype = self.rootnode.globalvartypes[node.name]
        # make sure the assigned value has the same type as the variable
        if node.value.type != vartype:
            raise CheckError(
                "Cannot assign {} type value to a {}-Variable".format(node.value.type, vartype), node)

    def visitLocaldef(self, node):
        self.visit(node.value)
        # a defintion is always also an assignment. pass it on.
        self.visitAssign(node)

    def visitGlobaldef(self, node):
        self.visit(node.value)
        # a defintion is always also an assignment. pass it on.
        self.visitAssign(node)

    def visitIf(self, node):
        self.visit(node.exp)
        if node.exp.type != "BOOL":
            raise CheckError(
                "IF condition has to return a BOOL. Instead found: "+node.exp.type, node)
        for statement in node.statements:
            self.visit(statement)
        if node.elsestatements:
            for statement in node.elsestatements:
                self.visit(statement)
        pass

    def visitWhile(self, node):
        self.visit(node.exp)
        if node.exp.type != "BOOL":
            raise CheckError(
                "WHILE condition has to return a BOOL. Instead found: "+node.exp.type, node)
        for statement in node.statements:
            self.visit(statement)

    def visitCall(self, node):
        # special treatment for builtin functions
        if node.name == "input":
            if len(node.args) > 0:
                raise CheckError(
                    "input() does not take any arguments", node)
            node.type = "INT"
        elif node.name == "print":
            if len(node.args) < 1:
                raise CheckError(
                    "print() needs at least one argument", node)
            self.visit(node.args[0])
            if node.args[0].type != "CONSTSTR":
                raise CheckError(
                    "First argument to print must be a string", node)
            node.type = None
        # every other function
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

            for i, arg in enumerate(node.args):
                self.visit(arg)
                # Make sure we do not pass a None-type to a function
                if arg.type != funcdef.argtypes[i]:
                    raise CheckError(
                        "Argument number {} for function {} needs to be of type {}, not {}".format(i, node.name, funcdef.argtypes[i], arg.type), node)
