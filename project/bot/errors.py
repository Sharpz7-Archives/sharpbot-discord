class UserNotFoundError(Exception):
    def __init__(self, message, _id):
        self.id = _id
        self.message = f"{message}: {_id}"

    def __str__(self):
        return self.message


class BoatNotFoundError(Exception):
    def __init__(self, message, _id):
        self.id = _id
        self.message = f"{message}: {_id}"

    def __str__(self):
        return self.message


class TestFailError(Exception):
    def __init__(self, message):
        self.message = f"{message}"

    def __str__(self):
        return self.message
