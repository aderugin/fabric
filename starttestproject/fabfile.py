# -*- coding: utf-8 -*-
import os

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
from fabric.api import prompt

from fabric.utils import puts


# Путь до шаблона django проекта
PROJECT_TEMPLATE_PATH = 'https://github.com/aderugin/django-project-template/zipball/master'
# Локальная папка с django проектами
PROJECTS_ROOT = os.path.expanduser('~/Sites/django/')
# Версия python
PYTHON = 'python3'  # 'python'
# Версия django
DJANGO_VERSION = ''  # Если не определено, то последняя


@task
def create_project():
    """
    Создает новый проект
    """
    # спрашиваем у пользователя название папки с проектом
    prompt('project root name: ', 'project_root',
           validate='^([A-Za-z0-9]|[A-Za-z0-9][A-Za-z0-9\-]*[A-Za-z0-9])$')

    # спрашиваем у пользователя название проекта
    prompt('project name: ', 'project',
           validate='^([A-Za-z0-9]|[A-Za-z0-9][A-Za-z0-9\-]*[A-Za-z0-9])$')
    puts('create project: {0}'.format(env.project))

    with lcd(PROJECTS_ROOT):
        # Создаем директорию с root проектом
        local('mkdir %s' % env.project_root)

        with lcd(env.project_root):
            # Создаем директорию с django проектом и переходим в нее
            local('mkdir {0}-django'.format(env.project))

            with lcd('{0}-django'.format(env.project)):
                # Создаем виртуальное окружение
                local('virtualenv -p {0} .venv'.format(PYTHON))

                with prefix('.venv/bin/activate'):
                    # Устанавливаем django
                    if DJANGO_VERSION:
                        local('pip install django=={0}'.format(DJANGO_VERSION))
                    else:
                        local('pip install django')

                # Создаем проект из шаблона
                local('django-admin --template={0} {1}'.format(PROJECT_TEMPLATE_PATH,
                                                               env.project))
