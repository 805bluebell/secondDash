import flask
from flask import request, jsonify, render_template, url_for, redirect, session
from flask_session import Session
from werkzeug import secure_filename
from flask_uploads import UploadSet, IMAGES, configure_uploads, UploadNotAllowed
from pymongo import MongoClient, CursorType, ASCENDING, DESCENDING
import json
from bson import json_util, ObjectId
from bson.int64 import Int64
import time
from random import randint
import os
import tempfile
import datetime
from functools import wraps

# For deleting uploads
import os
import shutil

# For helpers
import csv
from pathlib import Path

# For google login
from google.oauth2 import id_token
from google.auth.transport import requests


# Python standard libraries
import json
import os
import sqlite3

# Third party libraries
from flask import Flask, redirect, request, url_for
from flask_login import LoginManager, current_user, login_required, login_user, logout_user
from oauthlib.oauth2 import WebApplicationClient
import requests

# Internal imports
# from db import init_db_command
from FlaskApp.user import User


app = flask.Flask(__name__, static_url_path='',
				  static_folder='static',
				  template_folder='templates')
app.config["DEBUG"] = False

# DB links for main collection
client = MongoClient("mongodb://localhost:27017")
database = client["local"]
collection = database["dolphinDB"]

# DB links for ApprovedUsers collection
collection2 = database["ApprovedUsers"]

# From new dup
collection4 = database["jobPostingWiseDB"]

# For saving custom filters for each user
# collection5 = database["customFiltersDB"]


# Clearing caches
@app.after_request
def after_request(response):
	response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
	response.headers["Expires"] = 0
	response.headers["Pragma"] = "no-cache"
	return response

# Configure session to use filesystem (instead of signed cookies)
# app.config["SESSION_FILE_DIR"] = tempfile.mkdtemp()
# app.config["SESSION_PERMANENT"] = False
# app.config["SESSION_TYPE"] = "filesystem"
# Session(app)

# To delete /uploads folder at start of upload


def flushUploadsFolder():
	folder = '/var/www/FlaskApp/FlaskApp/uploaded_csv'
	for the_file in os.listdir(folder):
		file_path = os.path.join(folder, the_file)
		try:
			if os.path.isfile(file_path):
				os.unlink(file_path)
			# elif os.path.isdir(file_path): shutil.rmtree(file_path)
		except Exception as e:
			print(e)


# configure flask_upload API
documents = UploadSet("documents", ('csv'))
app.config["UPLOADED_DOCUMENTS_DEST"] = "/var/www/FlaskApp/FlaskApp/uploaded_csv"
configure_uploads(app, documents)


# def login_required(f):
#     """
#     Decorate routes to require login.
#     http://flask.pocoo.org/docs/0.12/patterns/viewdecorators/
#     """
#     @wraps(f)
#     def decorated_function(*args, **kwargs):
#         # print("333333333333 Inside Decorators 33333333333")
#         if session.get("user_id") is None:
#             # print("Inside")
#             # print(session)
#             return redirect("/")
#         # else:
#         #   print("Outisde")
#         #   print(session)
#         return f(*args, **kwargs)
#     return decorated_function

@app.route('/privacy', methods=['GET'])
def privacy():
	return render_template("privacyPolicy.html")


@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
	if request.method == 'GET':
		if checkAdmin(current_user.id):
			loginOption = True
			teamOptions = False
			if checkTeamMembership(current_user.id):
				teamOptions = True
			return render_template('uploader2.html', lastUpdated=getLastUpdatedTimestamp(), adminOptions=True, loginOption=loginOption, teamOptions=teamOptions, uploadHighlight="active")
		else:
			return render_template("unauthorized.html"), 403
	elif request.method == 'POST':

		# Deleting everything in uploads folder
		flushUploadsFolder()

		f = request.files['file']
		print(f.filename, secure_filename(f.filename))
		file = documents.save(request.files['file'], name="dump.csv")

		f2 = request.files['file2']
		print(f2.filename, secure_filename(f2.filename))
		file2 = documents.save(
			request.files['file2'], name="JobPostingDump.csv")

		# f = request.files['file']
		# f.save(secure_filename(f.filename))
		# os.remove(app.config["UPLOADED_DOCUMENTS_DEST"] + "/" + str())
		return redirect(url_for('uploadedSuccessfully'))


@app.route('/uploadedSuccessfully', methods=['GET', 'POST'])
@login_required
def uploadedSuccessfully():
	loginOption = True
	return render_template("uploadedSuccessfully.html", lastUpdated=getLastUpdatedTimestamp(), loginOption=loginOption)


# This route gives status when it's uploading
@app.route('/updating', methods=['GET', 'POST'])
@login_required
def updating():

	# The database uploading method comes here
	res = 'starting'
	updateMongo()
	# try:
	#   updateMongo()
	#   res = 'Database Successfully Updated'
	# except:
	#   res = 'Database update failed. Please contact admin'
	return res


@app.route('/test2', methods=['GET'])
@login_required
def test1():
	return render_template('test2.html')


@app.route('/trial3', methods=['GET'])
# @login_required
def trial3():
	return render_template('trial3.html')


@app.route('/trial4', methods=['GET'])
@login_required
def trial4():
	return "ss"


def generateMainPageDropdowns2(Status):
	postingOwner = set()
	postingArchiveStatus = set()
	profileArchiveStatus = set()

	# companiesAllowed = set()
	# companiesAllowed = {'Campus', 'Codechef', 'Flock', 'Radix', 'Shared Services'}

	rows = collection2.find({"users": current_user.id})
	for row in rows:
		companiesAllowed = row["companiesActuallyAllowed"]

	# Get all users registred TAT members from our user database
	rows = collection2.find({"tatMember": "Yeah"})
	allUsersSet = set()
	for row in rows:
		allUsersSet.add(row["users"])

	rows = collection4.find(
		{"Posting Department": {"$in": companiesAllowed}}, cursor_type=CursorType.EXHAUST)
	for row in rows:
		if row['Posting Owner Email'] not in allUsersSet:
			continue
		if row['Posting Department'] not in companiesAllowed:
			continue
		if row['Status'] != Status:
			continue
		else:
			postingOwner.add(row['Posting Owner'])

	# Sorting the set alphabatically
	postingOwner = sorted(postingOwner)

	# Packing everything to return
	returnList = {}
	returnList['postingOwner'] = postingOwner

	return returnList


def generateMainPageDropdowns():
	postingDepartment = set()
	postingArchiveStatus = set()
	profileArchiveStatus = set()

	# companiesAllowed = set()
	# companiesAllowed = {'Campus', 'Codechef', 'Flock', 'Radix', 'Shared Services'}

	rows = collection2.find({"users": current_user.id})
	for row in rows:
		companiesAllowed = row["companiesActuallyAllowed"]

	rows = collection.find({"Posting Department": {"$in": companiesAllowed}})
	for row in rows:
		if row['Posting Department'] not in companiesAllowed:
			continue
		else:
			postingDepartment.add(row['Posting Department'])
		postingArchiveStatus.add(row['Posting Archive Status'])
		profileArchiveStatus.add(row['Profile Archive Status'])

	# Sorting the set alphabatically
	postingDepartment = sorted(postingDepartment)

	# Packing everything to return
	returnList = {}
	returnList['postingDepartment'] = postingDepartment
	returnList['postingArchiveStatus'] = postingArchiveStatus
	returnList['profileArchiveStatus'] = profileArchiveStatus

	return returnList


# @app.route('/funnel', methods=['GET'])
# @login_required
# def funnel():
#   returnedDict = generateMainPageDropdowns()
#   return render_template('funnel.html', postingDepartment=returnedDict['postingDepartment'], postingArchiveStatus = returnedDict['postingArchiveStatus'], profileArchiveStatus = returnedDict['profileArchiveStatus'])


def getEligiblePostingTeams(companyName):
	print("companyName ", companyName)
	rows = collection4.find({"Posting Department": companyName})
	mySet = set()
	for row in rows:
		if row['Posting Department'] == companyName:
			mySet.add(row['Posting Team'])

	return mySet


def getEligiblePostingTitles(companyName, team):
	print("companyName ", companyName)
	print("team ", team)
	rows = collection4.find(
		{"Posting Department": companyName, "Posting Team": team})
	mySet = set()
	for row in rows:
		if row['Posting Department'] == companyName and row['Posting Team'] == team:
			mySet.add(row['Posting Title'])

	return mySet


def get_live_or_archived_dict():
	rows = collection4.find({})
	anotherDict = dict()
	for ro in rows:
		if ro['Posting ID'] not in anotherDict:
			anotherDict[ro['Posting ID']] = ro['Status']

	return anotherDict


@app.route('/elaborate', methods=['GET'])
@login_required
def elaborate():
	postingId = request.args.get('postingId')
	origin = request.args.get('origin')
	stage = request.args.get('stage')
	profileStatus = request.args.get('profileStatus')
	fromDate = request.args.get('fromDate')
	toDate = request.args.get('toDate')

	print("fromDate before is", fromDate)
	print("toDate before is", toDate)
	try:
		fromDate = datetime.datetime.strptime(fromDate, '%d-%m-%Y')
		toDate = datetime.datetime.strptime(toDate, '%d-%m-%Y')
	except:
		fromDate = datetime.datetime(2000, 1, 1)
		toDate = datetime.datetime(2030, 1, 1)

	print("fromDate is", fromDate)
	print("toDate is", toDate)

	# if (postingId is None) or (origin is None) or (stage = None):
	# return "Thers is some problem with your URL"

	adminOptions = False
	loginOption = True
	teamOptions = False
	if checkTeamMembership(current_user.id):
		teamOptions = True
	if checkAdmin(current_user.id):
		adminOptions = True

	results = whoAreTheseNPeople(postingId, origin, stage, profileStatus, fromDate, toDate)
	return render_template('numbersElaborated.html', candidates=results, lastUpdated=getLastUpdatedTimestamp(), adminOptions=adminOptions, loginOption=loginOption, teamOptions=teamOptions, livePostingHighlight="active")
	# return jsonify(results)


