# coding=utf-8
__author__ = 'pochnsong@163.com'

"""
终端输入
fab deploy 部署（安装相关软件+同步代码，已包含包含sync）
fab sync 同步代码
"""


from fabric.api import *
import time
from fab.utils import *
from fab import apache
import os
import re
from fabric.contrib.files import exists
from fabric.contrib.project import rsync_project
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

""" User Configuration """

env.user = 'song'
env.hosts = ['133.130.55.240']
""" End of User Configuration """

proj_name = os.path.basename(os.path.dirname(__file__))
proj_path = '/home/%s/proj' % env.user
site_port = 80


# -------------------------------------------
@task
def get_current_site():
    """
    return ensite, dissite
    """
    for line in run("ls /etc/apache2/sites-enabled").split():
        if re.match('^%s' % proj_name, line):
            if line.strip() == '%s_a.conf' % proj_name:
                return 'a', 'b'
            else:
                return 'b', 'a'

    return 'b', 'a'


@task
def config_apache2():
    """setup Apache2 conf files
    双缓冲, 默认开启 xxx_a.conf
    """

    _site_conf_a = os.path.join(BASE_DIR, 'server/%s_a.conf' % proj_name)
    _site_conf_b = os.path.join(BASE_DIR, 'server/%s_b.conf' % proj_name)

    with open(_site_conf_a, 'w') as wf:
        wf.write(apache.get_config(env, proj_name,
                                   os.path.join(proj_path, 'a', proj_name),
                                   "%s/a" % proj_name,
                                   site_port))

    with open(_site_conf_b, 'w') as wf:
        wf.write(apache.get_config(env, proj_name,
                                   os.path.join(proj_path, 'b', proj_name),
                                   "%s/b" % proj_name,
                                   site_port))

    # 上传apache2配置 a, b
    _conf_remote_a = '/etc/apache2/sites-available/%s_a.conf' % proj_name
    _conf_remote_b = '/etc/apache2/sites-available/%s_b.conf' % proj_name


    if exists(_conf_remote_a):
        sudo('rm %s' % _conf_remote_a)
    if exists(_conf_remote_b):
        sudo('rm %s' % _conf_remote_b)

    sudo('mkdir -p /var/www/%s/a/log/apache2/' % proj_name)
    sudo('mkdir -p /var/www/%s/b/log/apache2/' % proj_name)
    sudo('chmod -R 777 /var/www/%s/a/log' % proj_name)
    sudo('chmod -R 777 /var/www/%s/b/log' % proj_name)
    put(_site_conf_a, _conf_remote_a, use_sudo=True)
    put(_site_conf_b, _conf_remote_b, use_sudo=True)
    sudo('a2dissite 000-default.conf')
    # sudo('a2ensite %s_b.conf' % proj_name)
    sudo('service apache2 reload', warn_only=True)


@task
def init_www():
    """
    更新www文件夹
    """
    _remote_proj_path_a = os.path.join(proj_path, 'a')
    _remote_proj_root_a = os.path.join(_remote_proj_path_a, proj_name)
    if not exists(_remote_proj_path_a):
        run('mkdir -p %s' % _remote_proj_path_a)

    _remote_proj_path_b = os.path.join(proj_path, 'b')
    _remote_proj_root_b = os.path.join(_remote_proj_path_b, proj_name)
    if not exists(_remote_proj_path_b):
        run('mkdir -p %s' % _remote_proj_path_b)

    # 删除旧的资源文件
    for x in ['/var/www/%s/a/static' % proj_name,
              '/var/www/%s/a/media' % proj_name,
              '/var/www/%s/b/static' % proj_name,
              '/var/www/%s/b/media' % proj_name,
              '/var/www/%s/db' % proj_name,
              ]:
        sudo('rm -rf %s' % x)

    # 更新资源目录
    # /home/user/proj/a 项目目录
    # /var/www/seal/static 链接到项目目录中
    # /var/www/seal/media

    sudo('mkdir -p /var/www/%s/a' % proj_name)
    sudo('mkdir -p /var/www/%s/b' % proj_name)
    sudo('mkdir -p /var/www/%s/db' % proj_name)

    if not exists('/var/www/%s/backup' % proj_name):
        sudo('mkdir -p /var/www/%s/backup' % proj_name)
    sudo('chmod 777 /var/www/%s/backup' % proj_name)

    sudo('ln -sfn %s/static /var/www/%s/a/static' % (_remote_proj_root_a, proj_name))
    sudo('ln -sfn %s/media /var/www/%s/a/media' % (_remote_proj_root_a, proj_name))
    sudo('ln -sfn %s/static /var/www/%s/b/static' % (_remote_proj_root_b, proj_name))
    sudo('ln -sfn %s/media /var/www/%s/b/media' % (_remote_proj_root_b, proj_name))


