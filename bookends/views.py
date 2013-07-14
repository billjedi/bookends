from flask import render_template, flash, redirect, url_for, abort

from flask.ext.login import login_required, login_user, current_user

from . import app, db, util
from .forms import (AccountCreateForm, AccountRecoverForm,
                    AccountRecoverWithTokenForm, SignInForm)
from .models import User


@app.route('/')
def index():
    """ Home page when anonymous, dashboard when authenticated. """

    if current_user.is_authenticated:
        return render_template("user_index.html")

    return render_template("index.html")


@app.route('/about')
def about():
    return render_template("about.html")


@app.route('/accounts/create', methods=["GET", "POST"])
def create_account():
    form = AccountCreateForm()
    if form.validate_on_submit():
        user = User(
                email = form.email.data,
                password = form.password.data
                )
        db.session.add(user)
        db.session.commit()

        user.send_activation_email()

        flash("You're account has been created. Check your email for your activation link.")
        return redirect(url_for("index"))

    return render_template("accounts/create.html", form=form)


@app.route('/accounts/activate/<token>')
def activate_account(token):
    try:
        email = util.ts.loads(token, salt="activation-key", max_age=86400)
    except:
        return abort(404)

    user = User.get(email=email)

    if user is None:
        return abort(404)

    user.email_confirmed = True

    db.session.add(user)
    db.session.commit()

    login_user(user)

    flash("Your account has been activated. Welcome to Bookends!")

    return redirect(url_for('index'))


@app.route('/accounts/recover', methods=["GET", "POST"])
def recover_account():
    form = AccountRecoverForm()
    if form.validate_on_submit():
        user = User.get(email=form.email.data)
        user.send_recover_email()

        flash("Check your email for an account recovery link.")

        return redirect(url_for('index'))

    return render_template('accounts/recover.html', form=form)



@app.route('/accounts/recover/<token>', methods=["GET", "POST"])
def recover_account_with_token(token):
    try:
        email = util.ts.loads(token, salt="recover-key", max_age=86400)
    except:
        return abort(404)

    form = AccountRecoverWithTokenForm()

    if form.validate_on_submit():
        user = User.get(email=email)

        if user is None:
            return abort(404)

        user.password = form.password.data

        db.session.add(user)
        db.session.commit()

        flash("You can now sign in with your new password.")

        return redirect('signin')

    return render_template("accounts/recover_with_token.html", form=form, token=token)


@app.route('/signin', methods=["POST", "GET"])
def signin():
    form = SignInForm()

    if form.validate_on_submit():
        user = User.get(email=form.email.data)

        if user is None:
            return abort(404)

        if user.check_password(form.password.data):
            login_user(user)

            return redirect(url_for('index'))
        else:
            flash("That's not the right email or password.")

    return render_template('signin.html', form=form)


@login_required
@app.route('/signout')
def signout():
    pass


@login_required
@app.route('/books')
def books():
    pass


@login_required
@app.route('/books/add', methods=["GET", "POST"])
def add_book():
    pass


@login_required
@app.route('/books/view/<int:book_id>')
def view_book(book_id):
    pass


@login_required
@app.route('/sets')
def sets():
    pass


@login_required
@app.route('/sets/add')
def add_set():
    pass


@login_required
@app.route('/sets/view/<int:set_id>')
def view_set(set_id):
    pass


@login_required
@app.route('/accounts/password')
def account_password():
    pass


@login_required
@app.route('/accounts/email')
def account_email():
    pass


@login_required
@app.route('/accounts/cancel')
def account_cancel():
    pass


@login_required
@app.route('/accounts/billing')
def account_billing():
    pass
