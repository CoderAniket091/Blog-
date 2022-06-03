from flask import Flask, render_template, request, session, redirect
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from flask_mail import Mail
import json
from datetime import datetime
import os
import math

with open("config.json", "r") as c:
    params = json.load(c)["params"]

local_server = True

app = Flask(__name__)     #If we create a website then it's an application in flask
app.secret_key = 'secret-key'
app.config['UPLOAD_FOLDER'] = params['upload_location']
app.config.update(
    MAIL_SERVER = 'smtp.gmail.com',
    MAIL_PORT = '465',
    MAIL_USE_SSL = True,
    MAIL_USERNAME = params["gmail-user"],
    MAIL_PASSWORD = params["gmail-password"]
)
mail = Mail(app)
if local_server:
    app.config['SQLALCHEMY_DATABASE_URI'] = params["local_uri"]
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = params["prod_uri"]

db = SQLAlchemy(app)

#CONTACTS CLASS
class Contacts(db.Model):
    srno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80),  nullable=False)
    email = db.Column(db.String(20),  nullable=False)
    phone_num = db.Column(db.String(12),  nullable=False)
    msg = db.Column(db.String(120),  nullable=False)
    date = db.Column(db.String(12),  nullable=True)

#POSTS CLASS
class Posts(db.Model):
    srno = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80),  nullable=False)
    tagline = db.Column(db.String(120), nullable=False)
    slug = db.Column(db.String(21),  nullable=False)
    content = db.Column(db.String(120),  nullable=False)
    date = db.Column(db.String(12),  nullable=True)
    img_file = db.Column(db.String(12),  nullable=True)

#HOME PAGE ROUTE
@app.route("/")
def home():
    posts = Posts.query.filter_by().all()
    last = math.ceil(len(posts)/params['no_of_posts'])
    page=request.args.get('page')
    if (not str(page).isnumeric()):
        page = 1
    page = int(page)
    posts = posts[(page - 1) * params['no_of_posts']:(page - 1) * params['no_of_posts'] + params['no_of_posts']]
    if page==1:
        prev = '#'
        next = "/?page="+ str(page+1)

    elif page==last:
        next = '#'
        prev = "/?page=" + str(page - 1)

    else:
        prev = "/?page=" + str(page - 1)
        next = "/?page=" + str(page + 1)
    # posts = Posts.query.filter_by().all()[0:params['no_of_posts']]
    return render_template('index.html', params=params, posts = posts, prev=prev, next=next)

#ABOUT PAGE ROUTE
@app.route("/about")
def about():
    return render_template('about.html', params=params)

#POST FETCHING THROUGH SLUG
@app.route("/post/<string:post_slug>", methods = ['GET'])
def post_route(post_slug):
    post = Posts.query.filter_by(slug=post_slug).first()

    return render_template('post.html', params=params, post=post)

#DASHBOARD PAGE ROUTE
@app.route("/dashboard", methods=['GET', 'POST'])
def dashboard():

    if 'user' in session and session['user'] == params['admin_user']:
        posts = Posts.query.all()
        return render_template('dashboard.html', params = params, posts = posts)

    if request.method == 'POST':
        #REDIRECT TO ADMIN PANNEL
        username = request.form.get('uname')
        userpass = request.form.get('pass')
        if (username == params['admin_user'] and userpass == params['admin_password']) :
            session['user'] = username
            posts = Posts.query.all()
            return render_template('dashboard.html', params=params, post=posts)
    else:
        return render_template('login.html' , params=params)

    return render_template('login.html', params=params)

#EDIT BUTTON ROUTE
@app.route("/edit/<string:srno>", methods = ['GET', 'POST'])
def edit(srno):
    if 'user' in session and session['user'] == params['admin_user']:
        if request.method == 'POST':
            box_title = request.form.get('title')
            tline = request.form.get('tline')
            slug = request.form.get('slug')
            content = request.form.get('content')
            img_file = request.form.get('img_file')
            date = datetime.now()

            if srno == '0':
                post = Posts(title = box_title, tagline=tline, slug = slug, content = content,  img_file = img_file, date=date)
                db.session.add(post)
                db.session.commit()

            else:
                post = Posts.query.filter_by(srno=srno).first()
                post.title = box_title
                post.tagline = tline
                post.slug = slug
                post.content = content
                post.img_file = img_file
                post.date = date
                db.session.commit()
                return redirect('/edit/'+srno)
        post = Posts.query.filter_by(srno=srno).first()
        return render_template('edit.html', params=params, post=post, srno=srno)

#CONTACT PAGE ROUTE
@app.route("/contact", methods = ['GET', 'POST'])
def contact():
    if (request.method=='POST'):
        '''ADD ENTRY TO DB'''
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        message = request.form.get('message')
        entry = Contacts(name=name, phone_num=phone, msg=message, email=email, date = datetime.now())
        db.session.add(entry)
        db.session.commit()
        mail.send_message('New message from' + name, sender=email,
                          recipients=params['gmail-user'],
                          body = message + "\n" + phone)

    return render_template('contact.html', params=params)

#Files Uploader
@app.route("/uploader", methods = ['GET', 'POST'])
def uploader():
    if 'user' in session and session['user'] == params['admin_user']:
        if request.method == 'POST':
            f = request.files['file']
            f.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(f.filename) ))
            return "Uploaded Successfully"

#Delete Endpoint
@app.route("/delete/<string:srno>", methods = ['GET', 'POST'])
def delete(srno):
    if 'user' in session and session['user'] == params['admin_user']:
        post = Posts.query.filter_by(srno=srno).first()
        db.session.delete(post)
        db.session.commit()
    return redirect('/dashboard')

#LogOut Endpoint
@app.route("/logout")
def logout():
    session.pop('user') #It kills user session
    return redirect('/dashboard')


# app.run()
app.run(debug=False, host='0.0.0.0') #If you do this then it will return your change instantly and don't need to restart
