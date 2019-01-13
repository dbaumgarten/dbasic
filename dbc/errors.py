""" Contains error classes shared by multiple modules """


class CheckError(Exception):
    """ Is raised if the compiled programm fails a compile-time check """

    def __init__(self, msg):
        self.msg = msg
        self.fullmessage = "Error when validating code: {}".format(msg)
        super().__init__(self.fullmessage)
