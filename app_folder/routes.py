import os
import secrets
from PIL import Image
from flask import render_template, url_for, flash, redirect, request, abort
from app_folder import app, db, bcrypt, mail
from app_folder.forms import (RegistrationForm, LoginForm, UpdateAccountForm,
                             PostForm, RequestResetForm, ResetPasswordForm,SearchForm,SearchDateForm,BMIForm,BMRForm)
from app_folder.models import User, Post,Food,Summary
from flask_login import login_user, current_user, logout_user, login_required
from flask_mail import Message
import requests
from bs4 import BeautifulSoup
import re
import datetime,time
from sqlalchemy import and_
from sqlalchemy import desc


@app.route("/")
@app.route("/home")
def home():
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.date_posted.desc()).paginate(page=page, per_page=5)
    return render_template('home.html', posts=posts)


@app.route("/bmi", methods=['GET', 'POST'])
def bmi():
    message = 'Your BMI: '
    form = BMIForm()

    if request.method == 'POST' and form.validate():
        userWeight = form.weight.data
        userHeight = form.height.data
        message = message + str(round((userWeight / (userHeight*userHeight))*703, 2))

    return render_template('bmi.html', title='Caculate My BMI', form=form, message=message)

@app.route("/bmr", methods=['GET', 'POST'])
def bmr():
    message = 'Your BMR: '
    message2 = '';
    form = BMRForm()

    if request.method == 'POST' and form.validate():
        userWeight = form.weight.data
        userHeight = form.height.data
        userAge = form.age.data
        if(form.gender.data == 'M'):
            bmr = (66 + (6.23 * userWeight) + (12.7 * userHeight) + (6.8*userAge))
        else:
            bmr = (655 + (4.35 * userWeight) + (4.7 * userHeight) + (4.7*userAge))

        message = message + str(round(bmr, 1))
        multiplier = float(form.activity.data)
        message2 = 'Your BMR: (x' + str(multiplier) + "): " + str(round(bmr*multiplier, 1))

    return render_template('bmr.html', title='Caculate My BMR', form=form, message=message, message2=message2)


@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You are now able to log in', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html', title='Login', form=form)


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))



