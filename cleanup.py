#Script for clearing out all memos from a DB
from pymongo import MongoClient

import CONFIG

try:
	#CHRIS: MODIFY THESE FOR DB DATA
	dbclient = MongoClient(CONFIG.MONGO_URL)
	db = dbclient.memos
	collection = db.dated

except:
	print("Failure opening database. Is Mongo running? Correct password?")
	sys.exit(1)

for record in collection.find({}):
	print(record)
