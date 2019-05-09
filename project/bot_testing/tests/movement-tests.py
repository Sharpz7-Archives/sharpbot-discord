def setup(file):
    commands = [
        ("player", "/start"),
        ("owner", "/insta inv 1 rowboat"),
        ("owner", "/insta move shore"),
        ("boat", "/ship sail"),
        ("boat", "/ship info", ("keynotinmessage", "You don't have a boat!")),
        ("boat", "/ship board"),
        ("owner", "/insta inv 1 rod"),
        ("boat", "/fish"),
    ]

    file.create_test("boat-test", commands=commands)

    commands = [("player", "/start"), ("owner", "/insta move pthon palace")]

    file.create_test("move-test", commands=commands)
