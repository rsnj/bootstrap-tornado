from fabric.api import *
from fabric.contrib.files import append, exists
from fabric.contrib.project import rsync_project
from jinja2 import Environment, PackageLoader
import boto
from boto.route53.record import ResourceRecordSets

def install_requirements():
    put('./requirements.txt', 'requirements.txt')
    with prefix('workon %(name)s' % env):
        run('pip install -r ~/requirements.txt')
    run('rm ~/requirements.txt')

def bootstrap():
    with settings(warn_only=True):
        # just in case it already exists, let's ditch it
        run('rmvirtualenv %(name)s' % env)

    run('mkvirtualenv %(name)s' % env)
    install_requirements()

    #create website path
    if not exists(env.path):
        sudo('mkdir -p %(path)s' % env)
        sudo('chown ubuntu %(path)s' % env)
        run('mkdir -p %(path)s/logs' % env)

    configure_nginx()
    configure_supervisor()
    deploy()
    #configure_domain()

def deploy():
    if not exists(env.path):
        #First deploy to the server
        bootstrap()
        return

    install_requirements()
    rsync_project(env.path, local_dir="website/", exclude=env.exclude_list)
    #put("website/settings.%(environment)s.py" % env, "%(path)s/settings.py" % env)
    put("website/static/robots.%(environment)s.txt" % env, "%(path)s/static/robots.txt" % env)

    restart()

def restart():
    if env.instance_names:
        for instance_name in env.instance_names:
            sudo('supervisorctl restart %(name)s:' % env + instance_name)

jinja = Environment(loader=PackageLoader('fabfile', 'config'))
def configure_nginx():
    template = jinja.get_template('nginx.env.conf')

    f = open('/tmp/nginx-%(name)s.conf' % env, 'w')
    f.write(template.render(**env))
    f.close()

    put('/tmp/nginx-%(name)s.conf' % env, '/usr/local/nginx/conf/vhosts/%(name)s.conf' % env, use_sudo=True)
    sudo('service nginx restart')

def configure_supervisor():
    template = jinja.get_template('supervisord.env.conf')

    f = open('/tmp/supervisor-%(name)s.conf' % env, 'w')
    f.write(template.render(**env))
    f.close()

    put('/tmp/supervisor-%(name)s.conf' % env, '/etc/supervisord/%(name)s.conf' % env, use_sudo=True, mode=644)
    sudo('service supervisord restart')

def configure_domain():
    conn = boto.connect_route53()
    changes = ResourceRecordSets(conn, env.hosted_zone_id)

    for url in env.urls:
        change = changes.add_change("CREATE", url,"CNAME")
        change.add_value(env.public_host)
    changes.commit()

def remove_domain():
    conn = boto.connect_route53()
    changes = ResourceRecordSets(conn, env.hosted_zone_id)
    for url in env.urls:
        change = changes.add_change("DELETE", url,"CNAME")
        change.add_value(env.public_host)
    changes.commit()

def destroy():
    with settings(warn_only=True):
        run('rmvirtualenv %(name)s' % env)

        sudo('rm /usr/local/nginx/conf/vhosts/%(name)s.conf' % env)
        sudo('rm /etc/supervisord/%(name)s.conf' % env)
        sudo('rm -r %(path)s' % env)

        sudo('service supervisord restart')
        sudo('service nginx restart')

        remove_domain()