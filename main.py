# ----------- IMPORTS --------------- #
import smtplib
from flask import Flask, render_template, url_for, redirect, flash
from flask_bootstrap import Bootstrap5
from dotenv import load_dotenv
import os
from flask_ckeditor import CKEditor
from werkzeug.security import generate_password_hash, check_password_hash
from forms import ContactForm, RegisterForm, LoginForm
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Integer, String, Text
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user

load_dotenv()
# ----------- CONSTANTS --------------- #
MY_EMAIL = os.getenv("MY_EMAIL")
APP_PASSWORD = os.getenv("APP_PASSWORD")

# ----------- FUNCTIONS --------------- #
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

# ----------- INITIALISATIONS --------------- #
app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
ckeditor = CKEditor(app)
Bootstrap5(app)

# Create Database
class Base(DeclarativeBase):
    pass
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///blog.db"
db = SQLAlchemy(model_class=Base)
db.init_app(app)


# Configure User Table
class User(UserMixin, db.Model):
    __tablename__ = "users"
    id : Mapped[int] = mapped_column(Integer, primary_key=True)
    email : Mapped[str] = mapped_column(String(250), unique=True)
    name : Mapped[str] = mapped_column(String(250), nullable=False)
    password : Mapped[str] = mapped_column(String(500), nullable=False)


with app.app_context():
    db.create_all()

# Configure Flask Login
login_manager = LoginManager()
login_manager.init_app(app)

# Loading user from DB
@login_manager.user_loader
def load_user(user_id):
    return db.get_or_404(User, user_id)

# Route to home page
@app.route("/")
def home_page():
    return render_template("index.html")

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
def logout():
    logout_user()
    return redirect(url_for('home_page'))

if __name__ == "__main__":
    app.run(debug=True)