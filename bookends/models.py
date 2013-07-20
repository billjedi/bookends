from datetime import datetime
import re

from flask import render_template, url_for

from flask.ext.login import current_user
from sqlalchemy.ext.hybrid import hybrid_property

from . import db, util, bcrypt, app


sets = db.Table('sets',
    db.Column('set_id', db.Integer, db.ForeignKey('set.id')),
    db.Column('book_id', db.Integer, db.ForeignKey('book.id'))
)


class Set(db.Model):

    __tablename__ = 'set'

    # Columns

    #-------------------------------------------------------------------------

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    title = db.Column(db.String(128))

    date_added = db.Column(db.DateTime, default=datetime.utcnow())

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))


class Book(db.Model):

    __tablename__ = 'book'

    # Columns

    #-------------------------------------------------------------------------

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    title = db.Column(db.String(128))

    author = db.Column(db.String(64))

    url = db.Column(db.String(1024))

    date_added = db.Column(db.DateTime, default=datetime.utcnow())

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    reading = db.Column(db.Boolean, default=False)

    excited = db.Column(db.Boolean, default=False)

    finished = db.Column(db.Boolean, default=False)

    sets = db.relationship('Set', secondary=sets,
        backref=db.backref( 'books', lazy='dynamic'))


    def update_sets(self, set_list):

        for set in self.sets:
            self.sets.remove(set)

        db.session.flush()

        sets_given = re.findall(r"\{(.+?)\}", set_list)

        for set_title in sets_given:

            existing_set = Set().query.filter_by(
                title=set_title,
                user_id=current_user.id
            ).first()

            if existing_set and existing_set not in self.sets:
                print existing_set.title
                self.sets.append(existing_set)
            elif existing_set == None:
                print "TWO"
                new_set = Set(title=set_title, user_id=current_user.id)
                self.sets.append(new_set)

        return

class User(db.Model):

    __tablename__ = 'user'

    # Columns

    #-------------------------------------------------------------------------

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    email = db.Column(db.String(64), unique=True)

    _password = db.Column(db.String(64))

    email_confirmed = db.Column(db.Boolean, default=False)

    active = db.Column(db.Boolean, default=True)

    date_joined = db.Column(db.DateTime, default=datetime.utcnow())

    books = db.relationship('Book', backref='user', lazy='dynamic')

    #-------------------------------------------------------------------------

    # Flask-Login

    #-------------------------------------------------------------------------

    def is_active(self):
        return self.active

    def is_authenticated(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return self.id

    #-------------------------------------------------------------------------

    @hybrid_property
    def password(self):

        """ Return the password field """

        return self._password


    @password.setter
    def _set_password(self, password):

        """ Automatically hash the password with Flask-Bcrypt """

        self._password = bcrypt.generate_password_hash(
            password,
            rounds=app.config['BCRYPT_LEVEL'])

    def send_activation_email(self):

        """ Send the activation email for a user """

        subject = "Activate your Bookends account"

        token = util.ts.dumps(self.email, salt='activation-key')

        activation_url = url_for(
            'activate_account',
            token=token,
            _external=True)

        html = render_template(
            'email/activate.html',
            user=self,
            activation_url=activation_url)

        return util.send_email(
            self.email,
            subject,
            html)

    def send_email_update_email(self, new_email):

        """ Send the email update email for a user """

        subject = "Confirm your new email address on Bookends"

        token = util.ts.dumps(new_email, salt='email-update-key')

        email_update_url = url_for(
            'account_email_update',
            token=token,
            _external=True)

        html = render_template(
            'email/email_update.html',
            user=self,
            email_update_url=email_update_url)

        return util.send_email(
            new_email,
            subject,
            html)

    def send_recover_email(self):

        subject = "Reset your Bookends password"

        token = util.ts.dumps(self.email, salt='recover-key')

        recover_url = url_for(
            'recover_account_with_token',
            token=token,
            _external=True)

        html = render_template(
            'email/recover.html',
            user=self,
            recover_url=recover_url)

        return util.send_email(
            self.email,
            subject,
            html)

    @classmethod
    def authenticate(cls, username, password):

        """ Authenticate a user with a username and a password """

        user = cls.query.filter_by(username=username).first()

        if user:
            authenticated = user.check_password(password)
        else:
            authenticated = False

        return user, authenticated

    def check_password(self, pass_for_comp):

        """ Check if a string matches this user's password """

        if bcrypt.check_password_hash(self._password, pass_for_comp):
            return True

        return False

    @classmethod
    def get(cls, userid=False, email=False):

        """ Get a user object from an id or email"""

        if userid:
            user = cls.query.filter(User.id == userid).first()
        elif email:
            user = cls.query.filter(User.email == email).first()

        if user:
            return user

        return None

    def get_gravatar_url(self):
        """Calculates and returns the user's gravatar URL."""

        return "http://gravatar.com/avatar/" + util.md5hash(self.email)


    def get_sets(self):
        """Return a list of set objects"""

        sets = []

        for book in self.books:
            for set in book.sets:
                if set not in sets:
                    sets.append(set)

        return sets
