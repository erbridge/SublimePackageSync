import os
import subprocess

import sublime
import sublime_plugin


class SublimePackageSyncAll(sublime_plugin.ApplicationCommand):

    def __init__(self):
        self.settings = sublime.load_settings(
            "SublimePackageSync.sublime-settings")

    def run(self, autorun=False):
        print("[SublimePackageSync] Syncing all packages.")
        packages_to_sync = self.settings.get("sync_repos")
        installed_packages = os.listdir(sublime.packages_path())
        for package_name in packages_to_sync:
            if autorun and package_name in self.settings.get("auto_sync_ignore"):
                continue
            package = packages_to_sync.get(package_name)
            remotes = package.get("remotes")
            package_path = os.path.join(sublime.packages_path(), package_name)
            if package_name not in installed_packages:
                print("[SublimePackageSync] Cloning " + package_name + ".")
                remotes = self.git_clone(remotes, package_path)
            if self.is_git_repo(package_path):
                print("[SublimePackageSync] Updating " + package_name + ".")
                existing_remotes = self.git_remote_show(package_path)
                self.git_remotes_add(remotes, existing_remotes, package_path)
                self.git_checkout(
                    package.get("object_to_checkout"), package_path)
                self.git_submodule_update(package_path)
        print("[SublimePackageSync] Done!")

    def description(self):
        # TODO: Add a description here.
        return None

    def is_git_repo(self, cwd):
        process = subprocess.Popen(["git", "rev-parse", "--git-dir"],
                                   cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdoutdata, stderrdata = process.communicate()
        if process.returncode != 0:
            print(stdoutdata.decode("utf-8"), end="")
            print(stderrdata.decode("utf-8"), end="")
            raise SublimePackageSyncGitError
        return cwd == os.path.dirname(os.path.join(cwd, stdoutdata.decode("utf-8").strip().split("\n")[0]))

    def git_clone(self, remotes, path):
        if "origin" in remotes:
            remote = remotes.pop("origin")
        else:
            remote = remotes.pop(remotes.keys()[0])
        if not self.report_subprocess(subprocess.Popen(["git", "clone", remote, path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)):
            raise SublimePackageSyncGitError
        return remotes

    def git_remote_show(self, cwd):
        process = subprocess.Popen(
            ["git", "remote", "show"], cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdoutdata, stderrdata = process.communicate()
        if process.returncode != 0:
            print(stdoutdata.decode("utf-8"), end="")
            print(stderrdata.decode("utf-8"), end="")
            raise SublimePackageSyncGitError
        return stdoutdata.decode("utf-8").strip().split("\n")

    def git_remotes_add(self, remotes, existing_remotes, cwd):
        for remote_name in remotes:
            if remote_name not in existing_remotes:
                if not self.report_subprocess(subprocess.Popen(["git", "remote", "add", remote_name, remotes.get(remote_name)], cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)):
                    raise SublimePackageSyncGitError

    def git_checkout(self, object_to_checkout, cwd):
        if not self.report_subprocess(subprocess.Popen(["git", "checkout", object_to_checkout], cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)):
            raise SublimePackageSyncGitError

    def git_submodule_update(self, cwd):
        if not self.report_subprocess(subprocess.Popen(["git", "submodule", "update", "--init", "--recursive"], cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)):
            raise SublimePackageSyncGitError

    def report_subprocess(self, process):
        stdoutdata, stderrdata = process.communicate()
        if process.returncode == 0:
            return True
        print(stdoutdata.decode("utf-8"), end="")
        print(stderrdata.decode("utf-8"), end="")
        return False


class SublimePackageSyncGitError(Exception):
    pass


if sublime.load_settings("SublimePackageSync.sublime-settings").get("auto_sync"):
    SublimePackageSyncAll().run(autorun=True)
