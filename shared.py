import os
from enum import IntEnum
import hashlib
from functools import cache

SCRIPTS_DIR = os.path.dirname(__file__)
ROOT_DIR = os.path.dirname(SCRIPTS_DIR)
BUCKET_DIR = os.path.join(ROOT_DIR, "bucket")

class UpdateState(IntEnum):
    # REVERT_NEEDED = -3
    IGNORED = -2
    NEW = -1          # NEW BUCKET
    CLEAR = 0         # NOT NEEDED AT ALL
    UPDATE_BUMPED = 1 # UPDATE WITH CLEAR NEW VERSION
    FIX_HASHES = 2    # JUST FIX THE HASHES
    UPDATE_OTHER = 10 # UPDATE WITH NO CLEAR BUMPS

COMMIT_MESSAGES = {
    UpdateState.NEW: "{name}: add version {curver}",
    UpdateState.UPDATE_BUMPED: "{name}: Update to version {newver}",
    UpdateState.FIX_HASHES: "{name}@{curver}: Fix hash",
    UpdateState.UPDATE_OTHER: "{name}@{curver}: Update"
}

def get_sha256_from_string(string: str):
    return get_sha256_from_contents(string.encode("utf-8"))

def get_sha256_from_contents(contents):
    digest = hashlib.sha256(contents)
    return digest.hexdigest()

def get_sha256_from_string_file(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        data = f.read()
    return get_sha256_from_string(data)


def get_sha256_from_file(filepath):
    with open(filepath, "rb") as f:
        digest = hashlib.file_digest(f, "sha256")
    return digest.hexdigest()

def get_scriptignore_raw():
    with open(os.path.join(SCRIPTS_DIR, ".scriptignore"), "r", encoding="utf-8") as f:
        lines = f.read().strip("\n").split("\n")
    return lines

@cache
def get_scriptignore() -> dict[str, str]:
    lines_str = get_scriptignore_raw()
    return {x.split("@")[0]: x.split("@")[1] for x in lines_str}

def check_scriptignore(manifest_name: str) -> str | None:
    return get_scriptignore().get(manifest_name)
