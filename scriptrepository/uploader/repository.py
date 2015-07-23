"""Classes to model a Git repository. Methods just call
out to the shell git command.

The support is limited to the following abilities:
 - pull/push
 - commit
"""
from contextlib import contextmanager
import os
import subprocess as subp
import time

# ------------------------------------------------------------------------------
# Helper Functions
# ------------------------------------------------------------------------------
def _git(cmd, args):
    args.insert(0, cmd)
    return _shellcmd("git", args)

#-------------------------------------------------------------------------------
def _shellcmd(cmd, args=[]):
    """Use subprocess to call a given command.
    Return stdout/stderr if an error occurred
    """
    #cmd = '{0} {1}'.format(cmd, ' '.join(args))
    cmd = [cmd]
    cmd.extend(args)
    open("/tmp/mylog.txt","a").write(str(cmd))
    try:
        p = subp.Popen(cmd, stdout=subp.PIPE, stderr=subp.PIPE)
    except ValueError, err:
        raise RuntimeError(err)
    stdout, stderr = p.communicate()
    if p.returncode == 0:
        return stdout
    else:
        raise RuntimeError(stdout + stderr)

#-------------------------------------------------------------------------------
@contextmanager
def transaction(git_repo):
    dir_on_enter = os.getcwd()
    os.chdir(git_repo.root)
    git_repo.begin()
    try:
        yield None
    except Exception, exc:
        git_repo.rollback()
        os.chdir(dir_on_enter)
        raise exc
    else:
        os.chdir(dir_on_enter)

# ------------------------------------------------------------------------------
# Classes
# ------------------------------------------------------------------------------
class GitRepository(object):
    """Models a git repo. Currently it needs to have been cloned first.
    """

    def __init__(self, path):
        if not os.path.exists(path):
            raise ValueError('Unable to find git repository at "{0}". '\
                             'It must be have been cloned first.'.format(path))
        self.root = path

    def begin(self):
        """Capture the current state so that we can rollback"""
        self._sha1_at_begin = _git("rev-parse", ["HEAD"]).rstrip()

    def rollback(self):
        self.reset(self._sha1_at_begin)

    def commit_and_push(self, commit, add_changes=True):
        """This method is transactional. Any failure results in everything
        being rolled back
        """
        with transaction(self):
            remote, branch = "origin", "master"
            # If anyone has messed around locally,
            # make sure we are at the current origin
            self.reset(remote + "/" + branch)
            # Update
            self.pull(rebase=True)
            if add_changes:
                pub_date = self._published_date(commit.filelist[0])
                self.add(commit.filelist)
            else:
                self.remove(commit.filelist)
                pub_date = ''
            self.commit(commit.author, commit.email,
                        commit.committer, commit.comment)
            self.push(remote, branch)

        return pub_date

    def reset(self, sha1):
        """Performs a hard reset to the given treeish reference"""
        return _git("reset", args=["--hard",sha1])

    def add(self, filelist):
        _git("add", filelist)

    def remove(self, filelist):
        _git("rm", filelist)

    def commit(self, author, email, committer, msg):
        """Commits all of the changes detailed by the CommitInfo object"""
        author = '--author="{0} <{1}>"'.format(author, email)
        #open("/tmp/mylog.txt","w").write(msg)
        msg = '-m {0}'.format(msg)

        # Only way to reset the committer without
        os.environ['GIT_COMMITTER_NAME'] = committer
        _git('commit',[msg, author])
        del os.environ["GIT_COMMITTER_NAME"]

    def _published_date(self, filepath):
        timeformat = "%Y-%b-%d %H:%M:%S"
        stat = os.stat(filepath)
        modified_time = int(stat.st_mtime)
        # The original code added 2 minutes to the modification date of the file
        # so we preserve this behaviour here
        return time.strftime(timeformat, time.gmtime(modified_time + 120))

    def pull(self, rebase=True):
        args = ["--rebase"] if rebase else []
        _git("pull", args)

    def push(self, remote, branch):
        _git("push", [remote, branch])

#-------------------------------------------------------------------------------
class GitCommitInfo(object):
    """Models a git commit"""

    def __init__(self, author, email, comment, filelist, committer=None, add=True):
        self.author = author
        self.committer = committer if committer is not None else author
        self.email = email
        self.comment = comment
        self.filelist = filelist
        self.add = add
