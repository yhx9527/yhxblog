from flask import render_template, session, redirect, url_for, current_app,abort,flash,request,make_response
from ... import db
from ...models.user_model import User
from ...models.role_model import Role,Permission
from ...models.post_model import Post
from ...models.comment_model import Comment
#from ..email import send_email
from . import user
from .forms import EditProfileForm,PostForm,CommentForm,EditProfileAdminForm,ReplyForm
from ...utils.decorators import admin_required,permission_required
from flask_login import login_required,current_user
from flask_sqlalchemy import get_debug_queries
from datetime import datetime


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
    tab = request.args.get('tab', 1, type=int)
    user = User.query.filter_by(username=username).first_or_404()
    replys = Comment.query.filter_by(target_username = user.username)
    return render_template('user.html',user=user,replys=replys,tab=tab)

@user.route('/collect/<int:id>')
@login_required
def collect(id):
    post = Post.query.filter_by(id=id).first()
    if post in current_user.collects:
        current_user.collects.remove(post)
    else:
        current_user.collects.append(post)
    db.session.add(current_user)
    db.session.commit()
    return redirect(url_for('user.post',id=post.id))

#博客详情链接
@user.route('/post/<int:id>',methods=['GET','POST'])
def post(id):
    post = Post.query.get_or_404(id)
    form = CommentForm()
    if request.referrer != request.url:
        print(request.url==request.referrer)
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

#关于评论回复
@user.route('/reply-comment/<int:commentid>',methods=['GET','POST'])
@login_required
@permission_required(Permission.COMMENT)
def reply(commentid):
    commented = Comment.query.filter_by(id=commentid).first()
    form = ReplyForm()
    if form.validate_on_submit():
        commenting = Comment(target_username=commented.author.username,
                             body=form.body.data,
                          post=commented.post,
                          author=current_user._get_current_object())
        db.session.add(commenting)
        db.session.commit()
        return redirect(url_for('user.post',id=commented.post.id))
    return render_template('comment_reply.html',form=form,commented=commented)

#关于评论点赞
@user.route('/like-comment/<int:commentid>')
def like_comment(commentid):
    comment = Comment.query.filter_by(id=commentid).first()
    comment.like = comment.like+1
    db.session.add(comment)
    db.session.commit()
    return redirect(url_for('user.post',id=comment.post.id))

"""资料处理相关
    包括个人资料的管理，管理员进行用户资料管理
"""
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

@user.route('/del-comment/<int:id>',methods=['DELETE','GET'])
@login_required
def del_comment(id):
    comment = Comment.query.filter_by(id=id).first()
    tab = request.args.get('tab',1,type=int)
    if current_user.id == comment.author_id or current_user.can(Permission.MODERATE_COMMENTS):
        db.session.delete(comment)
        db.session.commit()
        flash('该评论已删除')
        return redirect(url_for('user.usering',username = current_user.username,tab=tab))


"""与关注相关的视图处理函数
    包括关注，取消关注，查看关注者与粉丝
"""
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
        return redirect(url_for('.usering',username=username))
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
        return redirect(url_for('.usering',username=username))
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


"""评论管理相关
    包括评论的查看，封禁，解封，删除

"""
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
        pagination = Comment.query.order_by(Comment.ost_id.desc()).paginate(
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

@user.route('/moderate/del/<int:id>')
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def moderate_del(id):
    comment = Comment.query.get_or_404(id)
    db.session.delete(comment)
    db.session.commit()
    flash('该评论已删除')
    return redirect(url_for('.moderate', page=request.args.get('page', 1, type=int)))





"""博客管理相关
    包括博客的撰写，删除，编辑，发布；
    管理员审核博客
"""
@user.route('/manage-post/<username>',methods=['GET','POST'])
@login_required
@permission_required(Permission.WRITE_ARTICLES)
def manage_post(username):
    form = PostForm()
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    tab = request.args.get('tab',1,type=int)
    if current_user.can(Permission.WRITE_ARTICLES) and form.validate_on_submit():
        if current_user.can(Permission.ADMINISTER):
            post = Post(title=form.title.data, body=form.body.data,
                        author=current_user._get_current_object(),if_check=True)
            db.session.add(post)
            db.session.commit()
            flash('已存入工作区,等待发布')
        else:
            post = Post(title=form.title.data,body=form.body.data,
                        author=current_user._get_current_object())
            db.session.add(post)
            db.session.commit()
            flash('已提交管理员审核,审核通过，您即可发布')
        return redirect(url_for('.manage_post',username=current_user.username))

    if user.can(Permission.ADMINISTER):
        pagination = Post.query.order_by(Post.timestamp.desc()).paginate(page, per_page= \
            current_app.config[
                'FLASKY_POSTS_PER_PAGE'], error_out=False)  # 里面有页数，文章等等等
    else:
        pagination = Post.query.filter_by(author_id=user.id).order_by(Post.timestamp.desc()).paginate(page, per_page= \
            current_app.config[
                'FLASKY_POSTS_PER_PAGE'], error_out=False)  # 里面有页数，文章等等等
    posts = pagination.items  # .items表示这一页的文章

    return render_template('manage_post.html',form=form,user=user,posts=posts,pagination=pagination,tab=tab)


@user.route('/manage-post/del/<int:id>',methods=['DELETE','GET'])
@login_required
@permission_required(Permission.WRITE_ARTICLES)
def del_post(id):
    post = Post.query.filter_by(id=id).first()
    if current_user.id != post.author_id and \
            not current_user.can(Permission.ADMINISTER):
        abort(403)
    Post.delete_post(post)
    flash('已删除文章')
    return redirect(url_for('.manage_post',username=current_user.username,tab=2))

@user.route('/manage-post/issue/<int:id>')
@login_required
@permission_required(Permission.WRITE_ARTICLES)
def issue_post(id):
    post = Post.query.filter_by(id=id).first()
    if post.if_check ==True:
        post.if_post = not post.if_post
        db.session.add(post)
        db.session.commit()
        if post.if_post:
            flash('文章已发布')
        else:
            flash('文章已收回')
    else:
        flash('请等待文章审核通过')
    return redirect(url_for('.manage_post', username=current_user.username, tab=2))

@user.route('/manage-post/check/<int:id>')
@login_required
@permission_required(Permission.WRITE_ARTICLES)
def check_post(id):
    post = Post.query.filter_by(id=id).first()
    post.if_check = not post.if_check
    db.session.add(post)
    db.session.commit()
    if post.if_check:
        flash('该文章通过审核')
    else:
        flash('该文章已被下架')
    return redirect(url_for('.manage_post', username=current_user.username, tab=2))


@user.route('/edit/<int:id>',methods=['GET','POST'])
@login_required
@permission_required(Permission.WRITE_ARTICLES)
def edit_post(id):
    post = Post.query.get_or_404(id)
    if current_user != post.author and \
        not current_user.can(Permission.ADMINISTER):
        abort(403)
    form = PostForm()
    if form.validate_on_submit():
        post.title = form.title.data
        post.body = form.body.data
        post.timestamp = datetime.utcnow()
        db.session.add(post)
        db.session.commit()
        flash('文章已更新')
        return redirect(url_for('user.manage_post', username=current_user.username,tab=2))
    form.title.data = post.title
    form.body.data = post.body
    return render_template('edit_post.html',form=form)

