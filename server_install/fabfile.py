# -*- coding: utf-8 -*-
import os

from fabric.api import run
from fabric.api import prefix
from fabric.api import task
from fabric.api import prompt
from fabric.api import env
from fabric.api import cd
from fabric.api import warn_only
from fabric.api import hide
from fabric.api import local
from fabric.contrib.files import append
from fabric.contrib.files import upload_template
from fabric.contrib.files import exists
from fabric.contrib.files import uncomment
from fabric.contrib.files import comment
from fabric.contrib.files import contains


SERVER_USER = 'user'

LOCAL_SSH_KEY = None

with open(os.path.expanduser('~/.ssh/id_rsa.pub'), 'r') as f:
    LOCAL_SSH_KEY = f.read()

APPS_ROOT = '/webapps'

PORT = 80

env.user = 'root'


@task
def server_install():
    """
    Автоматическая настройка сервера
    """
    # Спрашиваем у пользователя название проекта
    # Название будет использовано для именования всего связанного с проектом
    prompt(
        'Название проекта: ', 'project_name',
        validate=r'^([\w]+)$'
    )
    # Доменное имя
    prompt(
        'Домен: ', 'domain',
        validate=r'^([\w.-]+)$'
    )
    env.project_root = '%s/%s' % (APPS_ROOT, env.project_name)

    run('apt-get update')
    run('apt-get -y install locales')
    localesconfig()

    # Common
    run('apt-get -y install sudo')
    run('apt-get -y install nginx')
    run('apt-get -y install git')
    run('apt-get -y install python-virtualenv')
    run('apt-get -y install libpq-dev')
    run('apt-get -y install libffi-dev')
    run('apt-get -y install libevent-dev')
    run('apt-get -y install build-essential')
    run('apt-get -y install uuid-dev')
    run('apt-get -y install htop')
    run('apt-get -y install libbz2-dev')
    run('apt-get -y install supervisor')
    run('apt-get -y install python3-dev')
    run('apt-get -y install python-dev')

    # Pillow
    run('apt-get -y install libfreetype6-dev')
    run('apt-get -y install libjpeg-dev')
    run('apt-get -y install zlib1g-dev')
    run('apt-get -y install libpng12-dev')

    # lxml
    run('apt-get -y install libxml2-dev')
    run('apt-get -y install libxslt1-dev')

    # Email
    run('apt-get -y install mailutils')
    run('apt-get -y install exim4')

    # Папка для приложений
    run('mkdir -p %s' % APPS_ROOT)

    with warn_only():
        # Группа для приложений
        run('addgroup webapps')
        # Пользователь приложения
        create_app_user(username=env.project_name)
        # Пользователь сервера
        create_user(
            username=SERVER_USER,
            groups=['sudo'],
            password=True,
            homeroot='/home'
        )
    # Настройка email
    emailconfig()
    # Настройки nginx
    nginxconfig()
    # Настройки supervisor
    supervisorconfig()
    # Настройки безопасности
    safety()


@task
def docker_server_install():
    """
    Настройка сервера под Docker
    """
    run('apt-get update -y')
    run('apt-get -y install locales')
    localesconfig()

    run('apt-get -y install sudo')
    run('apt-get -y install nginx')
    run('apt-get -y install git')
    run('apt-get -y install htop')

    # Docker
    run('echo "deb http://http.debian.net/debian wheezy-backports main" >> '
        '/etc/apt/sources.list.d/backports.list')
    run('apt-get update -y')
    with warn_only():
        run('apt-get purge lxc-docker*')
        run('apt-get purge docker.io*')
    run('apt-get update -y')
    run('apt-get install -y curl apt-transport-https ca-certificates aufs-tools')
    run('apt-key adv --keyserver hkp://p80.pool.sks-keyservers.net:80 '
        '--recv-keys 58118E89F3A912897C070ADBF76221572C52609D')
    run('echo "deb https://apt.dockerproject.org/repo debian-jessie main" > '
        '/etc/apt/sources.list.d/docker.list')
    run('apt-get update -y')
    run('apt-get install -y docker-engine')

    with warn_only():
        run('addgroup user')
        create_user(
            username=SERVER_USER,
            groups=['docker', 'sudo'],
            group='user',
            password=True,
            homeroot='/home'
        )

    # Docker compose
    docker_compose_install()
    # Настройки безопасности
    safety()


