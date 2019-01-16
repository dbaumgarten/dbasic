"""This module contains functions to parse a list of Tokens into an AST.
All parsing-methods take a Tokenizer as Argument and return an AST-node if they can parse 
the token-sequence that is obtainable by tokenizer.next() or None if it isn't.
If the parsing-function is sure that it 'should' be able to parse the token-sequence, but encounters an error it throws a ParserError.
Example: 
The token-sequence starts with 'IF'. Ifstatement() is sure that it sould be able to parse it (because it starts with IF). 
But ifstatement() notices there is no 'THEN'. Therefore it will throw a Parser Error.
Showing the same token-sequenceto whilestatement() would just return None (and not throw an error) because whilestatement() sees that 
the first token is not 'WHILE' and therefore know the token-sequence is not meant for it.

The parsing is done using a hand written recursive descent parser.
"""
import dbc.ast as ast

""" If true, log debugging information about the parsing"""
debug = False
"""Internal variables needed to format the debug-logging properly"""
recursedirection = -1


def LogParsing(func):
    """ This is a decorator for parsing-functions. If debug is set to true it logs every called parsing-function
    along with the current token when calling and the returned AST-Class.
    It is not 'necessary' for the parser to work but really helpfull for debugging the parser.
    """
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
    """ ParserError is raised by the parser on finding a non-recoverable syntax-error"""

    def __init__(self, line, msg, found=None):
        """
        :params line: The line of the input-file where the parsing-error occured
        :params msg: A description of the error
        :params found: (optional) The token that was found instead of the expected token
        """
        self.msg = msg
        self.line = line
        self.fullmessage = "Parser error at line {}. {}".format(
            line, msg) + (("Found:" + str(found)) if found else "")
        super().__init__(self.fullmessage)


@LogParsing
def parse(t):
    """ Entry-point for parsing. Returns an ast:programm or raises a ParserError"""
    functions = []
    globalvars = []

    while t.peek():
        # a programm consists of function definitions and global variables in arbitary order
        func = funcdef(t)
        if func:
            functions.append(func)
            continue

        glob = globaldef(t)
        if glob:
            globalvars.append(glob)
            continue

        raise ParserError(
            t.peek().line, "Unknown statement-type: '{}'".format(t.peek()))

    return ast.Programm(functions, globalvars, 0)


@LogParsing
def funcdef(t):
    """ Parses function definitions """
    # The following 4 lines show a common pattern here. The function checks if it thinks it could parse the token-sequence and if not
    # just returns None to give other functions in the calling-functions the chance to parse it
    tok = t.peek()
    if tok.type != "FUNC":
        return None
    t.next()
    # At this point we are sure the token-sequence if a function definition. Advance in the token-sequence
    id = t.next()
    if id.type != "ID":
        raise ParserError(id.line, "Expected identifier after FUNC")
    if t.next().type != "(":
        raise ParserError(
            id.line, "Expected '(' in function definition")
    args = []
    argtypes = []
    # parse an aribitary long list of comma seperated arguments until ')' or an unexpected token is encountered
    while True:
        argt = t.next()
        if argt.type == ")":
            break
        if argt.type != "TYPE":
            raise ParserError(
                argt.line, "Expected type-identifier in function declaration", argt)
        argtypes.append(argt.value)
        arg = t.next()
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

    # Allow return-type to be specified optionally
    returntype = None
    funct = t.peek()
    if funct.type == "TYPE":
        # if the function has a return type, take note of it
        returntype = funct.value
        t.next()

    # There has to be a newline before the start of the function-body
    if t.next().type != "NL":
        raise ParserError(id.line, "Expected newline after FUNC definition")

    # parse the function-body
    body = block(t)

    # the next token after a block should be END. Otherwise something went wrong
    expectedend = t.next()
    if expectedend.type != "END":
        raise ParserError(id.line, "Unknown statement type", expectedend)

    # function blocks have to end with a newline
    if t.next().type != "NL":
        raise ParserError(
            expectedend.line, "Expected newline after END of function block")

    # construct the funcdef AST-Node from functionname, arguments and body and return it
    return ast.FuncDef(id.value, args, argtypes, body, returntype, id.line)


