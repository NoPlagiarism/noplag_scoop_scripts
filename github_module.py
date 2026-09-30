import os

from httpx2 import Client, URL

from base_module import BaseScoopModule, UpdateState

MAX_PAGES = 2

class GHModule(BaseScoopModule):
    def __init__(self, name: str, repo: str, arch_patterns: dict[str, str], extra: dict, *, ignore_prereleases = False):
        self.name = name
        self.repo = repo
        self.arch_patterns = arch_patterns
        self.extra = extra
        self.ignore_prereleases = ignore_prereleases

        gh_token = os.environ.get("GH_TOKEN")
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2026-03-10",
            "User-Agent": "NoplagiScoop"
        }
        if gh_token:
            headers["Authorization"] = "Bearer " + gh_token
        self.client = Client(headers=headers)

        self._cached_data = dict()
    
    def get_releases(self, page: int = 0):
        if (cached_release := self._cached_data.get("releases")) and page == 0:
            return cached_release
        url = URL(f"https://api.github.com/repos/{self.repo}/releases").copy_add_param("per_page", 10).copy_add_param("page", page)
        raw_resp = self.client.get(url)
        resp = raw_resp.json()
        self._cached_data["releases"] = resp
        return resp
    
    def find_latest_release(self, _page = 0):
        releases = self.get_releases(page=_page)
        release = None
        for x in releases:
            if x["prerelease"] and self.ignore_prereleases:
                continue
            release = x
            break
        if release is None:
            if _page >= MAX_PAGES:
                raise Exception(f"Can't find release on repo {self.repo}")
            return self.find_latest_release(_page=_page+1)
        return release
    
    def get_assets_from_release(self, release) -> dict[dict[str, str]] | None:
        assets = dict()
        for arch, pattern in self.arch_patterns.items():
            for asset in release["assets"]:
                if pattern in asset["name"]:
                    found = dict()
                    found["url"] = asset["browser_download_url"]
                    found["hash"] = asset["digest"][7:]
                    assets[arch] = found
        if not assets:
            return None
        return assets
    
    def get_version_from_release(self, release) -> str:
        return release["tag_name"]
    
    def get_assets(self) -> list[dict[str, str]] | None:
        return self.get_assets_from_release(self.find_latest_release())
    
    def create_manifest_part_from_release(self, release=None) -> dict:
        if release is None:
            release = self.find_latest_release()
        manifest = dict()
        manifest["version"] = self.get_version_from_release(release)
        assets = self.get_assets_from_release(release)
        if not assets:
            raise Exception("No assets found")
        manifest["architecture"] = assets
        return manifest
    
    def check_update(self) -> bool:
        if not self.exists():
            self.state = UpdateState.NEW
            return True
        if self.ignore_state == "*":
            return False
        release = self.find_latest_release()
        if self.curver != self.get_version_from_release(release):
            self.state = UpdateState.UPDATE_BUMPED
            self.newver = self.get_version_from_release(release)
            return True
        else:
            if self.submodules:
                for x in self.submodules:
                    if x.check_update():
                        self.state = UpdateState.UPDATE_OTHER
                        return True
            self.state = UpdateState.CLEAR
            return False
    
    def update(self) -> None:
        manifest_data = self.create_manifest_part_from_release()
        self.save_manifest(manifest_data)
