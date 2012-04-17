from os.path import join
from fabric.api import *

from . import utils


@task
@utils.inside_project
def install_req(update=False):
    """Install python requirements with pip"""
    cmd = run if 'virtualenv_dir' in env else sudo
    cmd('pip install {update} -r requirements.txt'
        .format(update='-U' if update else '', **env))

@task
@utils.inside_project
def ant_store():
    with cd('xqueries'):
        run('ant store')

@task
@utils.inside_project
def gen_jsdoc():
    run('tools/gen_jsdoc.sh')
