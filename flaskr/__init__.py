from flask import Flask
from rauth import OAuth1Service
import mysql.connector

app = Flask(__name__)
app.config.from_object('flaskr.config')

db_connector = mysql.connector.connect(
	user     = app.config['DB_USER'],
	password = app.config['DB_PASSWORD'],
	host     = app.config['DB_HOST'],
	database = app.config['DB_NAME'],
	charset  = app.config['DB_CHARSET'])

twitter = OAuth1Service(
	name              = 'twitter',
	consumer_key      = app.config['CONSUMER_KEY'],
	consumer_secret   = app.config['CONSUMER_SECRET'],
	request_token_url = 'https://api.twitter.com/oauth/request_token',
	access_token_url  = 'https://api.twitter.com/oauth/access_token',
	authorize_url     = 'https://api.twitter.com/oauth/authenticate',
	base_url          = 'https://api.twitter.com/1.1/')

import flaskr.api