@task
def base_server_install():
    """
    Базовые настройки сервера
    """
    run('apt-get update -y')
    run('apt-get -y install locales')
    localesconfig()

    run('apt-get -y install sudo')
    run('apt-get -y install nginx')
    run('apt-get -y install git')
    run('apt-get -y install htop')

    with warn_only():
        run('addgroup user')
        create_user(
            username=SERVER_USER,
            groups=['docker', 'sudo'],
            group='user',
            password=True,
            homeroot='/home'
        )

    # Docker compose
    docker_compose_install()
    # Настройки безопасности
    safety()


@task
def mysql():
    """
    Установка MySQL
    """
    run('apt-get -y install mysql-server')
    run('apt-get -y install libmysqlclient-dev')

    mysqlconfig()
    createdb(env.project_name)


@task
def mariadb():
    """
    Установка MariaDB
    """
    run('apt-get -y install software-properties-common')
    run('apt-key adv --recv-keys --keyserver keyserver.ubuntu.com 0xcbcb082a1bb943db')
    run("add-apt-repository 'deb [arch=amd64,i386] http://mirror.mephi.ru/mariadb/repo/10.1/debian jessie main'")
    run('apt-get update')
    run('apt-get -y install mariadb-server')
    run('apt-get -y install libmariadbclient-dev')

    mysqlconfig()
    createdb(env.project_name)


@task
def postgres(version='9.5'):
    """
    Установка PostgreSQL
    TODO: проверить и дописать создание конфига
    """
    run('echo "deb http://apt.postgresql.org/pub/repos/apt/ trusty-pgdg main 9.5" >> /etc/apt/sources.list.d/postgresql.list')
    run('wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add -')
    run('apt-get update')
    run('apt-get install postgresql-9.5')


@task
def redis():
    """
    Установка Redis
    """
    # Установка
    run('apt-get -y install build-essential tcl8.5')
    with cd('/tmp'):
        if exists('redis-stable.tar.gz'):
            run('rm redis-stable.tar.gz')
        if exists('redis-stable'):
            run('rm -r redis-stable')

        run('wget http://download.redis.io/releases/redis-stable.tar.gz')
        run('tar xzf redis-stable.tar.gz')
        with cd('redis-stable'):
            run('make')
            run('make test')
            run('make install')

    # Добавление демона
    with warn_only():
        run('useradd redis')
        with cd('/etc/init.d'):
            run('rm redis-server')
            with open('conf/redis.init.d', 'r') as f:
                append('redis-server', f.read())
            run('chmod 755 redis-server')
        run('touch /var/log/redis.log')
        run('chown redis:redis /var/log/redis.log')
        run('mkdir -p /var/lib/redis/6379')

    run('update-rc.d redis-server defaults')

    # Добавление конфига
    prompt(
        'Пароль для redis: ', 'redis_password',
        validate=r'^([\w]+)$'
    )
    run('mkdir -p /etc/redis')
    with cd('/etc/redis'):
        # TODO: почему то не работает строчка 397 в файле redis.conf
        # >>> ValueError: unsupported format character ')' (0x29) at index 6559
        # upload_template('conf/redis.conf', 'redis.conf', {
        #     'password': env.redis_password,
        # }, backup=False)
        upload_template('conf/redis.conf', 'redis.conf', {}, backup=False)
        run('echo "requirepass %s" >> redis.conf' % env.redis_password)

    lines = [
        'net.ipv4.tcp_tw_reuse=1',
        'net.ipv4.tcp_tw_recycle=1'
    ]
    for line in lines:
        if not contains('/etc/sysctl.conf', line, exact=True):
            run('echo %s >> /etc/sysctl.conf' % line)


@task
def ftp():
    """
    Установка vsftpd
    """
    run('apt-get -y install vsftpd')
    upload_template('conf/vsftpd.conf', '/etc/vsftpd.conf', backup=False)
    comment('/etc/pam.d/vsftpd', 'auth  required    pam_shells.so', backup=False)
    run('service vsftpd restart')


@task
def deploy_project(root):
    """
    Загрузка проекта
    """


@task(default=True)
def help():
    """
    Выводит эту справку
    """
    print """
Основные команды:
    fab server_install mariadb(mysql) redis ftp - настроит сервер, установит mysql, redis и ftp сервер
    """

    with hide('status', 'aborts', 'warnings', 'running', 'stderr', 'user'):
        local("fab --list")

    import fabric.state
    fabric.state.output.status = False


def localesconfig():
    """
    Конфигурирование локалей
    """
    uncomment('/etc/locale.gen', 'en_US.UTF-8 UTF-8')
    uncomment('/etc/locale.gen', 'ru_RU.UTF-8 UTF-8')
    run('echo LANG=ru_RU.UTF-8 > /etc/default/locale')
    run('dpkg-reconfigure --frontend=noninteractive locales')


