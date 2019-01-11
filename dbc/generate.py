import dbc.ast as ast


class GenerationError(Exception):
    def __init__(self, msg, node):
        self.msg = msg
        self.fullmessage = "Code-Generation-Error. Could not generate code for ast-node: {}. {}".format(
            str(node), msg)
        super().__init__(self.fullmessage)


class Generator():
    def __init__(self):
        self.labelcounter = 0
        self.variables = dict()
        self.funcmapping = {
            ast.Programm: self.generateProgramm,
            ast.Print: self.generatePrint,
            ast.Unary: self.generateUnary,
            ast.Binary: self.generateBinary,
            ast.Var: self.generateVar,
            ast.Const: self.generateConst,
            ast.Str: self.generateStr,
            ast.Assign: self.generateAssign,
            ast.If: self.generateIf,
            ast.While: self.generateWhile,
            ast.Input: self.generateInput,
            ast.Return: self.generateReturn,
            ast.Call: self.generateCall,
            ast.ExpressionStatement: self.generateExpressionStatement,
            ast.FuncDef: self.generateFuncdef,
            ast.GlobalDef: self.generateGlobaldef,
            ast.LocalDef: self.generateLocaldef,
        }

    def generate(self, node):
        generator = self.funcmapping[type(node)]
        if not generator:
            raise GenerationError("Unkown AST-Node-Type:", node)
        return generator(node)

    def generateProgramm(self, node):
        raise GenerationError("AST-Type not implemented", node)

    def generatePrint(self, node):
        raise GenerationError("AST-Type not implemented", node)

    def generateUnary(self, node):
        raise GenerationError("AST-Type not implemented", node)

    def generateBinary(self, node):
        raise GenerationError("AST-Type not implemented", node)

    def generateVar(self, node):
        raise GenerationError("AST-Type not implemented", node)

    def generateConst(self, node):
        raise GenerationError("AST-Type not implemented", node)

    def generateStr(self, node):
        raise GenerationError("AST-Type not implemented", node)

    def generateAssign(self, node):
        raise GenerationError("AST-Type not implemented", node)

    def generateIf(self, node):
        raise GenerationError("AST-Type not implemented", node)

    def generateWhile(self, node):
        raise GenerationError("AST-Type not implemented", node)

    def generateInput(self, node):
        raise GenerationError("AST-Type not implemented", node)

    def generateReturn(self, node):
        raise GenerationError("AST-Type not implemented", node)

    def generateCall(self, node):
        raise GenerationError("AST-Type not implemented", node)

    def generateExpressionStatement(self, node):
        raise GenerationError("AST-Type not implemented", node)

    def generateFuncdef(self, node):
        raise GenerationError("AST-Type not implemented", node)

    def generateGlobaldef(self, node):
        raise GenerationError("AST-Type not implemented", node)

    def generateLocaldef(self, node):
        raise GenerationError("AST-Type not implemented", node)
