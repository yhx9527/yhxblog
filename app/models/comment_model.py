from .. import db
import bleach
from datetime import datetime
from markdown import markdown
from ..utils.exceptions import ValidationError


class Reply(db.Model):
    __tablename__ = 'replys'
    replying_id = db.Column(db.Integer, db.ForeignKey('comment.id'), primary_key=True)
    replyed_id = db.Column(db.Integer,db.ForeignKey('comment.id'),primary_key=True)

    timestamp = db.Column(db.DateTime,default=datetime.utcnow)

#评论的模型
class Comment(db.Model):
    __table__name = 'comment'
    id = db.Column(db.Integer,primary_key=True)
    body = db.Column(db.Text)
    body_html = db.Column(db.Text)
    timestamp = db.Column(db.DateTime,index=True,default=datetime.utcnow)
    disabled = db.Column(db.Boolean)
    author_id = db.Column(db.Integer,db.ForeignKey('users.id'))
    post_id = db.Column(db.Integer,db.ForeignKey('posts.id'))

    replying = db.relationship('Reply',
                               foreign_keys=[Reply.replyed_id],
                               backref=db.backref('replyed', lazy='joined'),
                               lazy='dynamic',
                               cascade='all, delete-orphan')
    replyed = db.relationship('Reply',
                              foreign_keys=[Reply.replying_id],
                              backref = db.backref('replying',lazy='joined'),
                              lazy = 'dynamic',
                              cascade='all, delete-orphan')



    @staticmethod
    def on_changed_body(target,value,oldvalue,initiator):
        allowed_tags = ['a','abbr','acronym','b','code','em','i','strong','p']
        target.body_html = bleach.linkify(bleach.clean(markdown(value,output_format='html'),tags=allowed_tags,strip=True))

    @staticmethod
    def from_json(json_comment):
        body = json_comment.get('body')
        if body is None or body == '':
            raise ValidationError("评论不能为空")
        return Comment(body=body)

    def reply(self,comment):
        r = Reply(replyed=comment,replying=self)
        db.session.add(r)



db.event.listen(Comment.body,'set',Comment.on_changed_body)


