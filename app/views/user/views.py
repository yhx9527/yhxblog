from flask import render_template, session, redirect, url_for, current_app,abort,flash,request,make_response
from ... import db
from ...models.user_model import User
from ...models.role_model import Role,Permission
from ...models.post_model import Post
from ...models.comment_model import Comment
#from ..email import send_email
from . import user
from .forms import EditProfileForm,PostForm,CommentForm,EditProfileAdminForm
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
    return render_template('index.html', posts=posts, pagination=pagination,page=page)


@user.route('/user/<username>')
def usering(username):
    user = User.query.filter_by(username=username).first_or_404()
    return render_template('user.html',user=user)

@user.route('/edit-profile',methods=['GET','POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.location = form.location.data
        current_user.about_me = form.about_me.data
        db.session.add(current_user)
        db.session.commit()
        flash('You Profile Update')
        return redirect(url_for('.usering',username = current_user.username))
    form.location.data = current_user.location
    form.about_me.data = current_user.about_me
    return render_template('edit_profile.html',form=form,admin=False)


#与关注相关的视图处理函数
@user.route('/follow/<username>')
@login_required
@permission_required(Permission.FOLLOW)
def follow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('不合规用户')
        return redirect(url_for('.index'))
    if current_user.is_following(user):
        flash('你已经关注了此用户了')
        return redirect(url_for('.user',username=username))
    current_user.follow(user)
    flash('你成功关注了%s' %username)
    return redirect(url_for('.usering',username=username))

@user.route('/unfollow/<username>')
@login_required
@permission_required(Permission.FOLLOW)
def unfollow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('不合规用户')
        return redirect(url_for('.index'))
    if not user.is_followed_by(current_user):
        flash('你未关注了此用户了')
        return redirect(url_for('.user',username=username))
    current_user.unfollow(user)
    flash('你成功取消关注%s' %username)
    return redirect(url_for('.usering',username=username))

@user.route('/followers/<username>')
def followers(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('不合规用户')
        return redirect('.index')
    page = request.args.get('page',1,type=int)
    pagination = user.followers.paginate(
        page,per_page=current_app.config['FLASKY_FOLLOWERS_PER_PAGE'],
        error_out=False)
    follows = [{'user':item.follower,'timestamp':item.timestamp} for item in pagination.items]
    return render_template('followers.html',user=user,title='我的关注',
                           endpoint='.followers',pagination=pagination,
                           follows=follows)
@user.route('/followed-by/<username>')
def followed_by(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('不合规用户')
        return redirect('.index')
    page = request.args.get('page',1,type=int)
    pagination = user.followed.paginate(
        page,per_page=current_app.config['FLASKY_FOLLOWERS_PER_PAGE'],
        error_out=False)
    follows = [{'user':item.followed,'timestamp':item.timestamp} for item in pagination.items]
    return render_template('followers.html',user=user,title='粉丝',
                           endpoint='.followed_by',pagination=pagination,
                           follows=follows)


@user.route('/edit-profile/<int:id>',methods=['GET','POST'])
@login_required
@admin_required
def edit_profile_admin(id):
    user = User.query.get_or_404(id)
    form = EditProfileAdminForm(user)
    if form.validate_on_submit():
        user.email = form.email.data
        user.username = form.username.data
        user.confirmed = form.confirmed.data
        user.role = Role.query.get(form.role.data)
        user.name = form.name.data
        user.location = form.location.data
        user.about_me = form.about_me.data
        db.session.add(user)
        db.session.commit()
        flash('所选用户的资料已被更新')
        return redirect(url_for('user.usering',username = user.username))
    form.email.data = user.email
    form.username.data = user.username
    form.confirmed.data = user.confirmed
    form.role.data = user.role_id
    form.name.data = user.name
    form.location.data = user.location
    form.about_me.data = user.about_me
    return render_template('edit_profile.html',form=form,user=user,admin=True)



#博客详情链接
@user.route('/post/<int:id>',methods=['GET','POST'])
def post(id):
    post = Post.query.get_or_404(id)
    form = CommentForm()
    post.read = post.read +1
    db.session.add(post)
    db.session.commit()
    if form.validate_on_submit():
        comment = Comment(body=form.body.data,
                          post = post,
                          author= current_user._get_current_object())
        db.session.add(comment)
        db.session.commit()
        flash('你的评论已提交')
        return redirect(url_for('.post', id=post.id)) #page=-1用于请求最后一页
    page = request.args.get('page',1,type=int)
    if page == -1:
        page = (post.comments.count()-1) /\
                current_app.config['FLASKY_COMMENTS_PER_PAGE'] +1

    pagination = post.comments.order_by(Comment.timestamp.desc()).paginate(
        page,per_page=current_app.config['FLASKY_COMMENTS_PER_PAGE'],error_out=False
    )
    comments = pagination.items
    return render_template('post.html',post=post,form=form,
                           comments=comments,pagination=pagination)

#评论管理
@user.route('/moderate')
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def moderate():
    page = request.args.get('page',1,type=int)
    sorttype = request.args.get('sorttype','时间降序',type=str)
    if sorttype == '时间降序':
        pagination = Comment.query.order_by(Comment.timestamp.desc()).paginate(
            page,per_page=current_app.config['FLASKY_ADMIN_COMMENTS_PER_PAGE'],
            error_out=False
        )
    elif(sorttype == '时间升序'):
        pagination = Comment.query.order_by(Comment.timestamp.asc()).paginate(
            page, per_page=current_app.config['FLASKY_ADMIN_COMMENTS_PER_PAGE'],
            error_out=False
        )
    elif(sorttype == '博客id'):
        pagination = Comment.query.order_by(Comment.post_id.desc()).paginate(
            page, per_page=current_app.config['FLASKY_ADMIN_COMMENTS_PER_PAGE'],
            error_out=False
        )

    comments = pagination.items
    return render_template('moderate.html',comments=comments,pagination=pagination,sorttype=sorttype)



@user.route('/moderate/enable/<int:id>')
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def moderate_enable(id):
    comment = Comment.query.get_or_404(id)
    comment.disabled = False
    db.session.add(comment)
    db.session.commit()
    return redirect(url_for('.moderate',page=request.args.get('page',1,type=int)))

@user.route('/moderate/disable/<int:id>')
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def moderate_disable(id):
    comment = Comment.query.get_or_404(id)
    comment.disabled = True
    db.session.add(comment)
    db.session.commit()
    return redirect(url_for('.moderate', page=request.args.get('page', 1, type=int)))