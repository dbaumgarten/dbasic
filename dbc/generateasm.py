from textwrap import dedent

import dbc.ast as ast
from dbc.generate import Generator, GenerationError


class ASMGenerator(Generator):
    def __init__(self):
        self.labelcounter = 0
        self.variables = dict()
        super().__init__()

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

    def generateProgramm(self, node):
        code = dedent("""\
        .file	"test.c"
            .text
            .globl	main
            .type	main, @function

        
        main:
        {}


        .data

        {}
        """)
        instructions = ""
        for statement in node.statements:
            instructions += self.generate(statement)
        variables = self.generateGlobalVariables()
        return code.format(instructions, variables)

    def generateGlobalVariables(self):
        code = ""
        for k, v in self.variables.items():
            if isinstance(v, str):
                code += "{}:\n.string \"{}\"\n\n".format(k, v)
            else:
                code += "{}:\n.quad 0x00\n\n".format(k)

        code += "inputbuf:\n.skip 128\n\n"
        return code

    def generatePrint(self, node):
        code = ""
        for expression in node.expressions:
            if type(expression) == ast.Str:
                value = expression.value
                name = self.getlabel("str")
                self.variables[name] = value
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
        if not node.name in self.variables:
            raise GenerationError(
                "Referenced variable {} before assignment.".format(node.name), node)
        return "mov {}, %rax\n".format(node.name)

    def generateConst(self, node):
        return "mov ${}, %rax\n".format(node.value)

    def generateAssign(self, node):
        code = ""
        self.variables[node.name] = True
        code += self.generate(node.value)
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
        self.variables[node.name] = True
        code += "mov %rax, {}\n".format(node.name)
        return code

    def generateReturn(self, node):
        code = self.generate(node.expression)
        code += "ret\n"
        return code

    def printint(self, value):
        self.variables["intformat"] = "%d"
        return dedent("""\
            mov {}, %rsi
            mov $intformat, %rdi
            mov $0, %rax
            call printf
            movq stdout(%rip), %rdi
            call fflush
            """).format(value)
