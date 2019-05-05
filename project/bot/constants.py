import os
from pathlib import Path
from string import ascii_uppercase as alphabet
from unicodedata import lookup as emoji

import yaml

p = Path(".")
YML_FILE = (p / "bot" / "files" / "data.yml").as_posix()
COGS_FILE = (p / "bot" / "files" / "cogs.yml").as_posix()
MAP_FILE = (p / "bot" / "files" / "map.png").as_posix()
SEA_FILE = (p / "bot" / "files" / "sea.png").as_posix()
TEMPLATE_FILE = (p / "bot" / "files" / "template.png").as_posix()
FONT_FILE = (p / "bot" / "files" / "celtichand.ttf").as_posix()
SHORE_FILE = (p / "bot" / "files" / "shore.png").as_posix()
CLASSES_FILE = (p / "bot" / "files" / "classes.yml").as_posix()
DEFAULT_CLASSES_FILE = (p / "bot" / "files" / "classes.default.yml").as_posix()
GCONSTANTS_FILE = (p / "bot" / "files" / "constants.yml").as_posix()
DEFAULT_GCONSTANTS_FILE = (p / "bot" / "files" / "constants.default.yml").as_posix()
ARTIFACT_FOLDER = (p / "bot_testing" / "artifacts").as_posix()

CLANS = ["Clan Tiene", "Clan Uisge", "Clan Ogsaidean", "Clan Talamh"]

USER_TABLE = "users"
BUILD_TABLE = "buildings"
BOAT_TABLE = "boats"

DATABASE_NAME = "sharpbot"

PREFIXES = ["/", "!/"]

SEA_CHECKS = 20

HOST = 149286699187437568  # TODO remove this!

OFFICIAL_SERVERS = (
    468432687997124618,  # testing server
    572866688802881560,  # offical server
)

WATER_COLOUR = (0, 148, 255)  # blue
SWAMP_COLOUR = (124, 27, 0)  # some form of brown
LAND_COLOUR = (255, 255, 255)  # white
SHORE_COLOUR = (255, 0, 220)  # pink

CONFIRM_REACTION_TIMEOUT = 5.0  # how long to wait for the user's reaction
MINE_REACTION_TIMEOUT = 5.0  # how long to wait for the user's reaction


WALKING = {}  # stores all people walking
BATTLING = {}  # stores all people battling
SHORE = []  # stores shore points


NUM_TO_ALPHA = alphabet

ALPHA_TO_NUM = {letter: n + 1 for n, letter in enumerate(alphabet)}

try:
    with open(GCONSTANTS_FILE, "r") as f:
        data = yaml.safe_load(f)

except FileNotFoundError:
    with open(DEFAULT_GCONSTANTS_FILE, "r") as f:
        data = yaml.safe_load(f)

if os.environ.get("CICD", "FALSE") == "TRUE":
    with open(DEFAULT_GCONSTANTS_FILE, "r") as f:
        data = yaml.safe_load(f)

# All constants required by the game
EXHAUST_MINE_CHANCE = data.get(
    "EXHAUST_MINE_CHANCE"
)  # the chance of exhausting a coord's materials
TOWNSIZE = data.get("TOWNSIZE")
MAX_FEED_AMOUNT = data.get(
    "MAX_FEED_AMOUNT"
)  # The maximum number of items you can feed a pet
MAX_MINE_AMOUNT = data.get(
    "MAX_MINE_AMOUNT"
)  # the maximum possible yield of materials per attempt


class Emoji:
    """
    Emojis to be called in all files
    """

    pickaxe = emoji("PICK")
    axe = emoji("HAMMER")
    confirm = emoji("WHITE HEAVY CHECK MARK")
    fist = emoji("RAISED FIST")