def whoAreTheseNPeople(postingId, origin, stage, profileStatus, fromDate, toDate):
	stageBank = {
		"newLead": "New lead",
		"reachedOut": "Reached out",
		"newApplicant": "New applicant",
		"recruiterScreen": "Recruiter screen",
		"phoneInterview": "Phone interview",
		"onsiteInterview": "On-site interview",
		"offer": "Offer",
		"offerApproval": "Offer Approval",
		"offerApproved": "Offer Approved"
	}

	query = dict()
	query['Posting ID'] = postingId

	if origin != "Total":
		if len(origin) < 12:
			query['Origin'] = origin

	if profileStatus == "Both":
		query['$or'] = [{'Posting Archive Status' : 'false'}, {'Posting Archive Status' : 'true'}]
	else:
		query['Posting Archive Status'] = profileStatus

	# We have Offer, Offer Approved, Offer Approval all counted in offer, To encounter that
	result = list()
	if stage == "offer":
		query['$or'] = [{'Current Stage': 'Offer Approval'}, {'Current Stage': 'Offer Approved'}, {'Current Stage': 'Offer'}]
		result = list(collection.find(query, cursor_type=CursorType.EXHAUST))
	elif stage == "hired":
		benchDate = datetime.datetime(2015, 1, 1)
		outcome = list(collection.find(query, cursor_type=CursorType.EXHAUST))
		for out in outcome:
			if out["Hired"] > benchDate:
				result.append(out)
	else:
		query['Current Stage'] = stageBank[stage]
		result = list(collection.find(query, cursor_type=CursorType.EXHAUST))

	packet = []
	count = 1
	for res in result:
		if res['Last Story At (GMT)'] >= fromDate and res['Last Story At (GMT)'] <= toDate:
			dic = dict()
			dic["Candidate Name"] = res["Candidate Name"]
			dic["Profile ID"] = res["Profile ID"]
			dic["count"] = count
			packet.append(dic)
			count += 1
	return packet


@app.route('/getTable', methods=['POST'])
@login_required
def getTable():
	# collection.createIndex('Posting Department')
	recruiter = request.form.get('recruiter')
	postingTitle = request.form.getlist('postingTitle[]')
	companyName = request.form.get('companyName')
	postingTeam = request.form.get('postingTeam')
	requestType = request.form.get('requestType')
	print("PPPPosting title here ---- ", postingTitle)
	# postingArchiveStatus = request.form.get('postingArchiveStatus')
	profileArchiveStatus = request.form.get('profileArchiveStatus')
	fromDate = request.form.get('from')
	toDate = request.form.get('to')

	results = getResults(postingTitle, companyName, postingTeam,
						 profileArchiveStatus, fromDate, toDate, requestType, recruiter)
	# results = getResults("Backend Engineer", "Flock", "Software Engineering", "All")
	return jsonify(results)


def getResults(title, companyName, team, profileArchiveStatus, fromDate, toDate, requestType, recruiter=None):
	try:
		fromDate = datetime.datetime.strptime(fromDate, '%d-%m-%Y')
		toDate = datetime.datetime.strptime(toDate, '%d-%m-%Y')
	except:
		fromDate = datetime.datetime(2000, 1, 1)
		toDate = datetime.datetime(2030, 1, 1)
	ts = time.time()
	rows = getFromDB(title, companyName, team, recruiter)
	print('db: ' + str(time.time() - ts))
	res = []
	counts = dict()

	# This variable will hold the live or archived status of all posting, yes all
	live_or_archived_dict = get_live_or_archived_dict()

	# The restriction is there mark this flag
	# We want to display only postings related to him/her if he/she is marked so
	whichPositions = "all"
	whichPositionsrows = collection2.find({"users": current_user.id})
	for row in whichPositionsrows:
		whichPositions = row["whichPositions"]

	for item in rows:
		# If that flag was marked check whether the email of
		# ... signed in user is in "Posting Owners email id" or "Hiring mangers email id"
		# ... if yes then only display otherwise skip (continue) the loop
		if whichPositions == "respective":
			if not (item["Posting Owner Email"] == current_user.id or item["Posting Hiring Manager Email"] == current_user.id):
				continue

		if item['Posting ID'] in live_or_archived_dict:
			if requestType == "live":
				if not (live_or_archived_dict[item['Posting ID']] == "active"):
					continue
			if requestType == "archived":
				if not (live_or_archived_dict[item['Posting ID']] == "closed"):
					continue
		else:
			continue

		if '(I)' in item['Posting Title']:
			continue

		# if "All" not in title:
		#   if item['Posting Title'] not in eligiblePostingTitles:
		#       continue
		# elif item['Posting Title'] not in title:
		#   continue

		# if team != "All":
		#   if item['Posting Team'] not in eligiblePostingTeams:
		#       continue
		# elif item['Posting Team'] != team:
		#   continue

		# if item['Posting Title'] not in title and 'All' not in title:
		#   continue
		# if item['Posting Team'] != team and team != 'All':
		#   continue
		# if item['Posting Archive Status'] != archiveStatus and archiveStatus != 'All' and archiveStatus != 'Both':
		#     continue
		if item['Posting Archive Status'] != profileArchiveStatus and profileArchiveStatus != 'All' and profileArchiveStatus != 'Both':
			continue

		# if item['Min Date'] < fromDate and item['Max Date'] > toDate:
		#   # print(f"{item['Min Date']} < {benchmark_date}")
		#   continue

		# if item['Max Date'] > toDate:
			# print(f"{item['Min Date']} < {benchmark_date}")
			# continue

		# Modified posting ID for display
		# item['Created At (GMT)'] =  datetime.datetime.strptime(str(item['Created At (GMT)']), '%Y-%m-%d %H:%M:%S').strftime('%B %Y')
		# postId = str(item['Posting ID']) + ", " + str(item['Posting Title']) + ", " + str(item['Posting Location']) + ", " + item['Created At (GMT)']

		if 'postingCreatedDate' in item:
			dateForLabel = f"{str(item['postingCreatedDate'].strftime('%b'))} {str(item['postingCreatedDate'].strftime('%Y'))}, "
			# dateForLabel = str(item['postingCreatedDate'].strftime('%b')) + " " + str(item['postingCreatedDate'].strftime('%Y'))
			dateForLabel += str(item['Actual Posting Owner Name'])
		else:
			dateForLabel = f" $ "
			dateForLabel += str(item['Actual Posting Owner Name'])
		postId = str(item['Posting Title']) + ", " + \
			str(item['Posting Location']) + ", " + dateForLabel
		postIdHash = item['Posting ID']

		origin = item['Origin']
		if not postId in counts:
			counts[postId] = dict()
		if not origin in counts[postId]:
			counts[postId][origin] = dict()
			counts[postId][origin]['new_lead'] = 0
			counts[postId][origin]['reached_out'] = 0
			counts[postId][origin]['new_applicant'] = 0
			counts[postId][origin]['recruiter_screen'] = 0
			counts[postId][origin]['phone_interview'] = 0
			counts[postId][origin]['onsite_interview'] = 0
			counts[postId][origin]['offer'] = 0
			counts[postId][origin]['offerApproval'] = 0
			counts[postId][origin]['hired'] = 0
			counts[postId][origin]['posting_id'] = postIdHash

			# var for % counts
			counts[postId][origin]['phone_To_Onsite'] = 0
			counts[postId][origin]['phone_To_Offer'] = 0
			counts[postId][origin]['onsite_To_Offer'] = 0

		originCounts = counts[postId][origin]

		# if 'Stage - New lead' in item and item['Stage - New lead'] != None:
		#   originCounts['new_lead'] += 1
		# if 'Stage - Reached out' in item and item['Stage - Reached out'] != None:
		#   originCounts['reached_out'] += 1
		# if 'Stage - New applicant' in item and item['Stage - New applicant'] != None:
		#   originCounts['new_applicant'] += 1
		# if 'Stage - Recruiter screen' in item and item['Stage - Recruiter screen'] != None:
		#   originCounts['recruiter_screen'] += 1

		# if 'Stage - Phone interview' in item and item['Stage - Phone interview'] != None:
		#   originCounts['phone_interview'] += 1
		#   # Counting for % conversion
		#   if 'Stage - On-site interview' in item and item['Stage - On-site interview'] != None:
		#       originCounts['phone_To_Onsite'] += 1
		#   if 'Stage - Offer' in item and item['Stage - Offer'] != None:
		#       originCounts['phone_To_Offer'] += 1

		# if 'Stage - On-site interview' in item and item['Stage - On-site interview'] != None:
		#   originCounts['onsite_interview'] += 1
		#   # Counting for % conversion
		#   if 'Stage - Offer' in item and item['Stage - Offer'] != None:
		#       originCounts['onsite_To_Offer'] += 1

		# if 'Stage - Offer' in item and item['Stage - Offer'] != None:
		#   originCounts['offer'] += 1

		# if 'Stage - Offer Approval' in item and item['Stage - Offer Approval'] != None:
		#   originCounts['offerApproval'] += 1

		# if 'Stage - Offer Approved' in item and item['Stage - Offer Approved'] != None:
		#   originCounts['offerApproval'] += 1

		# if 'Hired' in item and item['Hired'] != None:
		#   originCounts['hired'] += 1

		if item['Last Story At (GMT)'] >= fromDate and item['Last Story At (GMT)'] <= toDate and item['Current Stage'] == "New lead":
			originCounts['new_lead'] += 1
		if item['Last Story At (GMT)'] >= fromDate and item['Last Story At (GMT)'] <= toDate and item['Current Stage'] == "Reached out":
			originCounts['reached_out'] += 1
		if item['Last Story At (GMT)'] >= fromDate and item['Last Story At (GMT)'] <= toDate and item['Current Stage'] == "New applicant":
			originCounts['new_applicant'] += 1
		if item['Last Story At (GMT)'] >= fromDate and item['Last Story At (GMT)'] <= toDate and item['Current Stage'] == "Recruiter screen":
			originCounts['recruiter_screen'] += 1

		if item['Last Story At (GMT)'] >= fromDate and item['Last Story At (GMT)'] <= toDate and item['Current Stage'] == "Phone interview":
			originCounts['phone_interview'] += 1
			# Counting for % conversion
			if 'Stage - On-site interview' in item and item['Stage - On-site interview'] != None:
				originCounts['phone_To_Onsite'] += 1
			if 'Stage - Offer' in item and item['Stage - Offer'] != None:
				originCounts['phone_To_Offer'] += 1

		if item['Last Story At (GMT)'] >= fromDate and item['Last Story At (GMT)'] <= toDate and item['Current Stage'] == "On-site interview":
			originCounts['onsite_interview'] += 1
			# Counting for % conversion
			if 'Stage - Offer' in item and item['Stage - Offer'] != None:
				originCounts['onsite_To_Offer'] += 1

		if item['Last Story At (GMT)'] >= fromDate and item['Last Story At (GMT)'] <= toDate and item['Current Stage'] == "Offer":
			originCounts['offer'] += 1

		if item['Last Story At (GMT)'] >= fromDate and item['Last Story At (GMT)'] <= toDate and item['Current Stage'] == "Offer Approval":
			originCounts['offer'] += 1

		if item['Last Story At (GMT)'] >= fromDate and item['Last Story At (GMT)'] <= toDate and item['Current Stage'] == "Offer Approved":
			originCounts['offer'] += 1

		if item['Hired'] >= fromDate and item['Hired'] <= toDate:
			originCounts['hired'] += 1

	for postId in counts:
		res.append(actualPostId(postId, counts[postId]))

	# Adding a total row for each posting so that we can utilize grand total
	wereTheyAllZeros = getTotalForEachPosting(res)

	print('total: ' + str(time.time() - ts))

	# If they are all zeros return blank else return all the complete result
	if wereTheyAllZeros:
		return []
	else:
		return res