@task
def dev2prod():
    ensite, disstie = get_current_site()
    _remote_proj_root = '/'.join([proj_path, disstie, proj_name])

    """convert development env to production env"""
    with file(os.path.join(BASE_DIR, proj_name,'settings.py' ), 'r') as rf:
        c = rf.readlines()

    with file(os.path.join(BASE_DIR, 'server','settings.py'), 'w+') as wf:
        for ln in c:
            if 'DEBUG' in ln or 'ALLOWED_HOSTS' in ln:
                continue
            wf.write(ln)

        wf.write('\n# for production\n')
        wf.write('ALLOWED_HOSTS = ["*", "%s"]\n' % env.host)
        wf.write('DEBUG = False\n')

    with file(os.path.join(BASE_DIR, '%s/wsgi.py' % proj_name), 'r') as rf:
        c = rf.readlines()

    with file(os.path.join(BASE_DIR, 'server/wsgi.py'), 'w+') as wf:
        for ln in c:
            if 'import os' in ln:
                wf.write(ln)
                wf.write('import sys\n')
                #wf.write('site.addsitedir(\'/home/%s/.virtualenvs/%s/lib/python2.7/site-packages\')\n' % (env.user, proj_name))
                wf.write('sys.path.append(\'%s\')\n' % _remote_proj_root)
            elif 'application = get_wsgi_application' in ln:
                wf.write('activate_env=os.path.expanduser("/home/%s/.virtualenvs/%s/bin/activate_this.py")\n' % (env.user, proj_name))
                wf.write('execfile(activate_env, dict(__file__=activate_env))\n')
                wf.write(ln)
            else:
                wf.write(ln)

    put(os.path.join(BASE_DIR, 'server', 'settings.py'), _remote_proj_root+'/'+proj_name+'/settings.py')
    put(os.path.join(BASE_DIR, 'server', 'wsgi.py'), _remote_proj_root+'/'+proj_name+'/wsgi.py')


@task
def init_env():
    """ Initialize server environment """
    install_apache()
    install_mod_wsgi()
    install_virtualenv()

    create_virtualenv(proj_name)
    config_apache2()
    init_www()


def upload(_remote_proj_path, ignore='.fabfileignore'):
    tf_local = tar1(os.path.dirname(__file__), ignore=ignore)
    tf_name = proj_name + '.tar.gz'
    with cd(_remote_proj_path):
        print("uploading the project...(just wait:P)", str(os.path.getsize(tf_local)/1024)+'KB')
        put(tf_local, tf_name)
        sudo('rm -rf %s' % proj_name)
        print("untar ...")
        run('tar --no-overwrite-dir -zxvf %s' % tf_name)
        print('remove tar')
        run('rm %s' % tf_name)

    os.remove(tf_local)


@task
def deploy2():
    ensite, dissite = get_current_site()
    ensite_conf = '%s_%s.conf' % (proj_name, dissite)
    dissite_conf = '%s_%s.conf' % (proj_name, ensite)
    _remote_proj_path = "/".join([proj_path, dissite])
    _remote_proj_root = "/".join([_remote_proj_path, proj_name])
    pre_deploy(ensite)
    upload(_remote_proj_path)
    dev2prod()
    with virtualenv(_remote_proj_root, proj_name):
        run("pip install -r requirements.txt")
        run('python manage.py collectstatic --noinput')
        run('rm -rf static')
        run('mv prod/static static')
        sudo('chmod -R 777 db')
        sudo('chmod -R 777 media')

    post_deploy(ensite_conf, dissite_conf)


@task
def update2():
    ensite, dissite = get_current_site()
    ensite_conf = '%s_%s.conf' % (proj_name, dissite)
    dissite_conf = '%s_%s.conf' % (proj_name, ensite)
    _remote_proj_path = os.path.join(proj_path, dissite)
    _remote_proj_root = os.path.join(_remote_proj_path, proj_name)

    pre_deploy(ensite)
    # rsync_repo(_remote_proj_root)
    upload(_remote_proj_path, ignore='.fabfileignore_update')
    dev2prod()
    with virtualenv(_remote_proj_root, proj_name):
        run("pip install -r requirements.txt")
        run('python manage.py collectstatic --noinput')
        run('rm -rf static')
        run('mv prod/static static')
        run("cp %s/%s/%s/db/db.sqlite3 db/db.sqlite3" % (proj_path, ensite, proj_name))
        run("cp -r %s/%s/%s/media/ media/" % (proj_path, ensite, proj_name))
        sudo('chmod -R 777 db')
        sudo('chmod -R 777 media')

    post_deploy(ensite_conf, dissite_conf)


