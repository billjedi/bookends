from flask import render_template, flash, redirect, url_for, abort

from flask.ext.login import login_required, login_user, current_user, logout_user, confirm_login, fresh_login_required

from . import app, db, util
from .forms import (AccountCreateForm, AccountRecoverForm,
                    PasswordForm, SignInForm, AddEditBookForm,
                    ChangeEmailForm, DeleteBookForm )
from .models import User, Book, Set


@app.route('/')
def index():
    """ Home page when anonymous, dashboard when authenticated. """

    if current_user.is_anonymous():
        return render_template("home_index.html")

    return render_template(
        "app_index.html",
        books_excited=Book.query.filter_by(user_id=current_user.id, excited=True),
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
def books():
    """ List the current user's books. """

    return render_template('books/index.html', books=current_user.books)


@app.route('/books/add', methods=["GET", "POST"])
@login_required
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

        book.update_sets(form.sets.data)

        current_user.books.append(book)

        db.session.add(current_user)
        db.session.commit()

        flash(book.title + " has been added.")

        return redirect(url_for('add_book'))

    return render_template('books/add.html', form=form)


@app.route('/books/edit/<int:book_id>', methods=["GET", "POST"])
@login_required
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

        book.update_sets(form.sets.data)

        db.session.add(book)

        db.session.commit()

        flash(book.title + " was updated.")

        return redirect(url_for('index'))

    return render_template('books/edit.html', book=book, form=form, delete_form=DeleteBookForm())


@app.route('/books/delete/<int:book_id>', methods=["POST"])
@login_required
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
def sets():
    """List all of a user's sets."""

    return render_template('/sets/index.html', sets=current_user.get_sets())


@app.route('/sets/view/<int:set_id>')
@login_required
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


@app.route('/accounts/billing')
@fresh_login_required
def account_billing():
    return render_template('accounts/billing.html')
