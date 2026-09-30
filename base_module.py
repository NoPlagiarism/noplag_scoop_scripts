from enum import IntEnum
import os
import json
from functools import cached_property

from shared import UpdateState, check_scriptignore

import typing as t


class BaseScoopModule:
    name: str
    state: UpdateState | None
    bucket_dir = None
    _newver_manual = None
    submodules = None
    extra: dict = dict()

    def __str__(self) -> str:
        return f"{self.name} ({type(self).__name__})"
    
    def sub(self, submodule):
        if not self.submodules:
            self.submodules = list()
        if isinstance(submodule, (tuple, list)):
            self.submodules.append(submodule[0](parent=self, **submodule[1]))
        else:
            self.submodules.append(submodule(parent=self))
        return self
    
    def set_dir(self, dir):
        self.bucket_dir = dir

    def check_update(self) -> bool:
        raise NotImplemented

    def update(self) -> None:
        raise NotImplemented

    @cached_property
    def ignore_state(self) -> str | None:
        return check_scriptignore(self.name)

    @property
    def manifest_path(self) -> str:
        return os.path.join(self.bucket_dir, self.name + ".json")

    def exists(self) -> bool:
        return os.path.exists(self.manifest_path)

    def read_manifest(self) -> t.Optional[dict]:
        if not self.exists():
            return None
        with open(self.manifest_path, mode="r", encoding="utf-8") as f:
            data = json.load(f)
        return data

    @property
    def curver(self) -> t.Optional[str]:
        data = self.read_manifest()
        if not data:
            return None
        return data["version"]

    @property
    def newver(self) -> t.Optional[str]:
        return self.__dict__.get("new", dict()).get("version") or self._newver_manual
    
    @newver.setter
    def newver(self, val: str) -> None:
        self._newver_manual = val

    def save_manifest(self, data: dict, *, inject_extra: bool = True):
        if inject_extra:
            data = self.extra | data
        if self.submodules:
            for x in self.submodules:
                data = x.edit_manifest(data)
        with open(self.manifest_path, mode="w+", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
            f.write("\n")


class BaseScoopSubmodule:
    parent: BaseScoopSubmodule

    def __init__(self, parent):
        self.parent = parent

    def check_update(self) -> bool:
        raise NotImplemented
    
    def edit_manifest(self, manifest_data: dict) -> dict:
        raise NotImplemented
