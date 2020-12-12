from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from flask_login import current_user
from wtforms import StringField, PasswordField, SubmitField, BooleanField, TextAreaField, IntegerField, SelectField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError, NumberRange
from app_folder.models import User
from wtforms.fields.html5 import DateField


class RegistrationForm(FlaskForm):
    username = StringField('Username',
                           validators=[DataRequired(), Length(min=2, max=20)],render_kw={"placeholder": "Username"})
    email = StringField('Email',
                        validators=[DataRequired(), Email()],render_kw={"placeholder": "123@gmail.com"})
    password = PasswordField('Password', validators=[DataRequired()],render_kw={"placeholder": "Password"})
    confirm_password = PasswordField('Confirm Password',
                                     validators=[DataRequired(), EqualTo('password')],render_kw={"placeholder": "Password"})
    submit = SubmitField('Sign Up')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('That username is taken. Please choose a different one.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('That email is taken. Please choose a different one.')


class LoginForm(FlaskForm):
    email = StringField('Email',validators=[DataRequired(), Email()],render_kw={"placeholder": "123@gmail.com"})
    password = PasswordField('Password',validators=[DataRequired()],render_kw={"placeholder": "Password"})
    submit = SubmitField('Login')


    def validate_username(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is None:
            raise ValidationError('Invalid Username or Password')
        elif not user.check_password(self.password.data):
            raise ValidationError('Invalid Username or Password')


class UpdateAccountForm(FlaskForm):
    username = StringField('Username',
                           validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    picture = FileField('Update Profile Picture', validators=[FileAllowed(['jpg', 'png'])])
    submit = SubmitField('Update')

    def validate_username(self, username):
        if username.data != current_user.username:
            user = User.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError('That username is taken. Please choose a different one.')

    def validate_email(self, email):
        if email.data != current_user.email:
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError('That email is taken. Please choose a different one.')

class BMIForm(FlaskForm):
    weight = IntegerField('Weight (lbs)', validators=[DataRequired(message='Invalid Number'), NumberRange(min=0, max=1000, message='Invalid Range (max=1000 lbs)')])
    height = IntegerField('Height (in)', validators=[DataRequired(message='Invalid Number'), NumberRange(min=0, max=200, message='Invalid Range (max=200 in)')])
    submit = SubmitField('Caculate BMI')

class BMRForm(FlaskForm):
    weight = IntegerField('Weight (lbs)', validators=[DataRequired(message='Invalid Number'), NumberRange(min=0, max=1000, message='Invalid Range (max=1000 lbs)')])
    height = IntegerField('Height (in)', validators=[DataRequired(message='Invalid Number'), NumberRange(min=0, max=200, message='Invalid Range (max=200 in)')])
    age = IntegerField('Age (yrs)', validators=[DataRequired(message='Invalid Number'), NumberRange(min=0, max=150, message='Invalid Range (max=150 yrs)')])
    gender = SelectField('Gender', choices=[('M', 'Male'), ('F', 'Female')])
    submit = SubmitField('Caculate BMR')

class PostForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(),Length(min=4, max=20)])
    content = TextAreaField('Content', validators=[DataRequired(),Length(min=4)])
    submit = SubmitField('Post')


class RequestResetForm(FlaskForm):
    email = StringField('Email',
                        validators=[DataRequired(),])
    submit = SubmitField('Request Password Reset')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is None:
            raise ValidationError('Email is not exist,please register first')


class ResetPasswordForm(FlaskForm):
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password',
                                     validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Reset Password')

class SearchForm(FlaskForm):
    food = StringField('Food', validators=[DataRequired()])
    submit = SubmitField('Search')

class SearchDateForm(FlaskForm):
    date = DateField('Date', format='%Y-%m-%d',validators=[DataRequired()])
    submit = SubmitField('Search')





