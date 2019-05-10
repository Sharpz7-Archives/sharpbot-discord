def setup(file):

    commands = [
        ("player", "/start"),
        ("owner", "/insta inv 1 cat"),
        ("animal", "/pet create cat"),
        ("player", "/inv", ("keyinmessage", "Name: Cat")),
    ]

    file.create_test("pet-test", commands=commands)

    commands = [
        ("player", "/start"),
        ("owner", "/insta inv 1 cat"),
        ("owner", "/insta inv 10 acorn"),
        ("player", "/inv", ("keyinmessage", "Cat - lvl", "Acorn -  10")),
        ("animal", "/pet create cat"),
        ("animal", "/pet feed acorn"),
        ("player", "/inv", ("keyinmessage", "Acorn -  9"))
    ]

    file.create_test("feed-test", commands=commands)