def getTotalForEachPosting(res):

	holderForTotalCountHolder = 0

	for i in range(len(res)):
		holder = res[i]['_children']

		monte = ["hiredCount", "newApplicantCount", "newLeadCount", "offerApprovalCount", "offerCount", "onsiteInterviewCount",
				 "onsiteToOfferCount", "phoneInterviewCount", "phoneToOfferCount", "phoneToOnsiteCount", "reachedOutCount", "recruiterScreenCount"]
		totalCountHolder = [0] * 12

		for h in holder:
			for q in range(len(monte)):
				sawTooth = monte[q]
				totalCountHolder[q] += h[sawTooth]

		# counting grand total of all total counts
		holderForTotalCountHolder += sum(totalCountHolder)

		tempDict = dict(zip(monte, totalCountHolder))

		# Writing total with the title row itself so that total will appear on the top of each posting 
		for k,v in tempDict.items():
			res[i][k] = v
		res[i]['topTag'] = "true"   # Used to indicate at front-end about top tag
		res[i]['posting_id'] = res[i]['_children'][0]['posting_id']

		# By commenting the below, we are not writing total field
		# tempDict['title'] = 'Total'
		# tempDict['posting_id'] = holder[0]['posting_id']
		# holder.append(tempDict)

	# Returning back with a signal that all counts were Zero, don't display table for this
	return True if holderForTotalCountHolder == 0 else False


# title, companyName, team, archiveStatus):
def getFromDB(title, companyName, team, recruiter=None):
	# collection.drop()
	# collection.insert_one({'posting_id' : randint(1,10), 'origin' : randint(1,3), 'Stage - New Lead' : '2019-01-01'})
	# collection.insert_one({'posting_id' : randint(1,10), 'origin' : randint(1,3), 'Stage - Recruiter Screen': '2019-02-02'})
	query = dict()

	if title[0] == 'All':
		title = {'$regex': '.*'}
	else:
		title = {"$in": title}
	if team == 'All':
		team = {'$regex': '.*'}
	if companyName == 'All':
		companyName = {'$regex': '.*'}
	if recruiter == "All" or recruiter == None:
		print("recruiter is actually --- ", recruiter)
		recruiter = {'$regex': '.*'}

	query['Posting Department'] = companyName
	query['Posting Title'] = title
	query['Posting Team'] = team
	query['Actual Posting Owner Name'] = recruiter
	# query['Posting Archive Status'] = archiveStatus
	return list(collection.find(query, cursor_type=CursorType.EXHAUST))


def actualPostId(postId, postIdCounts):
	children = []
	for origin in postIdCounts:
		children.append(actualResultForOrigin(origin, postIdCounts[origin]))
	return {
		'title': postId,
		'_children': children
	}


def actualResultForOrigin(origin, originCounts):
	return {
		'title': origin,
		'newApplicantCount': originCounts['new_applicant'],
		"newLeadCount": originCounts['new_lead'],
		"recruiterScreenCount": originCounts['recruiter_screen'],
		"phoneInterviewCount": originCounts['phone_interview'],
		"onsiteInterviewCount": originCounts['onsite_interview'],
		"offerCount": originCounts['offer'],
		"offerApprovalCount": originCounts['offerApproval'],
		"hiredCount": originCounts['hired'],
		"reachedOutCount": originCounts['reached_out'],
		"phoneToOnsiteCount": originCounts['phone_To_Onsite'],
		"phoneToOfferCount": originCounts['phone_To_Offer'],
		"onsiteToOfferCount": originCounts['onsite_To_Offer'],
		"posting_id": originCounts['posting_id']
	}


def smallRandomNumber():
	return randint(0, 10)

# Returns back date n days from now based on string passed


def interpretAge(age):
	if age == "beginningOfTime":
		return(datetime.datetime(2005, 12, 1))
	lis = age.split()
	multiplier = int(lis[0])
	day_or_month = lis[1]

	if day_or_month == "Days":
		# code for day
		benchmark_date = datetime.datetime.now() - datetime.timedelta(days=multiplier)

	if day_or_month == "Months":
		# code for month
		benchmark_date = datetime.datetime.now() - datetime.timedelta(days=multiplier*30)

	return benchmark_date

# Makaing a long list of dicts containing all the items required for dropdown


def prepareDropdownOptionsSending(whale):
	box = list()

	for k, v in whale.items():
		for kk, vv in whale[k].items():
			for kkk, vvv in whale[k][kk].items():
				for kkkk in whale[k][kk][kkk]:
					t = dict()
					t["recruiter"] = k
					t["company"] = kk
					t["dept"] = kkk
					t["post"] = kkkk
					box.append(t)
	return box


def makeDropdownOptions(bigDict, postOwn, postDept, postTeam, postTitle):
	if postOwn not in bigDict:
		bigDict[str(postOwn)] = {}

	if postDept not in bigDict[postOwn]:
		bigDict[postOwn][str(postDept)] = {}

	if postTeam not in bigDict[postOwn][postDept]:
		bigDict[postOwn][str(postDept)][str(postTeam)] = list()

	if postTitle not in bigDict[postOwn][postDept][postTeam]:
		bigDict[postOwn][postDept][postTeam].append(postTitle)


@app.route('/getDropdownOptionsLive', methods=['GET'])
@login_required
def getDropdownOptionsLive():
	liveBigDictPre = dict()

	rows = collection2.find({"users": current_user.id})
	for row in rows:
		companiesAllowed = row["companiesActuallyAllowed"]

	rows = collection4.find(
		{"Posting Department": {"$in": companiesAllowed}, "Status": "active"})

	for row in rows:
		if row['Posting Department'] not in companiesAllowed:
			print("Continuing as Posting Department not in companiesAllowed")
			continue
		if row['Status'] != "active":
			continue
		if '(I)' in row['Posting Title']:
			continue

		# Making a big data structure for all dropdowns in front end
		makeDropdownOptions(
			liveBigDictPre, row['Posting Owner'], row['Posting Department'], row['Posting Team'], row['Posting Title'])
		liveBigDict = prepareDropdownOptionsSending(liveBigDictPre)
	return jsonify(liveBigDict)


