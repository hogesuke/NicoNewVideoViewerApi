from flask import Flask
import mysql.connector

app = Flask(__name__)
app.config.from_object('flaskr.config')

db_connector = mysql.connector.connect(
	user     = app.config['DB_USER'],
	password = app.config['DB_PASSWORD'],
	host     = app.config['DB_HOST'],
	database = app.config['DB_NAME'],
	charset  = app.config['DB_CHARSET'])

import flaskr.api
