import re

keywords = ["PRINT", "IF", "THEN", "INPUT",
            "LET", "RETURN", "END", "WHILE", "DO", "ELSE"]
symbols = [",", "(", ")", "+", "-", "*", "/", "==",
           "=", ">=", "<=", ">", "<", "!=", "&", "|"]

idre = re.compile("^[a-zA-Z]+")
constre = re.compile("^[0-9]+")
stringre = re.compile("^\"([^\"]*)\"", re.MULTILINE)


class Token:
    def __init__(self, t, v=None, line=0):
        self.type = t
        self.value = v
        self.line = line

    def __str__(self):
        return self.type+":"+repr(self.value)+":"+str(self.line)

    def __repr__(self):
        return "'"+str(self)+"'"


class Tokenizer:
    def __init__(self, inp):
        self.input = inp
        self.tokens = []
        self.pos = 0

    def newtokenize(self):
        linenr = 1
        text = self.input
        while len(text) > 0:
            matched = False
            for word in keywords:
                if text.startswith(word):
                    self.tokens.append(Token(word, None, linenr))
                    text = text[len(word):]
                    matched = True
                    break
            if matched:
                continue
            for symbol in symbols:
                if text.startswith(symbol):
                    self.tokens.append(Token(symbol, None, linenr))
                    text = text[len(symbol):]
                    matched = True
                    break
            if matched:
                continue
            matcher = idre.match(text)
            if matcher:
                self.tokens.append(Token("ID", matcher.group(0), linenr))
                text = text[len(matcher.group(0)):]
                continue
            matcher = constre.match(text)
            if matcher:
                self.tokens.append(
                    Token("CONST", matcher.group(0), linenr))
                text = text[len(matcher.group(0)):]
                continue
            matcher = stringre.match(text)
            if matcher:
                self.tokens.append(Token("STR", matcher.group(1), linenr))
                text = text[len(matcher.group(0)):]
                continue
            if text[0] == "\n":
                if len(self.tokens) == 0 or self.tokens[-1].type != "NL":
                    self.tokens.append(Token("NL", None, linenr))
                text = text[1:]
                linenr += 1
                continue
            if text[0] == " " or text[0] == "\t":
                text = text[1:]
                continue
            # if we reach this nothing matched
            e = SyntaxError()
            e.filename = "main"
            e.lineno = linenr
            e.msg = "Unknown token: "+text[:20]
            raise e
        self.tokens.append(Token("NL", None, linenr))

    def next(self):
        t = self.peek()
        if t:
            self.pos += 1
        return t

    def peek(self):
        if len(self.tokens) > self.pos:
            return self.tokens[self.pos]
        else:
            return None
