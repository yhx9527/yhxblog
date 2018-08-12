from functools import wraps
from flask import abort
from flask_login import current_user
from ..models.role_model import Permission

def permission_required(permission):
    def decoator(f):
        @wraps(f)
        def decorated_function(*args,**kwargs):
            if not current_user.can(permission):
                abort(403)
            return f(*args,**kwargs)
        return decorated_function
    return decoator

def admin_required(f):
    return permission_required(Permission.ADMINISTER)(f)