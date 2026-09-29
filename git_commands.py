import os

from git import Repo, Actor

import typing as t


class Git:
    def __init__(self, git_dir) -> None:
        self.repo = Repo(git_dir)

    def add_n_commit(self, filepath: str | os.PathLike[str], commit_msg: str):
        # TODO: throw away GitPython
        index = self.repo.index
        index.add(filepath)
        author = Actor(name="github-actions[bot]", email="41898282+github-actions[bot]@users.noreply.github.com")
        index.commit(commit_msg, author=author, committer=author)