@LogParsing
def globaldef(t):
    """ parses a global variable definition 
        A global variable definition is basically a local variable definition prepended with GLOBAL and outside of a function.
        Therefore we can re-use the parsing of local variable definitions.
    """
    tok = t.peek()
    if tok.type != "GLOBAL":
        return None
    t.next()
    ldef = localdef(t)
    if not ldef:
        raise ParserError(
            tok.line, "Expected variable declaration after GLOBAL")

    # global var definitions have to end with a newline
    if t.next().type != "NL":
        raise ParserError(
            tok.line, "Expected newline after END of variable definition")

    return ast.GlobalDef(ldef.name, ldef.value, ldef.type, tok.line)


@LogParsing
def localdef(t):
    """ parses the declaration of a local variable """
    tok = t.peek()
    if tok.type != "TYPE":
        return None
    vartype = t.next()
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
    return ast.LocalDef(id.value, val, vartype.value, tok.line)


@LogParsing
def statement(t):
    """ Parses statements. A statement is some kind of 'command' that does something. It defines an action to be performed by the programm"""
    # There are multiple different kind of statements. Everyone of them is possible but only one of ther parsing functions will return a non-None value
    st = ifstatement(t) or assignstatement(t) or whilestatement(
        t) or returnstatement(t) or funccall(t) or localdef(t)
    if not st:
        return None
    # The C-generator needs to know if a funccall was a statement or part of the expression.
    if type(st) == ast.Call:
        st.isStatement = True
    nl = t.next()
    # All statements have to end in a newline
    if nl.type != "NL":
        raise ParserError(nl.line, "Missing newline")
    return st


@LogParsing
def returnstatement(t):
    """ parses a return statement """
    tok = t.peek()
    if tok.type != "RETURN":
        return None
    t.next()
    # expression can by None. In this case the function returns nothing
    exp = expression(t)
    return ast.Return(exp, tok.line)


@LogParsing
def ifstatement(t):
    """ parses an if-statement """
    tok = t.peek()
    if tok.type != "IF":
        return None
    t.next()
    # parse the condition of the if
    exp = expression(t)
    if not exp:
        raise ParserError(tok.line, "No expr after IF")

    then = t.next()
    if then.type != "THEN":
        raise ParserError(then.line, "Missing THEN after IF")

    nl = t.next()
    if nl.type != "NL":
        raise ParserError(nl.line, "Expected Newline after THEN")

    # the block to execute if the condition is true
    statements = block(t)
    elsestatements = None

    # ELSE-blocks are optional. Check if there is one
    tok = t.peek()
    if tok.type == "ELSE":
        t.next()
        nl = t.next()
        if nl.type != "NL":
            raise ParserError(nl.line, "Expected Newline after ELSE")
        elsestatements = block(t)

    if t.next().type != "END":
        raise ParserError(then.line, "Missing END of IF-Block")

    return ast.If(exp, statements, elsestatements, tok.line)


@LogParsing
def whilestatement(t):
    """ parses a while-statement """
    tok = t.peek()
    if tok.type != "WHILE":
        return None
    t.next()
    # the condition of the loop
    exp = expression(t)
    if not exp:
        raise ParserError(tok.line, "No expr after WHILE")

    then = t.next()
    if then.type != "DO":
        raise ParserError(then.line, "Missing DO after WHILE")

    nl = t.next()
    if nl.type != "NL":
        raise ParserError(nl.line, "Expected Newline after DO")

    # the body of the loop
    statements = block(t)

    if t.next().type != "END":
        raise ParserError(then.line, "Missing END of IF-Block")

    return ast.While(exp, statements, tok.line)


@LogParsing
def assignstatement(t):
    """ Parse the assignment of a value to a variable """
    # To tell apart an assignment (name = value) from a func-call (name()) we need to look into the future of the token-sequence
    # because when only looking onto the next token both would look the same.
    # In compiler-theory this would be a big thing. We could change the grammar to avoid this, but it would make the grammar a lot more complicated.
    # But for us this has no drawbacks, so f*ck it!
    if t.peek().type != "ID" or t.peek(1).type != "=":
        return None
    vartok = t.next()
    t.next()
    expr = expression(t)
    if not expr:
        raise ParserError(
            vartok.line, "No expression after assignment operator")
    return ast.Assign(vartok.value, expr, vartok.line)


