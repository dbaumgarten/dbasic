from textwrap import dedent

import dbc.ast as ast
from dbc.visit import Visitor, VisitorError


class ASMGenerator(Visitor):
    def __init__(self):
        self.labelcounter = 0
        self.argorder = ["RDI", "RSI", "RDX", "RCX", "R8", "R9"]
        self.constants = None
        self.globalvars = None
        self.localvars = None
        self.localvaroffsets = dict()
        super().__init__()

    def generate(self, node):
        self.constants = node.constants
        self.globalvars = node.globalvars
        return self.visitProgramm(node)

    def visitProgramm(self, node):
        code = dedent("""\
        .file	"test.c"
            .text
            .globl	main
            .type	main, @function
        

        """)
        for statement in node.parts:
            code += self.visit(statement)

        code += self.builtinFunctions()

        code += ".data\n"
        code += self.globalVariables(node)
        return code

    def visitFuncdef(self, node):
        self.localvars = node.localvars
        for i, k in enumerate(self.localvars.keys()):
            self.localvaroffsets[k] = (i+1)*8
        stacksize = len(self.localvars)*8

        code = node.name + ":\n"
        code += "push %rbp\n"
        code += "mov %rsp, %rbp\n"
        code += "sub ${}, %rsp\n".format(stacksize)

        for i, arg in enumerate(node.args):
            code += "mov %{}, -{}(%rbp)\n".format(
                self.argorder[i], self.localvaroffsets[arg])

        for statement in node.statements:
            code += self.visit(statement)

        return code+"\n\n"

    def visitCall(self, node):
        code = ""
        for i, arg in enumerate(node.args):
            code += self.visit(arg)
            code += "push %{}\n".format(self.argorder[i])
            code += "mov %rax, %{}\n".format(self.argorder[i])
        code += "call {}\n".format(node.name)
        for i in range(len(node.args), 0, -1):
            code += "pop %{}\n".format(self.argorder[i-1])
        return code

    def visitBinary(self, exp):
        code = ""
        code += self.visit(exp.val1)
        code += "push %rax\n"
        code += self.visit(exp.val2)
        code += "pop %rcx\n"
        if exp.op == "+":
            code += "add %rcx, %rax\n"
        elif exp.op == "-":
            code += "sub %rax, %rcx\n"
            code += "mov %rcx, %rax\n"
        elif exp.op == "==":
            code += "cmp %rax, %rcx\n"
            code += "mov $0, %rax\n"
            code += "sete %al\n"
        elif exp.op == "!=":
            code += "cmp %rax, %rcx\n"
            code += "mov $0, %rax\n"
            code += "setne %al\n"
        elif exp.op == "|":
            code += "or %rcx, %rax\n"
        elif exp.op == "&":
            code += "and %rcx, %rax\n"
        elif exp.op == "<":
            code += "cmp %rax, %rcx\n"
            code += "mov $0, %rax\n"
            code += "setl %al\n"
        elif exp.op == ">":
            code += "cmp %rax, %rcx\n"
            code += "mov $0, %rax\n"
            code += "setg %al\n"
        elif exp.op == "<=":
            code += "cmp %rax, %rcx\n"
            code += "mov $0, %rax\n"
            code += "setle %al\n"
        elif exp.op == ">=":
            code += "cmp %rax, %rcx\n"
            code += "mov $0, %rax\n"
            code += "setge %al\n"
        else:
            raise VisitorError(
                "Unsupported binary operation: "+"exp.op", exp)
        return code

    def visitVar(self, node):
        if node.name in self.localvars:
            return "mov -{}(%rbp), %rax\n".format(self.localvaroffsets[node.name])
        else:
            return "mov {}, %rax\n".format(node.name)

    def visitConst(self, node):
        return "mov ${}, %rax\n".format(node.value)

    def visitAssign(self, node):
        code = self.visit(node.value)
        if node.name in self.localvars:
            code += "mov %rax, -{}(%rbp)\n".format(
                self.localvaroffsets[node.name])
        else:
            code += "mov %rax, {}\n".format(node.name)
        return code

    def visitIf(self, node):
        code = ""
        endif = self.getlabel("endif")
        endelse = self.getlabel("endelse")
        code += self.visit(node.exp)
        code += "test %rax,%rax\n"
        code += "jz "+endif+"\n"
        for statement in node.statements:
            code += self.visit(statement)
        if node.elsestatements:
            code += "jmp "+endelse+"\n"
        code += endif+":\n"
        if node.elsestatements:
            for statement in node.elsestatements:
                code += self.visit(statement)
                code += endelse+":\n"
        return code

    def visitWhile(self, node):
        code = ""
        startlabel = self.getlabel("whilestart")
        endlabel = self.getlabel("whileend")
        code += startlabel+":\n"
        code += self.visit(node.exp)
        code += "test %rax,%rax\n"
        code += "jz "+endlabel+"\n"
        for statement in node.statements:
            code += self.visit(statement)
        code += "jmp "+startlabel+"\n"
        code += endlabel+":\n"
        return code

    def visitReturn(self, node):
        code = self.visit(node.expression)
        code += "leave\nret\n"
        return code

    def visitStr(self, node):
        value = node.value
        label = self.constants[value]
        return "mov ${}, %rax\n".format(label)

    def visitGlobaldef(self, node):
        return ""

    def visitLocaldef(self, node):
        return self.visitAssign(node)

    # ---- Start of x64 specific helper functions

    def getlabel(self, pfx, glob=False):
        self.labelcounter += 1
        l = pfx+str(self.labelcounter)
        if not glob:
            l = ".L"+l
        return l

    def generateSyscall(self, call, *args):
        regs = ["rdi", "rsi", "rdx", "r10", "r8", "r9"]
        code = "mov ${}, %eax\n".format(call)
        i = 0
        for arg in args:
            code += "mov {}, %{}\n".format(arg, regs[i])
            i += 1
        code += "syscall\n"
        return code

    def globalVariables(self, programm):
        code = ""
        for k, v in programm.constants.items():
            code += "{}:\n.string \"{}\"\n\n".format(v, k)

        for k, v in programm.globalvars.items():
            code += "{}:\n.quad {}\n\n".format(k, v)

        code += "inputbuf:\n.skip 128\n\n"
        return code

    def builtinFunctions(self):
        input = "\n\ninput:\n"
        input += self.generateSyscall(0, "$0", "$inputbuf", "$127")
        input += "mov $inputbuf, %rdi\n"
        input += "call atoi\n"
        input += "ret\n\n\n"
        print = "\n\nprint:\n"
        print += "mov $0, %rax\n"
        print += "call printf\n"
        print += "movq stdout(%rip), %rdi\n"
        print += "call fflush\n"
        print += "ret\n\n"
        return input+print
