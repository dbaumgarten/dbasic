from textwrap import dedent

import dbc.ast as ast
from dbc.generate import Generator, GenerationError


class ASMGenerator(Generator):
    def __init__(self):
        self.labelcounter = 0
        self.argorder = ["RDI", "RSI", "RDX", "RCX", "R8", "R9"]
        self.localvars = dict()
        self.globalvars = dict()
        self.constants = dict()
        super().__init__()

    def generateProgramm(self, node):
        code = dedent("""\
        .file	"test.c"
            .text
            .globl	main
            .type	main, @function
        
        {}

        .data
        {}
        """)
        instructions = ""
        for statement in node.parts:
            instructions += self.generate(statement)
        variables = self.globalVariables()
        return code.format(instructions, variables)

    def generateFuncdef(self, node):
        for arg in node.args:
            self.addLocalVar(arg)

        code = ""
        for statement in node.statements:
            code += self.generate(statement)

        stacksize = len(self.localvars)*8
        preamble = node.name + ":\n"
        preamble += "push %rbp\n"
        preamble += "mov %rsp, %rbp\n"
        preamble += "sub ${}, %rsp\n".format(stacksize)
        argnumber = 0
        for arg in node.args:
            preamble += "mov %{}, -{}(%rbp)\n".format(
                self.argorder[argnumber], self.localvars[arg])
            argnumber += 1

        self.localvars = dict()
        return preamble+code+"\n\n"

    def generateCall(self, node):
        code = ""
        argnr = 0
        for arg in node.args:
            if argnr >= len(self.argorder):
                raise GenerationError(
                    "To many arguments for function: "+node.name, node)
            code += self.generate(arg)
            code += "mov %rax, %{}\n".format(self.argorder[argnr])
            argnr += 1
        code += "call {}\n".format(node.name)
        return code

    def generatePrint(self, node):
        code = ""
        for expression in node.expressions:
            if type(expression) == ast.Str:
                value = expression.value
                name = self.getlabel("str")
                self.constants[name] = value
                code += self.generateSyscall(1, "$1", "$" +
                                             name, "$" + str(len(value)))
            else:
                code += self.generate(expression)
                code += self.printint("%rax")
        return code

    def generateBinary(self, exp):
        code = ""
        code += self.generate(exp.val1)
        code += "push %rax\n"
        code += self.generate(exp.val2)
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
            raise GenerationError(
                "Insupported binary operation: "+"exp.op", exp)
        return code

    def generateVar(self, node):
        if node.name in self.localvars:
            return "mov -{}(%rbp), %rax\n".format(self.localvars[node.name])
        elif node.name in self.globalvars:
            return "mov {}, %rax\n".format(node.name)
        else:
            raise GenerationError(
                "Referenced variable {} before assignment.".format(node.name), node)

    def generateConst(self, node):
        return "mov ${}, %rax\n".format(node.value)

    def generateAssign(self, node):
        code = self.generate(node.value)
        if node.name in self.localvars:
            code += "mov %rax, -{}(%rbp)\n".format(self.localvars[node.name])
        elif node.name in self.globalvars:
            code += "mov %rax, {}\n".format(node.name)
        return code

    def generateIf(self, node):
        code = ""
        endif = self.getlabel("endif")
        endelse = self.getlabel("endelse")
        code += self.generate(node.exp)
        code += "test %rax,%rax\n"
        code += "jz "+endif+"\n"
        for statement in node.statements:
            code += self.generate(statement)
        if node.elsestatements:
            code += "jmp "+endelse+"\n"
        code += endif+":\n"
        if node.elsestatements:
            for statement in node.elsestatements:
                code += self.generate(statement)
                code += endelse+":\n"
        return code

    def generateWhile(self, node):
        code = ""
        startlabel = self.getlabel("whilestart")
        endlabel = self.getlabel("whileend")
        code += startlabel+":\n"
        code += self.generate(node.exp)
        code += "test %rax,%rax\n"
        code += "jz "+endlabel+"\n"
        for statement in node.statements:
            code += self.generate(statement)
        code += "jmp "+startlabel+"\n"
        code += endlabel+":\n"
        return code

    def generateInput(self, node):
        code = ""
        code += self.generateSyscall(0, "$0", "$inputbuf", "$127")
        code += "mov $inputbuf, %rdi\n"
        code += "call atoi\n"
        varoffset = self.addLocalVar(node.name)
        code += "mov %rax, -{}(%rbp)\n".format(varoffset)
        return code

    def generateReturn(self, node):
        code = self.generate(node.expression)
        code += "leave\nret\n"
        return code

    def generateExpressionStatement(self, node):
        return self.generate(node.exp)

    def generateStr(self, node):
        value = node.value
        name = self.getlabel("str")
        self.constants[name] = value
        return "mov ${}, %rax\n".format(name)

    def generateGlobaldef(self, node):
        self.globalvars[node.name] = node.value
        return ""

    def generateLocaldef(self, node):
        self.addLocalVar(node.name)
        return self.generateAssign(node)

    # ---- Start of x64 specific helper functions

    def printint(self, value):
        return dedent("""\
            mov {}, %rsi
            mov $intformat, %rdi
            mov $0, %rax
            call printf
            movq stdout(%rip), %rdi
            call fflush
            """).format(value)

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

    def globalVariables(self):
        code = ""
        for k, v in self.constants.items():
            code += "{}:\n.string \"{}\"\n\n".format(k, v)

        for k, v in self.globalvars.items():
            code += "{}:\n.quad {}\n\n".format(k, v)

        code += "inputbuf:\n.skip 128\n\n"
        code += "intformat:\n.string \"%d\""
        return code

    def addLocalVar(self, name):
        if name in self.localvars:
            return self.localvars[name]
        offset = (len(self.localvars)+1)*8
        self.localvars[name] = offset
        return offset
