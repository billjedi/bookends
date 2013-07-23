from datetime import datetime, timedelta
from functools import wraps
from werkzeug.contrib.fixers import ProxyFix

import stripe

from flask import Flask, flash, redirect, url_for, request

from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.bcrypt import Bcrypt
from flask.ext.login import LoginManager, current_user

from sqlalchemy.orm.interfaces import SessionExtension

app = Flask(__name__, instance_relative_config=True)
app.config.from_object('config')
app.config.from_pyfile('config.py')
app.wsgi_app = ProxyFix(app.wsgi_app)

db = SQLAlchemy(app)

bcrypt = Bcrypt(app)

stripe.api_key = app.config["STRIPE_API_KEY"]

def check_expired(f):
    """
    A decorator to check that the user's account is active.

    It will check that the user's account_expires date is no more than 7 days
    in the past.

    Flashes a message if the user is in the 7 day grace period.

    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.is_authenticated() and request.method == "GET":
            if datetime.utcnow() - current_user.account_expires > timedelta(days=7):
                flash("It looks like it's time to start paying for Bookends.")
                return redirect(url_for('account_billing'))
            elif datetime.utcnow() > current_user.account_expires:
                delta = timedelta(days=7) - (datetime.utcnow() - current_user.account_expires)
                flash("You have " + str(delta.days) + " days until you have to <a href='" + url_for('account_billing') + "'>start paying</a>.")
        return f(*args, **kwargs)

    return decorated_function

from . import views

from .models import User, Book, Set

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view =  "signin"
login_manager.login_message = "Please sign in to view this page"
login_manager.refresh_view = "refresh_login"

@login_manager.user_loader
def load_user(userid):
    return User.get(userid=userid)
