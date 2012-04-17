import os.path
import urllib
import urllib2
from fabric.api import *

from . import maintenance, utils, django

@task
def git_push():
    require('ref')
    local('git push {user}@{host}:{project_dir} {refspec}'.format(**env))
    with cd(env.project_dir):
        run('git checkout {0}'.format(env.ref))

@task(default=True)
def deploy(quiet='off', **kwargs):
    """Deploy a ref from the Github repository"""
    git_push()
    env.app.get('post_deploy', post_deploy)(**kwargs)
    if quiet == 'off':
        notify_flowdock()

@task
def rollback(**kwargs):
    with cd(env.project_dir):
        run('git checkout HEAD@{1}')
    env.app.get('post_deploy', post_deploy)(**kwargs)
    notify_flowdock(rollback=True)

def should_run_task(task, on_change=None):
    tasks = {}
    for t in env.app.get('post_deploy_tasks', []):
        roles, sep, t = t.rpartition(':')
        roles = roles.split(',') if roles else []
        tasks[t] = roles
    if task not in tasks:
        return False
    if tasks[task] and not any(env.host_string in env.roledefs[role] for role in tasks[task]):
        return False
    if on_change and not utils.path_changed(on_change):
        return False
    return True

def post_deploy(fake_migration=False, ignore_docs=False):
    tasks = env.app.get('post_deploy_tasks', {})
    if should_run_task('install_req', on_change='requirements.txt'):
        maintenance.install_req()
    if should_run_task('syncdb'):
        django.syncdb()
    if should_run_task('migrate'):
        django.migrate(fake=fake_migration)
    if should_run_task('compile_messages'):
        django.compile_messages()
    if should_run_task('gen_jsdoc', on_change='viewworld/static/js'):
        maintenance.gen_jsdoc()
    if should_run_task('ant_store', on_change='xqueries'):
        maintenance.ant_store()
    if should_run_task('reload_gunicorn'):
        run('/etc/init.d/gunicorn-{0} reload'.format(env.app['name']))
    if should_run_task('restart_celery'):
        run('/etc/init.d/celeryd-{0} restart'.format(env.app['name']))

def abort_deploy():
    with cd(env.project_dir):
        run('git checkout HEAD@{1}')

def get_commit_list():
    commits = run('git log --pretty=oneline --no-color HEAD@{1}...HEAD', pty=False).splitlines()
    commitlist = []
    for commit in commits[:15]:
        chash, msg = commit.split(' ', 1)
        commitlist.append(('<li><a class="commit" href="https://github.com/viewworld/{name}/commit/{hash}">{abbrevhash}</a>'
                           '<span class="message">{msg}</span></li>').format(
                               name=env.app['name'],
                               hash=chash,
                               abbrevhash=chash[0:7],
                               msg=msg))
    if len(commits) > 15:
        commitlist.append('<li>and {0} more...</li>'.format(len(commits)-15))
    return '<div class="commits"><ul class="commit-list">{0}</ul></div>'.format(''.join(commitlist))

notices = []
def notify_flowdock(rollback=False):
    if (env.ref, env.settings) in notices:
        return
    else:
        notices.append((env.ref, env.settings))
    with hide('running', 'stdout'):
        name = local('git config user.name', capture=True)
        email = local('git config user.email', capture=True)
        with cd(env.project_dir):
            new_hash = run('git rev-parse HEAD')
            old_hash = run('git rev-parse HEAD@{1} 2>/dev/null || true')
            if not old_hash:
                old_hash = new_hash
                commits = 'No previous deploy.'
            else:
                commits = get_commit_list()

    data = {
        'source': 'Fabric',
        'from_name': name,
        'from_address': email,
        'link': 'https://github.com/viewworld/{2}/compare/{0}...{1}'.format(
            old_hash, new_hash, env.app['name'])
    }
    if not rollback:
        refname = os.path.basename(env.ref)
        data['subject'] = '{app[name]} {refname} deployed to {host}'.format(refname=refname, **env)
        data['content'] = 'Following commits were deployed: {0}'.format(commits)
        data['tags'] = 'deploy,{app[name]},{settings},{refname}'.format(refname=refname, **env)
    else:
        data['subject'] = '{app[name]} {host} rolled back to {hash}'.format(hash=new_hash[:7], **env)
        data['content'] = 'Following commits were rolled back: {0}'.format(commits)
        data['tags'] = 'rollback,{app[name]},{settings}'.format(**env)
    try:
        urllib2.urlopen('https://api.flowdock.com/v1/messages/influx/901e31b15ef550fca2c0653d436e91d6',
                        urllib.urlencode(data))
    except urllib2.HTTPError as e:
        print e.read()