@app.route("/account", methods=['GET', 'POST'])
@login_required
def account():
    form = UpdateAccountForm()
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash('Your account has been updated!', 'success')
        return redirect(url_for('account'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email

    return render_template('account.html', title='Account',form=form)


@app.route("/post/new", methods=['GET', 'POST'])
@login_required
def new_post():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(title=form.title.data, content=form.content.data, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash('Your post has been created!', 'success')
        return redirect(url_for('home'))
    return render_template('create_post.html', title='New Post',
                           form=form, legend='New Post')


def send_reset_email(user):
    token = user.get_reset_token()
    msg = Message('Password Reset Request',
                  sender='noreply@demo.com',
                  recipients=[user.email])
    msg.body = f'''To reset your password, visit the following link:
{url_for('reset_token', token=token, _external=True)}

If you did not make this request then simply ignore this email and no changes will be made.
'''
    mail.send(msg)


@app.route("/reset_password", methods=['GET', 'POST'])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        send_reset_email(user)
        flash('An email has been sent with instructions to reset your password.', 'info')
        return redirect(url_for('login'))
    return render_template('reset_request.html', title='Reset Password', form=form)


@app.route("/reset_password/<token>", methods=['GET', 'POST'])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    user = User.verify_reset_token(token)
    if user is None:
        flash('That is an invalid or expired token', 'warning')
        return redirect(url_for('reset_request'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user.password = hashed_password
        db.session.commit()
        flash('Your password has been updated! You are now able to log in', 'success')
        return redirect(url_for('login'))
    return render_template('reset_token.html', title='Reset Password', form=form)


@app.route("/search", methods=['GET', 'POST'])
def search_food_calories():
    form = SearchForm()
    if form.validate_on_submit():
        foodname=form.food.data
        #print(foodname)
        r = requests.get("https://www.myfitnesspal.com/food/search?page=1&search="+foodname)
        source=r.content
        soup = BeautifulSoup(source,'html.parser')
        notfound='There were no results for your search'
        html=soup.get_text()
        if notfound in html:
            #print("yes")
            return render_template('search_food_calories.html', title='search food calories',form=form,notfound=notfound)
        new = soup.find('div',attrs={'class':'jss16'})
        #print(new)
        #print("==========")
        newstring = re.findall(r">(.*?)<",str(new))
        #print(newstring)
        data=[]
        for i in newstring:
            if(re.search(r'\d', i)):
                num = re.sub(r'\D', "", i)
                data.append(num)      
        #return redirect(url_for('search',data=data))
        today=datetime.date.today()
        #print(today)
        data = Food(name=foodname,calories=data[0],carbon=data[1],fat=data[2],protein=data[3],date = today,quantity=1)
        #post = Post(title=form.title.data, content=form.content.data, author=current_user)
        return render_template('search_food_calories.html', title='search food calories',form=form,data=data)
    return render_template('search_food_calories.html', title='search food calories',form=form)

@app.route("/record", methods=['GET', 'POST'])
@login_required
def record_daily_calories():
    '''
    will show the food you add and make change on it.
    '''
    food_list=[]
    date = request.args.get('date')
    today = date
    if date:
        fmt = '%Y-%m-%d'
        time_tuple = time.strptime(date,fmt)
        year, month, day = time_tuple[:3]
        date = datetime.date(year, month, day)
        totday=date
    else:
        today=datetime.date.today()
    food_list = Food.query.filter(Food.date == today).filter(Food.user_id==current_user.id).order_by(desc(Food.calories)).all()
    total=0
    for item in food_list:
        total=total+item.calories*item.quantity
    if total == 0:
        total = 'None'
    return render_template('record.html', title='record calories',food_list=food_list,total=total,today=today)

@app.route('/add',methods=["GET","POST"])
@login_required
def add():
    name = request.args.get('name')
    date = request.args.get('date')
    newdate=date
    quantity = request.args.get('quantity')
    calories = request.args.get('calories')
    fmt = '%Y-%m-%d'
    time_tuple = time.strptime(date,fmt)
    year, month, day = time_tuple[:3]
    date = datetime.date(year, month, day)
    food = Food.query.filter_by(name=name,date=date,calories=calories,user_id=current_user.id).first()
    
    if quantity == '0':
        print("quantity is 0")
        db.session.delete(food)
        db.session.commit()
    elif food:
        print("+")
        db.session.delete(food)
        db.session.commit()
        food = Food(name=name,date=date,quantity=quantity,calories=calories,user_id=current_user.id)
        db.session.add(food)
        db.session.commit()
    else:
        food = Food(name=name,date=date,quantity=quantity,calories=calories,user_id=current_user.id)
        print("add")
        db.session.add(food)
        db.session.commit()

    return redirect('/record?date='+newdate)


@app.route('/deleteRecord',methods=["GET","POST"])
@login_required
def deleteRecord():
    date = request.args.get('date')
    newdate = date
    name = request.args.get('name')
    calories = request.args.get('calories')
    quantity = request.args.get('quantity')
    fmt = '%Y-%m-%d'
    time_tuple = time.strptime(date,fmt)
    year, month, day = time_tuple[:3]
    date = datetime.date(year, month, day)
    food = Food.query.filter_by(name=name,date=date,quantity=quantity,calories=calories,user_id=current_user.id).first()
    if food:
        print("food delete")
        db.session.delete(food)
        db.session.commit()
    else:
        print("pass")
    return redirect('/record?date='+newdate)

@app.route('/submitSummary',methods=["GET","POST"])
@login_required
def submitSummary():
    date = request.args.get('date')
    total_calories = request.args.get('total')
  
    fmt = '%Y-%m-%d'
    time_tuple = time.strptime(date,fmt)
    year, month, day = time_tuple[:3]
    date = datetime.date(year, month, day)
    summary = Summary.query.filter_by(date=date,user_id=current_user.id).first()
    if summary:
        db.session.delete(summary)
        db.session.commit()
    summary = Summary(date=date,total_calories=total_calories,user_id=current_user.id)
    db.session.add(summary)
    db.session.commit()
    return redirect("/dailySummary")

@app.route('/dailySummary',methods=["GET","POST"])
@login_required
def dailySummary():
    form = SearchDateForm()
    if form.validate_on_submit():
        print("jinlail")
        date = form.date.data
        food_list = Food.query.filter(Food.date == date).filter(Food.user_id==current_user.id).all()
        total = Summary.query.filter_by(date=date,user_id=current_user.id).first()
        if(total is None):
            food_list=[]
            return render_template("dailysummary.html",food_list=food_list,total=total,form=form)
        return render_template("dailysummary.html",food_list=food_list,total=total,form=form)
    else:
        today=datetime.date.today()
        food_list = Food.query.filter(Food.date == today).filter(Food.user_id==current_user.id).all()
        total = Summary.query.filter_by(date=today,user_id=current_user.id).first()
        if(total is None):
            food_list=[]
            return render_template("dailysummary.html",food_list=food_list,total=total,form=form)
        return render_template("dailysummary.html",food_list=food_list,total=total,form=form)
