def setup(file):
    commands = [
        ("player", "/start"),
        ("owner", "/insta inv 1 rowboat"),
        ("owner", "/insta move shore"),
        ("boat", "/ship sail"),
        ("boat", "/ship info", ("keynotinmessage", "You don't have a boat!")),
        ("boat", "/board"),
        ("owner", "/insta inv 1 rod"),
        ("boat", "/fish")
    ]

    file.create_test("boat-test", commands=commands)

    commands = [
        ("player", "/start"),
        ("owner", "/insta inv 1 cat"),
        ("animal", "/pet cat"),
        ("player", "/inv", ("keyinmessage", "1", "Cat")),
    ]

    file.create_test("pet-test", commands=commands)

    commands = [
        ("player", "/start"),
        ("owner", "/insta inv 1 cat"),
        ("owner", "/insta inv 10 acorn"),
        ("player", "/inv", ("keyinmessage", "1", "Cat", "10", "Acorn")),
        ("animal", "/pet cat"),
        ("animal", "/feed acorn"),
        ("player", "/inv", ("keyinmessage", "9", "Acorn"))
    ]

    file.create_test("feed-test", commands=commands)

    commands = [
        ("default", "/invite"),
        ("default", "/calc 6 + 6"),
        ("default", "/announce"),
        ("default", "/ping"),
    ]

    file.create_test("default-test", commands=commands)

    commands = [
        ("gather", "/mine"),
    ]

    file.create_test("error-test", commands=commands)
