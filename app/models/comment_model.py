from .. import db
import bleach
from datetime import datetime
from markdown import markdown
from ..utils.exceptions import ValidationError


#评论的模型
class Comment(db.Model):
    __table__name = 'comment'
    id = db.Column(db.Integer,primary_key=True)
    body = db.Column(db.Text)
    body_html = db.Column(db.Text)
    timestamp = db.Column(db.DateTime,index=True,default=datetime.utcnow)
    disabled = db.Column(db.Boolean)
    like = db.Column(db.Integer,default=1)
    author_id = db.Column(db.Integer,db.ForeignKey('users.id'))
    target_username = db.Column(db.String(64),index=True)
    ost_id = db.Column(db.Integer,db.ForeignKey('posts.id'))



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




db.event.listen(Comment.body,'set',Comment.on_changed_body)


