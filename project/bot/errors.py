class UserNotFoundError(Exception):
    def __init__(self):
        pass


class UserNotOwner(Exception):
    def __init__(self):
        pass


class BoatNotFoundError(Exception):
    def __init__(self):
        pass


class TestFailError(Exception):
    def __init__(self, message):
        self.message = f"{message}"

    def __str__(self):
        return self.message
