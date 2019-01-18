from textwrap import dedent
from collections import Counter

import dbc.ast as ast
from dbc.visit import Visitor, VisitorError

""" if this is true, the generated code contains debug-information about register-allocation"""
debug = False


class RegisterAllocator:
    """ This class is responsible for register allocation. It tracks which registers are currently in use and offers methods to
        request, use and return registers.
        Register allocation should happen on a per-statement basis. This is less efficient but easyer to implement and produces more readable assembler code.
        When a statement needs a register during code-generation the following steps must happen:
        1. call choose() to get the name of a free register (or choose a register manually)
        2. call allocate(reg).
        3. generate the code for the expression that will use the register
        3b. The expression will call mark_used(reg) once it fills the register with a value
        4. the statement uses the value in the register (for whatever it needs to)
        5. the statement calls free(reg)
        !!! allocate() and free() may emit assembler instructions which have to be added to the output-code on the appropriate location!!!

    """

    def __init__(self):
        """ list of possible x86-64 registers"""
        self.registerlist = ["rax", "rbx", "rcx", "rdx",
                             "rsi", "rdi"] + ["r"+str(i) for i in range(8, 16)]
        """ registers to pass function-arguments in (ordered)"""
        self.argorder = ["rdi", "rsi", "rdx", "rcx", "r8", "r9"]
        """ the set of registers currently in use """
        self.inuse = set()
        """ Keeps track which register has been saved to the stack how often """
        self.borrowed = Counter()
        """ All expressions should place their result in THIS register """
        self.target = None

    def allocate(self, reg):
        """ Make the register reg available for use. If reg is already in use, it's value is saved to the stack.
            Returns code that HAS TO be added to the statements code.
            Also sets target to reg, so all following expressions will place the value in the newly allocated register.
            DOES NOT mark a register as in-use.
        """
        self.target = reg
        if reg in self.inuse:
            # the register is already in use. Make it available by pushing it's content to the stack
            self.borrowed[reg] += 1
            self.inuse.remove(reg)
            return "push %{}\n".format(reg) if not debug else "push %{}#borrowed\n".format(reg)
        else:
            return "" if not debug else "#prepared: "+reg+"\n"

    def mark_used(self, reg):
        """ Marks register reg as in-use"""
        self.inuse.add(reg)

    def free(self, reg):
        """ Reg is not longer needed. In-use is set to false. If reg's contents were saved to the stack in prepare(), it is restored.
            Returns code that HAS TO be added to the statements code.
        """
        borrowcount = self.borrowed[reg]
        if borrowcount == 0:
            # register is not longer needed
            self.inuse.discard(reg)
            return "" if not debug else "#unused: "+reg+"\n"
        else:
            # register value has been saved to the stack. restore it
            self.borrowed[reg] = borrowcount - 1
            self.inuse.add(reg)
            return "pop %{}\n".format(reg) if not debug else "pop %{}#returned\n".format(reg)

    def choose(self, exclude=[]):
        """ returns a register. If a free register is available, it is returned. Otherwise some arbitary in-use register is returned.
            Will never return a register that is listed in exlude.
        """
        for r in self.registerlist:
            if r not in self.inuse:
                return r
        for r in self.registerlist:
            if r not in exclude:
                return r

    def low(self, reg):
        """ Returns the register-name for the low-byte of the given register"""
        return reg.replace("r", "").replace("x", "") + "l"


