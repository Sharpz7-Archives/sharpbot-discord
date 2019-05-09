def setup(file):
    commands = [
        ("player", "/start"),
        ("owner", "/insta move pthon palace"),
        ("place", "/town info", ("keyinmessage", "Trade A")),
        ("owner", "/insta inv 5 wood"),
        ("player", "/trade A"),
        ("player", "/inv", ("keyinmessage", "Wood -  1"))
    ]

    file.create_test("trade-test", commands=commands)
