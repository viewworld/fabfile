from fabric.api import *

from . import utils


@task
@utils.inside_project
def manage(command):
    """ Runs django management command.
    Example::

        fab manage:createsuperuser
    """
    run('python manage.py ' + command)

@task
def compile_messages():
    manage('compilemessages')

@task
def syncdb(params=''):
    manage('syncdb --noinput ' + params)

@task
def migrate(fake=False):
    cmd = 'migrate'
    if fake:
        cmd += ' --fake'
    manage(cmd)
