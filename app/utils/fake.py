from .. import db
from ..models.user_model import User
from ..models.post_model import Post

def generate_fake_posts(count=100):
    from random import seed, randint
    import forgery_py
    seed()
    user_count = User.query.count()
    for i in range(count):
        u = User.query.offset(randint(0, user_count - 1)).first()
        p = Post(body=forgery_py.lorem_ipsum.sentences(randint(1, 3)),
                 timestamp=forgery_py.date.date(True),
                 if_post=True,author=u,read=randint(50,200),
                 title=forgery_py.lorem_ipsum.title())
        db.session.add(p)
        db.session.commit()

def generate_fake_users(count=100):
    from sqlalchemy.exc import IntegrityError
    from random import seed
    import forgery_py

    seed()
    for i in range(count):
        u = User(email=forgery_py.internet.email_address(),
                username=forgery_py.internet.user_name(),
                password=forgery_py.lorem_ipsum.word(),
                confirmed=True,
                name=forgery_py.name.full_name(),
                location=forgery_py.address.city(),
                about_me=forgery_py.lorem_ipsum.sentence(),
                member_since=forgery_py.date.date(True))
        db.session.add(u)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()

def generate_fake_delete(table):
    datas = table.query.all()
    for data in datas:
        db.session.delete(data)
        db.session.commit()



