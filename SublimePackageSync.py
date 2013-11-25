import os
import subprocess

import sublime
import sublime_plugin


class SublimePackageSyncAll(sublime_plugin.ApplicationCommand):

    def __init__(self):
        self.settings = sublime.load_settings(
            "SublimePackageSync.sublime-settings")

    def run(self, autorun=False):
        packages_to_sync = self.settings.get("sync_repos")
        installed_packages = os.listdir(sublime.packages_path())
        for package_name in packages_to_sync:
            if autorun and package_name in self.settings.get("auto_sync_ignore"):
                return
            package = packages_to_sync.get(package_name)
            remotes = package.get("remotes")
            package_path = os.path.join(sublime.packages_path(), package_name)
            if package_name not in installed_packages:
                remotes = self.git_clone(remotes, package_path)
            # FIXME: Check we're in a git repo before continuing.
            self.git_remotes_add(remotes, package_path)
            self.git_checkout(package.get("object_to_checkout"), package_path)
            # TODO: Update submodules.

    def description(self):
        # TODO: Add a description here.
        return None

    def git_clone(self, remotes, path):
        if "origin" in remotes:
            remote = remotes.pop("origin")
        else:
            remote = remotes.pop(remotes.keys()[0])
        if not self.report_subprocess(subprocess.Popen(["git", "clone", remote, path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)):
            raise SublimePackageSyncGitError
        return remotes

    def git_remotes_add(self, remotes, cwd):
        # FIXME: Ignore remotes that already exist.
        for remote_name in remotes:
            if not self.report_subprocess(subprocess.Popen(["git", "remote", "add", remote_name, remotes.get(remote_name)], cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)):
                raise SublimePackageSyncGitError

    def git_checkout(self, object_to_checkout, cwd):
        if not self.report_subprocess(subprocess.Popen(["git", "checkout", object_to_checkout], cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)):
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
