import dbc.ast as ast

variables = dict()
labelcounter = 0


def generateCode(ast):
    code = """
.file	"test.c"
	.text
	.globl	main
	.type	main, @function
main:
"""

    for statement in ast.statements:
        code += generateStatement(statement)

    code += "\n.data\n\n"

    for k, v in variables.items():
        if isinstance(v, str):
            code += "{}:\n.string \"{}\"\n\n".format(k, v)
        else:
            code += "{}:\n.quad 0x00\n\n".format(k)

    code += "inputbuf:\n.skip 128\n\n"

    return code


def getlabel(pfx, glob=False):
    global labelcounter
    labelcounter += 1
    l = pfx+str(labelcounter)
    if not glob:
        l = ".L"+l
    return l


def generateStatement(st):
    code = ""
    if type(st) == ast.Return:
        code += generateExpression(st.expression)
        code += "ret\n"
        return code

    if type(st) == ast.Assign:
        variables[st.name] = True
        code += generateExpression(st.value)
        code += "mov %rax, {}\n".format(st.name)
        return code

    if type(st) == ast.Print:
        for expression in st.expressions:
            if type(expression) == ast.Str:
                value = expression.value
                name = getlabel("str")
                variables[name] = value
                code += generateSyscall(1, "$1", "$" +
                                        name, "$" + str(len(value)))
            else:
                code += generateExpression(expression)
                code += printint("%rax")
        return code

    if type(st) == ast.While:
        startlabel = getlabel("whilestart")
        endlabel = getlabel("whileend")
        code += startlabel+":\n"
        code += generateExpression(st.exp)
        code += "test %rax,%rax\n"
        code += "jz "+endlabel+"\n"
        for statement in st.statements:
            code += generateStatement(statement)
        code += "jmp "+startlabel+"\n"
        code += endlabel+":\n"
        return code

    if type(st) == ast.If:
        endif = getlabel("endif")
        endelse = getlabel("endelse")
        code += generateExpression(st.exp)
        code += "test %rax,%rax\n"
        code += "jz "+endif+"\n"
        for statement in st.statements:
            code += generateStatement(statement)
        if st.elsestatements:
            code += "jmp "+endelse+"\n"
        code += endif+":\n"
        if st.elsestatements:
            for statement in st.elsestatements:
                code += generateStatement(statement)
                code += endelse+":\n"
        return code

    if type(st) == ast.Input:
        code += generateSyscall(0, "$0", "$inputbuf", "$127")
        code += "mov $inputbuf, %rdi\n"
        code += "call atoi\n"
        variables[st.name] = True
        code += "mov %rax, {}\n".format(st.name)
        return code
    raise AttributeError(st.__class__)


def generateSyscall(call, *args):
    regs = ["rdi", "rsi", "rdx", "r10", "r8", "r9"]
    code = "mov ${}, %eax\n".format(call)
    i = 0
    for arg in args:
        code += "mov {}, %{}\n".format(arg, regs[i])
        i += 1
    code += "syscall\n"
    return code


def generateExpression(exp):
    code = ""
    if type(exp) == ast.Const:
        return "mov ${}, %rax\n".format(exp.value)

    if type(exp) == ast.Var:
        return "mov {}, %rax\n".format(exp.name)

    if type(exp) == ast.Binary:
        code += generateExpression(exp.val1)
        code += "push %rax\n"
        code += generateExpression(exp.val2)
        code += "pop %rcx\n"
        if exp.op == "+":
            code += "add %rcx, %rax\n"
            return code
        if exp.op == "-":
            code += "sub %rax, %rcx\n"
            code += "mov %rcx, %rax\n"
            return code
        if exp.op == "==":
            code += "cmp %rax, %rcx\n"
            code += "mov $0, %rax\n"
            code += "sete %al\n"
            return code
        if exp.op == "!=":
            code += "cmp %rax, %rcx\n"
            code += "mov $0, %rax\n"
            code += "setne %al\n"
            return code
        if exp.op == "|":
            code += "or %rcx, %rax\n"
            return code
        if exp.op == "&":
            code += "and %rcx, %rax\n"
            return code
        if exp.op == "<":
            code += "cmp %rax, %rcx\n"
            code += "mov $0, %rax\n"
            code += "setl %al\n"
            return code
        if exp.op == ">":
            code += "cmp %rax, %rcx\n"
            code += "mov $0, %rax\n"
            code += "setg %al\n"
            return code
        if exp.op == "<=":
            code += "cmp %rax, %rcx\n"
            code += "mov $0, %rax\n"
            code += "setle %al\n"
            return code
        if exp.op == ">=":
            code += "cmp %rax, %rcx\n"
            code += "mov $0, %rax\n"
            code += "setge %al\n"
            return code
    raise AttributeError(str(exp.__class__)+":"+exp.op)


def printint(value):
    variables["intformat"] = "%d"
    code = """mov {}, %rsi
mov $intformat, %rdi
mov $0, %rax
call printf
movq stdout(%rip), %rdi
call fflush
""".format(value)
    return code
