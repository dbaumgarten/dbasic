import dbc.ast as ast


from textwrap import dedent

import dbc.ast as ast
from dbc.generate import Generator, GenerationError


class CGenerator(Generator):
    def __init__(self):
        self.localvars = dict()
        self.globalvars = dict()
        super().__init__()

    def generateProgramm(self, node):
        preamble = dedent("""\
                # include <stdio.h>
                # include <string.h>
                # include <stdlib.h>
                # include <stdarg.h>
                char inputbuffer[60];
                """)

        code = self.builtinFunctions()
        for func in node.parts:
            code += self.generate(func)

        globalvarcode = ""
        for k, v in self.globalvars.items():
            globalvarcode += "int {} = {};\n".format(k, v)

        return preamble+globalvarcode+code

    def generateFuncdef(self, node):
        code = "int " + node.name + "("
        code += ",".join([("int "+x) for x in node.args])
        code += "){\n"
        for statement in node.statements:
            code += self.generate(statement)
        code += "}\n\n"
        return code

    def generateBinary(self, exp):
        return "("+self.generate(exp.val1)+exp.op+self.generate(exp.val2)+")"

    def generateVar(self, node):
        return str(node.name)

    def generateConst(self, node):
        return str(node.value)

    def generateAssign(self, node):
        code = ""
        if not node.name in self.localvars and not node.name in self.globalvars:
            raise GenerationError(
                "Referenced variable {} before assignment.".format(node.name), node)
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

    def generateReturn(self, node):
        return "return {};\n".format(self.generate(node.expression))

    def generateCall(self, node):
        code = node.name + "("
        for arg in node.args:
            code += self.generate(arg)
            code += ","
        code = code.rstrip(",")
        code += ")"
        if node.isStatement:
            code += ";\n"
        return code

    def generateStr(self, node):
        return "\""+node.value+"\""

    def generateGlobaldef(self, node):
        self.globalvars[node.name] = node.value
        return ""

    def generateLocaldef(self, node):
        return "int {} = {};\n".format(node.name, self.generate(node.value))

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