def pre_deploy(ensite):
    spv_stop(ensite)

@task
def db_pull(ensite=None):
    if not ensite:
        ensite, dissite = get_current_site()
    _remote_db_path = "/".join([proj_path, ensite, proj_name, 'db', 'db.sqlite3'])
    # 重命名旧的数据库
    _local_db_path = os.path.dirname(__file__)
    if os.path.exists(os.path.join(_local_db_path, 'db', 'db.sqlite3')):
        time_tag = get_time_tag()
        os.rename(os.path.join(_local_db_path, 'db', 'db.sqlite3'), os.path.join(_local_db_path,'db', 'db_%s.sqlite3'%time_tag))
    # 新的数据库
    get(_remote_db_path, 'db/db.sqlite3')

@task
def db_push(ensite=None):
    if not ensite:
        ensite, dissite = get_current_site()
    _remote_db_path = "/".join([proj_path, ensite, proj_name, 'db', 'db.sqlite3'])
    # 重命名旧的数据库
    # 新的数据库
    put(os.path.join(BASE_DIR,'db/db.sqlite3'), _remote_db_path)


def post_deploy(ensite_conf, dissite_conf):
    sudo('sudo a2ensite %s' % ensite_conf)
    sudo('sudo a2dissite %s' % dissite_conf)
    sudo('service apache2 reload', warn_only=True)
    # do not turn on spv as of yet
    spv_start()
    print("yes! all done!")

@task
def media_rsync(ensite=None):
    """rsync project dirctory to server"""
    # 一个一个文件上传太慢啦
    # 上传到未开启的网站　dissite
    if not ensite:
        ensite, dissite = get_current_site()
    _remote_path = "/".join([proj_path, ensite, proj_name, 'media'])
    rsync_project(local_dir=os.path.join(BASE_DIR, 'media'),
                  remote_dir=_remote_path)

@task
def media_pull(ensite=None):
    if not ensite:
        ensite, dissite = get_current_site()
    _remote_path = "/".join([proj_path, ensite, proj_name])

    with cd(_remote_path):
        run('tar -zcvf media.tar.gz media')
    get('%s/media.tar.gz' % _remote_path, 'media.tar.gz')

@task
def check_db(ensite=None):
    """
    检测远程数据库更改
    """
    if not ensite:
        ensite, dissite = get_current_site()
    _remote_db_path = "/".join([proj_path, ensite, proj_name, 'db', 'db.sqlite3'])

    _remote_db_md5 = run('md5sum %s' % _remote_db_path).split()[0]
    _local_db_md5 = local('md5sum %s' % os.path.join(BASE_DIR, 'db', 'db.sqlite3'), capture=True).split()[0]

    print _remote_db_md5, _local_db_md5, _remote_db_md5 == _local_db_md5
    if not _remote_db_md5 == _local_db_md5:
        db_pull(ensite)


@task
def spv_start(ensite=None):
    """ Start supervisor Stop supervisor Stop supervisor"""
    if not ensite:
        ensite, dissite = get_current_site()

    _remote_proj_root = "/".join([proj_path, ensite, proj_name])
    """
    with virtualenv(_remote_proj_root, proj_name):
        sudo('supervisord -c supervisord.conf')
    """
@task
def spv_stop(ensite=None):
    """ Stop supervisor """
    if not ensite:
        ensite, dissite = get_current_site()
    _remote_proj_root = "/".join([proj_path, ensite, proj_name])

    """
    with virtualenv(_remote_proj_root, proj_name):
        sudo('supervisorctl -c supervisord.conf stop all', warn_only=True)
        sudo('supervisorctl -c supervisord.conf stop celery:', warn_only=True)
        sudo('supervisorctl -c supervisord.conf shutdown', warn_only=True)
    """

@task
def spv_list():
    """ List supervisor managed programs """
    ensite, dissite = get_current_site()
    _remote_proj_root = "/".join([proj_path, ensite, proj_name])
    with virtualenv(_remote_proj_root, proj_name):
        sudo('supervisorctl -c supervisord.conf status', warn_only=True)
