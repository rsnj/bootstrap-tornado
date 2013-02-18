from fabric.api import *
from deploy import deploy, destroy
from webserver import build_webserver

env.exclude_list = ('*.pyc', 'config', 'bin', 'build,' 'include', 'lib', 'share', ".*", "settings.py", "*.dev.*", "*.staging.*", "*.production.*")
env.user = 'ubuntu'
env.name = 'bootstrap'
env.path = '/srv/www/' + env.name
env.start_port = 8010
env.hosted_zone_id = ''

def dev():
    env.environment = 'dev'
    env.hosts = ['54.235.201.207']
    env.urls = ['%(environment)s.%(name)s.labsmb.com' % env]
    env.public_host = 'ec2-54-234-52-125.compute-1.amazonaws.com'
    build_instances(2)

def staging():
    env.environment = 'staging'
    env.hosts = ['ec2-184-73-214-246.compute-1.amazonaws.com']
    env.urls = ['%(environment)s.%(name)s.labsmb.com' % env]
    env.public_host = 'ec2-23-21-172-14.compute-1.amazonaws.com'
    build_instances(2)

def production():
    env.environment = 'production'
    env.hosts = ['ec2-23-23-80-57.compute-1.amazonaws.com']
    env.urls = ['%(name)s.labsmb.com' % env]
    env.public_host = 'Prod-ELB01-1322507128.us-east-1.elb.amazonaws.com'
    build_instances(2)

def build_instances(total):
    env.instance_names = []
    env.instance_ports = []
    for i in range(0, total):
        env.instance_names.append('server-' + str(env.start_port+i))
        env.instance_ports.append(env.start_port + i)