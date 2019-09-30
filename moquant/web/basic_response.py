class BasicResponse(object):
    code: int
    message: str
    data: object

    def __init__(self, code: int, message: str, data: object):
        self.code = code
        self.message = message
        self.data = data
