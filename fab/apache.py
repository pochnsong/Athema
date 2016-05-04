# coding=utf-8
from fabric.api import task, sudo, put
from utils import check_installed
import os


@task
def start():
    """start apache2 service"""
    sudo('service apache2 start')


@task
def reload():
    """reload apache2 service"""
    sudo('service apache2 reload')

@task
def stop():
    """stop apache2 service"""
    sudo('service apache2 stop')

@task
def restart():
    """restart apache2 service"""
    sudo('service apache2 restart')

@task
def setup():
    """install Apache2 and its mod_wsgi module"""
    apps = ['apache2', 'libapache2-mod-wsgi']
    for app in apps:
        if not check_installed(app):
            sudo("apt-get -y install %s" % app)

# WSGIPythonPath {{PROJ_ROOT}}:/home/{{USER}}/.virtualenvs/{{PROJ_NAME}}/lib/python2.7/site-packages

TEMPLATE_CONFIG = """
WSGIDaemonProcess {{PROJ_NAME}} python-path={{PROJ_ROOT}}:/home/{{USER}}/.virtualenvs/{{PROJ_NAME}}/lib/python2.7/site-packages
<VirtualHost *:{{PORT}}>
  WSGIProcessGroup {{PROJ_NAME}}
  WSGIScriptAlias / {{PROJ_ROOT}}/{{PROJ_NAME}}/wsgi.py

  ErrorLog /var/www/{{WWW_SRC}}/log/apache2/error.log
  CustomLog /var/www/{{WWW_SRC}}/log/apache2/access.log combined

  <Directory {{PROJ_ROOT}}/{{PROJ_NAME}}>
     <Files wsgi.py>
       Require all granted
     </Files>
  </Directory>

  Alias /static /var/www/{{WWW_SRC}}/static
  Alias /media /var/www/{{WWW_SRC}}/media

  <Directory /var/www/{{WWW_SRC}}/static>
    #Order deny,allow
    #Allow from all
    Options FollowSymLinks
    Require all granted
  </Directory>

  <Directory /var/www/{{WWW_SRC}}/media>
    #Options FollowSymLinks
    Require all granted
  </Directory>
</VirtualHost>
"""


def get_config(env, proj_name, proj_root, www_src, port=80):
    """setup Apache2 conf files"""
    c = TEMPLATE_CONFIG
    c = c.replace('{{USER}}', env.user)
    c = c.replace('{{PROJ_NAME}}', proj_name)
    c = c.replace('{{PROJ_ROOT}}', proj_root)
    c = c.replace('{{WWW_SRC}}', www_src)
    c = c.replace('{{PORT}}', str(port))
    return c

