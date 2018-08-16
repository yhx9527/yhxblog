from . import admin
from flask import url_for,request,current_app,render_template
from ...models.user_model import User
from flask_login import login_required,current_user
from ...utils.decorators import  admin_required

@admin.route('/manage-user')
@login_required
@admin_required
def manage_user():
    page = request.args.get('page', 1, type=int)
    pagination = User.query.order_by(User.member_since.desc()).paginate(page,per_page=current_app.config['FLASKY_ADMIN_USERS_PER_PAGE'],
            error_out=False)
    users = pagination.items
    return render_template('manage_user.html', users=users, pagination=pagination)