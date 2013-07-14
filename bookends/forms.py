from wtforms.validators import ValidationError
from flask.ext.wtf import ( Form, TextField, PasswordField, Required, Email,
                            Length )

from .models import User


class Unique(object):
    """ Validator that makes sure the field is unique."""

    def __init__(self, model, field, message=None):
        self.model = model
        self.field = field
        if not message:
            message = u'This element already exists.'
        else:
            self.message = message

    def __call__(self, form, field):
        check = self.model.query.filter(self.field == field.data).first()
        if check:
            raise ValidationError(self.message)


class AccountCreateForm(Form):
    """ Basic account creation form."""

    email       = TextField('Email', validators=[
                    Required(), Email(), Unique(
                        User,
                        User.email,
                        message='There\'s already an account with that email.'
                    )])
    password    = PasswordField('Password', validators=[Required()])


class AccountRecoverForm(Form):
    """ The form to request an account recovery. """

    email       = TextField('Email', validators=[Required(), Email()])


class AccountRecoverWithTokenForm(Form):
    """ The form to choose a new password. """

    password    = PasswordField('Password', validators=[Required()])


class SignInForm(Form):
    """ Basic authentication form."""

    email       = TextField('Email', validators=[Required(), Email()])
    password    = PasswordField('Password', validators=[Required()])
