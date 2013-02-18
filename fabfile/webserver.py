from fabric.api import *
from fabric.contrib.files import append, exists

def build_webserver():
    #GCC and Python-dev are needed to install some of the Python Modules
    if exists('/etc/update-motd.d/51_update-motd'):
        sudo('rm /etc/update-motd.d/51_update-motd')
    sudo('apt-get update')
    sudo('apt-get -y upgrade')
    sudo('apt-get -y install libpcre3-dev build-essential libssl-dev python-dev git-core')
    sudo('apt-get -y install libjpeg-dev optipng')

    install_python_extras()
    install_nginx()

def install_python_extras():
    sudo('apt-get -y install python-setuptools')
    sudo('easy_install pip')
    sudo('pip install virtualenv')
    sudo('pip install supervisor')

    sudo('mkdir -p /var/log/supervisor/')
    sudo('mkdir -p /etc/supervisord/')
    put('./fabfile/config/supervisord.conf', '/etc/supervisord.conf', use_sudo=True)

    #Configure supervisor in init.d
    #sudo('curl https://raw.github.com/gist/176149/88d0d68c4af22a7474ad1d011659ea2d27e35b8d/supervisord.sh > ~/supervisord')
    #sudo('mv ~/supervisord /etc/init.d/supervisord')
    put('./fabfile/config/supervisord-init.txt', '/etc/init.d/supervisord', use_sudo=True)
    sudo('chmod +x /etc/init.d/supervisord')
    sudo('/usr/sbin/update-rc.d -f supervisord defaults')
    sudo('service supervisord start')

    #Install VirtualEnvWrapper
    sudo('pip install virtualenvwrapper')
    run('export WORKON_HOME=$HOME/.virtualenvs && source /usr/local/bin/virtualenvwrapper.sh')
    append('~/.bash_profile', """if [ $USER == ubuntu ]; then
    export WORKON_HOME=$HOME/.virtualenvs
    source /usr/local/bin/virtualenvwrapper.sh
fi""")

def install_nginx():
    nginx_version = '1.2.6'

    sudo('adduser --system --no-create-home --disabled-login --disabled-password --group nginx')
    with cd('~'):
        run('wget http://nginx.org/download/nginx-' + nginx_version + '.tar.gz')
        run('tar -zxvf nginx-' + nginx_version + '.tar.gz')
        #run('wget http://www.grid.net.ru/nginx/download/nginx_upload_module-2.2.0.tar.gz')
        run('wget https://github.com/vkholodkov/nginx-upload-module/tarball/2.2 -O nginx-upload-module.tar.gz')
        run('tar -zxvf nginx-upload-module.tar.gz')
        run('mv vkholodkov-nginx-upload-module* nginx-upload-module')
        with cd('nginx-' + nginx_version):
            run('./configure --user=nginx --group=nginx --add-module=$HOME/nginx-upload-module')
            run('make')
            sudo('make install')
        run('rm -rf ~/nginx*')

        sudo('mkdir -p /usr/local/nginx/conf/vhosts/')
        put('./fabfile/config/nginx.conf', '/usr/local/nginx/conf/nginx.conf', use_sudo=True)

        put('./fabfile/config/nginx-init.txt', '/etc/init.d/nginx', use_sudo=True)
        sudo('chmod +x /etc/init.d/nginx')
        sudo('/usr/sbin/update-rc.d -f nginx defaults')

        for i in range(0, 9):
            sudo('mkdir -p /usr/local/nginx/upload_images/' + str(i))
        sudo('chown -R nginx:nginx /usr/local/nginx/upload_images')

        sudo('service nginx start')