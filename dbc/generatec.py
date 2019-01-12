import dbc.ast as ast


from textwrap import dedent

import dbc.ast as ast
from dbc.visit import Visitor, VisitorError


class CGenerator(Visitor):
    def __init__(self):
        self.localvars = dict()
        self.globalvars = dict()
        super().__init__()

    def generate(self, node):
        return self.visitProgramm(node)

    def visitProgramm(self, node):
        self.globalvars = node.globalvars

        code = dedent("""\
                # include <stdio.h>
                # include <string.h>
                # include <stdlib.h>
                # include <stdarg.h>
                char inputbuffer[60];
                """)

        for k, v in self.globalvars.items():
            code += "int {} = {};\n".format(k, v)

        code += self.builtinFunctions()

        for func in node.parts:
            code += self.visit(func)

        return code

    def visitFuncdef(self, node):
        code = "int " + node.name + "("
        code += ",".join([("int "+x) for x in node.args])
        code += "){\n"
        for statement in node.statements:
            code += self.visit(statement)
        code += "}\n\n"
        return code

    def visitBinary(self, exp):
        return "("+self.visit(exp.val1)+exp.op+self.visit(exp.val2)+")"

    def visitVar(self, node):
        return str(node.name)

    def visitConst(self, node):
        return str(node.value)

    def visitAssign(self, node):
        return "{} = {};\n".format(node.name, self.visit(node.value))

    def visitIf(self, st):
        code = "if ({}) {{\n".format(self.visit(st.exp))
        for statement in st.statements:
            code += self.visit(statement)
        code += "}"
        if st.elsestatements:
            code += "else{\n"
            for statement in st.elsestatements:
                code += self.visit(statement)
            code += "}"
        code += "\n"
        return code

    def visitWhile(self, st):
        code = "while ({}) {{\n".format(self.visit(st.exp))
        for statement in st.statements:
            code += self.visit(statement)
        code += "}\n"
        return code

    def visitReturn(self, node):
        return "return {};\n".format(self.visit(node.expression))

    def visitCall(self, node):
        code = node.name + "("
        for arg in node.args:
            code += self.visit(arg)
            code += ","
        code = code.rstrip(",")
        code += ")"
        if node.isStatement:
            code += ";\n"
        return code

    def visitStr(self, node):
        return "\""+node.value+"\""

    def visitGlobaldef(self, node):
        return ""

    def visitLocaldef(self, node):
        return "int {} = {};\n".format(node.name, self.visit(node.value))

    def builtinFunctions(self):
        print = dedent("""\
        void print(const char *format, ...){
            va_list args;
            va_start(args, format);
            vprintf(format, args);
            va_end(args);
            fflush(stdout);
        }
        """)
        input = dedent("""\
        int input(void){
            fgets(inputbuffer,60,stdin);
            if(inputbuffer[strlen(inputbuffer) - 1] == '\\n'){
                inputbuffer[strlen(inputbuffer) - 1] = '\\0';
            }
            return atoi(inputbuffer);
        }
        """)
        return print+input