@app.route('/getDropdownOptionsArchived', methods=['GET'])
@login_required
def getDropdownOptionsArchived():
	archivedBigDictPre = dict()

	rows = collection2.find({"users": current_user.id})
	for row in rows:
		companiesAllowed = row["companiesActuallyAllowed"]

	rows = collection4.find(
		{"Posting Department": {"$in": companiesAllowed}, "Status": "closed"})

	for row in rows:
		if row['Posting Department'] not in companiesAllowed:
			print("Continuing as Posting Department not in companiesAllowed")
			continue
		if row['Status'] != "closed":
			continue
		if '(I)' in row['Posting Title']:
			continue

		# Making a big data structure for all dropdowns in front end
		makeDropdownOptions(archivedBigDictPre, row['Posting Owner'],
							row['Posting Department'], row['Posting Team'], row['Posting Title'])
		archivedBigDict = prepareDropdownOptionsSending(archivedBigDictPre)
	return jsonify(archivedBigDict)


@app.route('/getBigDictLive', methods=['GET'])
@login_required
def getBigDictLive():
	liveBigDict = dict()

	rows = collection2.find({"users": current_user.id})
	for row in rows:
		companiesAllowed = row["companiesActuallyAllowed"]

	rows = collection4.find(
		{"Posting Department": {"$in": companiesAllowed}, "Status": "active"})

	for row in rows:
		if row['Posting Department'] not in companiesAllowed:
			print("Continuing as Posting Department not in companiesAllowed")
			continue
		if row['Status'] != "active":
			continue
		if '(I)' in row['Posting Title']:
			continue

		# Making a big data structure for all dropdowns in front end
		makeBigDict(liveBigDict, row['Posting Department'],
					row['Posting Team'], row['Posting Title'])
	return jsonify(liveBigDict)


@app.route('/getBigDictArchived', methods=['GET'])
@login_required
def getBigDictArchived():
	archivedBigDict = dict()

	rows = collection2.find({"users": current_user.id})
	for row in rows:
		companiesAllowed = row["companiesActuallyAllowed"]

	rows = collection4.find(
		{"Posting Department": {"$in": companiesAllowed}, "Status": "closed"})

	for row in rows:
		if row['Posting Department'] not in companiesAllowed:
			print("Continuing as Posting Department not in companiesAllowed")
			continue
		if row['Status'] != "closed":
			continue
		if '(I)' in row['Posting Title']:
			continue

		# Making a big data structure for all dropdowns in front end
		makeBigDict(archivedBigDict, row['Posting Department'],
					row['Posting Team'], row['Posting Title'])
	return jsonify(archivedBigDict)


@app.route('/getBigDict', methods=['GET'])
@login_required
def getBigDict():
	bigDict = dict()

	rows = collection2.find({"users": current_user.id})
	for row in rows:
		companiesAllowed = row["companiesActuallyAllowed"]

	rows = collection.find({"Posting Department": {
						   "$in": companiesAllowed}}, cursor_type=CursorType.EXHAUST)

	# rows = collection.find(cursor_type=CursorType.EXHAUST)

	# companiesAllowed = set()
	# companiesAllowed = {'Campus', 'Codechef', 'Flock', 'Radix', 'Shared Services'}

	for row in rows:
		if row['Posting Department'] not in companiesAllowed:
			continue

		# Making a big data structure for all dropdowns in front end
		makeBigDict(bigDict, row['Posting Department'],
					row['Posting Team'], row['Posting Title'])
	return jsonify(bigDict)


def getLastUpdatedTimestamp():
	timestamp = None
	try:
		o = collection.find_one({})
		# for o in ob:
		timestamp = str(o['_id'])
		timestamp = timestamp[0:8]
		timestamp = int(timestamp, 16)

		timestamp = time.strftime(
			'%d-%m-%Y %H:%M:%S', time.localtime(timestamp))
		print(timestamp)
	except:
		timestamp = "Coudn't get last updated date"
		print(timestamp)
	return timestamp


def generateReferalDict(fromDate, toDate, originType, allowedOrigins):

	if originType not in allowedOrigins:
		return jsonify([])

	try:
		fromDate = datetime.datetime.strptime(fromDate, '%d-%m-%Y')
		toDate = datetime.datetime.strptime(toDate, '%d-%m-%Y')
		toDate += datetime.timedelta(days=1)

	except:
		fromDate = datetime.datetime(2000, 1, 1)
		toDate = datetime.datetime(2030, 1, 1)

	if originType != "referred":
		query = {"Origin": originType, "$and": [{"Applied At (GMT)": {"$gte": fromDate}}, {
			"Applied At (GMT)": {"$lte": toDate}}]}
		rows = collection.find(query, cursor_type=CursorType.EXHAUST)
	else:
		query = {"$and": [{"Applied At (GMT)": {"$gte": fromDate}}, {
			"Applied At (GMT)": {"$lte": toDate}}]}
		rows = list()
		rows_temp = collection.find(query, cursor_type=CursorType.EXHAUST)
		for row in rows_temp:
			if row["Referred"] == "true" or row["Is Social Referral"] == "true" or row["Is Employee Referral"] == "true" or row["Is Manual Referral"] == "true":
				rows.append(row)

	upperPack = dict()
	lowerPack = list()
	tem2 = dict()
	monthList = ['*', 'Jan', 'Feb', 'Mar', 'Apr', 'May',
				 'Jun', 'Jul', 'Aug', 'Sept', 'Oct', 'Nov', 'Dec']

	for ro in rows:
		if ro['Posting Archived At (GMT)'] == datetime.datetime(1990, 1, 1) and ro['Current Stage'] == 'New applicant':
			tem = dict()

			tem['Profile ID'] = ro['Profile ID']
			tem['Posting Owner Name'] = ro['Posting Owner Name']
			tem['Application ID'] = ro['Application ID']
			tem['Posting ID'] = ro['Posting ID']
			tem['Posting Title'] = ro['Posting Title']
			tem['Applied At (GMT)'] = ro['Applied At (GMT)']
			tem['Last Story At (GMT)'] = ro['Last Story At (GMT)']
			tem['CandidateName'] = ro['Candidate Name']
			tem['Ageing'] = datetime.datetime.now() - tem['Applied At (GMT)']
			tem['Ageing'] = tem['Ageing'].days
			tem['ProfileLink'] = 'https://hire.lever.co/candidates/' + \
				tem['Profile ID']

			if tem['Posting Owner Name'] not in upperPack:
				upperPack[tem['Posting Owner Name']] = [0] * 13
				upperPack[tem['Posting Owner Name']
						  ][tem['Applied At (GMT)'].month] = 1
				# for i in range(1,len(monthList) + 1):
				#   upperPack[tem['Candidate Owner Name']][monthList[i]] = 0
			else:
				upperPack[tem['Posting Owner Name']
						  ][tem['Applied At (GMT)'].month] += 1

			lowerPack.append(tem)

	# print(upperPack)

	# Making a dict to be readable at Front end Tabulator
	upperPackForTabulator = []
	# for key,value in upperPack.items():
	#   justLikeThat = {}
	#   justLikeThat['Recruiter'] = key

	#   justLikeThat['_children'] = {}

	#   for i in range(len(value)):
	#       justLikeThat['_children'][monthList[i]] = value[i]

	#   upperPackForTabulator.append(justLikeThat)

	# print(upperPackForTabulator)

	for key, value in upperPack.items():
		tempDict = {}
		tempDict['Recruiter'] = key
		# tempDict['monthValues'] = value

		thatTotal = sum(value)
		tempDict['Grand Total'] = thatTotal

		i = 0
		for mon in monthList:
			if value[i] != 0:
				# value[i] += 1
				tempDict[mon] = value[i]
			else:
				tempDict[mon] = value[i]
			i += 1

		upperPackForTabulator.append(tempDict)

	print(upperPackForTabulator)

	return jsonify({'low': lowerPack, 'up': upperPackForTabulator})


def generateReferalArchivedDict(fromDate, toDate, originType, allowedOrigins):

	if originType not in allowedOrigins:
		return jsonify([])

	try:
		fromDate = datetime.datetime.strptime(fromDate, '%d-%m-%Y')
		toDate = datetime.datetime.strptime(toDate, '%d-%m-%Y')

	except:
		fromDate = datetime.datetime(2000, 1, 1)
		toDate = datetime.datetime(2030, 1, 1)

	if originType != "referred":
		query = {"Origin": originType, "$and": [{"Applied At (GMT)": {"$gte": fromDate}}, {
			"Applied At (GMT)": {"$lte": toDate}}]}
		rows = collection.find(query, cursor_type=CursorType.EXHAUST)
	else:
		query = {"$and": [{"Applied At (GMT)": {"$gte": fromDate}}, {
			"Applied At (GMT)": {"$lte": toDate}}]}
		rows = list()
		rows_temp = collection.find(query, cursor_type=CursorType.EXHAUST)
		for row in rows_temp:
			if row["Referred"] == "true" or row["Is Social Referral"] == "true" or row["Is Employee Referral"] == "true" or row["Is Manual Referral"] == "true":
				rows.append(row)

	upperPack = dict()
	lowerPack = list()
	upperPackForTabulator = []

	for ro in rows:
		if ro['Posting Archive Status'] == "true" and not isinstance(ro['Posting Owner Name'], datetime.date):
			# Do things
			tem = dict()

			tem['Profile ID'] = ro['Profile ID']
			tem['Posting Owner Name'] = ro['Posting Owner Name']
			tem['Application ID'] = ro['Application ID']
			tem['Posting ID'] = ro['Posting ID']
			tem['Posting Title'] = ro['Posting Title']
			tem['Applied At (GMT)'] = ro['Applied At (GMT)']
			tem['Last Story At (GMT)'] = ro['Last Story At (GMT)']
			tem['Posting Archived At (GMT)'] = ro['Posting Archived At (GMT)']
			tem['CandidateName'] = ro['Candidate Name']
			tem['Last Story At (GMT)'] = ro['Last Story At (GMT)']

			# tem['Ageing'] = tem['Posting Archived At (GMT)'] - tem['Created At (GMT)']
			# tem['Ageing'] = tem['Ageing'].days

			# If Aging days is -ve it's sort of icorrect data captured
			# To rectify that we use another column's date
			# if tem['Ageing'] < 0:
			#   # In fact we should always use 'Posting Archived At (GMT)'
			#   tem['Ageing'] = tem['Last Advanced At (GMT)'] - tem['Created At (GMT)']
			#   tem['Ageing'] = tem['Ageing'].days

			tem['Ageing'] = tem['Posting Archived At (GMT)'] - \
				tem['Applied At (GMT)']
			tem['Ageing'] = tem['Ageing'].days

			tem['ProfileLink'] = 'https://hire.lever.co/candidates/' + \
				tem['Profile ID']

			if tem['Posting Owner Name'] not in upperPack:
				upperPack[tem['Posting Owner Name']] = [0] * 13
				upperPack[tem['Posting Owner Name']
						  ][tem['Applied At (GMT)'].month] = 1
				# for i in range(1,len(monthList) + 1):
				#   upperPack[tem['Candidate Owner Name']][monthList[i]] = 0
			else:
				upperPack[tem['Posting Owner Name']
						  ][tem['Applied At (GMT)'].month] += 1

			lowerPack.append(tem)

	return jsonify({'low': lowerPack, 'up': upperPackForTabulator})


