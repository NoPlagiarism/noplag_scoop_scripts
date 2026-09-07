import os

from git import Repo, Actor

from shared import ROOT_DIR

import typing as t


class Git:
    def __init__(self) -> None:
        self.repo = Repo(ROOT_DIR)

    def add_n_commit(self, filepath: str | os.PathLike[str], commit_msg: str):
        # TODO: throw away GitPython
        index = self.repo.index
        index.add(filepath)
        author = Actor(name="github-actions[bot]", email="41898282+github-actions[bot]@users.noreply.github.com")
        index.commit(commit_msg, author=author, committer=author)
