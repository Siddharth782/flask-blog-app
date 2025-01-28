# ----------- IMPORTS --------------- #
import smtplib
from flask import Flask, render_template, request
from flask_bootstrap import Bootstrap5
from dotenv import load_dotenv
import os
from flask_ckeditor import CKEditor
from forms import ContactForm, RegisterForm, LoginForm

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
@app.route("/register")
def register():
    form = RegisterForm()
    return render_template("register.html", form=form)

# Route to login page
@app.route("/login")
def login():
    form = LoginForm()
    return render_template("login.html", form=form)

if __name__ == "__main__":
    app.run(debug=True)