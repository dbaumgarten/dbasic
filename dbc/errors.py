class CheckError(Exception):
    def __init__(self, msg):
        self.msg = msg
        self.fullmessage = "Error when validating code: {}".format(msg)
        super().__init__(self.fullmessage)