def generateReferalOfferDict(fromDate, toDate, originType, allowedOrigins):

	if originType not in allowedOrigins:
		return jsonify([])

	try:
		fromDate = datetime.datetime.strptime(fromDate, '%d-%m-%Y')
		toDate = datetime.datetime.strptime(toDate, '%d-%m-%Y')

	except:
		fromDate = datetime.datetime(2000, 1, 1)
		toDate = datetime.datetime(2030, 1, 1)

	if originType != "referred":
		query = {"Origin": originType, "$and": [{"Applied At (GMT)": {"$gte": fromDate}}, {
			"Applied At (GMT)": {"$lte": toDate}}]}
		rows = collection.find(query, cursor_type=CursorType.EXHAUST)
	else:
		query = {"$and": [{"Applied At (GMT)": {"$gte": fromDate}}, {
			"Applied At (GMT)": {"$lte": toDate}}]}
		rows = list()
		rows_temp = collection.find(query, cursor_type=CursorType.EXHAUST)
		for row in rows_temp:
			if row["Referred"] == "true" or row["Is Social Referral"] == "true" or row["Is Employee Referral"] == "true" or row["Is Manual Referral"] == "true":
				rows.append(row)

	upperPack = dict()
	lowerPack = list()
	upperPackForTabulator = []

	for ro in rows:
		if (ro['Current Stage'] == 'Offer' or ro['Current Stage'] == 'Offer Approval' or ro['Current Stage'] == 'Offer Approved') and not isinstance(ro['Posting Owner Name'], datetime.date):
			# Do things
			tem = dict()

			tem['Profile ID'] = ro['Profile ID']
			tem['Posting Owner Name'] = ro['Posting Owner Name']
			tem['Application ID'] = ro['Application ID']
			tem['Posting ID'] = ro['Posting ID']
			tem['Posting Title'] = ro['Posting Title']
			tem['Applied At (GMT)'] = ro['Applied At (GMT)']
			tem['Stage - Offer'] = ro['Stage - Offer']
			tem['Posting Archived At (GMT)'] = ro['Posting Archived At (GMT)']
			tem['CandidateName'] = ro['Candidate Name']
			tem['Stage - Offer Approval'] = ro['Stage - Offer Approval']
			tem['Stage - Offer Approved'] = ro['Stage - Offer Approved']

			# Picking up the Offer dates appropiately as Offer has sub stages
			if tem['Stage - Offer'] == datetime.datetime(1990, 1, 1):
				if tem['Stage - Offer Approval'] == datetime.datetime(1990, 1, 1):
					if tem['Stage - Offer Approved'] == datetime.datetime(1990, 1, 1):
						continue
					else:
						tem['Ageing'] = tem['Stage - Offer Approved'] - \
							tem['Applied At (GMT)']
				else:
					tem['Ageing'] = tem['Stage - Offer Approval'] - \
						tem['Applied At (GMT)']
			else:
				tem['Ageing'] = tem['Stage - Offer'] - tem['Applied At (GMT)']

			tem['Ageing'] = tem['Ageing'].days
			tem['ProfileLink'] = 'https://hire.lever.co/candidates/' + \
				tem['Profile ID']

			if tem['Posting Owner Name'] not in upperPack:
				upperPack[tem['Posting Owner Name']] = [0] * 13
				upperPack[tem['Posting Owner Name']
						  ][tem['Applied At (GMT)'].month] = 1
				# for i in range(1,len(monthList) + 1):
				#   upperPack[tem['Candidate Owner Name']][monthList[i]] = 0
			else:
				upperPack[tem['Posting Owner Name']
						  ][tem['Applied At (GMT)'].month] += 1

			lowerPack.append(tem)

	return jsonify({'low': lowerPack, 'up': upperPackForTabulator})

def getfiltersToBeSavedReady(filterName, pageType, recruiter, postingTitle, companyName, postingTeam, requestType, profileArchiveStatus, fromDate, toDate):
	temp = dict()
	temp["filterName"] = filterName
	temp["pageType"] = pageType
	temp["recruiter"] = recruiter
	temp["postingTitle"] = postingTitle
	temp["companyName"] = companyName
	temp["postingTeam"] = postingTeam
	temp["requestType"] = requestType
	temp["profileArchiveStatus"] = profileArchiveStatus
	try:
		fromDate = datetime.datetime.strptime(fromDate, '%d-%m-%Y')
		toDate = datetime.datetime.strptime(toDate, '%d-%m-%Y')
	except:
		fromDate = ""
		toDate = ""
	temp["fromDate"] = fromDate
	temp["toDate"] = toDate

	return temp 

def saveCustomFilterPlease(oneUser, filterName, pageType, recruiter, postingTitle, companyName, postingTeam, requestType, profileArchiveStatus, fromDate, toDate):
	# Redeclaring these
	filterName = filterName
	pageType = pageType
	recruiter = recruiter
	postingTitle = postingTitle
	companyName = companyName
	postingTeam = postingTeam
	requestType = requestType
	profileArchiveStatus = profileArchiveStatus
	fromDate = fromDate

	dbDataStarting = collection2.find({"users": oneUser}, cursor_type=CursorType.EXHAUST)
	dbData = None
	for d in dbDataStarting:
		dbData = d
	if "customFilters" in dbData:
		dbData = dbData["customFilters"]
	else:
		dbData = []

	duplicateFound = False
	for dbD in dbData:
		print("This is duplicate filterName", filterName)
		if dbD["filterName"] == filterName:
			duplicateFound = True
			break

	if duplicateFound:
		return "No two filters can have same name"
	else:
		filtersToBeSaved = getfiltersToBeSavedReady(filterName, pageType, recruiter, postingTitle, companyName, postingTeam, requestType, profileArchiveStatus, fromDate, toDate)
		dbData.append(filtersToBeSaved)
		print("dbData before writing", dbData)
		# try:
		collection2.update(
				{"users": oneUser},
				{"$set" : {"customFilters": dbData}}
			)
		return "Filter saved Successfully"
		# except:
		#     return "Some error occured while saving filter"

def getThoseParticularOptions(filterName):
	dbDataStarting = collection2.find({"users": current_user.id}, cursor_type=CursorType.EXHAUST)
	dbData = None
	for d in dbDataStarting:
		dbData = d
	if "customFilters" in dbData:
		dbData = dbData["customFilters"]
	else:
		dbData = []

	dictToBeReturned = dict()
	dictToBeReturned["resultFound"] = "no"
	for d in dbData:
		if d["filterName"] == filterName:
			dictToBeReturned["filterName"] = d["filterName"]
			dictToBeReturned["pageType"] = d["pageType"]
			dictToBeReturned["recruiter"] = d["recruiter"]
			dictToBeReturned["postingTitle"] = d["postingTitle"]
			dictToBeReturned["companyName"] = d["companyName"]
			dictToBeReturned["postingTeam"] = d["postingTeam"]
			dictToBeReturned["requestType"] = d["requestType"]
			dictToBeReturned["profileArchiveStatus"] = d["profileArchiveStatus"]
			dictToBeReturned["fromDate"] = str(d["fromDate"])[:10]
			dictToBeReturned["toDate"] = str(d["toDate"])[:10]
			dictToBeReturned["resultFound"] = "yes"
			break

	return jsonify(dictToBeReturned)

def deleteThisParticularFilter(filterName):
	dbDataStarting = collection2.find({"users": current_user.id}, cursor_type=CursorType.EXHAUST)
	dbData = None
	for d in dbDataStarting:
		dbData = d
	if "customFilters" in dbData:
		dbData = dbData["customFilters"]
	else:
		dbData = []

	dictToBeStoredAgain = list() # All data except for the filter which needs to be deleted will be stored again
	for d in dbData:
		if d["filterName"] != filterName:
			dictToBeStoredAgain.append(d)

	collection2.update(
		{"users": current_user.id},
		{"$set" : {"customFilters": dictToBeStoredAgain}}
	)
	return "Filter Deleted"

