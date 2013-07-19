import re

from flask import render_template, flash, redirect, url_for, abort

from flask.ext.login import login_required, login_user, current_user

from . import app, db, util
from .forms import (AccountCreateForm, AccountRecoverForm,
                    ChangePasswordForm, SignInForm, AddEditBookForm,
                    ChangeEmailForm )
from .models import User, Book, Set


@app.route('/')
def index():
    """ Home page when anonymous, dashboard when authenticated. """

    if current_user.is_anonymous():
        return render_template("index.html")

    return render_template(
        "user_index.html",
        books_excited=Book.query.filter_by(user_id=current_user.id, excited=True)
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

    form = ChangePasswordForm()

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


@login_required
@app.route('/signout')
def signout():
    pass


@login_required
@app.route('/books')
def books():
    """ List the current user's books. """

    return render_template('books/index.html', books=current_user.books)


@login_required
@app.route('/books/add', methods=["GET", "POST"])
def add_book():
    """Add a book."""

    form = AddEditBookForm()

    if form.validate_on_submit():

        book = Book(
            title=form.title.data,
            author=form.author.data,
            url=form.url.data,
            reading=form.reading.data,
            excited=form.excited.data,
            finished=form.finished.data
        )

        sets_given = re.findall(r"\{(.+?)\}", form.sets.data)

        for set_title in sets_given:

            existing_set = Set().query.filter_by(
                title=set_title,
                user_id=current_user.id
            ).first()

            if existing_set:
                book.sets.append(existing_set)
            else:
                new_set = Set(title=set_title)
                current_user.sets.append(new_set)
                book.sets.append(new_set)

        current_user.books.append(book)

        db.session.add(current_user)
        db.session.commit()

        flash("<em>" + book.title + "</em> has been added.")

        return redirect(url_for('add_book'))

    return render_template('books/add.html', form=form)


@login_required
@app.route('/books/edit/<int:book_id>', methods=["GET", "POST"])
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
        book.excited = form.excited.data
        book.reading = form.reading.data
        book.finished = form.finished.data

        db.session.add(book)
        db.session.commit()

        flash("<em>" + book.title + "</em> was updated")

        return redirect(url_for('index'))

    return render_template('books/edit.html', book=book, form=form)


@login_required
@app.route('/sets')
def sets():
    """List all of a user's sets."""

    return render_template('/sets/index.html', sets=current_user.sets)


@login_required
@app.route('/sets/view/<int:set_id>')
def view_set(set_id):
    """View all of the books in a given set."""

    set = current_user.sets.filter_by(id=set_id).first_or_404()

    return render_template('/sets/view.html', set=set)


@login_required
@app.route('/accounts/password', methods=["GET", "POST"])
def account_password():
    form = ChangePasswordForm()

    if form.validate_on_submit():
        current_user.password = form.password.data

        db.session.add(current_user)
        db.session.commit()

        flash("Your password has been updated")

        return redirect(url_for('account_password'))

    return render_template("accounts/password.html", form=form)


@login_required
@app.route('/accounts/email', methods=["GET", "POST"])
def account_email():
    form = ChangeEmailForm()

    if form.validate_on_submit():
        current_user.send_email_update_email(form.email.data)

        flash("Check your new email address to confirm the update.")

        return redirect(url_for('index'))

    return render_template('accounts/email.html', form=form)

@login_required
@app.route('/accounts/email/update/<token>')
def account_email_update(token):
    try:
        email = util.ts.loads(token, salt="email-update-key", max_age=86400)
    except:
        return abort(404)

    current_user.email = email

    db.session.add(current_user)
    db.session.commit()

    flash("Your email has been updated")

    return redirect(url_for('index'))


@login_required
@app.route('/accounts/billing')
def account_billing():
    pass
