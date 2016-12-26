# -*- coding: utf-8 -*-
from fabric.api import task
from fabric.api import run
from fabric.api import local
from fabric.api import env
from fabric.api import cd
from fabric.api import get
from fabric.api import lcd
from fabric.api import prefix
from fabric.api import sudo
from fabric.api import hide
from fabric.api import shell_env

from fabric.contrib.files import append
from fabric.contrib.files import exists


# ==============================================================================
# Docker
# ==============================================================================

@task
def build():
    local('docker-compose build')


@task
def start(port='8000'):
    with prefix('export APP_PORT=%s' % port):
        local('docker-compose up -d')


@task
def stop():
    local('docker-compose down')


@task
def status():
    local('docker-compose ps')


@task
def migrate(app='', fake=False):
    local('docker-compose exec webapp python manage.py migrate %s %s' % (
        app,
        '--fake-initial' if fake else ''
    ))


@task
def makemigrations(app=''):
    local('docker-compose exec webapp python manage.py makemigrations %s' % app)


@task
def runserver():
    local('docker-compose exec webapp python manage.py runserver 0.0.0.0:8000')


@task
def shell():
    local('docker-compose exec webapp python manage.py shell')


@task
def manage(command):
    local('docker-compose exec webapp python manage.py %s' % command)
