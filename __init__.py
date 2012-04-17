from fabric.api import *
import os.path

from . import deploy
from . import maintenance as maint
from . import django

import app

env.use_ssh_config = True
env.app = app.APP
env.user = 'appmgr'
env.project_dir = os.path.join('~/src', env.app['name'])
env.virtualenv_dir = os.path.join('~/venv', env.app['name'])
env.settings = 'undefined'
env.roledefs = {
    'app': [],
    'web': [],
    'worker': []
}
if not env.roles:
    env.roles = list(env.roledefs.keys())


def app_roledefs(roledefs):
    for k in roledefs.keys():
        if k not in env.app['roles']:
            roledefs[k] = []
    return roledefs


"""
Environments
"""
@task
def prod():
    """Work on production environment"""
    env.settings = 'production'
    env.roledefs = app_roledefs({
        'app':    ['viewworld.dk'],
        'web':    ['viewworld.net'],
        'worker': ['worker1.viewworld.dk'],
    })
    print env.roledefs

@task
def test():
    """Work on staging environment"""
    env.settings = 'test'
    env.roledefs = app_roledefs({
        'app':    ['test.viewworld.dk'],
        'web':    [],
        'worker': [],
    })

@task
def dev():
    """Work on staging environment"""
    env.settings = 'development'
    env.roledefs = app_roledefs({
        'app':    [],
        'web':    [],
        'worker': [],
    })


"""
Branches
"""
@task
def branch(branch_name):
    """Work on the specified branch"""
    env.ref = 'origin/{0}'.format(branch_name)
    env.refspec = '+{0}:refs/remotes/origin/{0}'.format(branch_name)

@task
def master():
    """Work on master branch"""
    branch('master')

@task
def next():
    """Work on next branch"""
    branch('next')

@task
def release(version):
    """Work on a release branch"""
    branch('release/{0}'.format(version))

@task
def tag(tag_name):
    """Work on the specified tag"""
    env.ref = tag_name
    env.refspec = '+{0}:refs/tags/{0}'.format(tag_name)


"""
Services
"""
@task
def start(service):
    """Start a service"""
    sudo('/etc/init.d/{0} start'.format(service))

@task
def stop(service):
    """Stop a service"""
    sudo('/etc/init.d/{0} stop'.format(service))

@task
def restart(service):
    """Restart a service"""
    sudo('/etc/init.d/{0} restart'.format(service))

@task
def reload(service):
    """Reload a service"""
    sudo('/etc/init.d/{0} reload'.format(service))

@task
def whoami():
    run('whoami')
