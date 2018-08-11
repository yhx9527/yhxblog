from .. import db


class Permission:
    COLLECT = 0x01
    FOLLOW = 0x02
    COMMENT = 0x04
    WRITE_ARTICLES = 0x08
    MODERATE_COMMENTS = 0x10
    ADMINISTER = 0x80

class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    default = db.Column(db.Boolean,default=False,index=True)
    permissions = db.Column(db.Integer)
    users = db.relationship('User', backref='role', lazy='dynamic')

    @staticmethod
    def insert_roles():
        roles={
            'User':(Permission.FOLLOW |
                    Permission.COMMENT |
                    Permission.COLLECT,True),
            'VIP': (Permission.FOLLOW |
                    Permission.COMMENT |
                    Permission.COLLECT |
                    Permission.WRITE_ARTICLES,False),
            'Moderator':(Permission.FOLLOW |
                         Permission.COMMENT |
                         Permission.WRITE_ARTICLES |
                         Permission.COLLECT |
                         Permission.MODERATE_COMMENTS,False),
            'Administrator':(0xff,False)
        }
        for r in roles:
            role = Role.query.filter_by(name=r).first()
            if role is None:
                role = Role(name=r)
            role.permissions = roles[r][0]
            role.default = roles[r][1]
            db.session.add(role)
        db.session.commit()

    def __repr__(self):
        return '<Role %r>' % self.name


