import httpx

from base_module import BaseScoopModule, UpdateState
# from shared import get_sha256_from_string, get_sha256_from_string_file


class StealModule(BaseScoopModule):
    def __init__(self, name: str, url: str) -> None:
        super().__init__()
        self.name, self.url = name, url
        self.new = None
        self.new_text = None
        self.state = None

    def download_new(self) -> None:
        resp = httpx.get(self.url)
        self.new = resp.json()
        self.new_text = resp.text

    def check_update(self) -> bool:
        if not self.exists():
            self.state = UpdateState.NEW
            return True
        if self.ignore_state == "*":
            return False
        # cursha = get_sha256_from_string_file(self.manifest_path)
        self.download_new()
        assert self.new_text is not None and self.new is not None
        if self.new["version"] == self.ignore_state:
            self.state = UpdateState.IGNORED
            return False
        # mirsha = get_sha256_from_string(self.new_text)
        cur = self.read_manifest()
        if self.new == cur:
            self.state = UpdateState.CLEAR
            return False
        if self.curver != self.new["version"]:
            self.state = UpdateState.UPDATE_BUMPED
        else:
            self.state = UpdateState.UPDATE_OTHER
        return True

    def update(self) -> None:
        if self.new is None:
            self.download_new()
        assert self.new is not None
        self.save_manifest(self.new)