def getAllUsernameForSharing():
	dbDataStarting = collection2.find({}, cursor_type=CursorType.EXHAUST)
	allUsernames = list()
	for d in dbDataStarting:
		allUsernames.append(d["users"])

	sendDict = dict()
	if len(allUsernames) > 0:
		sendDict["foundUsernames"] = "yes"
	else:
		sendDict["foundUsernames"] = "no"

	sendDict["usernames"] = allUsernames
	return jsonify(sendDict)


def shareToThesePeople(usernamesToBeSharedWith, filterName, pageType, recruiter, postingTitle, companyName, postingTeam, requestType, profileArchiveStatus, fromDate, toDate):
	# Redeclaring these
	filterName = filterName
	pageType = pageType
	recruiter = recruiter
	postingTitle = postingTitle
	companyName = companyName
	postingTeam = postingTeam
	requestType = requestType
	profileArchiveStatus = profileArchiveStatus
	fromDate = fromDate

	duplicateCount = 0
	successCount = 0
	resp = ""

	for us in usernamesToBeSharedWith:

		dbDataStarting = collection2.find({"users": us}, cursor_type=CursorType.EXHAUST)
		dbData = None
		for d in dbDataStarting:
			dbData = d
		if "customFilters" in dbData:
			dbData = dbData["customFilters"]
		else:
			dbData = []

		duplicateFound = False
		for dbD in dbData:
			print("This is duplicate filterName", filterName)
			if dbD["filterName"] == filterName:
				duplicateFound = True
				break

		if duplicateFound:
			resp = "No two filters can have same name"
		else:
			filtersToBeSaved = getfiltersToBeSavedReady(filterName, pageType, recruiter, postingTitle, companyName, postingTeam, requestType, profileArchiveStatus, fromDate, toDate)
			dbData.append(filtersToBeSaved)
			print("dbData before writing", dbData)
			# try:
			collection2.update(
					{"users": us},
					{"$set" : {"customFilters": dbData}}
				)
			resp = "Filter saved Successfully"
			# except:
			#     return "Some error occured while saving filter"





		if resp == "No two filters can have same name":
			duplicateCount += 1
		if resp == "Filter saved Successfully":
			successCount += 1

	resp = f"Sent to {successCount} people"
	if duplicateCount > 0:
		resp += f"\n But, Sharing with {duplicateCount} people failed due to duplicate filter names"

	return resp


@app.route('/customFilters', methods=['POST'])
@login_required
def customFilters():
	if request.method == "POST":
		filterName = request.form.get('filterName') 
		pageType = request.form.get('pageType')
		recruiter = request.form.get('recruiter')
		postingTitle = request.form.getlist('postingTitle[]')
		companyName = request.form.get('companyName')
		postingTeam = request.form.get('postingTeam')
		requestType = request.form.get('requestType')
		# postingArchiveStatus = request.form.get('postingArchiveStatus')
		profileArchiveStatus = request.form.get('profileArchiveStatus')
		fromDate = request.form.get('from')
		toDate = request.form.get('to')
		usernamesToBeSharedWith = request.form.getlist('usernamesToBeSharedWith[]')

		if requestType == "save":
			oneUser = current_user.id
			msg = saveCustomFilterPlease(oneUser, filterName, pageType, recruiter, postingTitle, companyName, postingTeam, requestType, profileArchiveStatus, fromDate, toDate)
			return msg

		if requestType == "getThoseOptions":
			return getThoseParticularOptions(filterName)

		if requestType == "delete":
			return deleteThisParticularFilter(filterName)

		if requestType == "getAllUsernameForSharing":
			return getAllUsernameForSharing()

		if requestType == "shareToThesePeople":
			return shareToThesePeople(usernamesToBeSharedWith, filterName, pageType, recruiter, postingTitle, companyName, postingTeam, requestType, profileArchiveStatus, fromDate, toDate)







@app.route('/team', methods=['GET', 'POST'])
@login_required
def team():
	if request.method == "GET":

		teamOptions = False

		if checkTeamMembership(current_user.id):
			# Do all
			adminOptions = False
			loginOption = True
			teamOptions = True

			if checkAdmin(current_user.id):
				adminOptions = True
			return render_template('teamPage.html', lastUpdated=getLastUpdatedTimestamp(), adminOptions=adminOptions, loginOption=loginOption, teamOptions=teamOptions, teamHighlight="active")
		else:
			return render_template("unauthorized.html"), 403

	# Return json data
	if request.method == "POST":
		fromDate = request.form.get('fromDate')
		toDate = request.form.get('toDate')
		requestType = request.form.get('requestType')
		originType = request.form.get('origin')

		allowedOrigins = ["referred", "agency", "applied", "sourced"]

		if requestType == "InNewApplicantStage":
			returnedDict = generateReferalDict(
				fromDate, toDate, originType, allowedOrigins)

		if requestType == "applicationToArchive":
			returnedDict = generateReferalArchivedDict(
				fromDate, toDate, originType, allowedOrigins)

		if requestType == "applicationToOffer":
			returnedDict = generateReferalOfferDict(
				fromDate, toDate, originType, allowedOrigins)

		return returnedDict


@app.route('/archivedPostings', methods=['GET'])
@login_required
def archivedPostings():

	adminOptions = False
	loginOption = True
	teamOptions = False
	if checkTeamMembership(current_user.id):
		teamOptions = True
	if checkAdmin(current_user.id):
		adminOptions = True
	returnedDict = generateMainPageDropdowns()
	return render_template('archivedPostings.html', postingDepartment=returnedDict['postingDepartment'], postingArchiveStatus=returnedDict['postingArchiveStatus'], profileArchiveStatus=returnedDict['profileArchiveStatus'], lastUpdated=getLastUpdatedTimestamp(), adminOptions=adminOptions, loginOption=loginOption, teamOptions=teamOptions, archivedPostingHighlight="active")

def generateCustomFilterNames():
	dbDataStarting = collection2.find({"users": current_user.id}, cursor_type=CursorType.EXHAUST)
	dbData = None
	for d in dbDataStarting:
		dbData = d
	if "customFilters" in dbData:
		dbData = dbData["customFilters"]
	else:
		dbData = []

	allNames = []
	for d in dbData:
		allNames.append(d["filterName"])
	return allNames


@app.route('/livePostings', methods=['GET'])
@login_required
def livePostings():
	adminOptions = False
	loginOption = True
	teamOptions = False
	if checkTeamMembership(current_user.id):
		teamOptions = True
	if checkAdmin(current_user.id):
		adminOptions = True
	returnedDict = generateMainPageDropdowns()
	customFilterNames = generateCustomFilterNames()
	return render_template('livePostings.html', postingDepartment=returnedDict['postingDepartment'], postingArchiveStatus=returnedDict['postingArchiveStatus'], profileArchiveStatus=returnedDict['profileArchiveStatus'], lastUpdated=getLastUpdatedTimestamp(), adminOptions=adminOptions, loginOption=loginOption, teamOptions=teamOptions, livePostingHighlight="active", customFilterNames=customFilterNames)


@app.route('/recruiterArchivedPostings', methods=['GET'])
@login_required
def recruiterArchivedPostings():

	adminOptions = False
	loginOption = True
	teamOptions = False
	if checkTeamMembership(current_user.id):
		teamOptions = True
	if checkAdmin(current_user.id):
		adminOptions = True
	returnedDict = generateMainPageDropdowns2('closed')
	return render_template('recruiterArchivedPostings.html', postingOwner=returnedDict['postingOwner'], lastUpdated=getLastUpdatedTimestamp(), adminOptions=adminOptions, loginOption=loginOption, teamOptions=teamOptions, recruiterLiveOrArchived="Archived postings - Recruiter filter")


@app.route('/recruiterLivePostings', methods=['GET'])
@login_required
def recruiterLivePostings():

	adminOptions = False
	loginOption = True
	teamOptions = False
	if checkTeamMembership(current_user.id):
		teamOptions = True
	if checkAdmin(current_user.id):
		adminOptions = True
	returnedDict = generateMainPageDropdowns2('active')
	return render_template('recruiterLivePostings.html', postingOwner=returnedDict['postingOwner'], lastUpdated=getLastUpdatedTimestamp(), adminOptions=adminOptions, loginOption=loginOption, teamOptions=teamOptions, recruiterLiveOrArchived="Live postings - Recruiter filter")


def checkAdmin(user):
	# Checking whether user is admin or not
	pa = collection2.find({'users': current_user.id})
	for p in pa:
		if p['type'] == 'admin':
			return True
		else:
			return False


def checkTeamMembership(user):
	# Checking whether user is admin or not
	pa = collection2.find({'users': user})
	for p in pa:
		if p['tatMember'] == 'Yeah':
			return True
		else:
			return False