def safety():
    """
    Настройки безопасности на сервере
        - Добавление правил iptables
        - Конфигурирование сервера
    """
    run('apt-get -y install iptables-persistent')
    run('mkdir -p /etc/iptables')
    with cd('/etc/iptables'):
        with warn_only():
            with open('conf/iptables.v4.conf', 'r') as f:
                append('rules.v4', f.read())
            with open('conf/iptables.v6.conf', 'r') as f:
                append('rules.v6', f.read())

    # Настройки безопасности
    lines = [
        'net.ipv4.conf.all.accept_redirects=0',
        'net.ipv6.conf.all.accept_redirects=0',
        'net.ipv4.tcp_syncookies=1',
        'net.ipv4.tcp_timestamps=0',
        'net.ipv4.conf.all.rp_filter=1',
        'net.ipv4.tcp_max_syn_backlog=1280',
        'kernel.core_uses_pid=1'
    ]
    for line in lines:
        if not contains('/etc/sysctl.conf', line, exact=True):
            run('echo %s >> /etc/sysctl.conf' % line)


def mysqlconfig():
    """
    Конфигурирование mysql
    """
    run('mysql -u root -p -e "set character_set_client=\'utf8\'; '
        'set character_set_connection=\'utf8\'; set character_set_database=\'utf8\'; '
        'set character_set_results=\'utf8\'; set character_set_server=\'utf8\'; '
        'set collation_database=\'utf8_general_ci\'; set collation_connection=\'utf8_general_ci\'; '
        'set collation_server=\'utf8_general_ci\';"')


def docker_compose_install(version='1.11.2'):
    """
    Утсановка docker-compose
    """
    run('curl -L https://github.com/docker/compose/releases/download/%s/docker-compose-Linux-x86_64'
        ' > /tmp/docker-compose' % version)
    run('chmod +x /tmp/docker-compose')
    run('mv /tmp/docker-compose /usr/local/bin')


def nginxconfig():
    """
    Конфигурирование nginx
    """
    with cd(env.project_root + '/conf'):
        upload_template('conf/nginx.conf', 'nginx.conf', {
            'project_name': env.project_name,
            'project_root': env.project_root,
            'domain': env.domain,
            'port': PORT
        }, backup=False)

    with warn_only():
        run('rm /etc/nginx/sites-enabled/%s.conf' % env.project_name)

    run('ln -s %s/conf/nginx.conf /etc/nginx/sites-enabled/%s.conf' % (
        env.project_root, env.project_name))

    uncomment('/etc/nginx/nginx.conf', 'server_names_hash_bucket_size')


def supervisorconfig():
    """
    Конфигурирование supervisor
    """
    with cd(env.project_root + '/conf'):
        with open('conf/supervisor.conf') as f:
            with warn_only():
                append('supervisor.conf', f.read())

    with warn_only():
        run('rm /etc/supervisor/conf.d/%s.conf' % env.project_name)

    run('ln -s %s/conf/supervisor.conf /etc/supervisor/conf.d/%s.conf' % (
        env.project_root, env.project_name))


def emailconfig():
    """
    Конфигурирование email
    """
    pass


def createdb(name):
    with warn_only():
        run('mysql -u root -p -e "create database %s character set utf8"' % name)


def create_app_user(username):
    """
    Создает пользователя для приложения
        - Создает структуру папок
        – Добавляет ssh ключ
        - Выставляет владельца папок
    """
    create_user(username)
    with cd('%s/%s' % (APPS_ROOT, username)):
        run('mkdir -p run')
        run('mkdir -p logs')
        run('mkdir -p conf')
        run('mkdir -p www/public/static')
        run('mkdir -p www/public/media')

    with cd(APPS_ROOT):
        run('chown -R %(user)s:webapps %(user)s', {'user': username})


def create_user(username, sudo=False, password=False, group='webapps', groups=None, homeroot=APPS_ROOT):
    """
    Создает пользователя
    """
    if not isinstance(groups, (list, tuple)):
        groups = []
    if sudo:
        groups.append('sudo')
    if groups:
        groups = ' -G ' + ','.join(groups)
    else:
        groups = ''

    with warn_only():
        run('useradd -m -d %(homeroot)s/%(user)s --shell /bin/bash -g %(group)s%(groups)s %(user)s' % {
            'homeroot': homeroot,
            'user': username,
            'group': group,
            'groups': groups
        })
        if password:
            run('passwd %s' % username)

        # Сразу заливаем ssh ключ
        with cd('%s/%s' % (homeroot, username)):
            run('mkdir -p .ssh')
            with cd('.ssh'):
                append('authorized_keys', LOCAL_SSH_KEY)
