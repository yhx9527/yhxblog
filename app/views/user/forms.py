from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField,TextAreaField,BooleanField,SelectField
from wtforms.validators import DataRequired,Length,Email,Regexp,ValidationError
from ...models.user_model import User
from ...models.role_model import Role
from flask_pagedown.fields import PageDownField


class EditProfileForm(FlaskForm):
    location = StringField('住址',validators=[Length(0,64)])
    about_me = TextAreaField('介绍一下自己吧')
    submit = SubmitField('提交')

class EditProfileAdminForm(FlaskForm):
    email = StringField('邮箱',validators=[DataRequired(),Length(1,64),Email()])
    username = StringField('用户名',validators=[DataRequired(),Length(1,64),Regexp('^[A-Za-z][A-Za-z0-9_.]*$',0,'用户名称只能有字母，数字，点，下划线组成')])
    confirmed = BooleanField('是否已邮箱确认')
    role = SelectField('角色',coerce=int)
    name = StringField('备注', validators=[Length(0, 64)])
    location = StringField('住址', validators=[Length(0, 64)])
    about_me = TextAreaField('介绍一下自己吧')
    submit = SubmitField('提交')

    def __init__(self,user,*args,**kwargs):
        super(EditProfileAdminForm,self).__init__(*args,**kwargs)
        self.role.choices = [(role.id,role.name) for role in Role.query.order_by(Role.name).all()]
        self.user = user

    def validate_email(self,field):
        if field.data != self.user.email and \
              User.query.filter_by(email=field.data).first():
            raise ValidationError('邮箱已被注册过了')

    def validate_username(self,field):
        if field.data != self.user.username and \
              User.query.filter_by(username=field.data).first():
            raise ValidationError('用户名已被注册过了')


#博客表单
class PostForm(FlaskForm):
    title = StringField('博客标题',validators=[DataRequired()])
    body = PageDownField("灵感来了写博客",validators=[DataRequired()])
    submit = SubmitField('提交')

#评论表单
class CommentForm(FlaskForm):
    body = StringField('发表你的评论',validators=[DataRequired()])
    submit = SubmitField('提交')

#回复表单
class ReplyForm(FlaskForm):
    body = StringField('回复ta',validators=[DataRequired()])
    submit = SubmitField('发送')