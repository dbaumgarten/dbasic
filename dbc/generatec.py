import dbc.ast as ast


from textwrap import dedent

import dbc.ast as ast
from dbc.generate import Generator, GenerationError


class CGenerator(Generator):
    def __init__(self):
        self.variables = dict()
        super().__init__()

    def generateProgramm(self, node):
        code = dedent("""\
                # include <stdio.h>
                # include <string.h>
                # include <stdlib.h>
                char inputbuffer[60];
                int main(){
                """)

        for statement in node.statements:
            code += self.generate(statement)
        code += "}"
        return code

    def generatePrint(self, node):
        code = ""
        for exp in node.expressions:
            if type(exp) == ast.Str:
                code += "printf(\"%s\",\""+exp.value+"\");\n"
            else:
                code += "printf(\"%i\","+self.generate(exp)+");\n"
        return code

    def generateBinary(self, exp):
        return "("+self.generate(exp.val1)+exp.op+self.generate(exp.val2)+")"

    def generateVar(self, node):
        return str(node.name)

    def generateConst(self, node):
        return str(node.value)

    def generateAssign(self, node):
        code = ""
        if not node.name in self.variables:
            code += "int {};\n".format(node.name)
            self.variables[node.name] = True
        code += "{} = {};\n".format(node.name, self.generate(node.value))
        return code

    def generateIf(self, st):
        code = "if ({}) {{\n".format(self.generate(st.exp))
        for statement in st.statements:
            code += self.generate(statement)
        code += "}"
        if st.elsestatements:
            code += "else{\n"
            for statement in st.elsestatements:
                code += self.generate(statement)
            code += "}"
        code += "\n"
        return code

    def generateWhile(self, st):
        code = "while ({}) {{\n".format(self.generate(st.exp))
        for statement in st.statements:
            code += self.generate(statement)
        code += "}\n"
        return code

    def generateInput(self, st):
        code = ""
        if not st.name in self.variables:
            code += "int {};\n".format(st.name)
            self.variables[st.name] = True
        code += "fgets(inputbuffer,60,stdin);if(inputbuffer[strlen(inputbuffer) - 1] == '\\n'){inputbuffer[strlen(inputbuffer) - 1] = '\\0';}\n"
        code += "{} = atoi(inputbuffer);\n".format(st.name)
        return code

    def generateReturn(self, node):
        return "return {};".format(self.generate(node.expression))
