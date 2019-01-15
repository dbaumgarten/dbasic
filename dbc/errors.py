""" Contains error classes shared by multiple modules """


class CheckError(Exception):
    """ Is raised if the compiled programm fails a compile-time check """

    def __init__(self, msg, node):
        self.msg = msg
        self.node = node
        self.fullmessage = "Semantic error on line {}: {}".format(
            node.line, msg)
        super().__init__(self.fullmessage)
