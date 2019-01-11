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
        fd = funcdef(t)
        if fd:
            statements.append(fd)
            continue

        raise ParserError(
            t.peek().line, "Unknown statement-type: '{}'".format(t.peek().value))

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

    if t.next().type != "END":
        raise ParserError(id.line, "Expected END at the end of function body")

    if t.next().type != "NL":
        raise ParserError(
            id.line, "Expected newline after END of function body")

    return ast.FuncDef(id.value, args, body)


@LogParsing
def statement(t):
    st = printstatement(t) or ifstatement(
        t) or letstatement(t) or whilestatement(t) or inputstatement(t) or returnstatement(t) or expressionstatement(t)
    if not st:
        return None
    nl = t.next()
    if nl.type != "NL":
        raise ParserError(nl.line, "Missing newline")
    return st


@LogParsing
def funccallargs(t):
    tok = t.peek()
    if tok.type != "(":
        return None
    t.next()
    args = exprlist(t)
    if not args:
        args = []
    endtoken = t.next()
    if endtoken.type != ")":
        raise ParserError(tok.line, "Missing ) in function call.")
    return args


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
def printstatement(t):
    tok = t.peek()
    if tok.type != "PRINT":
        return None
    t.next()
    expl = exprlist(t)
    if expl:
        return ast.Print(expl)
    raise ParserError(tok.line, "Expression list missing after PRINT.")


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
def letstatement(t):
    tok = t.peek()
    if tok.type != "LET":
        return None
    t.next()
    vartok = t.next()
    if vartok.type != "ID":
        raise ParserError(vartok.line, "No variable name after LET")
    if t.next().type != "=":
        raise ParserError(vartok.line, "No '=' after LET:")
    expr = expression(t)
    if not expr:
        raise ParserError(vartok.line, "No expression after LET")
    return ast.Assign(vartok.value, expr)


@LogParsing
def inputstatement(t):
    tok = t.peek()
    if tok.type != "INPUT":
        return None
    t.next()
    vartok = t.next()
    if vartok.type != "ID":
        raise ParserError(vartok.line, "No variable name after INPUT")
    return ast.Input(vartok.value)


@LogParsing
def expressionstatement(t):
    exp = expression(t)
    if exp:
        return ast.ExpressionStatement(exp)
    return None


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
    idexp = identifyerexpression(t)
    if idexp:
        return idexp
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
    else:
        return None


@LogParsing
def identifyerexpression(t):
    tok = t.peek()
    if tok.type != "ID":
        return None
    id = t.next()

    funcargs = funccallargs(t)
    if funcargs:
        return ast.Call(id.value, funcargs)

    return ast.Var(id.value)
