from datetime import datetime, timedelta
import json

from flask import render_template, flash, redirect, url_for, abort, request

from flask.ext.login import login_required, login_user, current_user, logout_user, confirm_login, fresh_login_required

from . import app, db, util, check_expired, stripe
from .forms import (AccountCreateForm, AccountRecoverForm,
                    PasswordForm, SignInForm, AddEditBookForm,
                    ChangeEmailForm, DeleteBookForm, BillingForm, StopBillingForm,
                    AccountDeleteForm )
from .models import User, Book, Set


@app.route('/')
@check_expired
def index():
    """ Home page when anonymous, dashboard when authenticated. """

    if current_user.is_anonymous():
        return render_template("home_index.html")

    return render_template(
        "app_index.html",
        books_exciting=Book.query.filter_by(user_id=current_user.id, exciting=True),
        books_reading=Book.query.filter_by(user_id=current_user.id, reading=True).all()
    )


@app.route('/about')
def about():
    """Tell a little about the site."""

    return render_template("about.html")


@app.route('/accounts/create', methods=["GET", "POST"])
def create_account():
    """Create a new account."""

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
    """Activate the account by confirming their email address."""
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
    """Request an account recovery token to reset the password."""

    form = AccountRecoverForm()
    if form.validate_on_submit():
        user = User.get(email=form.email.data)
        user.send_recover_email()

        flash("Check your email for an account recovery link.")

        return redirect(url_for('index'))

    return render_template('accounts/recover.html', form=form)



@app.route('/accounts/recover/<token>', methods=["GET", "POST"])
def recover_account_with_token(token):
    """Let the user enter a new password if they have a valid token."""

    try:
        email = util.ts.loads(token, salt="recover-key", max_age=86400)
    except:
        return abort(404)

    form = PasswordForm()

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
    """Authenticate a user."""

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


@app.route('/signout')
@login_required
def signout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/books')
@login_required
@check_expired
def books():
    """ List the current user's books. """

    return render_template('books/index.html', books=current_user.books)


@app.route('/books/add', methods=["GET", "POST"])
@login_required
@check_expired
def add_book():
    """Add a book."""

    form = AddEditBookForm()

    if form.validate_on_submit():

        book = Book(
            title=form.title.data,
            author=form.author.data,
            url=form.url.data,
            reading=form.reading.data,
            exciting=form.exciting.data,
            finished=form.finished.data
        )

        book.update_sets(form.sets.data)

        current_user.books.append(book)

        db.session.add(current_user)
        db.session.commit()

        flash(book.title + " has been added.")

        return redirect(url_for('add_book'))

    return render_template('books/add.html', form=form)


@app.route('/books/edit/<int:book_id>', methods=["GET", "POST"])
@login_required
@check_expired
def edit_book(book_id):
    """Edit the book with a given id.

    Make sure that the book belongs to this user!

    """

    book = Book().query.filter_by(
        id=book_id,
        user_id=current_user.id
    ).first_or_404()

    form = AddEditBookForm()

    if form.validate_on_submit():

        book.title = form.title.data
        book.author = form.author.data
        book.url = form.url.data
        book.exciting = form.exciting.data
        book.reading = form.reading.data
        book.finished = form.finished.data

        book.update_sets(form.sets.data)

        db.session.add(book)

        db.session.commit()

        flash(book.title + " was updated.")

        return redirect(url_for('index'))

    return render_template('books/edit.html', book=book, form=form, delete_form=DeleteBookForm())


@app.route('/books/delete/<int:book_id>', methods=["POST"])
@login_required
@check_expired
def delete_book(book_id):
    form = DeleteBookForm()

    if form.validate_on_submit():
        book = Book().query.filter_by(id=book_id, user_id=current_user.id).first_or_404()

        db.session.delete(book)
        db.session.commit()

        flash(book.title + " was deleted.")

    return redirect(url_for('index'))


@app.route('/sets')
@login_required
@check_expired
def sets():
    """List all of a user's sets."""

    return render_template('/sets/index.html', sets=current_user.get_sets())


@app.route('/sets/view/<int:set_id>')
@login_required
@check_expired
def view_set(set_id):
    """View all of the books in a given set."""

    set = Set().query.filter_by(id=set_id, user_id=current_user.id).first_or_404()

    return render_template('/sets/view.html', set=set)


