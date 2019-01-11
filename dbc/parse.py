import dbc.ast as ast


debug = False
recursedirection = -1


def LogParsing(func):
    def log(t):
        global recursedirection
        if debug:
            inputtoken = t.peek()

            if recursedirection == -1:
                print("//-----------------")
                recursedirection = 1

            print("//Calling ", func.__name__, "with token", str(inputtoken))
            astelement = func(t)

            if recursedirection == 1:
                print("//>")
                recursedirection = -1

            if astelement:
                print("//", func.__name__, "returned",
                      type(astelement).__name__)
            else:
                print("//", func.__name__, "returned None")
            return astelement
        else:
            return func(t)
    return log


class ParserError(Exception):
    def __init__(self, line, msg, found=None):
        self.msg = msg
        self.line = line
        self.fullmessage = "Parser error at line {}. {}".format(
            line, msg) + (("Found:" + str(found)) if found else "")
        super().__init__(self.fullmessage)


@LogParsing
def parse(t):
    statements = []

    while t.peek():
        fd = funcdef(t) or globaldef(t)
        if fd:
            statements.append(fd)
            if t.next().type != "NL":
                raise ParserError(
                    fd.line, "Expected newline after END of definition")
            continue

        raise ParserError(
            t.peek().line, "Unknown statement-type: '{}'".format(t.peek()))

    return ast.Programm(statements)


@LogParsing
def funcdef(t):
    tok = t.peek()
    if tok.type != "FUNC":
        return None
    t.next()
    id = t.next()
    if id.type != "ID":
        raise ParserError(id.line, "Expected identifier after FUNC")
    if t.next().type != "(":
        raise ParserError(
            id.line, "Expected '(' in function definition")
    args = []
    while True:
        arg = t.next()
        if arg.type == ")":
            break
        if arg.type != "ID":
            raise ParserError(
                arg.line, "Expected identifier in FUNC argument list", arg)
        args.append(arg.value)
        n = t.peek()
        if n.type == ")":
            continue
        if n.type != ",":
            raise ParserError(
                arg.line, "Expected ',' after argument in argument list")
        t.next()

    if t.next().type != "NL":
        raise ParserError(id.line, "Expected newline after FUNC definition")

    body = block(t)

    expectedend = t.next()
    if expectedend.type != "END":
        raise ParserError(id.line, "Unknown statement type", expectedend)

    return ast.FuncDef(id.value, args, body)


@LogParsing
def globaldef(t):
    tok = t.peek()
    if tok.type != "GLOBAL":
        return None
    t.next()
    ldef = localdef(t)
    if not ldef:
        raise ParserError(
            tok.line, "Expected variable declaration after GLOBAL")
    if type(ldef.value) != ast.Const:
        raise ParserError(
            tok.line, "Global variables can only be initialize using constants")
    return ast.GlobalDef(ldef.name, ldef.value.value)


@LogParsing
def localdef(t):
    tok = t.peek()
    if tok.type != "TYPE":
        return None
    t.next()
    id = t.next()
    if id.type != "ID":
        raise ParserError(
            id.line, "Expected identifyer in variable declaration.")
    if t.next().type != "=":
        raise ParserError(id.line, "Missing '=' in variable declaration")
    val = expression(t)
    if not val:
        raise ParserError(
            id.line, "Missing expression for value of declared variable.")
    return ast.LocalDef(id.value, val)


@LogParsing
def statement(t):
    st = ifstatement(t) or assignstatement(t) or whilestatement(
        t) or returnstatement(t) or funccall(t) or localdef(t)
    if not st:
        return None
    if type(st) == ast.Call:
        st.isStatement = True
    nl = t.next()
    if nl.type != "NL":
        raise ParserError(nl.line, "Missing newline")
    return st


@LogParsing
def returnstatement(t):
    tok = t.peek()
    if tok.type != "RETURN":
        return None
    t.next()
    exp = expression(t)
    if not exp:
        raise ParserError(tok.line, "Expected expression after return value")
    return ast.Return(exp)


