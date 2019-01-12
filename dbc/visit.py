import dbc.ast as ast


class VisitorError(Exception):
    def __init__(self, msg, node):
        self.msg = msg
        self.fullmessage = "Code-VisitorError-Error. Could not generate code for ast-node: {}. {}".format(
            str(node), msg)
        super().__init__(self.fullmessage)


class Visitor():
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
        visitfunc = self.funcmapping[type(node)]
        if not visitfunc:
            raise VisitorError("Unkown AST-Node-Type:", node)
        return visitfunc(node)

    def visitProgramm(self, node):
        raise VisitorError("AST-Type not implemented", node)

    def visitUnary(self, node):
        raise VisitorError("AST-Type not implemented", node)

    def visitBinary(self, node):
        raise VisitorError("AST-Type not implemented", node)

    def visitVar(self, node):
        raise VisitorError("AST-Type not implemented", node)

    def visitConst(self, node):
        raise VisitorError("AST-Type not implemented", node)

    def visitStr(self, node):
        raise VisitorError("AST-Type not implemented", node)

    def visitAssign(self, node):
        raise VisitorError("AST-Type not implemented", node)

    def visitIf(self, node):
        raise VisitorError("AST-Type not implemented", node)

    def visitWhile(self, node):
        raise VisitorError("AST-Type not implemented", node)

    def visitReturn(self, node):
        raise VisitorError("AST-Type not implemented", node)

    def visitCall(self, node):
        raise VisitorError("AST-Type not implemented", node)

    def visitFuncdef(self, node):
        raise VisitorError("AST-Type not implemented", node)

    def visitGlobaldef(self, node):
        raise VisitorError("AST-Type not implemented", node)

    def visitLocaldef(self, node):
        raise VisitorError("AST-Type not implemented", node)
