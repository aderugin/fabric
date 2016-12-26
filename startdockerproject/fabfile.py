# -*- coding: utf-8 -*-
import os
import time
from fabric.api import task, local, env, lcd, prompt
from fabric.utils import puts


# Путь до шаблона django проекта
PROJECT_TEMPLATE_PATH = 'https://github.com/aderugin/django-project-template/zipball/master'
# Локальная папка с django проектами
PROJECTS_ROOT = os.path.expanduser('~/Sites/django/')


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
        local('mkdir -p {0}'.format(env.project_root))

        with lcd(env.project_root):
            # Создаем директорию с django проектом и переходим в нее
            local('mkdir -p {0}-django'.format(env.project))

            with lcd('{0}-django'.format(env.project)):
                # Создаем проект из шаблона
                local('django-admin startproject --extension=py,yml --name=Dockerfile --template={template} {name} {path}'.format(
                    template=PROJECT_TEMPLATE_PATH, name=env.project, path='.'
                ))

                # Билд контейнера
                local('fab build')
                local('fab start')

                # Создание базы данных
                create_database()


def create_database():
    time.sleep(5)
    local('docker-compose exec db mysql -e \'CREATE DATABASE %s CHARACTER SET utf8;\'' % env.project)
