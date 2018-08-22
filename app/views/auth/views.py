from flask import render_template,redirect,request,url_for,flash,session
from flask_login import login_user,logout_user,login_required
from . import auth
from ...models.user_model import User
from .forms import LoginForm,RegistrationForm,ChangePasswordForm,PasswordResetRequestForm,PasswordRestForm,ChangeEmailForm
from ... import db
from ...utils.email import send_email
from flask_login import current_user

@auth.route('/login',methods=['GET','POST'])
def login():
        form = LoginForm()
        if form.validate_on_submit():
            user_temp = User.query.filter_by(email=form.email.data).first()
            user = user_temp if user_temp is not None else  User.query.filter_by(username=form.email.data).first()
            if user is not None and user.vertify_password(form.password.data):
                login_user(user, remember=form.remember_me.data)
                return redirect(request.args.get('next') or url_for('user.index'))
            flash('Invalid username or password')
        return render_template('auth/login.html', form=form)

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logout Success')
    return redirect(url_for('user.index'))

@auth.route('/register',methods=['GET','POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(email=form.email.data,
                    username=form.username.data,
                    password=form.password.data
                    )
        db.session.add(user)
        db.session.commit()
        flash('Register success!Please Login...')
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html',form=form)

@auth.route('/confirm/<token>')
@login_required
def confirm(token):
    if current_user.confirmed:
        return redirect(url_for('user.index'))
    if current_user.confirm(token):
        flash('You have confirmed your account.Thanks!')
    else:
        flash('The confirmation link is invalid or has expired')
    return redirect(url_for('user.index'))

@auth.before_app_request
def before_request():
    if current_user.is_authenticated:
        current_user.ping() #刷新用户访问时间
        """if not current_user.confirmed \
            and request.endpoint \
            and request.blueprint != 'auth' \
            and request.endpoint != 'static':
            return redirect(url_for('auth.unconfirmed'))
        """
@auth.route('/unconfirmed')
def unconfirmed():
    if current_user.is_anonymous or current_user.confirmed:
        return redirect(url_for('user.index'))
    token = current_user.generate_confirmation_token()
    send_email(current_user.email, '请确认你的账户', 'auth/email/confirm', user=current_user, token=token)
    return render_template('auth/unconfirmed.html')

@auth.route('/resend_confirmation')
@login_required
def resend_confirmation():
    token = current_user.generate_confirmation_token()
    send_email(current_user.email,'请确认你的账户','auth/email/confirm',user=current_user,token=token)
    flash('一封确认邮件已发送到你的邮箱中')
    return redirect(url_for('auth.unconfirmed'))

@auth.route('/change_password',methods=['GET','POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    #print([{key:value} for key,value in session.items()])
    if form.validate_on_submit():
        if current_user.vertify_password(form.old_password.data):
            current_user.password = form.password.data
            db.session.add(current_user)
            db.session.commit()
            flash('密码修改成功,请重新登录')
            logout_user()
            return redirect(url_for('user.index'))
        else:
            flash('原密码错误')
    return render_template("auth/change_password.html",form=form)


@auth.route('/reset',methods=['GET','POST'])
def password_reset_request():
    if not current_user.is_anonymous:
        return redirect(url_for('main.index'))
    form = PasswordResetRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            token = user.generate_reset_token()
            send_email(user.email,'重设你的密码','auth/email/reset_password',user=user,token=token)
        flash('关于重设密码的一封邮件已发往您的邮箱中')
        return redirect(url_for('auth.login'))
    return render_template('auth/reset_password.html',form=form)

@auth.route('/reset/<token>',methods=['GET','POST'])
def password_reset(token):
    if not current_user.is_anonymous:
        return redirect(url_for('main.index'))
    form = PasswordRestForm()
    if form.validate_on_submit():
        if User.reset_password(token,form.password.data):
            db.session.commit()
            flash('你的密码已经更改')
            return redirect(url_for('auth.login'))
        else:
            flash('操作失败')
            return redirect(url_for('user.index'))
    return render_template('auth/reset_password.html',form = form)

@auth.route('/change_email_no',methods=['GET','POST'])
@login_required
def change_email_no():
    form=ChangeEmailForm()
    if form.validate_on_submit():
        if current_user.email == form.email.data:
            flash('It’s not new email!')
        else:
            if current_user.vertify_password(form.password.data):
                current_user.email=form.email.data
                current_user.confirmed = False
                db.session.add(current_user)
                db.session.commit()
                flash('Change Email Success!')
                return redirect(url_for('auth.unconfirmed'))
            else:
                flash('Wrong Password')
    return render_template('auth/change_email_no.html', form=form)