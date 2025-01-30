# ----------- IMPORTS --------------- #
import smtplib
from functools import wraps
from flask import Flask, render_template, url_for, redirect, flash, abort
from flask_bootstrap import Bootstrap5
from dotenv import load_dotenv
import os
from flask_ckeditor import CKEditor
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Integer, String, Text
from datetime import datetime
import hashlib
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user, login_required
from forms import ContactForm, RegisterForm, LoginForm, NewPostForm, CommentForm

load_dotenv()
# ----------- CONSTANTS --------------- #
MY_EMAIL = os.getenv("MY_EMAIL")
APP_PASSWORD = os.getenv("APP_PASSWORD")

# ----------- FUNCTIONS & DECORATORS --------------- #
def send_email(name, email, phone, message):

    with smtplib.SMTP("smtp.gmail.com") as connection:

        # Send email to the one contacted you.
        connection.starttls()
        connection.login(user=MY_EMAIL, password=APP_PASSWORD)
        connection.sendmail(
            from_addr=MY_EMAIL,
            to_addrs=email,
            msg=f"Subject:Message Received\n\nHey {name}, received your message.\nIt was lovely, will catch you up on your phone or email."
        )

        # Send email to yourself relaying the message received.
        connection.sendmail(
            from_addr=MY_EMAIL,
            to_addrs=MY_EMAIL,
            msg=f"Subject:Message from your blog website.\n\n{name} contacted you to say..\n  \n{message}\n  \nYou can contact them on his email {email} or his phone {phone}"
        )

def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.is_authenticated:
            if current_user.id != 1:
                return abort(403)
        else:
            flash("You have to log in first")
            return redirect(url_for('login'))
        return f(*args, **kwargs)

    return decorated_function

# ----------- INITIALISATIONS --------------- #
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY')
ckeditor = CKEditor(app)
Bootstrap5(app)


# For adding profile images to the comment section
def gravatar_url(email, size=100):
    hash_email = hashlib.md5(email.strip().lower().encode()).hexdigest()
    return f"https://www.gravatar.com/avatar/{hash_email}?s={size}&d=identicon"

# Create Database
class Base(DeclarativeBase):
    pass
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv('SQLALCHEMY_DATABASE_URI')
db = SQLAlchemy(model_class=Base)
db.init_app(app)

# Configure User Table
class User(UserMixin, db.Model):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(250), unique=True)
    name: Mapped[str] = mapped_column(String(250), nullable=False)
    password: Mapped[str] = mapped_column(String(500), nullable=False)
    # All the comments
    comments = relationship("Comment", back_populates="comment_author")
    # All the posts
    posts = relationship("BlogPost", back_populates="author")

# Configure Blog Post Table
class BlogPost(db.Model):
    __tablename__ = "blog_posts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    subtitle: Mapped[str] = mapped_column(String(300), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    img_url: Mapped[str] = mapped_column(String(250), nullable=False)
    date: Mapped[str] = mapped_column(String(250), nullable=False)
    # The author who wrote the blog
    author_id : Mapped[int] = mapped_column(Integer, db.ForeignKey("users.id"))
    author = relationship("User", back_populates="posts")
    # All the comments
    comments = relationship("Comment", back_populates="parent_post")

# Configure Comments Table
class Comment(db.Model):
    __tablename__ = "comments"
    id : Mapped[int] = mapped_column(Integer, primary_key=True)
    comment : Mapped[str] = mapped_column(Text, nullable=False)
    # The author who wrote the comment
    author_id : Mapped[int] = mapped_column(Integer, db.ForeignKey("users.id"))
    comment_author = relationship("User", back_populates="comments")
    # The post where the comment was written
    post_id : Mapped[int] = mapped_column(Integer, db.ForeignKey("blog_posts.id"))
    parent_post = relationship("BlogPost", back_populates="comments")

with app.app_context():
    db.create_all()

# Configure Flask Login
login_manager = LoginManager()
login_manager.init_app(app)

# Load user from DB
@login_manager.user_loader
def load_user(user_id):
    return db.get_or_404(User, user_id)

