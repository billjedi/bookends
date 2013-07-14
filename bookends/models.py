from flask import render_template, url_for

from sqlalchemy.ext.hybrid import hybrid_property

from . import db, util, bcrypt, app


class User(db.Model):

    __tablename__ = 'users'

    # Columns

    #-------------------------------------------------------------------------

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    email = db.Column(db.String(64), unique=True)

    _password = db.Column(db.String(64))

    email_confirmed = db.Column(db.Boolean, default=False)

    active = db.Column(db.Boolean, default=True)

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
