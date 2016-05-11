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

###
# Globals
###
app = flask.Flask(__name__)
import CONFIG


import uuid
app.secret_key = str(uuid.uuid4())
app.debug = CONFIG.DEBUG
app.logger.setLevel(logging.DEBUG)

with open('static/questions.txt','r') as inf:
    questions = eval(inf.read())
try:
    dbclient = MongoClient(CONFIG.MONGO_URL)
    db = dbclient.service
    collectionClassDB = db.classDB
    collectionAccounts = db.adminAccounts
    collectionFormsDB = db.forms
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
    if flask.sesion.get("questions") == None:
        flask.session['questions'] = questions
### ADDED OPTION FOR TWO PAGES FOR FORMS ###
### ONE PRE PRIORITY, ONE POST ###

    if flask.session.get('priorityList') == None:
        return flask.render_template('client.html')
    else:
        return flask.render_template('client.html')

### Admin Page ###

@app.route("/admin")
def admin():
    app.logger.debug("admin page entry")
    app.logger.debug(flask.session.get('login'))
    if flask.session.get('login') == None:
        return flask.render_template('login.html')
    classList = collectionAccounts.find_one({"_id":flask.session.get('login')}).get("classList")
    accList = []
    for aId in classList:
        accList.append(str(collectionClassDB.find_one({"_id":aId}).get("_id")))
    flask.session['myClassDB'] = accList
    return flask.render_template('admin.html')

@app.route('/login')
def login():
    if flask.session.get('login') != None:
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
        classList = [] #a list of team builder object ids for the administrator
        if collectionAccounts.find_one({'name':adminName}) == None:
            record = {"name":adminName, "password":adminKey, "date":arrow.utcnow().naive, "classList": classList}
            collectionAccounts.insert(record)
            d = "added"
        else:
            d = "account exists"
    elif setting == "removeAdmin":
        aClassList = collectionAccounts.find_one({"_id":flask.session.get('login')}).get("classList")
        for aVal in aClassList:
            deleteForms(aVal)
        collectionAccounts.remove({'_id':flask.session.get('login')})
        removeState()
        return flask.redirect(url_for('login'))
    elif setting == "logout":
        removeState()
        return flask.redirect(url_for('login'))
    else:
        d = "wat"
    return jsonify(result = d)

def removeState():
    flask.session['name'] = None
    flask.session['login'] = None
    flask.session['myClassDB'] = None
###############################################################################
####################------READY FOR TESTING------##############################


##
#    requests:
#       setting
#           "addClass"
#               get "className"
#               return "added"
#           "removeClass"
#               get "classId"
#               return "removed" | "failed" (for future)
#          "setPriorities"
#              get "classId"
#              return "priorty updated"
#

@app.route("/_classDBSettings")
def preSettings():
    setting = request.args.get('setting',0,type=str)
    className = request.args.get('className',0,type=str)
    classId = request.args.get('classId',0,type=str)
    priorityList = request.args.get('priorityList',0,type=str)
    d = classDBSettings(setting,className,classId,priorityList)
    return jsonify(result = d)

def classDBSettings(setting,className,classId,priorityList):
    if setting == "addClass":
        qPriority = [0,0,0,0,0,0,0,0,0,0]
        aTime = arrow.utcnow().naive
        formList = []
        record = {"name": className, "date":aTime , "formList":formList, "qPriority":qPriority}
        collectionClassDB.insert(record)
        aClass = collectionClassDB.find_one({"date": aTime})
        locId = str(aClass.get('_id'))
        locList = collectionAccounts.find_one({"_id":flask.session.get('login')}).get("classList")
        locList.append(locId)
        collectionAccounts.update_one(
            {"_id": ObjectId(flask.session.get('login'))},
            {"$set": {"classList":locList}}
        )
        d = "added"
    elif setting == "removeClass":
        collectionClassDB.remove({"_id":ObjectId(classId)})
        locList = collectionAccounts.find_one({"_id":flask.session.get('login')}).get("classList")
        ### add checker for if ID exists
        deleteForms(classId)
        locList.remove(classId)
        collectionAccounts.update_one(
            {"_id": ObjectId(flask.session.get('login'))},
            {"$set": {"classList":locList}}
        )
        d = "removed"
    elif setting == "setPriorities":
        collectionClassDB.update_one(
            {"_id": ObjectId(flask.session.get('login'))},
            {"$set": {"qPriority":priorityList}}
        )
        d = "priority updated"
    else:
        d =" wat"
    return d

def deleteForms(classId):
    formList = collectionClassDB.find_one({"_id":classId}).get("formList")
    for fId in formList:
        collectionFormsDB.remove({"_id":fId})
    return
##
#    settings
#        addForm
#            get parentId
#            get dictResponse
#            return "added"
#        getPriorities
#            get parentId
#            return "priorities gathered"

@app.route("/_formSettings")
def preForms():
    setting = request.args.get('setting',0,type=str)
    parentId = request.args.get('parentId',0,type=str)
    dictResponse = request.args.get('dictResponse',0,type=str)
    d = formSettings(setting,parentId,dictResponse)
    return jsonify(result = d)

def formSettings(setting,parentId,dictResponse):
    if setting == "addForm":
        aTime = arrow.utcnow().naive
        record = {"parentId":parentId,"dictResponse":dictResponse, "date":aTime,"teamNum": 0}
        collectionFormsDB.insert(record)
        aForm = collectionFormsDB.find_one({"date": aTime})
        locId = str(aForm.get('_id'))
        aClass = collectionClassDB.find_one({"_id":parentId})
        locList = aClass.get("formList")
        locList.append(locId)
        collectionClassDB.update_one(
            {"_id": ObjectId(parentId)},
            {"$set": {"formList":locList}}
        )
        flask.session['priorityList'] = None
        d = "added"
    elif setting == "getPriorities":
        aClass = collectionClassDB.find_one({"_id":ObjectId(parentId)})
        aList = aClass.get("priorityList")
        flask.session['priorityList'] = aList
        d = "priorities gathered"
    else:
        d = "wat"
    return d

###############################################################################
###############################################################################

##############################
##########Filters#############
##############################
@app.template_filter('convert_time')
def convert_time(timestamp):
    val = arrow.get(timestamp)
    return val.format('h:mm A')

@app.template_filter('classObj')
def convert_class_id(classId):
    val = collectionClassDB.find_one({"_id":classId})
    return val


if __name__ == "__main__":
    import uuid
    app.secret_key = str(uuid.uuid4())
    app.debug = CONFIG.DEBUG
    app.logger.setLevel(logging.DEBUG)
    app.run(port=CONFIG.PORT,threaded=True)
