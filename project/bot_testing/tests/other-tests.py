def setup(file):

    commands = [
        ("default", "/invite"),
        ("default", "/calc 6 + 6"),
        ("default", "/announce"),
        ("default", "/ping"),
    ]

    file.create_test("default-test", commands=commands)
