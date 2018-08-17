import os
from app import create_app,db
from app.models.role_model import Role,Permission
from app.models.user_model import User,Follow
from app.models.post_model import Post
from app.models.comment_model import Reply,Comment

from flask_script import Manager,Shell
from flask_migrate import Migrate,MigrateCommand
from flask_login import login_required

app = create_app(os.getenv('FLASK_CONFIG') or 'default')
manager = Manager(app)
migrate = Migrate(app,db)

COV = None
if os.environ.get('FLASKY_COVERAGE'):
    import coverage
    COV = coverage.coverage(branch=True,include='app/*')
    COV.start()


def make_shell_context():
    return dict(app=app,db=db,User=User,Role=Role,Permission=Permission,Post=Post,Follow=Follow,Comment=Comment,Reply=Reply)
#manager.add_command("shell",Shell(make_context=make_shell_context()))
manager.add_command('db',MigrateCommand)


#python manage.py test --coverage 代码测试的覆盖报告
@manager.command
def test(coverage=False):
    if coverage and not os.environ.get('FLASKY_COVERAGE'):
        import sys
        os.environ['FLASKY_COVERAGE'] ='1'
        os.execvp(sys.executable,[sys.executable]+sys.argv)
    import unittest
    tests = unittest.TestLoader().discover('tests')
    unittest.TextTestRunner(verbosity=2).run(tests)
    if COV:
        COV.stop()
        COV.save()
        print('Coverage Summary:')
        COV.report()
        basedir = os.path.abspath(os.path.dirname(__file__))
        covdir = os.path.join(basedir,'tmp/coverage')
        COV.html_report(directory=covdir)
        print('HTML version:file://%s/index.html'%covdir)
        COV.erase()

#启动分析源码性能的命令
@manager.command
def profile(length=25,profile_dir=None):
    from werkzeug.contrib.profiler import ProfilerMiddleware
    app.wsgi_app = ProfilerMiddleware(app.wsgi_app,restrictions=[length],
                                      profile_dir=profile_dir)
    app.run()

@manager.command
def createdb():
    from app import db
    from app.models.role_model import Role

    db.create_all()
    #migrate.init()
    #migrate.migrate(message='第一次迁移')
    #migrate.upgrade()

    Role.insert_roles()

@manager.command
def deploy():
    from flask_migrate import migrate,upgrade
    from app.models.role_model import Role

    #将数据库迁移到最新修订版本
    upgrade()

    #创建用户角色
    Role.insert_roles()


if __name__ == '__main__':
    manager.run()