class ASMGenerator(Visitor):
    """ A code-generator that takes an annotated AST as input and outputs linux x86-64 assembly code.
    As all Generators this one extends Visitor to traverse the AST.

    Generated code for a node is independent of the nodes context (happends always the same way no matter what nodes are before or after it)(excluding register allocation)

    The generated code (mostly) honors the SystemV x86-64 calling convention and can therefore interact with c-functions (like from glibc).
    """

    def __init__(self):
        """ count the generated labels to always generate unique ones"""
        self.labelcounter = 0
        """ constants of this programm. Obtained fromm annotated AST"""
        self.constants = None
        """ global variables of this programm. Obtained fromm annotated AST"""
        self.globalvars = None
        """ local variables used by the currently processed function. Obtained fromm annotated AST"""
        self.localvars = None
        """ map from variable name to %ebp offset. Needed to locate local variables on the stack """
        self.localvaroffsets = dict()

        self.regs = RegisterAllocator()
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
        # generate code for all functions of the programm recursively
        for func in node.funcdefs:
            code += self.visit(func)

        # append code for the builtin functions
        code += self.builtinFunctions()

        # start and fill the section containing global variables
        code += ".data\n"
        code += self.globalVariables(node)

        # sanity check. if there are registers in-use after compilation, there is a bug in this code
        if len(self.regs.inuse) != 0:
            print("WARNING: Some registers still in use after completed compilation!")

        return code

    def visitFuncdef(self, node):
        # calculate %ebp offsets for all local variables and the total size of this functions stackframe
        # assumes that all variables are 8 bytes long
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
                self.regs.argorder[i], self.localvaroffsets[arg])

        # generate code for all statements of the functions
        for statement in node.statements:
            code += self.visit(statement)

        return code+"\n\n"

    def visitCall(self, node):
        target = self.regs.target
        # take note of all registers that were in use at this point
        callersaved = list(self.regs.inuse)
        code = ""

        # allocate the parameter-registers and place parameters in them
        for i, arg in enumerate(node.args):
            # save previous content of the register to the stack. Also the following expression will place it's result in self.regs.argorder[i]
            code += self.regs.allocate(self.regs.argorder[i])
            # generate the code to compute the parameter
            code += self.visit(arg)
            # mark the resgiter as in-use to save it from beeing overwritten
            self.regs.mark_used(self.regs.argorder[i])

        # save all in-use registers (except argument-registers) to the stack (caller-saved)
        for reg in callersaved:
            # allcate() will save the contants and mark the registers as free to use
            code += self.regs.allocate(reg)

        # perform the function call
        code += "call {}\n".format(node.name)

        # If the calls return value is needed and the target-register is not rax, move the result to the target register
        if not node.isStatement and target != None:
            self.regs.mark_used(target)
            if target != "rax":
                code += "mov %rax, %{}\n".format(target)

        # restore the registers that were saved before call()
        for reg in reversed(callersaved):
            # free() will restore the contents saved by allocate()
            code += self.regs.free(reg)

        # free all argument-registers. Restores their values if they were in use before call()
        for i in range(len(node.args), 0, -1):
            code += self.regs.free(self.regs.argorder[i-1])

        return code

    def visitBinary(self, exp):
        # store whoch register the parent-expression expects the result in
        reg1 = self.regs.target
        # generate code to obtain value1 of the binary operator
        # will inherit self.regs.target, so the results of val1 will already be in the correct register
        code = self.visit(exp.val1)
        # choose and allocate a register for val2
        reg2 = self.regs.choose(exclude=[reg1])
        code += self.regs.allocate(reg2)
        # generate code to obtain value2 of the binary operator
        # result will be in the previously allocated register
        code += self.visit(exp.val2)

        # generate the code to compute the waned result from value1 and value2
        if exp.op == "+":
            code += "add %{1}, %{0}\n"
        elif exp.op == "-":
            code += "sub %{1}, %{0}\n"
        elif exp.op == "|":
            code += "or %{1}, %{0}\n"
        elif exp.op == "&":
            code += "and %{1}, %{0}\n"
        # the comparison operators need to use setXX because following statements will expect a value in %rax (0 if false, something else if true)
        # setting flags in the flag-register is not always enough
        elif exp.op == "==":
            code += "cmp %{1}, %{0}\n"
            code += "mov $0, %{0}\n"
            code += "sete %{2}\n"
        elif exp.op == "!=":
            code += "cmp %{1}, %{0}\n"
            code += "mov $0, %{0}\n"
            code += "setne %{2}\n"
        elif exp.op == "<":
            code += "cmp %{1}, %{0}\n"
            code += "mov $0, %{0}\n"
            code += "setl %{2}\n"
        elif exp.op == ">":
            code += "cmp %{1}, %{0}\n"
            code += "mov $0, %{0}\n"
            code += "setg %{2}\n"
        elif exp.op == "<=":
            code += "cmp %{1}, %{0}\n"
            code += "mov $0, %{0}\n"
            code += "setle %{2}\n"
        elif exp.op == ">=":
            code += "cmp %{1}, %{0}\n"
            code += "mov $0, %{0}\n"
            code += "setge %{2}\n"
        else:
            raise VisitorError(
                "Unsupported binary operation: "+exp.op)
        # fill the chosen registers into the code-template
        code = code.format(reg1, reg2, self.regs.low(reg1))
        # free reg2, as it is not needed anymore
        code += self.regs.free(reg2)

        return code

    def visitVar(self, node):
        # mark the target-register as in-use, as it now contains a value
        reg = self.regs.target
        self.regs.mark_used(reg)
        # check if the value of a global or a local variable is needed
        if node.name in self.localvars:
            # local variables are located on the stack relative to %ebp
            return "mov -{}(%rbp), %{}\n".format(self.localvaroffsets[node.name], reg)
        else:
            # global variables are referenced via an assembler label with their name
            return "mov {}, %{}\n".format(node.name, reg)

    def visitConst(self, node):
        # mark the target-register as in-use, as it now contains a value
        reg = self.regs.target
        self.regs.mark_used(reg)
        # constants are 'produced' by moving their value into %rax
        return "mov ${}, %{}\n".format(node.value, reg)

    def visitAssign(self, node):
        # choose and allocate a register
        reg = self.regs.choose()
        code = self.regs.allocate(reg)
        # generate the code computing the value for the assignment. Result will be in reg
        code += self.visit(node.value)
        # check if we assign to a global or local variable
        if node.name in self.localvars:
            # local variables are located on the stack relative to %ebp
            code += "mov %{}, -{}(%rbp)\n".format(reg,
                                                  self.localvaroffsets[node.name])
        else:
             # global variables are referenced via an assembler label with their name
            code += "mov %{}, {}\n".format(reg, node.name)

        # free reg
        code += self.regs.free(reg)
        return code

    def visitIf(self, node):
        # choose and allocate a register for the condition-result
        reg = self.regs.choose()
        code = self.regs.allocate(reg)
        # generate labels to jump to
        endif = self.getlabel("endif")
        endelse = self.getlabel("endelse")
        # generate the code for the condition
        code += self.visit(node.exp)
        # at this point the register is not longer needed
        code += self.regs.free(reg)
        # the codition-expression will leave it's result in %rax
        # 0 means false, anything else means true
        # jump (skip the if block) if 0
        code += "test %{},%{}\n".format(reg, reg)
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
        # choose and allocate a register for the condition-result
        reg = self.regs.choose()
        code = self.regs.allocate(reg)
        self.regs.target = reg
        # generate labels to jump to
        startlabel = self.getlabel("whilestart")
        endlabel = self.getlabel("whileend")
        # place the start-label
        code += startlabel+":\n"
        # generate the code for the condition
        code += self.visit(node.exp)
        # at this point the register is not longer needed
        code += self.regs.free(reg)
        # if condition returned 0 via %rax, skip to endlabel
        code += "test %{},%{}\n".format(reg, reg)
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
        code = ""
        # allocate specifically rax (because function results are aleays returned via rax)
        code += self.regs.allocate("rax")
        # calculate the value to return (if anything is returned)
        if node.expression:
            code += self.visit(node.expression)
        # mark rax as available
        self.regs.free("rax")
        # dealocate local variables with 'leave', return via 'ret'
        code += "leave\nret\n"
        return code

    def visitStr(self, node):
        reg = self.regs.target
        # lookup the label for this string constant
        value = node.value
        label = self.constants[value]
        self.regs.mark_used(reg)
        # place the address of the label into %rax (as result of this operation)
        return "mov ${}, %{}\n".format(label, reg)

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
