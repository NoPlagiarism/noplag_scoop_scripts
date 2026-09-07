import os
import sys

from shared import COMMIT_MESSAGES
from steal import StealModule
from gh_nightly import GHNightlyModule
from git_commands import Git

MANIFESTS_DICT = {
    "main": [StealModule("fagram", "https://raw.githubusercontent.com/fagramdesktop/fagram-scoop/refs/heads/main/fagram.json")],
    "versions": [
        GHNightlyModule(name="nicotine-plus-git", repo="NoPlagiarism/nicotine-plus", workflow_name="packaging.yml",
                        arch_patterns={"64bit": "windows-x86_64-portable", "32bit": "windows-x86_64-portable", "arm64": "windows-arm64-portable"},
                        branch="temp_nightly",
                        extra={"description": "Graphical client for the Soulseek file sharing network", "homepage": "https://nicotine-plus.org", "license": "GPL-3.0-or-later", "extract_dir": "Nicotine+", "notes": "This is currently using fork with fully portable working. After code merges, it will use original code", "pre_install": [r'if (!(Test-Path \"$dir\\portable")) { New-Item \"$dir\\portable\" -ItemType Directory | Out-Null }'], "persist": "portable", "shortcuts":[["Nicotine+.exe","Nicotine+"]]})
    ]
}
CUR_BUCKET = sys.argv[-1]  # TODO: implement click instead of this
MANIFESTS = MANIFESTS_DICT[CUR_BUCKET]


def main():
    # TODO: async
    print(f"Current bucket: {CUR_BUCKET}")
    git = Git()
    for manifest in MANIFESTS:
        # TODO: actual logging needed LOL
        print(f"Checking {manifest} for updates")
        if manifest.check_update():
            print(f"Found update for {manifest} ({manifest.state})")
            manifest.update()
            assert manifest.state is not None
            commit_msg = COMMIT_MESSAGES[manifest.state].format(name=manifest.name, curver=manifest.curver, newver=manifest.newver)
            git.add_n_commit(manifest.manifest_path, commit_msg=commit_msg)
        else:
            print(f"No updates for {manifest} found")
        # TODO: Implement reverting from .scriptignore here


if __name__ == "__main__":
    main()
