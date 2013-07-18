import md5

from flask import flash
from itsdangerous import URLSafeTimedSerializer
import mandrill

from . import app


ts = URLSafeTimedSerializer(app.config["SECRET_KEY"])

mandrill_client = mandrill.Mandrill(app.config["MANDRILL_KEY"])

def flash_errors(form):
    for field, errors in form.errors.items():
        for error in errors:
            flash(u"Error in the %s field - %s" % (
                getattr(form, field).label.text,
                error))


def send_email(to_email, subject, html):

    message = {
        'html': html,
        'subject': subject,
        'from_email': app.config["MAIL_FROM_EMAIL"],
        'from_name': app.config["MAIL_FROM_NAME"],
        'to': [{'email': to_email}]
    }

    result = mandrill_client.messages.send(message=message)

    return result

def md5hash(string):
    """Return the hex digest of an MD5 hash of a string (for Gravatar)."""

    m = md5.new()

    m.update(string)

    return m.hexdigest()
