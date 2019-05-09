def setup(file):

    commands = [
        ("player", "/start"),
        ("owner", "/insta inv 1000 wood"),
        ("build", "/build create shack"),
        ("player", "/inv", ("keyinmessage", "Wood -  500")),
        ("build", "/build info", ("keynotinmessage", "You don't have a home!"))
    ]

    file.create_test("build-test", commands=commands)

    commands = [
        ("player", "/start"),
        ("owner", "/insta inv 1000 wood"),
        ("build", "/build create shack"),
        ("player", "/inv", ("keyinmessage", "Wood -  500")),
        ("build", "/build upgrade"),
        ("build", "/build info", ("keynotinmessage", "You don't have a home!"), ("keyinmessage", "Level**: 2")),
        ("player", "/inv", ("keynotinmessage", "Wood"))
    ]

    file.create_test("upgrade-test", commands=commands)

    commands = [
        ("player", "/start"),
        ("owner", "/insta inv 1000 wood"),
        ("build", "/build create shack"),
        ("player", "/inv", ("keyinmessage", "Wood -  500")),
        ("build", "/build store 100 wood"),
        ("build", "/build store 100 wood private"),
        ("player", "/inv", ("keyinmessage", "Wood -  300")),
        ("build", "/build info", ("keyinmessage", "Wood", "100")),
        ("build", "/build withdraw 100 wood"),
        ("build", "/build withdraw 100 wood private", ("keynotinmessage", "You do not own this building!")),
        ("player", "/inv", ("keyinmessage", "Wood -  500")),
        ("build", "/build info", ("keynotinmessage", "Wood - 100"))
    ]

    file.create_test("vault-test", commands=commands)
