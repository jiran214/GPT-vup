class InterruptException(Exception):
    def __init__(self, message=None):
        if message is None:
            message = "Interrupt Exception"
        super().__init__(message)


class ParseException(Exception):
    def __init__(self, message=None):
        if message is None:
            message = "Parse Exception"
        super().__init__(message)