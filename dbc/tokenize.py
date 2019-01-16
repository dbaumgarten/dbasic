""" The first part of every compiler is the Tokenizer. It converts the input text to a series of 'tokens'.
During this all irrelevant parts of the source code (whitespace, blank lines etc.) are removed, so later parts of the compiler 
will only have to deal with relevant parts (keywords, identifiers etc.)
"""
import re

"""These are all keywords of the language. The all represent some kinde of language construct"""
keywords = ["IF", "THEN", "RETURN",
            "END", "WHILE", "DO", "ELSE", "FUNC", "GLOBAL"]

"""These are all symbols that are permitted for use in calculations.
As some of the symbols are prefixes of others ('>' is a prefix if '>=') they have to be ordered by length. Otherwise '>=' could be detected
as '>' followed by '=' instead of a single '>='."""
symbols = [">=", "<=", "!=", "==", ",", "(", ")", "+", "-", "*", "/", "==",
           "=", ">", "<", "&", "|"]

"""These are all type-identifiers of the language"""
types = ["INT", "BOOL"]

"""Regexes to detect identifiers, numerical constants and strings"""
idre = re.compile("^[a-zA-Z]+")
# the strings TRUE and FALSE are also constants
constre = re.compile("^[0-9]+|^TRUE|^FALSE")
stringre = re.compile("^\"([^\"]*)\"", re.MULTILINE)


class Token:
    """ A Token represents a single, parsing-relevant part of the input-text"""

    def __init__(self, t, v=None, line=0):
        """ The type of this token. Is a string. Could be a keyword, a symbol or the strings 'TYPE','ID','STR','CONST','NL'
            If you would want to do this 'correctly' you would probably use constants instead of plain strings.
        """
        self.type = t
        """ Some types of tokens have additional information. Like in case of type 'STR'. 
        It is nice to know that it is a string, but we also need to know the actual value of the string"""
        self.value = v
        """ We also take note on which line the token was found. This way we can output more helpfull errors in case of parsing-errors."""
        self.line = line

    def __str__(self):
        """For debugging purposes its always nice if a token can be displayed as a human-readable string"""
        return self.type+":"+repr(self.value)+":"+str(self.line)

    def __repr__(self):
        return "'"+str(self)+"'"


class Tokenizer:
    """ Tokenizer handles the whole tokenization"""

    def __init__(self, inp):
        """ Given an input-string the tokenizer will tokenize it.
        Automatically calls tokenize()

        :params inp: The input-string to tokenize"""

        """ The input to tokenize"""
        self.input = inp
        """ The list of tokens found during tokenisation"""
        self.tokens = []
        """ The current position in the token list. Is used by next() and peek()"""
        self.pos = 0

        self.tokenize()

    def tokenize(self):
        """ Perform the tokenisation on the string provided via the constructor.
        The whole tokenisation happens at once. There is no on-the fly tokenization when calling next(). This would be better for memory-consumption
        but at the moment it is just easier this way

        Raises SyntaxError if an unkown token is encountered.
        """
        # keep track of the current line
        linenr = 1
        text = self.input
        # Start with the whole input text. Examine the beginning of the string and check if it is a token and what kind of token it is.
        # Remove the found token from the start of the string and start over as long the string still contains characters
        while len(text) > 0:
            # check if the beginning of the string is a keyword. The follwing checks for symbols and type-identifiers behave exactly the same.
            matched = False
            for word in keywords:
                if text.startswith(word):
                    # we found a keyword. Kreate a token and append it to the list of tokens
                    self.tokens.append(Token(word, None, linenr))
                    # remove the matched text from the start of the string
                    text = text[len(word):]
                    # note down that we found a token
                    matched = True
                    break
            if matched:
                # we found a token. Go to top of while loop and repeat.
                continue
            for symbol in symbols:
                if text.startswith(symbol):
                    self.tokens.append(Token(symbol, None, linenr))
                    text = text[len(symbol):]
                    matched = True
                    break
            if matched:
                continue
            for t in types:
                if text.startswith(t):
                    self.tokens.append(Token("TYPE", t, linenr))
                    text = text[len(t):]
                    matched = True
                    break
            if matched:
                continue
            # At this point we know it is neither a keyword, symbol or type.

            # Is it a constant (3,42,85748)?
            matcher = constre.match(text)
            if matcher:
                self.tokens.append(
                    Token("CONST", matcher.group(0), linenr))
                text = text[len(matcher.group(0)):]
                continue
            # Is it a identifier (variable name, function name etc.)?
            matcher = idre.match(text)
            if matcher:
                self.tokens.append(Token("ID", matcher.group(0), linenr))
                text = text[len(matcher.group(0)):]
                continue
            # Is it a string constant ("abc","geh")?
            matcher = stringre.match(text)
            if matcher:
                self.tokens.append(Token("STR", matcher.group(1), linenr))
                text = text[len(matcher.group(0)):]
                continue
            # Is it a newline character?
            if text[0] == "\n":
                # Note: the found newline is NEVER part of a string constant, as string constants would be recognized before we reach this code
                if len(self.tokens) == 0 or self.tokens[-1].type != "NL":
                    self.tokens.append(Token("NL", None, linenr))
                text = text[1:]
                # we found a newline. This means we tokenized a full line
                linenr += 1
                continue
            if text[0] == " " or text[0] == "\t":
                text = text[1:]
                continue
            # if we reach this nothing matched. We have no idea what kind of token this is. Throw an error and give up.
            e = SyntaxError()
            e.filename = "main"
            e.lineno = linenr
            e.msg = "Unknown token: "+text[:20]
            raise e
        # We tokenized everything. Throw in an artifical newline. This way the parser wont fail if the programmer forgot
        # the newline after his last line of code
        self.tokens.append(Token("NL", None, linenr))

    def next(self):
        """ Return the current token and advance the position by one
            Will return None if the end of the token-list is reached
        """
        t = self.peek()
        if t:
            self.pos += 1
        return t

    def peek(self, ahead=0):
        """ Return the current token without advancing the position.
            Will return None if the end of the token-list is reached 

        :params ahead: How many tokens to look into the future. 0=current token, 1 = next token after current, and so on
        """
        if len(self.tokens) > (self.pos+ahead):
            return self.tokens[self.pos+ahead]
        else:
            return None