@LogParsing
def funccall(t):
    """ parses a function-call. Function calls are somewhat special. 
    They are expressions (return a value), but can also be used as standalone statements """
    # see assignstatement for the reason for t.peek(1)
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
    return ast.Call(id.value, args, False, id.line)


@LogParsing
def block(t):
    """ a block is a series of statements (usually terminated by END or sometimes ELSE) 
        this function does return a list of Nodes instead of a single node
    """
    statements = []
    # while we can parse a statement -> do it and append it to the list
    st = statement(t)
    while st != None:
        statements.append(st)
        st = statement(t)
    # we can no longer parse statements. The block is complete.
    return statements


@LogParsing
def exprlist(t):
    """ parses a comma seperated list of expressions (or strings). Is used for function calls. 
        All variables are of type INT, BUT we allow string-constants as function arguments.
        Custom functions can't realy use them as arguments, but it is possible to call C-Functions and internal functions
        that accept strings
        this function does return a list of expressions instead of a single node
    """
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
    """ parses string constants (like "foobar") """
    tok = t.peek()
    if tok.type == "STR":
        t.next()
        return ast.Str(tok.value, tok.line)
    return None


@LogParsing
def expression(t):
    """ Parses an expression. An expression is everything that results in a value like 1+3, myfunc(), 3|4 and so on.
        Expressions can include sub-expressions, which can also include sub-expressions etc.
        Different kind of expressions are parsed in a specific order based on operator priority. See the comments for details"""

    # logic expression (comparisons) have the next higher priority. parse them before parsing & and | expressions
    root = logicexpression(t)
    if not root:
        return None
    bintype = t.peek().type
    while bintype == "|" or bintype == "&":
        t.next()
        f = logicexpression(t)
        if not f:
            return None
        root = ast.Binary(bintype, root, f, root.line)
        bintype = t.peek().type
    return root


@LogParsing
def logicexpression(t):
    """ expressions using comparison operators """
    # sum expressions have the next higher priority. parse them first
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
    return ast.Binary(operator.type, t1, t2, operator.line)


@LogParsing
def sumexpression(t):
    """ expressions using + or - """
    tok = t.peek()
    root = None
    # check if there is anegation operator
    if tok.type == "-":
        t.next()
        root = term(t)
        if root:
            root = ast.Unary("-", root, root.line)
    else:
        # multiplication expressions have t (terms) he next higher priority. parse them first
        root = term(t)

    if not root:
        return None

    bintype = t.peek().type
    while bintype == "-" or bintype == "+":
        t.next()
        nterm = term(t)
        if not nterm:
            return None
        root = ast.Binary(bintype, root, nterm, root.line)
        bintype = t.peek().type
    return root


@LogParsing
def term(t):
    """ expressions using multiplicative operators """
    # constants, variables and bracketed expressions have the next higher priority. Do them first
    root = factor(t)
    if not root:
        return None
    bintype = t.peek().type
    while bintype == "*" or bintype == "/":
        t.next()
        f = factor(t)
        if not f:
            return None
        root = ast.Binary(bintype, root, f, root.line)
        bintype = t.peek().type
    return root


@LogParsing
def factor(t):
    """ expressions that are variables, constants or bracketed expressions """
    # check if we are dealing with a funccall
    call = funccall(t)
    if call:
        return call
    tok = t.peek()
    # or a constant
    if tok.type == "CONST":
        t.next()
        # treat the special const values TRUE and FALSE as 1 and 0
        value = tok.value
        vtype = "INT"
        if value == "TRUE":
            value = "1"
            vtype = "BOOL"
        if value == "FALSE":
            value == "0"
            vtype = "BOOL"
        return ast.Const(value, vtype, tok.line)
    # or a bracketed expression
    elif tok.type == "(":
        t.next()
        exp = expression(t)
        if not exp or t.next().type != ")":
            return None
        return exp
    # or a variable
    elif tok.type == "ID":
        t.next()
        return ast.Var(tok.value, tok.line)
    # or neither
    else:
        return None
