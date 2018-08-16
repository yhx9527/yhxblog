from .. import db
from flask import url_for
from datetime import datetime
import bleach
from markdown import markdown
from ..utils.exceptions import ValidationError
from .comment_model import Comment

collect = db.Table('collect',
                   db.Column('user_id',db.Integer,db.ForeignKey('users.id')),
                   db.Column('post_id',db.Integer,db.ForeignKey('posts.id'))
                   )

class Post(db.Model):
    __tablename__ = 'posts'
    id = db.Column(db.Integer,primary_key=True)
    title = db.Column(db.String(64))
    body = db.Column(db.Text)
    timestamp = db.Column(db.DateTime,index=True,default=datetime.utcnow)
    body_html = db.Column(db.Text)
    if_post = db.Column(db.Boolean,default=False)
    if_check = db.Column(db.Boolean,default=False)
    read = db.Column(db.Integer,default = 1)
    author_id = db.Column(db.Integer,db.ForeignKey('users.id'))

    comments = db.relationship('Comment',backref='post',lazy='dynamic')

    fans = db.relationship('User',secondary=collect,backref=db.backref('collects',lazy='dynamic'),lazy='dynamic')


    @staticmethod
    def on_changed_body(target,value,oldvalue,initiator):
        allowed_tags = ['a','abbr','acronym','b','blockquote','code','em','li','i','ol','pre','strong','ul','h1','h2','h3','p']
        target.body_html = bleach.linkify(bleach.clean(
            markdown(value,output_format='html'),
            tags=allowed_tags,strip=True
        ))


    @staticmethod
    def delete_post(post):
        for comment in post.comments:
            db.session.delete(comment)
        db.session.delete(post)
        db.session.commit()

    # 刷新文章编辑时间
    def ping(self):
        self.timestamp = datetime.utcnow()
        db.session.add(self)

    #将文章转换成json格式的序列化字典
    def to_json(self):
        json_psot = {
            'url':url_for('api.get_post',id=self.id,_external=True),
            'body':self.body,
            'body_html':self.body_html,
            'timestamp':self.timestamp,
            'author': url_for('api.get_user',id=self.author_id,_external=True),
            'comments':url_for('api.get_post_comments',id=self.id,_external=True),
            'comment_count':self.comments.count()
        }
        return json_psot

    @staticmethod
    def from_json(json_post):
        body = json_post.get('body')
        if body is None or body == '':
            raise ValidationError('博客无内容')
        return Post(body=body)

    """
        @staticmethod
        def generate_fake(count=100):
            from random import seed,randint
            import forgery_py

            seed()
            user_count = User.query.count()
            for i in range(count):
                u = User.query.offset(randint(0,user_count-1)).first()
                p = Post(body=forgery_py.lorem_ipsum.sentences(randint(1,3)),timestamp=forgery_py.date.date(True),author=u)
                db.session.add(p)
                db.session.commit()

    """


db.event.listen(Post.body,'set',Post.on_changed_body) #用于监听body字段的变化,一变就重新修改body_html


