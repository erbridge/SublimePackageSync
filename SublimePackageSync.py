import os
import subprocess

import sublime
import sublime_plugin


class SublimePackageSyncGitError(Exception):
    pass


class SublimePackageSyncCommand(sublime_plugin.ApplicationCommand):

    def __init__(self):
        self.settings = None

    def get_setting(self, key):
        if self.settings is None:
            self.settings = sublime.load_settings(
                "SublimePackageSync.sublime-settings")
        return self.settings.get(key)

    def sync_package(self, package_name, package, installed_packages):
        try:
            remotes = package.get("remotes")
            package_path = os.path.join(sublime.packages_path(), package_name)

            if package_name not in installed_packages:
                print("[SublimePackageSync] Cloning " + package_name + ".")
                remotes = self.git_clone(remotes, package_path)

            if not self.is_git_repo(package_path):
                return

            print("[SublimePackageSync] Updating " + package_name + ".")

            existing_remotes = self.git_remote_show(package_path)
            if not self.git_remotes_check(remotes, existing_remotes, package_path):
                print("[SublimePackageSync] ERROR - Mismatched remote." +
                      " Check your remote settings.")
                return

            self.git_remotes_add(remotes, existing_remotes, package_path)
            self.git_fetch(package_path)
            self.git_checkout(package.get("object_to_checkout"), package_path)
            self.git_submodule_update(package_path)

        except SublimePackageSyncGitError:
            print(
                "[SublimePackageSync] ERROR - Git command failed." +
                " See output above.")

    def is_git_repo(self, cwd):
        process = subprocess.Popen(
            ["git", "rev-parse", "--git-dir"],
            cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdoutdata, stderrdata = process.communicate()
        if process.returncode != 0:
            print(stdoutdata.decode("utf-8"), end="")
            print(stderrdata.decode("utf-8"), end="")
            raise SublimePackageSyncGitError
        return cwd == os.path.dirname(
            os.path.join(
                cwd, stdoutdata.decode("utf-8").strip().split("\n")[0]))

    def git_clone(self, remotes, path):
        if "origin" in remotes:
            remote = remotes.pop("origin")
        else:
            remote = remotes.pop(remotes.keys()[0])
        self.run_git_command(["clone", remote, path])
        return remotes

    def git_remote_show(self, cwd, *args):
        process = subprocess.Popen(
            ["git", "remote", "show"] + list(args),
            cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdoutdata, stderrdata = process.communicate()
        if process.returncode != 0:
            print(stdoutdata.decode("utf-8"), end="")
            print(stderrdata.decode("utf-8"), end="")
            raise SublimePackageSyncGitError

        return stdoutdata.decode("utf-8").strip().split("\n")

    def git_remotes_check(self, remotes, existing_remotes, cwd):
        for remote_name in remotes:
            if remote_name not in existing_remotes:
                continue

            remote_info = self.git_remote_show(cwd, "-n", remote_name)
            for line in remote_info:
                if "Fetch URL:" not in line:
                    continue

                return line.split(" ")[-1].strip(".git") == remotes.get(remote_name).strip(".git")

        return True

    def git_remotes_add(self, remotes, existing_remotes, cwd):
        for remote_name in remotes:
            if remote_name in existing_remotes:
                continue

            self.run_git_command(
                ["remote", "add", remote_name, remotes.get(remote_name)],
                cwd=cwd)

    def git_fetch(self, cwd):
        self.run_git_command(["fetch"], cwd=cwd)

    def git_checkout(self, object_to_checkout, cwd):
        self.run_git_command(["checkout", object_to_checkout], cwd=cwd)

    def git_submodule_update(self, cwd):
        self.run_git_command(
            ["submodule", "update", "--init", "--recursive"], cwd=cwd)

    def run_git_command(self, args, cwd=None):
        if not self.report_subprocess(subprocess.Popen(["git"] + args, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)):
            raise SublimePackageSyncGitError

    def report_subprocess(self, process):
        stdoutdata, stderrdata = process.communicate()
        if process.returncode == 0:
            return True

        print(stdoutdata.decode("utf-8"), end="")
        print(stderrdata.decode("utf-8"), end="")
        return False


class SublimePackageSyncAllCommand(SublimePackageSyncCommand):

    def run(self, autorun=False):
        sublime.set_timeout_async(lambda: self.sync(autorun), 0)

    def description(self):
        # TODO: Add a description here.
        return None

    def sync(self, autorun):
        print("[SublimePackageSync] Syncing all packages.")
        packages_to_sync = self.get_setting("sync_repos")
        installed_packages = os.listdir(sublime.packages_path())
        for package_name in packages_to_sync:
            if autorun and package_name in self.get_setting("auto_sync_ignore"):
                continue
            self.sync_package(
                package_name, packages_to_sync.get(package_name),
                installed_packages)
        print("[SublimePackageSync] Done!")


class SublimePackageSyncSpecificCommand(SublimePackageSyncCommand):

    def run(self):
        synced_packages = self.get_setting("sync_repos")
        synced_package_names = list(synced_packages.keys())
        sublime.active_window().show_quick_panel(
            synced_package_names,
            lambda index: sublime.set_timeout_async(
                lambda: self.sync(
                    synced_package_names[index], synced_packages), 0))

    def description(self):
        # TODO: Add a description here.
        return None

    def sync(self, package_name, synced_packages):
        print("[SublimePackageSync] Syncing " + package_name + ".")
        self.sync_package(
            package_name, synced_packages.get(package_name),
            os.listdir(sublime.packages_path()))
        print("[SublimePackageSync] Done!")


def plugin_loaded():
    if sublime.load_settings("SublimePackageSync.sublime-settings").get("auto_sync"):
        SublimePackageSyncAllCommand().run(autorun=True)
