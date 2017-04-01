#!/usr/bin/env python

import os, logging, json, datetime
import requests
import dns.resolver
from bottle import route, request, response, redirect, hook, error, default_app, view, static_file, template
from logentries import LogentriesHandler

def resolveDomain(domain, recordType, dnsAddr):
	try:
		records = []
		
		resolver = dns.resolver.Resolver()
		resolver.nameservers = dnsAddr.split(',')
		
		if recordType in appRecords:
			lookup = resolver.query(domain, recordType)
			for data in lookup:
				if recordType in ['A', 'AAAA']:
					records.append(data.address)
				elif recordType in ['TXT']:
					for rec in data.strings:
						records.append(rec)
				else:
					records.append(str(data))
		return records
	except dns.resolver.NoAnswer:
		return records
	except dns.exception.Timeout:
		return records
	except dns.resolver.NoNameservers:
		return records
		
@error('404')
@error('403')
def returnError(code, msg, contentType="text/plain"):
	response.status = int(code)
	response.content_type = contentType
	return template('error')

@hook('before_request')
def determine_content_type():
	if request.headers.get('Accept') == "application/json":
		response.content_type = 'application/json'    
	elif request.headers.get('Accept') == "text/plain":
		response.content_type = 'text/plain'

@hook('after_request')
def log_to_console():
	log.info("{} {} {}".format(
		datetime.datetime.now(),
		response.status_code,
		request.url
	))

@route('/static/<filepath:path>')
def server_static(filepath):
	return static_file(filepath, root='views/static')

@route('/version')
def return_version():
	try:
		dirname, filename = os.path.split(os.path.abspath(__file__))
		del filename
		f = open(os.getenv('VERSION_PATH', dirname + '/.git/refs/heads/master'), 'r')
		content = f.read()
		response.content_type = 'text/plain'
		return content
	except:
		return "Unable to open version file."

@route('/<record>')
@route('/<record>/<type>')
@route('/<record>/<type>.<ext>')
def loadRecord(record="", type="", ext="html"):
	try:
		if record == "" or type == "":
			raise ValueError
		if not type.upper() in appRecords:
			raise ValueError
		if not ext in ["html","txt", "text","json"]:
			ext = "html"
		if ext == "json":
			response.content_type = 'application/json'    
		elif ext in ["txt","text"]:
			response.content_type = 'text/plain'
	except ValueError:
		return returnError(404, "Not Found", "text/html")

	# We make a request to get information
	data = resolveDomain(record, type.upper(), appResolver)
	
	recSet = []
	if len(data) > 0:
		for rec in data:
			recSet.append(rec.replace('"', '').strip())
	else:
		recSet.append("Unable to identify any records with type: {}".format(type))

	content = {
		'name': record,
		'type': type.upper(),
		'records': recSet,
		'recTypes': appRecords
	}

	if ext == "json" or response.content_type == 'application/json' :
		del content['recTypes']
		
		jsonContent = {
			"results": content
		}
			
		return json.dumps(jsonContent)
	elif ext in ["txt","text"] or response.content_type == "text/plain":
		return "\r\n".join(recSet)
	else:
		return template('rec', content)

@route('/', method="POST")
def postIndex():
	
	try:
		recordName = request.forms.get('recordName')
		recordType = request.forms.get('recordType')

		if not recordType == "Type" and not recordType in appRecords:
			raise ValueError
		if recordName == "" or recordType == "Type":
			raise ValueError
		return redirect("/{}/{}".format(recordName, recordType))
	except ValueError:
		return returnError(404, "Not Found", "text/html")
	except AttributeError:
		return returnError(404, "Not Found", "text/html")

@route('/')
def index():
	content = {
		'recTypes': appRecords
	}
	return template("home", content)

if __name__ == '__main__':

	app = default_app()

	appRecords = ["A", "AAAA", "CNAME", "DS", "DNSKEY", "MX", "NS", "NSEC", "NSEC3", "RRSIG", "SOA", "TXT"]
	appResolver = os.getenv('APP_RESOLVER', '8.8.8.8')
	
	serverHost = os.getenv('IP', 'localhost')
	serverPort = os.getenv('PORT', '5000')

	# Now we're ready, so start the server
	# Instantiate the logger
	log = logging.getLogger('log')
	console = logging.StreamHandler()
	log.setLevel(logging.INFO)
	log.addHandler(console)

	if not os.getenv('LOGENTRIES_TOKEN', '') is '':
		log.addHandler(LogentriesHandler(os.getenv('LOGENTRIES_TOKEN')))
		
	# Now we're ready, so start the server
	try:
		app.run(host=serverHost, port=serverPort, server='tornado')
	except:
		log.error("Failed to start application server")