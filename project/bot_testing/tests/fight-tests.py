def setup(file):

    commands = [
        ("player", "/start"),
        ("owner", "/insta inv 1 shield"),
        ("owner", "/insta inv 1 wood"),
        ("fight", "/f assign shield 1"),
        ("fight", "/f assign wood 2", ("keyinmessage", "You can not put this item here!")),
        ("fight", "/f info", ("keyinmessage", "Shield"))
    ]

    file.create_test("assignment-test", commands=commands)