# Make this function reject users who are already added
# Add a delete option as well
@app.route("/modifyUser", methods=['GET', 'POST'])
@login_required
def modifyUser():

	# Fetch users
	usersList = list()
	fetchUsers(usersList)

	print(f"Got current user iD , yeahhh!!! {current_user.id}")
	loginOption = True
	teamOptions = False

	if request.method == "GET":
		if checkTeamMembership(current_user.id):
			teamOptions = True

		if checkAdmin(current_user.id):
			return render_template("modifyUser.html", usersList=usersList, lastUpdated=getLastUpdatedTimestamp(), adminOptions=True, loginOption=loginOption, teamOptions=teamOptions, modifyUserHighlight="active")
		else:
			return render_template("unauthorized.html"), 403

	if request.method == "POST":
		# Do the insertion stuff
		if request.form.get('actionType') == "addUser":
			addThisUser = request.form.get('emailID')
			makeAdmin = request.form.get('typeOfUser')
			positionFilter = request.form.get('positionFilter')
			tatMember = request.form.get('tatmember')
			companiesToBeAllowed = request.form.getlist('companiesToBeAllowed')

			if makeAdmin == "Admin":
				if tatMember == "Nope":
					collection2.insert_one({"users": addThisUser, "type": "admin", "tatMember": "Nope",
											"companiesActuallyAllowed": companiesToBeAllowed, "whichPositions": positionFilter})
				elif tatMember == "Yeah":
					collection2.insert_one({"users": addThisUser, "type": "admin", "tatMember": "Yeah",
											"companiesActuallyAllowed": companiesToBeAllowed, "whichPositions": positionFilter})
			else:
				if tatMember == "Nope":
					collection2.insert_one({"users": addThisUser, "type": "regular", "tatMember": "Nope",
											"companiesActuallyAllowed": companiesToBeAllowed, "whichPositions": positionFilter})
				elif tatMember == "Yeah":
					collection2.insert_one({"users": addThisUser, "type": "regular", "tatMember": "Yeah",
											"companiesActuallyAllowed": companiesToBeAllowed, "whichPositions": positionFilter})
			return redirect(url_for('modifyUser'))

		if request.form.get('actionType') == "deleteUser":
			deleteThisUser = request.form.get('users')
			collection2.delete_many({"users": deleteThisUser})
			print(f"Deleted {deleteThisUser}")

		if request.form.get('actionType') == "modifyUser":
			modifyThisUser = request.form.get('users')
			hisType = request.form.get('typeData')
			hisTatMember = request.form.get('tatMemberData')
			hisWhichPositions = request.form.get('whichPositionsData')

			collection2.update({"users": modifyThisUser}, {"$set": {
				"type": hisType,
				"tatMember": hisTatMember,
				"whichPositions": hisWhichPositions
			}
			})

		return render_template("modifyUser.html", usersList=usersList, lastUpdated=getLastUpdatedTimestamp(), loginOption=loginOption)


@app.route("/docs", methods=['GET'])
@login_required
def docs():
	if request.method == "GET":
		if checkAdmin(current_user.id):
			return render_template("documentation.html")
		else:
			return render_template("unauthorized.html"), 403

# Feedback & bug central
@app.route('/bugs')
def filefeaturebugs():
	return redirect("https://docs.google.com/forms/d/e/1FAIpQLSetmFiudVkH9Ek60ZgiIpu06DCzSqqZaWcaKaFmPOyuz1OQKw/viewform", code=302)


@app.route('/bugscentral')
def featurebugscentral():
	return redirect("https://docs.google.com/spreadsheets/d/1L2Kmaq5r5YvzOErQqrefd60fJG3ko4CzpOXhUOU7Nns/edit#gid=280194824", code=302)


def fetchUsers(usersList):
	pa = collection2.find({}, cursor_type=CursorType.EXHAUST)
	for p in pa:
		print(p)
		# usersDict = dict()
		# usersDict['users'] = p['users']
		# usersDict['type'] = p['type']
		# usersDict['tatMember'] = p['tatMember']
		# if 'whichPositions' in p:
		# 	usersDict['whichPositions'] = p['whichPositions']
		# else:
		# 	usersDict['whichPositions'] = "Not defined"
		# usersList.append(usersDict)


# Make that bigDict step by step
def makeBigDict(bigDict, postDept, postTeam, postTitle):
	if postDept not in bigDict:
		bigDict[str(postDept)] = {}
	if postTeam not in bigDict[str(postDept)]:
		bigDict[str(postDept)][str(postTeam)] = []
	if 'All' not in bigDict[str(postDept)]:
		bigDict[str(postDept)]['All'] = []
	if postTitle not in bigDict[postDept][postTeam]:
		bigDict[str(postDept)][str(postTeam)].append(postTitle)
		bigDict[str(postDept)]['All'].append(postTitle)


# Helpers file
def customMessages(message):
	render_template("customMessages.html", message=message)

# Classification based on Stage in which candidate is
# For same Profile ID the no more than one entry is allowed


def addPostingToPostingDict(ro, postingDict, currentStages, postingActualOwnersDict):
	# if ro['Posting ID'] and ro['Profile ID'] is not None:
	if not isinstance(ro['Posting ID'], datetime.datetime) and not isinstance(ro['Profile ID'], datetime.datetime):
		pst = ro['Posting ID']
		prfl = ro['Profile ID']
	else:
		return

	if pst not in postingDict:
		postingDict[pst] = {}
		postingDict[pst][prfl] = ro

		# Create a new posting entry in dict
		postingActualOwnersDict[pst] = dict()
		postingActualOwnersDict[pst]["Actual Posting Owner Name"] = ro["Posting Owner Name"]
		postingActualOwnersDict[pst]["Applied At (GMT)"] = ro["Applied At (GMT)"]

	else:

		# Check posting date & if its earlier changing the Name
		if postingActualOwnersDict[pst]["Applied At (GMT)"] < ro["Applied At (GMT)"]:
			postingActualOwnersDict[pst]["Actual Posting Owner Name"] = ro["Posting Owner Name"]
			postingActualOwnersDict[pst]["Applied At (GMT)"] = ro["Applied At (GMT)"]

		if prfl not in postingDict[pst]:
			postingDict[pst][prfl] = ro

		else:
			stg1 = postingDict[pst][prfl]['Current Stage']
			stg2 = ro['Current Stage']

			# if currentStages.index(stg2) > currentStages.index(stg1):
			if ro['Max Date'] >= postingDict[pst][prfl]['Max Date']:
				postingDict[pst][prfl] = ro
			# postingDict[pst][prfl] = ro


def updateMongo():
	updatePostingInfo()
	updateDump()


def updatePostingInfo():
	client = MongoClient("mongodb://localhost:27017")
	database = client["local"]
	collection = database["jobPostingWiseDB"]

	collection.delete_many({})
	print("Deleted everything in posting info DB")
	print("Adding posting info records...")

	script_dir = os.path.dirname(__file__)  # <-- absolute dir the script is in
	data_folder = Path("/var/www/FlaskApp/FlaskApp/uploaded_csv")

	# data_folder = Path("C:\\Users\\pankaj.kum\\Desktop\\zetaDash")
	file_to_open = data_folder / "JobPostingDump.csv"

	with open(str(file_to_open), 'r', encoding="utf8") as csvfile:
		myReader = csv.reader(csvfile, delimiter=',')

		titlesWanted = ["Posting ID", "Posting Title", "Applications",
						"Date Created (GMT)", "Last Updated (GMT)", "Status", "Posting Team", "Posting Owner", "Posting Owner Email", "Posting Department", "State"]
		titles = list()
		titlesNumber = set()
		finalBox = list()
		i = 0
		ty = [0]
		for row in myReader:
			if i > 0:
				j = 0
				tempDict = dict()
				for r in row:
					if j in titlesNumber:
						# if titles[j] in ["Date Created (GMT)", "Last Updated (GMT)"]:
						#   r = getInDateFormat(r, ty)
						tempDict[titles[j]] = r
					j += 1
				finalBox.append(tempDict)
			else:
				titles = row
				for i in range(len(titles)):
					if titles[i] in titlesWanted:
						titlesNumber.add(i)

			i += 1

	collection.insert_many(finalBox)

	os.remove(file_to_open)
	print("File Deleted")

	print(ty)


