"""
POKE fab commands
"""
import sys
import os
from datetime import datetime
from datetime import timedelta
from fabric.api import require, env, run, local
from pyvcs.backends import get_backend


class VCS(object):

    def __init__(self, repo):
        self.repo = repo
        def _ctx_to_commit(ctx):
            commit = self.repo._old_ctx_to_commit(ctx)
            commit.commit_id = ctx.hex()
            return commit
        self.repo._old_ctx_to_commit = self.repo._ctx_to_commit
        self.repo._ctx_to_commit = _ctx_to_commit

    def __getattr__(self, name):
        if hasattr(self.repo, name):
            return getattr(self.repo, name)
        return object.__getattribute__(self, name)

    def get_last_commit(self):
        # by default repo.get_recent_commits looks back 5 days. that takes
        # ages and so we just look for the last day
        yesterday = datetime.now() + timedelta(hours=-24)
        return self.repo.get_recent_commits(yesterday)[0]


def vcs_factory(fab_root):
    vcs_type = env.get('vcs', 'hg')
    vcs = get_backend(vcs_type)
    return VCS(vcs.Repository(fab_root))


def set_environ(name):
    vcs_path = env.get('vcs_path', caller_directory(1))
    env.repo = vcs_factory(vcs_path)
    env.target = name
    env.venv = '%s/%s.%s' % (env.root, env.target, env.project)
    env.rollback_logfile = os.path.join(env.venv, 'log', 'rollback.log')
    deploy()


def caller_directory(level=0):

    # this is always called from somewhere else so it *might* be safe to
    # always increase the frame we examine
    f = sys._getframe(level + 1)
    caller = f.f_code
    return os.path.dirname(caller.co_filename)


def rollback():
    require()


def deploy(revision='default'):
    require('target', used_for=u'determining which environment to deploy to')
    commit = env.repo.get_last_commit()
    env.rev = commit.commit_id
    env.username = os.environ['USER']
