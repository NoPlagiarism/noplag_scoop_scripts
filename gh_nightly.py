import os

import httpx

from base_module import BaseScoopModuleWithExtra, UpdateState

class GHNightlyModule(BaseScoopModuleWithExtra):
    def __init__(self, name: str, repo: str, workflow_name: str, arch_patterns: dict[str, str], extra: dict, branch = None):
        self.name = name
        self.repo = repo
        self.workflow_name = workflow_name
        self.branch = branch
        self.arch_patterns = arch_patterns
        self.extra = extra

        gh_token = os.environ.get("GH_TOKEN")
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2026-03-10",
            "User-Agent": "NoplagiScoop"
        }
        if gh_token:
            headers["Authorization"] = "Bearer " + gh_token
        self.client = httpx.Client(headers=headers)

        self._cached_data = dict()

    @staticmethod
    def from_sha_to_ver(head_sha: str):
        return head_sha[:9]

    def get_runs(self) -> list[dict]:
        if cached_runs := self._cached_data.get("runs"):
            return cached_runs
        url = httpx.URL("https://api.github.com/repos/").join(f"{self.repo}/actions/runs")
        raw_resp = self.client.get(url)
        resp = raw_resp.json()
        self._cached_data["runs"] = resp["workflow_runs"]
        return resp["workflow_runs"]

    def get_artifacts(self, run_id: int) -> list[dict]:
        if cached_artifacts := self._cached_data.get("artifacts"):
            return cached_artifacts
        url = httpx.URL("https://api.github.com/repos/").join(f"{self.repo}/actions/runs/{run_id}/artifacts")
        raw_resp = self.client.get(url)
        resp = raw_resp.json()
        self._cached_data["artifacts"] = resp["artifacts"]
        return resp["artifacts"]

    def find_latest_run(self) -> dict:
        runs = self.get_runs()
        last_run = None
        for x in runs:
            if x["path"].endswith(self.workflow_name) and x["conclusion"] == "success":
                if self.branch:
                    if x["head_branch"] != self.branch:
                        continue
                last_run = x
                break
        if not last_run:
            raise Exception(f"No gh run found for {self.repo} ({self.workflow_name})")
        return last_run

    def check_update(self) -> bool:
        if not self.exists():
            self.state = UpdateState.NEW
            return True
        if self.ignore_state == "*":
            return False
        last_run = self.find_latest_run()
        if self.curver != self.from_sha_to_ver(last_run["head_sha"]):
            self.state = UpdateState.UPDATE_BUMPED
            return True
        else:
            self.state = UpdateState.CLEAR
            return False

    def get_nightly_link_from_artifact(self, artifact_id: int):
        return f"https://nightly.link/{self.repo}/actions/artifacts/{artifact_id}.zip"

    def update(self) -> None:
        manifest_data = {"architecture": dict()}
        last_run = self.find_latest_run()
        manifest_data["version"] = self.from_sha_to_ver(last_run["head_sha"])
        last_run_id = last_run['id']
        artifacts = self.get_artifacts(last_run_id)
        for arch, pattern in self.arch_patterns.items():
            artifact_id = None
            for artifact in artifacts:
                if pattern in artifact["name"]:
                    artifact_id = artifact["id"]
                    break
            if artifact_id is None:
                raise Exception(f"No artifact found for {self.repo} ({arch} {pattern})")
            manifest_data["architecture"][arch] = {"url": self.get_nightly_link_from_artifact(artifact_id), "hash": artifact["digest"][7:]}
        self.save_manifest(manifest_data)