def updateDump():
	client = MongoClient("mongodb://localhost:27017")
	database = client["local"]
	collection = database["dolphinDB"]

	all_The_Stages = ['Posting Archived At (GMT)', 'Created At (GMT)', 'Last Story At (GMT)', 'Last Advanced At (GMT)', 'Stage - New lead', 'Stage - Reached out', 'Stage - Responded', 'Stage - New applicant',
					  'Stage - Recruiter screen', 'Stage - Profile review', 'Stage - Case study', 'Stage - Phone interview', 'Stage - On-site interview', 'Stage - Offer', 'Stage - Offer Approval', 'Stage - Offer Approved', 'Hired']
	headers = tuple()
	line_count = 0
	dict_of_posting_creation_date = dict()
	box = []
	fileName = "uploaded_csv/dump.csv"

	collection.delete_many({})
	print("Deleted everything")
	print("Adding records...")

	# relative path inspired from here https://medium.com/@ageitgey/python-3-quick-tip-the-easy-way-to-deal-with-file-paths-on-windows-mac-and-linux-11a072b58d5f
	script_dir = os.path.dirname(__file__)  # <-- absolute dir the script is in
	data_folder = Path("/var/www/FlaskApp/FlaskApp/uploaded_csv")
	file_to_open = data_folder / "dump.csv"

	# The correcting code for Null found in csv
	fi = open(file_to_open, 'rb')
	data = fi.read()
	fi.close()
	fo = open(file_to_open, 'wb')
	fo.write(data.replace(b'\x00', b''))
	fo.close()

	with open(str(file_to_open), 'r', encoding="utf8") as csvfile:
		myReader = csv.reader(csvfile, delimiter=',')
		print("Opened file for uploading")
		for row in myReader:
			minDateCandidates = list()
			dict_to_be_written = dict()
			phoneToOnsite = False
			phoneToOffer = False
			onsiteToOffer = False
			if line_count > 0:
				# Making dict for DB

				row = [r.strip() for r in row]

				for i in range(numberOfColumns):

					# Adding column for % conversion calculation
					# Phone interview to ...
					if(row[53] != "" and (type(row[53]) is datetime.datetime or type(row[53]) is str)):
						# On-site
						if(row[54] != "" and (type(row[54]) is datetime.datetime or type(row[54]) is str)):
							phoneToOnsite = True
						else:
							phoneToOnsite = False
						# Offer
						if(row[55] != "" and (type(row[55]) is datetime.datetime or type(row[55]) is str)):
							phoneToOffer = True
						else:
							phoneToOffer = False

					# Onsite to ...
					if(row[54] != "" and (type(row[54]) is datetime.datetime or type(row[54]) is str)):
						# offer
						if(row[55] != "" and (type(row[55]) is datetime.datetime or type(row[55]) is str)):
							onsiteToOffer = True
						else:
							onsiteToOffer = False

					# Writing to dict
					dict_to_be_written['phoneToOnsite'] = phoneToOnsite
					dict_to_be_written['phoneToOffer'] = phoneToOffer
					dict_to_be_written['onsiteToOffer'] = onsiteToOffer

					# Converting date strings to datetime objects
					if headers[i] in all_The_Stages and row[i] != '':
						try:
							row[i] = datetime.datetime.strptime(
								row[i], '%Y-%m-%d %H:%M:%S')
							minDateCandidates.append(row[i])
						except:
							try:
								row[i] = datetime.datetime.strptime(
									row[i], '%d-%m-%Y %H:%M')
								minDateCandidates.append(row[i])
							except:
								try:
									row[i] = datetime.datetime.strptime(
										row[i], '%Y-%m-%d')
									minDateCandidates.append(row[i])
								except:
									try:
										row[i] = datetime.datetime.strptime(
											row[i], '%m-%d-%y %H:%M')
										minDateCandidates.append(row[i])
									except:
										try:
											row[i] = datetime.datetime.strptime(
												row[i], '%d-%m-%y %H:%M')
											minDateCandidates.append(row[i])
										except:
											print(
												f"{row[i]} is problematic -------*************-------------<<<<<")

					if row[i] == "":
						# row[i] = None
						row[i] = datetime.datetime(1990, 1, 1)

					# Deciding minimum Created date for posting
					# Note that this is actually an approximation since it finds the first applied date for a posting
					# row[21] is Created At date
					# row[24] is Posting ID
					try:
						row[22] = datetime.datetime.strptime(
							row[22], '%Y-%m-%d %H:%M:%S')
					except:
						try:
							row[22] = datetime.datetime.strptime(
								row[22], '%d-%m-%Y %H:%M')
						except:
							row[22] = row[22]
					if row[24] != "" and row[24] != None:
						if row[24] not in dict_of_posting_creation_date:
							dict_of_posting_creation_date[row[24]] = row[22]
						else:
							if dict_of_posting_creation_date[row[24]] > row[22]:
								dict_of_posting_creation_date[row[24]
															  ] = row[22]

					# Making dict entry for each column
					dict_to_be_written[headers[i]] = row[i]

				if len(minDateCandidates) > 0:
					dict_to_be_written['Min Date'] = min(minDateCandidates)
					dict_to_be_written['Max Date'] = max(minDateCandidates)
				else:
					dict_to_be_written['Min Date'] = datetime.datetime(
						2005, 12, 1)
					dict_to_be_written['Max Date'] = datetime.datetime(
						2030, 12, 1)

				box.append(dict_to_be_written)

				line_count += 1
				# print(f"Inserting: {line_count}")
				# if line_count == 3:
				#   break

			else:
				headers = tuple(row)
				numberOfColumns = len(headers)
				line_count += 1

	# Inserting the posting created date in dict
	for i in range(len(box)):
		if box[i]['Posting ID'] is not None:
			box[i]["postingCreatedDate"] = dict_of_posting_creation_date[box[i]['Posting ID']]

	# Inserting into MOngoDB
	# for di in box:
	#   collection.insert_one(di)

	postingActualOwnersDict = dict()

	# Removing duplicates & then adding to DB
	currentStages = ['New lead', 'Reached out', 'Responded', 'New applicant',   'Recruiter screen', 'Profile review',
					 'Case study', 'Phone interview', 'On-site interview', 'Offer', 'Offer Approval', 'Offer Approved']
	postingDict = {}
	for row in box:
		addPostingToPostingDict(
			row, postingDict, currentStages, postingActualOwnersDict)

	# Determining Actual Posting Owner Name before writing
	# Now fetchingActual Posting Owner Name directly from jobPostingWiseDB, we don't have to detemine that now
	jobPostingWiseDBCollection = database["jobPostingWiseDB"]
	jobPostingWiseDBBox = jobPostingWiseDBCollection.find({})
	postingActualOwnersDict2 = dict()
	for jobPostingWise in jobPostingWiseDBBox:
		if jobPostingWise["Posting ID"] not in postingActualOwnersDict2:
			postingActualOwnersDict2[jobPostingWise["Posting ID"]
									 ] = jobPostingWise["Posting Owner"]

	for x in postingDict.keys():
		for y in postingDict[x].keys():
			postingDict[x][y]["Actual Posting Owner Name"] = postingActualOwnersDict2[x]
			collection.insert_one(postingDict[x][y])

	# Compound Indexing DB
	# collection.create_index([("Posting Title", pymongo.DESCENDING)])
	collection.create_index([("Posting Department", ASCENDING), ("Posting Team", ASCENDING), (
		"Posting Title", ASCENDING), ("Actual Posting Owner Name", ASCENDING)])

	collection.create_index(
		[("Origin", DESCENDING), ("Applied At (GMT)", DESCENDING)])

	os.remove(file_to_open)
	print("File Deleted")


@app.errorhandler(404)
def page_not_found(e):
	# note that we set the 404 status explicitly
	return render_template('404.html'), 404


# Configuration
GOOGLE_CLIENT_ID = open('/etc/googleauth/googleauthid',
						'r').readlines()[0].strip()
GOOGLE_CLIENT_SECRET = open(
	'/etc/googleauth/googleauthsecret', 'r').readlines()[0].strip()
# GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", None)
# GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", None)
GOOGLE_DISCOVERY_URL = (
	"https://accounts.google.com/.well-known/openid-configuration"
)

# Flask app setup
# app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY") or os.urandom(24)

# User session management setup
# https://flask-login.readthedocs.io/en/latest
login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.unauthorized_handler
def unauthorized():
	# return render_template("unauthorized.html"), 403
	return render_template("login.html", loginOption=False)


# Naive database setup
# try:
#     init_db_command()
# except sqlite3.OperationalError:
#     # Assume it's already been created
#     pass

# OAuth2 client setup
client = WebApplicationClient(GOOGLE_CLIENT_ID)

# Flask-Login helper to retrieve a user from our db
@login_manager.user_loader
def load_user(user_id):
	return User.get(user_id)


@app.route("/settings")
@login_required
def settings():
	return "Authorized"


@app.route("/")
def index():
	if current_user.is_authenticated:
		return redirect(url_for('livePostings'))

	else:
		# return '<a class="button" href="/login">Google Login</a>'
		loginOption = False
		return render_template("login.html", loginOption=loginOption)


@app.route("/login")
def login():
	# Find out what URL to hit for Google login
	google_provider_cfg = get_google_provider_cfg()
	authorization_endpoint = google_provider_cfg["authorization_endpoint"]

	# Use library to construct the request for login and provide
	# scopes that let you retrieve user's profile from Google
	request_uri = client.prepare_request_uri(
		authorization_endpoint,
		redirect_uri=request.base_url + "/callback",
		scope=["openid", "email"],
	)
	return redirect(request_uri)


@app.route("/login/callback")
def callback():
	# Get authorization code Google sent back to you
	code = request.args.get("code")

	# Find out what URL to hit to get tokens that allow you to ask for
	# things on behalf of a user
	google_provider_cfg = get_google_provider_cfg()
	token_endpoint = google_provider_cfg["token_endpoint"]

	# Prepare and send request to get tokens! Yay tokens!
	token_url, headers, body = client.prepare_token_request(
		token_endpoint,
		authorization_response=request.url,
		redirect_url=request.base_url,
		code=code,
	)
	token_response = requests.post(
		token_url,
		headers=headers,
		data=body,
		auth=(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET),
	)

	# Parse the tokens!
	client.parse_request_body_response(json.dumps(token_response.json()))

	# Now that we have tokens (yay) let's find and hit URL
	# from Google that gives you user's profile information,
	# including their Google Profile Image and Email
	userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
	uri, headers, body = client.add_token(userinfo_endpoint)
	userinfo_response = requests.get(uri, headers=headers, data=body)

	# We want to make sure their email is verified.
	# The user authenticated with Google, authorized our
	# app, and now we've verified their email through Google!
	if userinfo_response.json().get("email_verified"):
		unique_id = userinfo_response.json()["sub"]
		users_email = userinfo_response.json()["email"]
	else:
		return "User email not available or not verified by Google.", 400

	# Create a user in our db with the information provided
	# by Google

	# Create a user in our db with the information provided
	# by Google
	user = User(
		id_=users_email
	)

	# Doesn't exist? Add to database of suspicious people
	if not User.get(users_email):
		User.suspicious(users_email)
		print("User doesn't exist")

	# Begin user session by logging the user in
	login_user(user)

	# Send user back to homepage
	return redirect(url_for("index"))


@app.route("/logout")
@login_required
def logout():
	logout_user()
	return redirect(url_for("index"))


def get_google_provider_cfg():
	return requests.get(GOOGLE_DISCOVERY_URL).json()


if __name__ == "__main__":
	app.run()