@app.route('/accounts/refresh', methods=["GET", "POST"])
@login_required
def refresh_login():
    form = PasswordForm()

    if form.validate_on_submit():
        if current_user.check_password(form.password.data):
            confirm_login()
            return redirect(request.args.get("next") or url_for("index"))
        else:
            flash("Incorrect password.")
            return redirect(url_for('refresh_login'))

    return render_template('accounts/refresh.html', form=form)


@app.route('/accounts/password', methods=["GET", "POST"])
@fresh_login_required
def account_password():
    form = PasswordForm()

    if form.validate_on_submit():
        current_user.password = form.password.data

        db.session.add(current_user)
        db.session.commit()

        flash("Your password has been updated.")

        return redirect(url_for('account_password'))

    return render_template("accounts/password.html", form=form)


@app.route('/accounts/email', methods=["GET", "POST"])
@fresh_login_required
def account_email():
    form = ChangeEmailForm()

    if form.validate_on_submit():
        current_user.send_email_update_email(form.email.data)

        flash("Check your new email address to confirm the update.")

        return redirect(url_for('index'))

    return render_template('accounts/email.html', form=form)

@app.route('/accounts/email/update/<token>')
@login_required
def account_email_update(token):
    try:
        email = util.ts.loads(token, salt="email-update-key", max_age=86400)
    except:
        return abort(404)

    current_user.email = email

    db.session.add(current_user)
    db.session.commit()

    flash("Your email has been updated.")

    return redirect(url_for('index'))


@app.route('/accounts/billing', methods=["GET", "POST"])
@fresh_login_required
def account_billing():
    """
    This is the route that starts billing the user.

    They submit a form, then their information is turned into a Stripe token,
    then that token is submitted here.

    """

    form = BillingForm()

    if form.validate_on_submit():
        token = form.stripeToken.data

        customer = None

        if current_user.stripe_id:
            customer = stripe.Customer.retrieve(current_user.stripe_id)

            customer.card = token

            customer.save()
        else:
            customer = stripe.Customer.create(
                card=token,
                plan='bookends1',
                email=current_user.email
            )

            current_user.stripe_id = customer.id

        if customer:
            current_user.account_expires = datetime.fromtimestamp(customer.subscription.current_period_end)
            current_user.card_last4 = customer.cards.data[0].last4

        db.session.add(current_user)
        db.session.commit()

        flash("Your billing information has been updated!")

        return redirect(url_for('index'))

    card = None

    if current_user.card_last4:
        flash("Your current card ends in " + current_user.card_last4 + ".")

    stop_form = StopBillingForm()

    return render_template('accounts/billing.html', form=form, card=card, stripe_publishable_key=app.config["STRIPE_PUBLISHABLE_KEY"], stop_form=stop_form)


@app.route('/accounts/billing/stop', methods=["POST"])
@login_required
def account_billing_stop():
    form = StopBillingForm()

    if form.validate_on_submit():
        customer = stripe.Customer.retrieve(current_user.stripe_id)

        customer.delete()
        current_user.card_last4 = None
        current_user.stripe_id = None

        db.session.add(current_user)
        db.session.commit()

        flash("Your payments have been stopped. Your account will expire in " + str((current_user.account_expires - datetime.utcnow()).days) + " days.")

        return redirect(url_for('index'))


@app.route('/accounts/delete', methods=["GET", "POST"])
@fresh_login_required
def account_delete():
    form = AccountDeleteForm()

    if form.validate_on_submit():
        db.session.delete(current_user)
        db.session.commit()

        logout_user()

        flash("Your account and all of your information was deleted.")

        return redirect(url_for('index'))

    return render_template('accounts/delete.html', form=form)


@app.route('/_stripe/webhook', methods=["POST"])
def stripe_webhook():
    """This is the route posted to by Stripe on events."""

    event = json.loads(request.data)

    if event.type is 'charge.succeeded':
        user = User().query.filter_by(stripe_id=event.customer).first_or_404()

        user.account_expires = datetime.fromtimestamp(event.data.subscription.current_period_end)

        db.sesion.add(user)
        db.session.commit()

        user.send_charge_succeeded_email()
    elif event.type is 'charge.failed':
        user = User().query.filter_by(stripe_id=event.customer).first_or_404()

        user.send_charge_failed_email()

    return abort(200)
