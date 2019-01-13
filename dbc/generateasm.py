from textwrap import dedent

import dbc.ast as ast
from dbc.visit import Visitor, VisitorError


class ASMGenerator(Visitor):
    """ A code-generator that takes an annotated AST as input and outputs linux x86-64 assembly code.
    As all Generators this one extends Visitor to traverse the AST.

    The generator generates relatively crude assembly but should be very easy to understand.
    Register allocation is done in the most basic way possible:
    - for the most of the operations only %rax is used. Binary operations also use %rcx
    - Every expression leaves it's result in %rax
    - no registers are used to permanently store any variables
    - generated code for a node is independent of the nodes context (happends always the same way no matter what nodes are before or after it)

    The generated code (mostly) honors the SystemV x86-64 calling convention and can therefore interact with c-functions (like from glibc).
    """

    def __init__(self):
        """ count the generated labels to always generate unique ones"""
        self.labelcounter = 0
        """ The (ordered) registers in which arguments are passed to functions according to the SystemV 64 calling convention"""
        self.argorder = ["RDI", "RSI", "RDX", "RCX", "R8", "R9"]
        """ constants of this programm. Obtained fromm annotated AST"""
        self.constants = None
        """ global variables of this programm. Obtained fromm annotated AST"""
        self.globalvars = None
        """ local variables used by the currently processed function. Obtained fromm annotated AST"""
        self.localvars = None
        """ map from variable name to %ebp offset. Needed to locate local variables on the stack """
        self.localvaroffsets = dict()
        super().__init__()

    def generate(self, node):
        """ Main generate method.

        :params node: The root node of the AST
        returns: A string containing the generated assembler code 
        """
        # obtain globals and constants from annotated AST
        self.constants = node.constants
        self.globalvars = node.globalvars
        return self.visitProgramm(node)

    def visitProgramm(self, node):
        # write the assembly header
        code = dedent("""\
        .file	"test.c"
            .text
            .globl	main
            .type	main, @function
        

        """)
        # generate code for all parts of the programm recursively
        for statement in node.parts:
            code += self.visit(statement)

        # append code for the builtin functions
        code += self.builtinFunctions()

        # start and fill the section containing global variables
        code += ".data\n"
        code += self.globalVariables(node)
        return code

    def visitFuncdef(self, node):
        # calculate %ebp offsets for all local variables and the total size of this functions stackframe
        self.localvars = node.localvars
        for i, k in enumerate(self.localvars.keys()):
            self.localvaroffsets[k] = (i+1)*8
        stacksize = len(self.localvars)*8

        # generate function prologue. Store old %ebp, setup %ebp and reserve space for local variables
        code = node.name + ":\n"
        code += "push %rbp\n"
        code += "mov %rsp, %rbp\n"
        code += "sub ${}, %rsp\n".format(stacksize)

        # move the arguments from the registers they were passed in to their local variable on the stack
        for i, arg in enumerate(node.args):
            code += "mov %{}, -{}(%rbp)\n".format(
                self.argorder[i], self.localvaroffsets[arg])

        # generate code for all statements of the functions
        for statement in node.statements:
            code += self.visit(statement)

        return code+"\n\n"

    def visitCall(self, node):
        code = ""
        # the function call will use some registers to pass parameters
        for i, arg in enumerate(node.args):
            # generate the code to compute the parameter
            code += self.visit(arg)
            # save the old value of the register to the stack. Needed to not break nested function calls ( like f(f(f)) )
            code += "push %{}\n".format(self.argorder[i])
            # move the computed parameter value to the correct parameter-register
            code += "mov %rax, %{}\n".format(self.argorder[i])
        # perform the function call
        code += "call {}\n".format(node.name)
        # restore all registers that were saved to the stack before
        for i in range(len(node.args), 0, -1):
            code += "pop %{}\n".format(self.argorder[i-1])
        return code

    def visitBinary(self, exp):
        code = ""
        # generate code to obtain value1 of the binary operator
        code += self.visit(exp.val1)
        # save the computed value to the stack, as the code generating value2 would otherwise overwrite it in %rax
        code += "push %rax\n"
        # generate code to obtain value2 of the binary operator
        code += self.visit(exp.val2)
        # restore the saved value1 into %rcx
        code += "pop %rcx\n"
        # generate the code to compute the waned result from value1 and value2
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
        # the comparison operators need to use setXX because following statements will expect a value in %rax (0 if false, something else if true)
        # setting flags in the flag-register is not always enough
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
        # check if the value of a global or a local variable is needed
        if node.name in self.localvars:
            # local variables are located on the stack relative to %ebp
            return "mov -{}(%rbp), %rax\n".format(self.localvaroffsets[node.name])
        else:
            # global variables are referenced via an assembler label with their name
            return "mov {}, %rax\n".format(node.name)

    def visitConst(self, node):
        # constants are 'produced' by moving their value into %rax
        return "mov ${}, %rax\n".format(node.value)

    def visitAssign(self, node):
        # generate the code computing the value for the assignment
        code = self.visit(node.value)
        # check if we assign to a global or local variable
        if node.name in self.localvars:
            # local variables are located on the stack relative to %ebp
            code += "mov %rax, -{}(%rbp)\n".format(
                self.localvaroffsets[node.name])
        else:
             # global variables are referenced via an assembler label with their name
            code += "mov %rax, {}\n".format(node.name)
        return code

    def visitIf(self, node):
        code = ""
        # generate labels to jump to
        endif = self.getlabel("endif")
        endelse = self.getlabel("endelse")
        # generate the code for the condition
        code += self.visit(node.exp)
        # the codition-expression will leave it's result in %rax
        # 0 means false, anything else means true
        # jump (skip the if block) if 0
        code += "test %rax,%rax\n"
        code += "jz "+endif+"\n"
        # generate code for the if-block
        for statement in node.statements:
            code += self.visit(statement)
        # condition was true, if there is an else block. skip it
        if node.elsestatements:
            code += "jmp "+endelse+"\n"
        # place the label that is jumped to if condition is false
        code += endif+":\n"
        if node.elsestatements:
            # if there is an else block, generate code for it
            for statement in node.elsestatements:
                code += self.visit(statement)
                code += endelse+":\n"
        return code

    def visitWhile(self, node):
        code = ""
        # generate labels to jump to
        startlabel = self.getlabel("whilestart")
        endlabel = self.getlabel("whileend")
        # place the start-label
        code += startlabel+":\n"
        # generate the code for the condition
        code += self.visit(node.exp)
        # if condition returned 0 via %rax, skip to endlabel
        code += "test %rax,%rax\n"
        code += "jz "+endlabel+"\n"
        # generate code for block
        for statement in node.statements:
            code += self.visit(statement)
        # jump back to the condition check
        code += "jmp "+startlabel+"\n"
        # place endlabel
        code += endlabel+":\n"
        return code

    def visitReturn(self, node):
        # calculate the value to return
        code = self.visit(node.expression)
        # dealocate local variables with 'leave', return via 'ret'
        code += "leave\nret\n"
        return code

    def visitStr(self, node):
        # lookup the label for this string constant
        value = node.value
        label = self.constants[value]
        # place the address of the label into %rax (as result of this operation)
        return "mov ${}, %rax\n".format(label)

    def visitGlobaldef(self, node):
        # nothing to do. all globals are already defined
        return ""

    def visitLocaldef(self, node):
        # do exactly the same as when assigning a value to a local variable
        return self.visitAssign(node)

    # ---- Start of x64 specific helper functions

    def getlabel(self, pfx, glob=False):
        """ Return the next unique label

        :params pfx: A name to include in the label
        :params glob: If false, the label is hidden from the linker and only exists locally
        :returns: A string containing a unique label
        """
        self.labelcounter += 1
        l = pfx+str(self.labelcounter)
        if not glob:
            l = ".L"+l
        return l

    def generateSyscall(self, call, *args):
        """ generate the code needed to perform a syscall """
        # the registers for passing arguments
        regs = ["rdi", "rsi", "rdx", "r10", "r8", "r9"]
        # choose syscall via number in %eax
        code = "mov ${}, %eax\n".format(call)
        i = 0
        # place arguments in registers
        for arg in args:
            code += "mov {}, %{}\n".format(arg, regs[i])
            i += 1
        # perform syscall
        code += "syscall\n"
        return code

    def globalVariables(self, programm):
        """ Generate the code defining all global variables and their default values"""
        code = ""
        # constants count as global variables in this context
        for k, v in programm.constants.items():
            code += "{}:\n.string \"{}\"\n\n".format(v, k)

        for k, v in programm.globalvars.items():
            code += "{}:\n.quad {}\n\n".format(k, v)

        code += "inputbuf:\n.skip 128\n\n"
        return code

    def builtinFunctions(self):
        """ generate code for some builtin functions """
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
