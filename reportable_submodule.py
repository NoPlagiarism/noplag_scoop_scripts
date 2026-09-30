from github_module import GHModule
from base_module import UpdateState, BaseScoopSubmodule, BaseScoopModule


class RePortableSub(BaseScoopSubmodule):
    HOOKSHOT_VERSION = "v2.0.0"
    PATHWINDER_VERSION = "v1.2.0"
    DOWNLOADS = {
            "url": [
                f"https://github.com/samuelgr/Hookshot/releases/download/{HOOKSHOT_VERSION}/Hookshot-{HOOKSHOT_VERSION}.zip",
                f"https://github.com/samuelgr/Pathwinder/releases/download/{PATHWINDER_VERSION}/Pathwinder-{PATHWINDER_VERSION}.zip"
            ],
            "hash": [
                "d41d150330249a564672cbe3a2f5b02bc7b4cecd36022bcfaf1b275e5b556d99",
                "6d18c499c818dba7f249172758f6dfdeadebdd5ff60d6a071cdec332c9c1e3d9"
            ]}
    # TODO(32bit): support extraction of 32bit.. Through post_install?
    EXTRACT_DIR = [f"Hookshot-{HOOKSHOT_VERSION}/x64",f"Pathwinder-{PATHWINDER_VERSION}/x64"]

    def __init__(self, parent: BaseScoopModule, redirects: list[list[str]]):
        self.parent = parent
        self.redirects = redirects

    @classmethod
    def deps_needs_update(cls, manifest_data: dict) -> bool:
        manifest_arch: dict = manifest_data["architecture"]
        if "arm64" in manifest_arch:
            raise ValueError("arm64 is not supported by RePortable")
        if "32bit" in manifest_arch: # TODO(32bit)
            raise NotImplementedError("32bit is not supported by RePortable yet")
        manifest_downloads = manifest_arch[list(manifest_arch.keys())[0]]
        rp_man_downloads = {"url": manifest_downloads["url"][1:3], "hash": manifest_downloads["hash"][1:3]}
        return rp_man_downloads != cls.DOWNLOADS
    
    def check_update(self) -> bool:
        if self.parent.exists():
            return self.deps_needs_update(self.parent.read_manifest())
        return False
    
    def edit_manifest(self, manifest_data: dict) -> dict:
        # Extract dir
        if "extract_dir" not in manifest_data:
            manifest_data["extract_dir"] = []
            if isinstance(manifest_data["architecture"][list(manifest_data["architecture"].keys())[0]]["url"], str):
                manifest_data["extract_dir"].append("")
            else:
                for _ in range(len(manifest_data["architecture"][arch]["url"])):
                    manifest_data["extract_dir"].append("")
        else:
            if isinstance(manifest_data["extract_dir"], str):
                manifest_data["extract_dir"] = [manifest_data["extract_dir"]]
        manifest_data["extract_dir"].extend(self.EXTRACT_DIR)
        # Downloads
        if "32bit" in manifest_data["architecture"]: # TODO(32bit)
            raise NotImplementedError("32bit is not supported by RePortable yet")
        for arch in manifest_data["architecture"]:
            if isinstance(manifest_data["architecture"][arch]["url"], list):
                manifest_data["architecture"][arch]["url"] = [manifest_data["architecture"][arch]["url"][0]] + self.DOWNLOADS["url"] + manifest_data["architecture"][arch]["url"][1:]
                manifest_data["architecture"][arch]["hash"] = [manifest_data["architecture"][arch]["hash"][0]] + self.DOWNLOADS["hash"] + manifest_data["architecture"][arch]["hash"][1:]
            else:
                manifest_data["architecture"][arch]["url"] = [manifest_data["architecture"][arch]["url"]] + self.DOWNLOADS["url"]
                manifest_data["architecture"][arch]["hash"] = [manifest_data["architecture"][arch]["hash"]] + self.DOWNLOADS["hash"]
        # Post install
        post_install_script = "# RePortable by NoPlagiarism"
        binaries = set()
        for x in manifest_data.get("shortcuts", []):
            if not x[0].endswith(".exe"):
                continue  # skip all non-exe
            binaries.add(x[0])
        if "bin" in manifest_data:
            if isinstance(manifest_data["bin"], str):
                binaries.add(manifest_data["bin"])
            else:
                for x in manifest_data["bin"]:
                    binaries.add(x)
        if len(binaries) != 1:
            raise ValueError("Only 1 binary is supported")
        binary = binaries.pop()
        post_install_script += f"\nMove-Item $dir\\{binary} $dir\\_HookshotLauncher_{binary}"
        # TODO(32bit)
        post_install_script += f"\nMove-Item $dir\\HookshotLauncher.64.exe $dir\\{binary}"
        pathwinder_config = ""
        vars_needed = False
        for i, x in enumerate(self.redirects):
            name = f"RP_{self.parent.name}_{i}"
            xx = x
            if "%CONF" in xx[0] or "%CONF" in xx[1]:
                vars_needed = True
            xx[0] = f"OriginDirectory = {xx[0]}"
            xx[1] = f"TargetDirectory = {xx[1]}"
            fpn = 2
            if len(xx) > 2 and xx[2] in ("Simple", "Overlay"):
                xx[2] = f"RedirectMode = {xx[2]}"
                fpn = 3
            for j in range(len(xx), fpn):
                xx[j] = f"FilePattern = {xx[j]}"
            pathwinder_config += f"[FilesystemRule:{name}]\n"
            pathwinder_config += "\n".join(xx)
            pathwinder_config += "\n"
        if vars_needed:
            vars_definition = "[Definitions]\n" \
            f"ScoopPersistApp = $persist_dir\\{self.parent.name}\n\n"
            pathwinder_config = vars_definition + pathwinder_config
        pathwinder_string = pathwinder_config.replace("\n", "`n").replace('"', '\\"').replace("\\", "\\\\")
        post_install_script += f"\n$pwContent = \"{pathwinder_string}\""
        post_install_script += "\nif (Test-Path \"$dir\\Pathwinder.ini\") { Remove-Item \"$dir\\Pathwinder.ini\" -Force }"
        post_install_script += "\nSet-Content -Path \"$dir\\Pathwinder.ini\" -Value $pwContent -Force"
        manifest_data["post_install"] = post_install_script.split("\n")
        # notes
        if "notes" not in manifest_data:
            manifest_data["notes"] = list()
        notes_rp = list()
        notes_rp.append("This is manifest from RePortable bucket, which hooks executable to be portable again using Pathwinder and Hookshot")
        notes_rp.append("By using this manifest, you agree to be aware of bugs and do not harass/reach out to developers of included apps about bugs caused by this manifest (Please test everything thoroughly)")
        notes_rp.append("You can see current redirects in $dir\\Pathwinder.ini")
        manifest_data["notes"].extend(notes_rp)
        return manifest_data
