#!/usr/bin/env python2.7
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
# engine = create_engine('postgresql://connection:catalogitems@localhost/catalog')
# Base.metadata.bind = engine
# DBSession = sessionmaker(bind=engine)
# session = DBSession()


# assigning flask object to var
app = Flask(__name__)



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
    return render_template('index.html', active='home')

@app.route('/info')
def info():
    return render_template('info.html', active='info')

@app.route('/projecten')
def projecten():
    return render_template('index.html', active='projecten')

@app.route('/bouwdrogers')
def bouwdrogers():
    return render_template('index.html', active='bouwdrogers')

@app.route('/contact')
def contact():
    return render_template('contact.html', active='contact')


if __name__ == '__main__':
    app.secret_key = "random token"
    app.debug = True
    app.run(host='0.0.0.0', port=8000)
