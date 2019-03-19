import asyncio
import os
from importlib import import_module

from bot.constants import ARTIFACT_FOLDER
from bot_testing.objects import File

names = os.listdir("bot_testing/tests")
mods = []
tests = []


# Finds all files in /tests/ to be included
for item in names:
    if item[-3:] == ".py":
        item = item.replace(".py", "")
        mods.append(item)


def run_tests():
    # Create artifacts folder
    try:
        os.mkdir(ARTIFACT_FOLDER)
    except FileExistsError:
        pass

    # Loads all the tests
    print("\nLoading tests for files...")
    print("\n====================")
    for counter, item in enumerate(mods):

        # Imports the file
        test_file = import_module("bot_testing.tests." + item)
        file = File()
        test_file.setup(file)
        print(f"File {test_file.__name__} setup! ({counter+1}/{len(mods)})")

        for test in file.all_tests:
            tests.append(test)

    # Creates a runner for the test
    print("\nCompleted! Ready to start tests...")
    print("\n====================")
    for counter, test in enumerate(tests):
        print(f"Running {test.name}...")

        # Creates a asyncio loop for the test.
        loop = asyncio.get_event_loop()
        loop.run_until_complete(test.runner())
        print(f"Finished {test.name}! ({counter+1}/{len(tests)})")
        print("=============")
