#!/usr/bin/env python2.7
import os
from flask import Flask, jsonify, request, url_for, abort, g, render_template
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import create_engine, desc
from flask_httpauth import HTTPBasicAuth
import json
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
from flask import make_response, redirect, flash, session as login_session
import requests
import random
import string
from redis import Redis
import time
from functools import update_wrapper
import psycopg2
from database_setup import Base, Project, Picture, Customer, Architect, projectPicture, customerPicture, architectPicture
from werkzeug.utils import secure_filename
#------------------------------------------------------------------------#
#                     Configuration code                                 #
#------------------------------------------------------------------------#

## Shortcuts

# Redis server application to limit the access amounts per IP
redis = Redis()


# HTTP Authentication
auth = HTTPBasicAuth()


#  Extensive lib to do requests
h = httplib2.Http()


# Connecting to the database
engine = create_engine('sqlite:///icu.db?check_same_thread=False')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()


# assigning flask object to var
app = Flask(__name__)

UPLOAD_FOLDER = 'static/img/'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg'])

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

#------------------------------------------------------------------------#
#                     Routes for the webpages                            #
#------------------------------------------------------------------------#



#                              #
## Routes for Authentication  ##
#                              #


## Sign in window ##

@app.route('/signin', methods=['GET', 'POST'])
def signin():
    # State token to prevent forgery attacks
    if request.method == 'POST':
        if request.form['stateToken'] != login_session['state']:
            return render_template('error.html', errormessage="Invalid state token {} expecting {}".format(request.form['stateToken'], login_session['state']))

        # Check if user exists and the password is correct
        user = session.query(User).filter_by(email = request.form['email']).first()
        pword = request.form['password']

        # User does not exist
        if user is None:
            flash("Username or password not found")
            return render_template('signin.html')
        # Password is wrong
        if user.verify_password(pword) == False:
            flash("Username or password not found")
            return render_template('signin.html')

        # Add the Users object paramaters to the session cookie
        login_session['name'] = user.name
        login_session['email'] = user.email
        login_session['picture'] = user.picture
        login_session['id'] = user.id
        login_session['provider'] = 'local'

        # Redirect the user to the mainpage and send message to indicate succes
        flash("Welcome back {}".format(login_session['name']))
        return redirect(url_for('showCatalog'))

    # Render a token and send it with the page to prevent MiM attacks
    state = renderToken(32)
    login_session['state'] = state
    return render_template('signin.html', state=state)


## Route to log out ##

@app.route('/logout/')
def logout():
    if 'id' in login_session:
        del login_session['name']
        del login_session['email']
        del login_session['id']
        del login_session['picture']
        flash("Logged out successfully")
        return redirect(url_for('showCatalog'))


    return render_template('error.html', errormessage="No user logged in")


## Main Page ##
@app.route('/')
def home():
    projects = session.query(Project).all()
    pictures = session.query(Picture).all()
    return render_template('index.html', active='home', projecten=projects, pictures=pictures)

@app.route('/info')
def info():
    return render_template('info.html', active='info')

@app.route('/projecten')
def projecten():
    projects = session.query(Project).order_by(desc(Project.id)).limit(3)
    pictures = session.query(Picture).all()
    return render_template('projecten.html', active='projecten', projecten=projects, pictures=pictures)

@app.route('/projecten/nieuw', methods=['GET', 'POST'])
def nieuwProject():
    if request.method == 'POST':
        newProject = Project(name=request.form['name'], style=request.form['style'], type=request.form['type'], description=request.form['description'], contribution=request.form['contribution'])
        session.add(newProject)
        session.commit()


        # Handle project pictures
        files = request.files.getlist("file[]")
        for file in files:
            # Check if filename is valid and does not trigger any command
            filename = secure_filename(file.filename)
            # Save the file in the img folder
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

            # Add the picture to the database
            newPic = Picture(path=UPLOAD_FOLDER+filename)
            session.add(newPic)
            session.commit()

            # Link the picture to the project
            getProject = session.query(Project).filter_by(name = request.form['name']).first()
            getPicture = session.query(Picture).filter_by(path = UPLOAD_FOLDER+filename).first()
            combine = projectPicture(project_id=getProject.id, picture_id=getPicture.id)
            session.add(combine)
            session.commit()

        # Handle Profile pic
        # Get the picutre from the form
        file = request.files['profilePic']
        filename = secure_filename(file.filename)

        # Save the file in the img folder
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        # Add the picture to the database
        newPic = Picture(path=UPLOAD_FOLDER+filename)
        session.add(newPic)
        session.commit()

        # Link the picture as profile picture
        getProject = session.query(Project).filter_by(name = request.form['name']).first()
        getProject.profile_pic_id = newPic.id
        session.add(getProject)
        session.commit()

        # profiPic = session.query(projectPicture).filter_by(project_id = newProject.id).first()
        # session.add(newProject)
        # session.commit()


        return redirect(url_for('projecten'), 301)
    return render_template('nieuwProject.html', active='projecten')


@app.route('/projecten/<string:project_name>')
def showProject(project_name):
    project = session.query(Project).filter_by(name=project_name).first()
    pic_ids = session.query(projectPicture).filter_by(project_id=project.id).all()
    paths = []
    for picture in pic_ids:
        paths.append(picture.picture.path)
    return render_template('project_test.html', active='projecten', project=project, pictures=paths)

@app.route('/projecten/<string:project_name>/delete', methods=['GET','POST'])
def deleteProject(project_name):
    project = session.query(Project).filter_by(name=project_name).first()
    pictures = session.query(projectPicture).filter_by(project_id = project.id)
    for picture in pictures:
        session.delete(picture)
        session.commit()
    session.delete(project)
    session.commit()
    return redirect(url_for('projecten'), 301)


@app.route('/projecten/<string:project_name>/edit', methods=['GET','POST'])
def editProject(project_name):
    project = session.query(Project).filter_by(name=project_name).first()
    pic_ids = session.query(projectPicture).filter_by(project_id=project.id).all()
    paths = []
    for picture in pic_ids:
        paths.append(picture.picture.path)

    return render_template('editProject.html', project=project, pictures=paths)


@app.route('/bouwdrogers')
def bouwdrogers():
    return render_template('bouwdrogers.html', active='bouwdrogers')

@app.route('/contact')
def contact():
    return render_template('contact.html', active='contact')


if __name__ == '__main__':
    app.secret_key = "random token"
    app.debug = True
    app.run(host='0.0.0.0', port=8000)
