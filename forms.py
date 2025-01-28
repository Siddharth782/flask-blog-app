from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField
from wtforms.validators import DataRequired, Email, Length
from flask_ckeditor import CKEditorField

# To Contact the Author of the form
class ContactForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired(), Email()])
    phone = StringField("Phone", validators=[DataRequired()])
    message = CKEditorField("Message", validators=[DataRequired()])
    submit = SubmitField("Send Message")

# To register a new user
class RegisterForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=8, message="Your password should be minimum 8 characters long")])
    submit = SubmitField("Sign Up!")

# To log in an existing user
class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=8, message="Your password should be minimum 8 characters long")])
    submit = SubmitField("Let me in")