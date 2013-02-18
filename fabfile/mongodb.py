from fabric.api import *
from fabric.contrib.files import append, exists

def build_mongodb():
    if exists('/etc/update-motd.d/51_update-motd'):
        sudo('rm /etc/update-motd.d/51_update-motd')
    sudo('apt-get update')
    sudo('apt-get -y upgrade')
    install_mongodb()

def install_mongodb():
    """
     http://www.mongodb.org/display/DOCS/Ubuntu+and+Debian+packages
     http://www.zacwitte.com/how-to-set-up-ubuntu-w-mongodb-replica-sets-on-amazon-ec2
    """
    sudo('apt-key adv --keyserver keyserver.ubuntu.com --recv 7F0CEB10')
    append('/etc/apt/sources.list', 'deb http://downloads-distro.mongodb.org/repo/ubuntu-upstart dist 10gen', use_sudo=True)
    sudo('apt-get update')
    sudo('apt-get -y install mongodb-10gen')

    sudo('mkfs -t ext4 /dev/sdf')
    sudo('mkdir /db')
    append('/etc/fstab', '/dev/sdf     /db     auto    noatime,noexec,nodiratime 0 0', use_sudo=True)
    sudo('mount /dev/sdf /db')
    sudo('mkdir /db/mongodb')
    sudo('chown mongodb:mongodb /db/mongodb')
    #Edit /etc/mongodb.conf  -  dbpath=/db/mongodb