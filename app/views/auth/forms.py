from flask_wtf import Form,FlaskForm
from wtforms import StringField,PasswordField,BooleanField,SubmitField
from wtforms.validators import DataRequired,Length,Email,Regexp,EqualTo
from wtforms import ValidationError
from ...models.user_model import User

class LoginForm(FlaskForm):
    email = StringField('Email/Username',validators=[DataRequired(),Length(1,64)])
    password= PasswordField('Password',validators=[DataRequired()])
    remember_me = BooleanField('Remember me!')
    submit = SubmitField('Login In')

class RegistrationForm(FlaskForm):
    email = StringField('Email',validators=[DataRequired(),Length(1,64),Email()])
    username = StringField('Username',validators=[DataRequired(),Length(1,64)])
    password = PasswordField("Password",validators=[DataRequired(),EqualTo('password2',message='两次密码必须一致')])
    password2 = PasswordField('Confirm password',validators=[DataRequired()])
    submit = SubmitField('Register')

    def validate_email(self,field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('该邮箱已被注册')

    def validate_username(self,field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('该用户名已被注册')

class ChangePasswordForm(FlaskForm):
    old_password = PasswordField('旧密码', validators=[DataRequired()])
    password = PasswordField('新密码', validators=[DataRequired(),EqualTo('password2',message='两次密码必须一致')])
    password2 = PasswordField('再次确认密码',validators=[DataRequired()])
    submit = SubmitField('修改密码')

class PasswordResetRequestForm(FlaskForm):
    email = StringField('邮箱',validators=[DataRequired(),Length(1,64),Email()])
    submit = SubmitField('重设密码')

class PasswordRestForm(FlaskForm):
    password = PasswordField('新密码',validators=[DataRequired(),EqualTo('password2',message='两次密码必须一致')])
    password2 = PasswordField('确认密码',validators=[DataRequired()])
    submit = SubmitField('重设密码')

class ChangeEmailForm(FlaskForm):
    email = StringField('新邮箱',validators=[DataRequired(),Length(1,64),Email()])
    password = PasswordField('请输入密码',validators=[DataRequired()])
    submit = SubmitField('修改邮箱')

    def validate_email(self,field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('该邮箱已被注册过了')

