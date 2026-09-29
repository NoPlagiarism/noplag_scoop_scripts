from shared import PARENT_DIR
from git.index import typ
import os
import sys

import click

from shared import COMMIT_MESSAGES
from steal import StealModule
from gh_nightly import GHNightlyModule
from git_commands import Git

MANIFESTS_DICT = {
    "main": [StealModule("fagram", "https://raw.githubusercontent.com/fagramdesktop/fagram-scoop/refs/heads/main/fagram.json")],
    "versions": [
        GHNightlyModule(name="nicotine-plus-git", repo="NoPlagiarism/nicotine-plus", workflow_name="packaging.yml",
                        arch_patterns={"64bit": "windows-x86_64-portable", "32bit": "windows-x86_64-portable", "arm64": "windows-arm64-portable"},
                        branch="master",
                        extra={"description": "Graphical client for the Soulseek file sharing network", "homepage": "https://nicotine-plus.org", "license": "GPL-3.0-or-later", "extract_dir": "Nicotine+", "pre_install": [r'if (!(Test-Path \"$dir\\portable")) { New-Item \"$dir\\portable\" -ItemType Directory | Out-Null }'], "persist": "portable", "shortcuts":[["Nicotine+.exe","Nicotine+"]]})
    ]
}

@click.command()
@click.argument("cur_bucket", type=str)
@click.option("--dir", type=click.Path(dir_okay=True, file_okay=False, writable=True, readable=True, resolve_path=True), default=PARENT_DIR)
@click.option("--dry-run", is_flag=True, default=False, flag_value=True)
def cli(cur_bucket: str, dir, dry_run: bool):
    # TODO: async
    click.echo(f"Current bucket: {cur_bucket}")
    bucket_dir = os.path.join(dir, "bucket")
    manifests = MANIFESTS_DICT[cur_bucket]
    git = None
    if not dry_run:
        git = Git(git_dir=dir)
    else:
        click.echo("Dry run is on, no actual git commits will be made")
    for manifest in manifests:
        manifest.set_dir(bucket_dir)
        # TODO: actual logging needed LOL
        click.echo(f"Checking {manifest} for updates")
        if manifest.check_update():
            click.echo(f"Found update for {manifest} ({manifest.state})")
            manifest.update()
            assert manifest.state is not None
            commit_msg = COMMIT_MESSAGES[manifest.state].format(name=manifest.name, curver=manifest.curver, newver=manifest.newver)
            if not dry_run:
                git.add_n_commit(manifest.manifest_path, commit_msg=commit_msg)
            else:
                click.echo(f"Tried to commit '{commit_msg}'")
        else:
            click.echo(f"No updates for {manifest} found")
        # TODO: Implement reverting from .scriptignore here


if __name__ == "__main__":
    cli()