@LogParsing
def ifstatement(t):
    tok = t.peek()
    if tok.type != "IF":
        return None
    t.next()
    exp = expression(t)
    if not exp:
        raise ParserError(tok.line, "No expr after IF")

    then = t.next()
    if then.type != "THEN":
        raise ParserError(then.line, "Missing THEN after IF")

    nl = t.next()
    if nl.type != "NL":
        raise ParserError(nl.line, "Expected Newline after THEN")

    statements = block(t)
    elsestatements = None

    tok = t.peek()
    if tok.type == "ELSE":
        t.next()
        nl = t.next()
        if nl.type != "NL":
            raise ParserError(nl.line, "Expected Newline after ELSE")
        elsestatements = block(t)

    if t.next().type != "END":
        raise ParserError(then.line, "Missing END of IF-Block")

    return ast.If(exp, statements, elsestatements)


@LogParsing
def whilestatement(t):
    tok = t.peek()
    if tok.type != "WHILE":
        return None
    t.next()
    exp = expression(t)
    if not exp:
        raise ParserError(tok.line, "No expr after WHILE")

    then = t.next()
    if then.type != "DO":
        raise ParserError(then.line, "Missing DO after WHILE")

    nl = t.next()
    if nl.type != "NL":
        raise ParserError(nl.line, "Expected Newline after DO")

    statements = block(t)

    if t.next().type != "END":
        raise ParserError(then.line, "Missing END of IF-Block")

    return ast.While(exp, statements)


@LogParsing
def assignstatement(t):
    if t.peek().type != "ID" or t.peek(1).type != "=":
        return None
    vartok = t.next()
    t.next()
    expr = expression(t)
    if not expr:
        raise ParserError(
            vartok.line, "No expression after assignment operator")
    return ast.Assign(vartok.value, expr)


@LogParsing
def funccall(t):
    if t.peek().type != "ID" or t.peek(1).type != "(":
        return None
    id = t.next()
    t.next()
    args = exprlist(t)
    if not args:
        args = []
    endtoken = t.next()
    if endtoken.type != ")":
        raise ParserError(id.line, "Missing ) in function call.")
    return ast.Call(id.value, args)


@LogParsing
def block(t):
    statements = []
    st = statement(t)
    while st != None:
        statements.append(st)
        st = statement(t)
    return statements


@LogParsing
def exprlist(t):
    exl = []

    elem = string(t) or expression(t)
    if not elem:
        return None
    exl.append(elem)

    tok = t.peek()
    while tok.type == ",":
        t.next()
        elem = string(t) or expression(t)
        if not elem:
            return None
        exl.append(elem)
        tok = t.peek()
    return exl


@LogParsing
def string(t):
    tok = t.peek()
    if tok.type == "STR":
        t.next()
        return ast.Str(tok.value)
    return None


@LogParsing
def expression(t):
    root = logicexpression(t)
    if not root:
        return None
    bintype = t.peek().type
    while bintype == "|" or bintype == "&":
        t.next()
        f = logicexpression(t)
        if not f:
            return None
        root = ast.Binary(bintype, root, f)
        bintype = t.peek().type
    return root


@LogParsing
def logicexpression(t):
    t1 = sumexpression(t)
    if not t1:
        return None
    operator = t.peek()
    if operator.type not in ["==", "=>", "<=", ">", "<", "!="]:
        return t1
    t.next()
    t2 = sumexpression(t)
    if not t2:
        return None
    return ast.Binary(operator.type, t1, t2)


@LogParsing
def sumexpression(t):
    tok = t.peek()
    root = None
    if tok.type == "-":
        t.next()
        root = term(t)
        if root:
            root = ast.Unary("-", root)
    else:
        root = term(t)

    if not root:
        return None

    bintype = t.peek().type
    while bintype == "-" or bintype == "+":
        t.next()
        nterm = term(t)
        if not nterm:
            return None
        root = ast.Binary(bintype, root, nterm)
        bintype = t.peek().type
    return root


@LogParsing
def term(t):
    root = factor(t)
    if not root:
        return None
    bintype = t.peek().type
    while bintype == "*" or bintype == "/":
        t.next()
        f = factor(t)
        if not f:
            return None
        root = ast.Binary(bintype, root, f)
        bintype = t.peek().type
    return root


@LogParsing
def factor(t):
    call = funccall(t)
    if call:
        return call
    tok = t.peek()
    if tok.type == "CONST":
        t.next()
        return ast.Const(tok.value)
    elif tok.type == "(":
        t.next()
        exp = expression(t)
        if not exp or t.next().type != ")":
            return None
        return exp
    elif tok.type == "ID":
        t.next()
        return ast.Var(tok.value)
    else:
        return None
