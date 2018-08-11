from flask import Blueprint
from ...models.role_model import Permission

user = Blueprint('user', __name__)

@user.app_context_processor    #上下文处理器，让自定义的变量在模板中可见，返回的结果必须是字典
def inject_permissions():
    return dict(Permission=Permission)

from . import views, errors