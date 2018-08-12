from flask import Flask
from flask_bootstrap import Bootstrap
from flask_mail import Mail
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from config import config
from flask_login import LoginManager
from flask_pagedown import PageDown
from flask_debugtoolbar import DebugToolbarExtension

bootstrap = Bootstrap()
mail = Mail()
moment = Moment()
db = SQLAlchemy()
login_manager = LoginManager()
login_manager.session_protection = 'strong' #防止用户会话被篡改
login_manager.login_view = 'auth.login'
pagedown = PageDown()
#toolbar = DebugToolbarExtension()

def create_app(config_name):
    app = Flask(__name__)
    #将指定的配置通过from_object()方法导入,app.config字典为可供选择的对象
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    #toolbar.init_app(app)
    bootstrap.init_app(app)
    mail.init_app(app)
    moment.init_app(app)
    db.init_app(app)
    login_manager.setup_app(app)
    pagedown.init_app(app)

    if not app.debug and not app.testing and not app.config['SSL_DISABLE']:
        from flask_sslify import SSLify
        sslify = SSLify(app)

    from .views.user import user as user_blueprint
    app.register_blueprint(user_blueprint)

    from .views.auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint,url_prefix='/auth')

    from .views.admin import admin as admin_blueprint
    app.register_blueprint(admin_blueprint,url_prefix='/admin')

    return app
