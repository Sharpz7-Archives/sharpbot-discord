def setup(file):
    commands = [("gather", "/mine")]

    file.create_test("error-test", commands=commands)
