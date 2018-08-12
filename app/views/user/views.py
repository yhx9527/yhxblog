from flask import render_template, session, redirect, url_for, current_app,abort,flash,request,make_response
from ... import db
from ...models.user_model import User
from ...models.role_model import Role,Permission
from ...models.post_model import Post
from ...models.comment_model import Comment
#from ..email import send_email
from . import user
from .forms import EditProfileForm,EditProfileAdminForm,PostForm,CommentForm
from ...utils.decorators import admin_required,permission_required
from flask_login import login_required,current_user
from flask_sqlalchemy import get_debug_queries


@user.route('/',methods=['GET','POST'])
def index():
    query = Post.query.filter_by(if_post=True)
    page = request.args.get('page', 1, type=int)
    pagination = query.order_by(Post.timestamp.desc()).paginate(page,
                                                                per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],
                                                                error_out=False)  # 里面有页数，文章等等等
    posts = pagination.items  # .items表示这一页的文章
    return render_template('index.html', posts=posts, pagination=pagination)
