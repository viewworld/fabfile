import os.path
from contextlib import contextmanager
from functools import wraps
from fabric.api import *
from fabric.operations import _shell_escape


def virtualenv():
    """
    Context manager. Use it for perform actions with virtualenv activated::

        with virtualenv():
            # virtualenv is active here

    """
    if not 'virtualenv_dir' in env:
        @contextmanager
        def dummy():
            yield
        return dummy()
    else:
        return prefix('source {virtualenv_dir}/bin/activate'.format(**env))

def inside_virtualenv(func):
    """
    Decorator. Use it for perform actions with virtualenv activated::

        @inside_virtualenv
        def my_command():
            # virtualenv is active here

    """
    @wraps(func)
    def inner(*args, **kwargs):
        with virtualenv():
            return func(*args, **kwargs)
    return inner

def inside_project(func):
    """
    Decorator. Use it to perform actions inside remote project dir
    (that's a folder where :file:`manage.py` resides) with
    virtualenv activated::

        from fabric.api import *
        from fab_deploy.utils import inside_project

        @inside_project
        def cleanup():
            # the current dir is a project source dir and
            # virtualenv is activated
            run('python manage.py cleanup')

    """
    @wraps(func)
    def inner(*args, **kwargs):
        with cd(env.project_dir):
            with virtualenv():
                return func(*args, **kwargs)
    return inner

def path_changed(*path):
    with settings(hide('warnings', 'running', 'stdout', 'stderr'),
                  warn_only=True):
        with cd(env.project_dir):
            return run('git diff --quiet HEAD@{1} -- ' +
                       os.path.join(*path)).failed

