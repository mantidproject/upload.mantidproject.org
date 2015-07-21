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
    cmd = cmd + ' '.join(args)
    # The command should always report exit 0 so we can grab the sterr
    cmd += '; exit 0'
    return subprocess.check_output(cmd, stderr=subprocess.STDOUT,
                                   shell=True)

class GitRepository(object):
    """Models a git repo. Currently it needs to have been cloned first.
    """

    def __init__(self, path):
        if not os.path.exists(path):
            raise ValueError('Unable to find git repository at "{0}". '\
                             'It must be have been cloned first.'.format(path))
        self.root = path

    def commit_and_push(self, commit, reset_first=True):
        if reset_first:
            self.reset("origin/master", hard=True)

        error = self.commit(commit)
        if error is None:
            return self.push()
        else:
            return error

    def commit(self, commit):
        """Commits all of the changes detailed by the CommitInfo object"""
        author = '--author "{0} <{1}>"'.format(commit.author, commit.email)
        msg = '--message="{0}"'.format(commit.comment)

        os.environ['GIT_COMMITTER_NAME'] = commit.committer
        del os.environ["GIT_COMMITTER_NAME"]

    def pull(self, rebase=True):
        pass

    def push(self):
        pass

    def reset(self, sha1, hard=True):
        """Performs a hard reset to the given treeish reference"""
        self._git("reset", args=["--hard",sha1])

    def _git(self, cmd, args):
        _shellcmd("git", args)

class GitCommitInfo(object):
    """Models a git commit"""

    def __init__(self, author, email, comment, filelist, committer=None):
        self.author = author
        self.committer = committer if committer is not None else author
        self.email = email
        self.comment = comment
        self.filelist = filelist