# Route to home page
@app.route("/")
def home_page():
    all_posts = db.session.execute(db.select(BlogPost)).scalars().all()

    return render_template("index.html", posts = all_posts)

# Route to about page
@app.route("/about")
def about():
    return render_template("about.html")

# Route to contact page
@app.route("/contact", methods=["GET", "POST"])
def contact():
    form = ContactForm()

    if form.validate_on_submit():

        name = form.name.data
        email = form.email.data
        phone = form.phone.data
        message = form.message.data

        send_email(name, email, phone, message)
        return render_template("contact.html", msg_sent=True, form=form)

    return render_template("contact.html", msg_sent=False, form=form)

# Route to register page
@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm()

    if form.validate_on_submit():
        check_user = db.session.execute(db.select(User).where(User.email == form.email.data)).scalar()

        if check_user:
            # User already exists
            flash("Email is already signed up. Log in instead!")
            return redirect(url_for('login'))

        hash_and_salted_password = generate_password_hash(
            form.password.data,
            method="pbkdf2:sha256",
            salt_length= 8
        )

        new_user = User(
            email = form.email.data,
            name = form.name.data,
            password = hash_and_salted_password
        )

        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)

        return redirect(url_for('home_page'))

    return render_template("register.html", form=form)

# Route to login page
@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()

    if form.validate_on_submit():

        user = db.session.execute(db.select(User).where(form.email.data == User.email)).scalar()
        password = form.password.data

        if not user:
            # User not found
            flash("That email id is not registered. Register please")
            return redirect(url_for('register'))
        elif not check_password_hash(user.password, password):
            # Incorrect Password
            flash("Incorrect Credentials. Try again!")
            return redirect(url_for('login'))
        else:
            login_user(user)
            return redirect(url_for('home_page'))

    return render_template("login.html", form=form)

# Logout method
@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('home_page'))

# Display selected post
@app.route("/post/<int:post_id>", methods = ["POST", "GET"])
def post(post_id):
    selected_post = db.get_or_404(BlogPost, post_id)

    comment_form = CommentForm()

    if comment_form.validate_on_submit():
        if not current_user.is_authenticated:
            flash("You need to login or register to comment.")
            return redirect(url_for("login"))

        new_comment = Comment(
            comment = comment_form.comment_text.data,
            comment_author = current_user,
            parent_post = selected_post
        )

        db.session.add(new_comment)
        db.session.commit()
        return redirect(url_for('post', post_id = post_id))

    return render_template("post.html",gravatar_url=gravatar_url, post=selected_post, form = comment_form)

# Method to create a new post
@app.route("/new-post", methods=["POST", "GET"])
@admin_only
def create_post():
    form = NewPostForm()

    if form.validate_on_submit():

        new_blog = BlogPost(
            title = form.title.data,
            subtitle = form.subtitle.data,
            body = form.body.data,
            img_url = form.img_url.data,
            date = datetime.now().strftime("%d %B, %Y"),
            author = current_user
        )

        db.session.add(new_blog)
        db.session.commit()

        return redirect(url_for('home_page'))

    return render_template("new-post.html", form=form)

@app.route("/edit-post/<int:post_id>", methods=["GET", "POST"])
@admin_only
def edit_post(post_id):

    post_to_edit = db.get_or_404(BlogPost, post_id)

    edit_post_form = NewPostForm(
        title = post_to_edit.title,
        subtitle = post_to_edit.subtitle,
        body = post_to_edit.body,
        img_url = post_to_edit.img_url,
    )

    if edit_post_form.validate_on_submit():
        post_to_edit.title = edit_post_form.title.data
        post_to_edit.subtitle = edit_post_form.subtitle.data
        post_to_edit.body = edit_post_form.body.data
        post_to_edit.img_url = edit_post_form.img_url.data
        db.session.commit()

        return redirect(url_for("post", post_id=post_id))
    return render_template("new-post.html", form=edit_post_form, is_edit=True)

@app.route("/delete-post/<int:post_id>")
@admin_only
def delete_post(post_id):
    post_to_delete = db.get_or_404(BlogPost, post_id)
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for('home_page'))


if __name__ == "__main__":
    app.run(debug=False)