import dbc.ast as ast


from textwrap import dedent

import dbc.ast as ast
from dbc.visit import Visitor, VisitorError


class CGenerator(Visitor):
    """ A code-generator that takes an annotated AST as input adn outputs the c representation of the code.
    It is mainly used for debugging and to show how simple the code-generation truely is if you leave out all the assembly-related voodoo.
    As all Generators this one extends Visitor to traverse the AST.

    The code-generation itself is pretty straight-forward and barely needs any additional comments.

    As you can see no error checking happens here. This happend in the checks that were executed befor code-generation.
    The code-generator can rely on the AST beeing correct.
    """

    def __init__(self):
        self.localvars = dict()
        self.globalvars = dict()
        super().__init__()

    def generate(self, node):
        """ Generate c-code from the given programm 

        :params node: The root-node of the AST
        :returns: A string containing the c representation of the AST
        """

        return self.visitProgramm(node)

    def visitProgramm(self, node):
        self.globalvars = node.globalvars

        # make some default-includes
        # inputbuffer is some buffer for the builtin input() function
        code = dedent("""\
                # include <stdio.h>
                # include <string.h>
                # include <stdlib.h>
                # include <stdarg.h>
                char inputbuffer[60];
                """)
        # declare all globals
        for k, v in self.globalvars.items():
            code += "int {} = {};\n".format(k, v)

        # add code for builtin functions
        code += self.builtinFunctions()

        # generate code for the childnodes of ast.Programm and append it
        for func in node.funcdefs:
            code += self.visit(func)

        return code

    def visitFuncdef(self, node):
        # generate function-code
        code = "int " + node.name + "("
        code += ",".join([("int "+x) for x in node.args])
        code += "){\n"
        for statement in node.statements:
            code += self.visit(statement)
        code += "}\n\n"
        return code

    def visitBinary(self, exp):
        # generate binary expressions. They are always enclosed in () to make clear how the compiler interpreded the original expression
        # in regards to operator priority
        return "("+self.visit(exp.val1)+exp.op+self.visit(exp.val2)+")"

    def visitVar(self, node):
        # just print the name of the referenced variable
        return str(node.name)

    def visitConst(self, node):
        # just print the value of the constant
        return str(node.value)

    def visitAssign(self, node):
        return "{} = {};\n".format(node.name, self.visit(node.value))

    def visitIf(self, st):
        # pretty literal translation from ast to C
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
        if node.expression:
            return "return {};\n".format(self.visit(node.expression))
        else:
            return "return\n"

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
        # nothing to do here globals are already defined when we reach this
        return ""

    def visitLocaldef(self, node):
        return "int {} = {};\n".format(node.name, self.visit(node.value))

    def builtinFunctions(self):
        # include some builtin functions in the code
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
