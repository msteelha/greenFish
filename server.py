import flask
from flask import request
from flask import url_for
from flask import jsonify # For AJAX transactions

import json
import logging

# Mongo database
import pymongo
from pymongo import MongoClient
from bson.objectid import ObjectId

# Date handling
import arrow # Replacement for datetime, based on moment.js
#import datetime # But we still need time
#from dateutil import tz  # For interpreting local times

# Our own module
#import pre  # Preprocess schedule file


###
# Globals
###
app = flask.Flask(__name__)
#schedule = "static/schedule.txt"  # This should be configurable
import CONFIG


import uuid
app.secret_key = str(uuid.uuid4())
app.debug = CONFIG.DEBUG
app.logger.setLevel(logging.DEBUG)


try:
    dbclient = MongoClient(CONFIG.MONGO_URL)
    db = dbclient.service
    collectionTeamBuildList = db.tbl
    collectionAccounts = db.adminAccounts
    collectionTeamBuilds = db.teamBuilds
except:
    print("Failure opening database.  Is Mongo running? Correct password?")
    #sys.exit(1)

#############
####Pages####
#############


### Home Page ###

@app.route("/")
@app.route("/index")
def index():
    app.logger.debug("Main page entry")
    return flask.render_template('index.html')

### Client Page ###

@app.route("/client")
def client():
    app.logger.debug("client page entry")
    return flask.render_template('client.html')

### Admin Page ###

@app.route("/admin")
def admin():
    app.logger.debug("admin page entry")
    app.logger.debug(flask.session.get('login'))
    if flask.session.get('login') == None:
        return flask.render_template('login.html')
    return flask.render_template('admin.html')

@app.route('/login')
def login():
    if flask.session.get('login') == True:
        return flask.redirect(url_for('admin'))
    else:
        return flask.render_template('login.html')

@app.route('/createAdmin')
def createAdmin():
        return flask.render_template('createAdmin.html')

@app.errorhandler(404)
def page_not_found(error):
    app.logger.debug("Page not found")
    flask.session['linkback'] = flask.url_for("index")
    return flask.render_template('page_not_found.html'), 404

################
###functions###
################

###for index page###
@app.route("/_portal")
def portalSelector():
    objId = request.args.get('portal', 0, type=str)
    app.logger.debug(objId)
    if objId == "client":
        return flask.redirect(url_for('client'))
    else:
        return flask.redirect(url_for('admin'))

###for login page###
@app.route("/_submitLoginRequest")
def loginGate():
    adminName = request.args.get('adminName',0,type=str)
    adminKey = request.args.get('adminKey',0,type=str)
    account = collectionAccounts.find_one({'name':adminName,'password':adminKey})
    app.logger.debug(account)
    if account != None:
        flask.session['login'] = str(account.get('_id'))
        flask.session['name'] = account.get('name')
        d = {'result':'success'}
    else:
        d = {'result':'failed'}
    d = json.dumps(d)
    return jsonify(result = d)

### for administrative settings###
@app.route("/_adminSettings")
def adminSettings():
    setting = request.args.get('setting',0,type=str)
    adminName = request.args.get('adminName',0,type=str)
    adminKey = request.args.get('adminKey',0,type=str)
    if setting  == "addAdmin":
        tbl = [] #a list of team builder object ids for the administrator
        record = {"name":adminName, "password":adminKey, "date":arrow.utcnow().naive, "teamBuildList": tbl}
        collectionAccounts.insert(record)
        d = {'result':'added'}
    elif setting == "removeAdmin":
        collectionAccounts.remove({'_id':flask.session.get('login')})
        flask.session['name'] = None
        flask.session['login'] = None
        return flask.redirect(url_for('login'))
    elif setting == "logout":
        flask.session['name'] = None
        flask.session['login'] = None
        return flask.redirect(url_for('login'))
    else:
        d = {'result':'wat'}
    d = json.dumps(d)
    return jsonify(result = d)


##############################
##########Filters#############
##############################
@app.template_filter('convert_time')
def convert_time(timestamp):
    val = arrow.get(timestamp)
    return val.format('h:mm A')


if __name__ == "__main__":
    import uuid
    app.secret_key = str(uuid.uuid4())
    app.debug = CONFIG.DEBUG
    app.logger.setLevel(logging.DEBUG)
    app.run(port=CONFIG.PORT,threaded=True)
