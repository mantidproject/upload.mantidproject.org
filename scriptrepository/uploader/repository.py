"""Classes to model a Git repository. Methods just call
out to the shell git command.

The support is limited to the following abilities:
 - pull/push
 - commit
"""
import os
import subprocess

def _shellcmd(cmd, args):
    """Use subprocess to call a given command and return the combined
    stdout/stderr
    """
    return subprocess.check_output(cmd, args, stderr=subprocess.STDOUT,
                                   shell=True)

class GitRepository(object):
    """Models a git repo. Currently it needs to have been cloned first.
    """

    def __init__(self, path):
        if not os.path.exists(path):
            raise ValueError("Unable to find git repository at '{0}'. "\
                             "It must be have been cloned first.".format(path))
        self.root = path

    def commit_and_push(self, commit):
        error = self.commit(commit)
        if error is None:
            return self.push()
        else:
            return error

    def commit(self, commit):
        """Commits all of the changes detailed by the CommitInfo object"""
        pass

    def pull(self, rebase=True):
        pass

    def push(self):
        pass

    def reset(self, sha1, hard=True):
        """Performs a hard reset to the given treeish """
        self._git("reset", args=["--hard",sha1])

    def _git(self, args):
        _shellcmd("git", args)

class GitCommitInfo(object):
    """Models a git commit"""

    def __init__(self, author, email, filelist, committer=None):
        self.author = author
        self.committer = committer if committer is not None else author
        self.email = email
        self.filelist = filelist
